from typing import Protocol
from packages.core.entities.count_result import CountResult

class NotifierPort(Protocol):
    async def post_result_comment(self, result: CountResult) -> None: ...
