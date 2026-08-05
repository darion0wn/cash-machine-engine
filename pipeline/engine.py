from database.opportunity_repository import OpportunityRepository
from models.opportunity import Opportunity


class Engine:

    def __init__(self):

        self.repository = OpportunityRepository()

    def process(
        self,
        opportunity: Opportunity,
    ) -> int | None:

        return self.repository.save(opportunity)