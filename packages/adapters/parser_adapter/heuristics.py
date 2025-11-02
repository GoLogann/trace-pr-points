import re
from typing import List
from packages.core.entities.pull_request import PullRequest
from packages.core.entities.functional_unit import FunctionalUnit, Evidence

PE_HINTS = [
    # Endpoints / handlers (FastAPI/Flask/Express/Gin)
    r"@app\.(get|post|put|patch|delete)\(",
    r"APIRouter\(",
    r"\brouter\.(get|post|put|patch|delete)\(",
    r"\bapp\.(get|post|put|patch|delete)\(",
    r"\br\.(GET|POST|PUT|PATCH|DELETE)\(",  # Gin
    # Jobs / batch
    r"(cron|schedule|Celery|Airflow|APScheduler)",
    # Transformação (ETL)
    r"(clean|normalize|transform|preprocess|tokeni[sz]e)"
]

# Invocar modelo (também conta como PE)
MODEL_HINTS = [
    r"\.predict\(", r"openai\.", r"anthropic\.", r"bedrock",
    r"langchain\..*(invoke|predict|stream)", r"pipeline\("
]

# AL (entidades/tabelas)
AL_HINTS = [
    r"\bCREATE\s+TABLE\b", r"\bALTER\s+TABLE\b",
    r"Column\(", r"Table\(", r"Base\s*=\s*declarative_base\(",
    r"class\s+\w+\(Base\):"
]

def _first_added_line_range(patch: str) -> tuple[int,int] | tuple[None,None]:
    if not patch: return (None, None)
    new_line = None; start = None; end = None
    for line in patch.splitlines():
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
        if m:
            new_line = int(m.group(1)); start = None; end = None
            continue
        if line.startswith('+') and not line.startswith('+++'):
            if start is None: start = new_line
            end = new_line
            new_line += 1
        elif line.startswith(' ') and new_line is not None:
            new_line += 1
    return (start, end) if start is not None else (None, None)

class HeuristicDiffParser:
    def detect_functional_units(self, pr: PullRequest) -> List[FunctionalUnit]:
        units: List[FunctionalUnit] = []
        for f in pr.files:
            patch = f.patch or ""
            # categoria
            cat = "INCL" if f.status == "added" else "EXC" if f.status == "removed" else "ALT"
            # boundary (heurística simples)
            boundary = "API" if re.search(r"\brouter\.|\bAPIRouter|\@app\.", patch) else "BATCH" if re.search(r"cron|Airflow|Celery|APScheduler", patch, re.I) else "UNKNOWN"
            # PE
            if any(re.search(p, patch) for p in PE_HINTS) or any(re.search(p, patch) for p in MODEL_HINTS):
                a,b = _first_added_line_range(patch)
                units.append(FunctionalUnit(
                    boundary=boundary, method="SFP", type="PE", category=cat,
                    evidence=Evidence(file=f.path, hunk="…", line_from=a or 0, line_to=b or 0,
                                      rationale="Endpoint/Job/Transform/Model invocation detectado")
                ))
            # AL
            if any(re.search(p, patch) for p in AL_HINTS):
                a,b = _first_added_line_range(patch)
                units.append(FunctionalUnit(
                    boundary=boundary, method="SFP", type="AL", category=cat,
                    evidence=Evidence(file=f.path, hunk="…", line_from=a or 0, line_to=b or 0,
                                      rationale="DDL/ORM detectado (entidade de dados)")
                ))
        return units
