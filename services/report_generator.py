from services.reports.markdown_writer import MarkdownReportWriter


class ReportGenerator:

    def __init__(self):
        self.markdown_writer = MarkdownReportWriter()

    def generate(self, opportunity, analysis):
        self.markdown_writer.write(opportunity, analysis)