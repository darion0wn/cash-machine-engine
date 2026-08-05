from database.analysis_repository import AnalysisRepository
from database.opportunity_repository import OpportunityRepository
from models.opportunity_status import OpportunityStatus
from services.analyzer import Analyzer
from services.report_generator import ReportGenerator
from services.ranking_engine import RankingEngine

class AnalysisWorker:

    def __init__(self):

        self.analyzer = Analyzer()

        self.opportunity_repository = OpportunityRepository()

        self.analysis_repository = AnalysisRepository()

        self.report_generator = ReportGenerator()

        self.ranking_engine = RankingEngine()

    def run_once(self):

        opportunity = (
            self.opportunity_repository.next_pending()
        )

        if opportunity is None:

            print("[INFO] No pending opportunities.")

            return False

        print(
            f"[INFO] Processing: {opportunity.title}"
        )

        self.opportunity_repository.update_status(
            opportunity.id,
            OpportunityStatus.PROCESSING,
        )

        try:

            _, analysis = self.analyzer.analyze(
                opportunity
            )

            analysis.opportunity_id = opportunity.id

            analysis = self.ranking_engine.calculate(
                analysis
            )

            self.analysis_repository.save(
                analysis
            )

            self.report_generator.generate(
                opportunity,
                analysis,
            )

            self.opportunity_repository.update_status(
                opportunity.id,
                OpportunityStatus.DONE,
            )

            print(
                f"[ OK ] Done: {opportunity.title}"
            )

            return True

        except Exception as e:

            self.opportunity_repository.update_status(
                opportunity.id,
                OpportunityStatus.FAILED,
            )

            print(e)

            return False