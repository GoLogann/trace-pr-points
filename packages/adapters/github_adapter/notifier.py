import httpx
from infra.config import settings
from packages.core.entities.count_result import CountResult
from packages.core.ports.notifier import NotifierPort

API = "https://api.github.com"

class GitHubNotifier(NotifierPort):
    async def post_result_comment(self, result: CountResult, explanation: str | None = None) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {settings.github_token}",
        }

        totals = result.totals
        body = (
            f"### 📏 APF (auto)\n"
            f"- **PE**: incl **{totals.pe_incl}**, alt **{totals.pe_alt}**, exc **{totals.pe_exc}**\n"
            f"- **AL**: incl **{totals.al_incl}**, alt **{totals.al_alt}**, exc **{totals.al_exc}**\n"
            f"- **Total APF**: **{result.total_apf:.2f}**\n"
            f"- Fórmula: `{result.formula_text}`\n"
        )

        # Se houver explicação detalhada, adiciona abaixo
        if explanation:
            body += f"\n---\n\n{explanation}\n"

        async with httpx.AsyncClient(timeout=20) as client:
            await client.post(
                f"{API}/repos/{result.repo}/issues/{result.pr_number}/comments",
                headers=headers,
                json={"body": body},
            )
