from dataclasses import dataclass
from typing import List, Optional

@dataclass
class FileChange:
    path: str
    status: str  # "added" | "modified" | "removed" | ...
    patch: Optional[str] = ""

@dataclass
class PullRequest:
    repo: str
    number: int
    head_sha: str
    files: List[FileChange]
    title: str = ""
    base_sha: str = ""
    html_url: str = ""
