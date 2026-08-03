from database.analysis_repository import AnalysisRepository
from database.opportunity_repository import OpportunityRepository
from services.analyzer import Analyzer
from services.report_generator import ReportGenerator


class Engine:

    def __init__(self):
        self.analyzer = Analyzer()
        self.opportunity_repository = OpportunityRepository()
        self.analysis_repository = AnalysisRepository()
        self.report_generator = ReportGenerator()

    def process(
        self,
        source: str,
        title: str,
        url: str | None,
        article: str | None = None,
    ):

        opportunity, analysis = self.analyzer.analyze(
            source=source,
            title=title,
            url=url,
            article=article,
        )

        opportunity_id = self.opportunity_repository.save(opportunity)

        if opportunity_id is None:
            return None

        analysis.opportunity_id = opportunity_id

        self.analysis_repository.save(analysis)

        self.report_generator.generate(
            opportunity,
            analysis,
        )

        return opportunity_id