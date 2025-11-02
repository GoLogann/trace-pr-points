from abc import ABC, abstractmethod
from packages.core.entities.pull_request import PullRequest

class PRReaderPort(ABC):
    @abstractmethod
    def read(self, repo: str, pr_number: int) -> PullRequest:
        """Lê a PR e retorna PullRequest com arquivos e patches."""
        raise NotImplementedError