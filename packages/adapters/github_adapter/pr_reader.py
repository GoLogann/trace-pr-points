from __future__ import annotations
import os, requests
from dataclasses import dataclass
from typing import List

from infra.config import settings
from packages.core.entities.pull_request import PullRequest, FileChange
from packages.core.ports.pr_reader import PRReaderPort

GITHUB_API = os.getenv("GITHUB_API_BASE", "https://api.github.com")

@dataclass
class GitHubPRReader(PRReaderPort):
    token: str = settings.github_token
    base_url: str = GITHUB_API
    timeout: int = 30

    def _headers(self) -> dict:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}" if self.token else "",
            "User-Agent": "pr-points-saas",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get_json(self, path: str):
        url = f"{self.base_url}{path}"
        r = requests.get(url, headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def read(self, repo: str, pr_number: int) -> PullRequest:
        """
        Lê metadados da PR e pagina os arquivos (per_page=100) retornando patches quando disponíveis.
        """
        # 1) metadata da PR
        pr = self._get_json(f"/repos/{repo}/pulls/{pr_number}")
        head_sha = pr.get("head", {}).get("sha", "")
        base_sha = pr.get("base", {}).get("sha", "")
        title = pr.get("title", "") or ""
        html_url = pr.get("html_url", "") or ""

        # 2) arquivos paginados
        files: List[FileChange] = []
        page = 1
        while True:
            arr = self._get_json(f"/repos/{repo}/pulls/{pr_number}/files?per_page=100&page={page}")
            if not arr:
                break
            for it in arr:
                files.append(
                    FileChange(
                        path=it.get("filename", ""),
                        status=it.get("status", ""),
                        patch=it.get("patch") or ""  # pode ser None p/ binários ou diffs grandes
                    )
                )
            if len(arr) < 100:
                break
            page += 1

        # log mínimo (opcional)
        print(f"Fetched PR {pr_number} from {repo} with {len(files)} files")
        print(f"PR title: {title}")

        return PullRequest(
            repo=repo,
            number=pr_number,
            head_sha=head_sha,
            files=files,
            title=title,
            base_sha=base_sha,
            html_url=html_url,
        )

    # Aliases para compatibilidade retroativa, se existir código chamando:
    def fetch(self, repo: str, pr_number: int) -> PullRequest:
        return self.read(repo, pr_number)

    def get(self, repo: str, pr_number: int) -> PullRequest:
        return self.read(repo, pr_number)
