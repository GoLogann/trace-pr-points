from typing import Protocol

class StatusPublisherPort(Protocol):
    async def set_status(self, repo: str, sha: str, state: str, context: str, description: str, target_url: str | None = None) -> None: ...
