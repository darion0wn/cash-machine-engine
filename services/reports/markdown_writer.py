from pathlib import Path

from services.report_context_builder import ReportContextBuilder
from services.template_engine import TemplateEngine


class MarkdownReportWriter:

    def __init__(self):
        self.template_engine = TemplateEngine()
        self.context_builder = ReportContextBuilder()

    def write(self, analysis):

        context = self.context_builder.build(analysis)

        report = self.template_engine.render(
            "templates/reports/investment_report.md",
            context,
        )

        output_dir = Path("reports/markdown")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{analysis.opportunity_id}.md"

        output_file.write_text(
            report,
            encoding="utf-8",
        )