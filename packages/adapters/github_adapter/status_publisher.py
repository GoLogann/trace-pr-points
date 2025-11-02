import httpx
from infra.config import settings
from packages.core.ports.status_publisher import StatusPublisherPort

API = "https://api.github.com"

class GitHubStatusPublisher(StatusPublisherPort):
    async def set_status(self, repo: str, sha: str, state: str, context: str, description: str, target_url: str | None = None):
        headers = {"Accept":"application/vnd.github+json","Authorization":f"Bearer {settings.github_token}"}
        async with httpx.AsyncClient(timeout=20) as client:
            await client.post(
                f"{API}/repos/{repo}/statuses/{sha}",
                headers=headers,
                json={
                    "state": state,                    # "pending" | "success" | "failure"
                    "context": context,                # ex.: "PRPoints/SFP"
                    "description": description[:140],
                    "target_url": target_url or settings.app_base_url
                }
            )
