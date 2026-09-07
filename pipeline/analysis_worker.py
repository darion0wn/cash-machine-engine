from database.analysis_repository import AnalysisRepository
from database.database import Database
from database.opportunity_repository import OpportunityRepository
from models.opportunity_status import OpportunityStatus
from services.analyzer import Analyzer
from services.report_generator import ReportGenerator
from services.ranking_engine import RankingEngine
from services.autonomous_opportunity_pipeline import AutonomousOpportunityPipeline


class AnalysisWorker:

    def __init__(self):

        self.analyzer = Analyzer()

        self.db = Database()
        self.opportunity_repository = OpportunityRepository(db=self.db)

        self.analysis_repository = AnalysisRepository(db=self.db)

        self.report_generator = ReportGenerator()

        self.ranking_engine = RankingEngine()

    def run_once(self):

        opportunity = self.opportunity_repository.next_pending()

        if opportunity is None:

            print("[INFO] No pending opportunities.")

            return None

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

            try:
                autonomous = AutonomousOpportunityPipeline.process(
                    opportunity,
                    analysis,
                    db=self.db,
                )
                if autonomous.get("skipped"):
                    print("[INFO] Autonomous post-processing skipped: " + str(autonomous.get("reason")))
                else:
                    print(
                        "[INFO] Autonomous evidence, validation, decision and "
                        "lifecycle synchronized: "
                        f"{autonomous['decision']['effective_decision']}"
                    )
            except Exception as automation_error:
                # The AI analysis remains a valid completed analysis even if
                # supporting automation has a transient persistence problem.
                # The error is logged so the refresh can finish and retrying
                # the analysis itself is avoided.
                print(
                    "[WARN] Autonomous opportunity post-processing failed: "
                    f"{automation_error}"
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

    def close(self):
        self.db.conn.close()
