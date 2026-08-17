from pathlib import Path

from services.report_context_builder import ReportContextBuilder
from services.template_engine import TemplateEngine


ROOT_DIR = Path(__file__).resolve().parents[2]


class MarkdownReportWriter:

    def __init__(self):
        self.template_engine = TemplateEngine()
        self.context_builder = ReportContextBuilder()

    def write(self, opportunity, analysis):

        context = self.context_builder.build(
            opportunity,
            analysis,
        )

        report = self.template_engine.render(
            "templates/reports/investment_report.md",
            context,
        )

        output_dir = ROOT_DIR / "reports" / "markdown"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{analysis.opportunity_id}.md"

        output_file.write_text(
            report,
            encoding="utf-8",
        )
