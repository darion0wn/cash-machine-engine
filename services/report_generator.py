from services.reports.markdown_writer import MarkdownReportWriter


class ReportGenerator:

    def __init__(self):

        self.markdown = MarkdownReportWriter()

    def generate(self, analysis):

        self.markdown.write(analysis)