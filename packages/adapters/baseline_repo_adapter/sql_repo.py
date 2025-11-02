import time
from dataclasses import asdict
from sqlalchemy.orm import Session
from infra.config import settings
from infra.db.sql import make_engine, make_session_factory
from infra.db.models import BaselineModel, PRReportModel
from packages.core.entities.baseline import Baseline
from packages.core.entities.count_result import CountResult
from packages.core.ports.baseline_repo import BaselineRepoPort
from packages.core.ports.report_repo import ReportRepoPort

_engine = make_engine(settings.database_url)
_Session = make_session_factory(_engine)

class SQLBaselineRepo(BaselineRepoPort):
    def get(self, app_id: str, method: str) -> Baseline | None:
        with _Session() as s:
            row = s.get(BaselineModel, {"app_id": app_id, "method": method})
            if not row:
                return None
            return Baseline(app_id=row.app_id, method=row.method, value=row.value, release=row.release)

    def upsert(self, baseline: Baseline) -> None:
        with _Session() as s:
            row = s.get(BaselineModel, {"app_id": baseline.app_id, "method": baseline.method})
            if not row:
                row = BaselineModel(
                    app_id=baseline.app_id,
                    method=baseline.method,
                    value=baseline.value,
                    release=baseline.release,
                )
                s.add(row)
            else:
                row.value = baseline.value
                row.release = baseline.release
            s.commit()

    def apply_from_result(self, baseline: Baseline | None, result: CountResult) -> Baseline:
        """Atualiza baseline conforme o método:
        - APF: soma direta do total APF do PR
        - SFP: regra antiga (incl - exc com pesos fixos)
        """
        prev = baseline.value if baseline else 0.0

        if getattr(result, "total_apf", None) is not None:
            # >>> baseline para APF
            return Baseline(
                app_id=result.repo,
                method="APF",
                value=max(prev + float(result.total_apf), 0.0),
                release=None,
            )

        # >>> fallback: baseline para SFP (regra antiga)
        incl = 4.6 * result.totals.pe_incl + 7.0 * result.totals.al_incl
        exc  = 4.6 * result.totals.pe_exc  + 7.0 * result.totals.al_exc
        return Baseline(
            app_id=result.repo,
            method="SFP",
            value=max(prev + incl - exc, 0.0),
            release=None,
        )

class SQLReportRepo(ReportRepoPort):
    def persist(self, r: CountResult) -> None:
        with _Session() as s:
            total_apf = getattr(r, "total_apf", None)
            total_sfp = getattr(r, "total_sfp", None)

            # Para compatibilidade com relatórios legados que leem total_sfp,
            # gravamos um fallback: APF se existir; senão SFP; senão 0.
            legacy_total = float(total_apf if total_apf is not None else (total_sfp or 0.0))

            row = PRReportModel(
                repo=r.repo,
                pr_number=r.pr_number,
                ts=int(time.time()),
                total_sfp=legacy_total,        # mantém dashboards antigos funcionando
                total_apf=total_apf,           # grava o APF “oficial”
                formula=r.formula_text,
                totals={
                    "pe_incl": r.totals.pe_incl, "pe_alt": r.totals.pe_alt, "pe_exc": r.totals.pe_exc,
                    "al_incl": r.totals.al_incl, "al_alt": r.totals.al_alt, "al_exc": r.totals.al_exc,
                },
                units=[
                    (
                        u.evidence.__dict__
                        | {"type": u.type, "category": u.category, "boundary": u.boundary}
                    )
                    for u in r.units
                ],
            )
            s.add(row)
            s.commit()
