from typing import Protocol, List
from packages.core.entities.pull_request import PullRequest
from packages.core.entities.functional_unit import FunctionalUnit

class DiffParserPort(Protocol):
    def detect_functional_units(self, pr: PullRequest) -> List[FunctionalUnit]: ...
