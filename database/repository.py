from database.database import Database
from models.opportunity import Opportunity


class OpportunityRepository:

    def __init__(self):
        self.db = Database()

    def save(self, opportunity: Opportunity, article: str = "") -> bool:
        return self.db.save(opportunity, article)