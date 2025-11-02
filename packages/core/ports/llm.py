from typing import Protocol

class LLMPort(Protocol):
    def complete(self, prompt: str) -> str: ...
