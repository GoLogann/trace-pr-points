from packages.core.entities.functional_unit import FunctionalUnit
from packages.core.entities.count_result import CountResult, CountTotals

# Pesos IFPUG (CPM 4.3.1)
W_TX = {
    "EE":  {"L": 3, "A": 4, "H": 6},
    "SE":  {"L": 4, "A": 5, "H": 7},
    "CE":  {"L": 3, "A": 4, "H": 6},
}
W_DADOS = {
    "ALI": {"L": 7, "A": 10, "H": 15},
    "AIE": {"L": 5, "A": 7,  "H": 10},
}

def _complex_tx(u: FunctionalUnit) -> str:
    # Regras simplificadas baseadas em CPM:
    # EE: L se DET<=4 e FTR<=1; A se (DET 5-15) ou FTR==2; H se DET>=16 ou FTR>=3
    # SE: L se DET<=5 e FTR<=1; A se (DET 6-19) ou FTR in {2,3}; H se DET>=20 ou FTR>=4
    # CE: L se DET<=4 e FTR<=1; A se (DET 5-19) ou FTR in {2,3}; H se DET>=20 ou FTR>=4
    det, ftr = u.det, u.ftr
    if u.type == "EE":
        if det <= 4 and ftr <= 1: return "L"
        if det >= 16 or ftr >= 3: return "H"
        return "A"
    if u.type == "SE":
        if det <= 5 and ftr <= 1: return "L"
        if det >= 20 or ftr >= 4: return "H"
        return "A"
    if u.type == "CE":
        if det <= 4 and ftr <= 1: return "L"
        if det >= 20 or ftr >= 4: return "H"
        return "A"
    return "L"

def _complex_dados(u: FunctionalUnit) -> str:
    # ILF/EIF (ALI/AIE) – heurística:
    # L se RET==1 e DET 1-19; A se RET 2-5 e DET 20-50; H se RET>=6 ou DET>=51
    det, ret = u.det, u.ret
    if ret <= 1 and det <= 19: return "L"
    if ret >= 6 or det >= 51:  return "H"
    return "A"

class APFCalculator:
    def compute_apf(self, repo: str, pr_number: int, units: list[FunctionalUnit]) -> CountResult:
        totals = CountTotals()
        total_apf = 0.0
        parts: list[str] = []

        for u in units:
            # Distribuir nos totais existentes (reutilize campos do CountTotals alterando nomenclatura)
            if u.type in {"EE", "SE", "CE"}:
                # Transacionais = "PE" no seu CountTotals; guardamos por categoria
                if u.category == "INCL":
                    totals.pe_incl += 1
                elif u.category == "ALT":
                    totals.pe_alt += 1
                elif u.category == "EXC":
                    totals.pe_exc += 1

                cx = _complex_tx(u)
                w = W_TX[u.type][cx]
            else:
                # Dados = "AL" no seu CountTotals; guardamos por categoria
                if u.category == "INCL":
                    totals.al_incl += 1
                elif u.category == "ALT":
                    totals.al_alt += 1
                elif u.category == "EXC":
                    totals.al_exc += 1

                cx = _complex_dados(u)
                w = W_DADOS[u.type][cx]

            total_apf += w

            parts.append(f"{u.type}[{cx}:{w}]")

        formula = f"APF = " + " + ".join(parts) + f" = {total_apf:.2f}"
        return CountResult(
            repo=repo,
            pr_number=pr_number,
            totals=totals,
            total_apf=total_apf,
            formula_text=formula,
            units=units,
        )
