from database.database import Database
from database.opportunity_repository import OpportunityRepository
from models.opportunity import Opportunity


class Engine:

    def __init__(self, db: Database | None = None):

        self.repository = OpportunityRepository(db=db)

    def process(
        self,
        opportunity: Opportunity,
    ) -> int | None:

        return self.repository.save(opportunity)