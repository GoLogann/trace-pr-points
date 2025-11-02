# packages/core/entities/count_result.py
from dataclasses import dataclass, field
from typing import List, Optional
from packages.core.entities.functional_unit import FunctionalUnit

@dataclass
class CountTotals:
    pe_incl: int = 0
    pe_alt: int = 0
    pe_exc: int = 0
    al_incl: int = 0
    al_alt: int = 0
    al_exc: int = 0

@dataclass
class CountResult:
    repo: str
    pr_number: int
    totals: CountTotals
    units: List[FunctionalUnit] = field(default_factory=list)
    formula_text: str = ""

    total_sfp: Optional[float] = None
    total_apf: Optional[float] = None

    def total(self) -> float:
        """Retorna o total prioritário (APF se houver, senão SFP, senão 0)."""
        if self.total_apf is not None:
            return self.total_apf
        if self.total_sfp is not None:
            return self.total_sfp
        return 0.0
