from typing import Protocol
from packages.core.entities.count_result import CountResult

class ReportRepoPort(Protocol):
    def persist(self, result: CountResult) -> None: ...
