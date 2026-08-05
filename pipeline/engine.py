from database.opportunity_repository import OpportunityRepository
from models.opportunity import Opportunity


class Engine:

    def __init__(self):

        self.repository = OpportunityRepository()

    def process(
        self,
        source: str,
        title: str,
        url: str | None,
        article: str | None = None,
    ):

        opportunity = Opportunity(
            source=source,
            title=title,
            url=url,
            article=article or "",
        )

        return self.repository.save(opportunity)