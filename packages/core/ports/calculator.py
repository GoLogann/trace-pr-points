from typing import Protocol
from packages.core.entities.functional_unit import FunctionalUnit
from packages.core.entities.count_result import CountResult

class CalculatorPort(Protocol):
    def compute_sfp(self, repo: str, pr_number: int, units: list[FunctionalUnit]) -> CountResult: ...
