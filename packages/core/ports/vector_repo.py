from typing import Protocol, Sequence, TypedDict

class VectorDoc(TypedDict):
    id: str
    text: str
    metadata: dict

class VectorRepoPort(Protocol):
    def upsert(self, docs: Sequence[VectorDoc]) -> None: ...
    def search(self, query: str, filters: dict | None = None, k: int = 4) -> list[VectorDoc]: ...
