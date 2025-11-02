from typing import Protocol, Sequence

class EmbedderPort(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...
