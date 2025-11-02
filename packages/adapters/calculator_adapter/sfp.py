from packages.core.entities.functional_unit import FunctionalUnit
from packages.core.entities.count_result import CountResult, CountTotals

PE_WEIGHT = 4.6
AL_WEIGHT = 7.0
FI_ALT    = 0.47   # fator de impacto para alterados
K_EXC     = 0.32   # coeficiente para excluídos

class SFPCalculator:
    def compute_sfp(self, repo: str, pr_number: int, units: list[FunctionalUnit]) -> CountResult:
        totals = CountTotals()
        for u in units:
            if u.type == "PE":
                if u.category == "INCL": totals.pe_incl += 1
                elif u.category == "ALT": totals.pe_alt += 1
                elif u.category == "EXC": totals.pe_exc += 1
            elif u.type == "AL":
                if u.category == "INCL": totals.al_incl += 1
                elif u.category == "ALT": totals.al_alt += 1
                elif u.category == "EXC": totals.al_exc += 1

        incl = PE_WEIGHT*totals.pe_incl + AL_WEIGHT*totals.al_incl
        alt  = FI_ALT*(PE_WEIGHT*totals.pe_alt + AL_WEIGHT*totals.al_alt)
        exc  = K_EXC*(PE_WEIGHT*totals.pe_exc + AL_WEIGHT*totals.al_exc)
        total = incl + alt + exc
        formula = f"SFP = INCL({incl:.2f}) + FI*ALT({alt:.2f}) + Kexc*EXC({exc:.2f}) | FI={FI_ALT}, Kexc={K_EXC}, PE={PE_WEIGHT}, AL={AL_WEIGHT}"
        return CountResult(repo=repo, pr_number=pr_number, totals=totals, total_sfp=total, formula_text=formula, units=units)
