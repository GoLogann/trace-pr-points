from packages.core.ports.pr_reader import PRReaderPort
from packages.core.ports.diff_parser import DiffParserPort
from packages.core.ports.calculator import CalculatorPort
from packages.core.ports.notifier import NotifierPort
from packages.core.ports.baseline_repo import BaselineRepoPort
from packages.core.ports.report_repo import ReportRepoPort
from packages.core.ports.status_publisher import StatusPublisherPort

class CountPR:
    def __init__(self, pr_reader: PRReaderPort, parser: DiffParserPort, calculator: CalculatorPort,
                 notifier: NotifierPort, baseline_repo: BaselineRepoPort, report_repo: ReportRepoPort,
                 status_pub: StatusPublisherPort | None = None):
        self.pr_reader, self.parser, self.calculator = pr_reader, parser, calculator
        self.notifier, self.baseline_repo, self.report_repo = notifier, baseline_repo, report_repo
        self.status_pub = status_pub

    async def execute(self, repo: str, number: int):
        pr = await self.pr_reader.get_pull_request(repo, number)

        if self.status_pub:
            await self.status_pub.set_status(repo, pr.head_sha, "pending", "PRPoints/SFP", "Calculando SFP…")

        units = self.parser.detect_functional_units(pr)
        result = self.calculator.compute_sfp(repo, number, units)

        # persist relatório + baseline
        self.report_repo.persist(result)
        current = self.baseline_repo.get(repo, "SFP")
        updated = self.baseline_repo.apply_from_result(current, result)
        self.baseline_repo.upsert(updated)

        # comenta na PR
        await self.notifier.post_result_comment(result)

        if self.status_pub:
            await self.status_pub.set_status(repo, pr.head_sha, "success", "PRPoints/SFP", f"{result.total_sfp:.2f} SFP")

        return result
