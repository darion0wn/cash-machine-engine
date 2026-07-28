from services.analyzer import Analyzer
from database.repository import OpportunityRepository


class Engine:

    def __init__(self):
        self.analyzer = Analyzer()
        self.repository = OpportunityRepository()

    def process(self, source: str, title: str, url: str | None):

        opportunity, article = self.analyzer.analyze(
            source=source,
            title=title,
            url=url,
        )

        inserted = self.repository.save(
            opportunity,
            article,
        )

        return inserted