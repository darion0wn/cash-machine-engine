from database.database import Database
from models.opportunity import Opportunity


class OpportunityRepository:

    def __init__(self):
        self.db = Database()

    def save(self, opportunity: Opportunity) -> int | None:

        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO opportunities (
                source,
                title,
                url,
                article
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                opportunity.source,
                opportunity.title,
                opportunity.url,
                opportunity.article,
            ),
        )

        self.db.conn.commit()

        if cursor.rowcount == 0:
            return None

        return cursor.lastrowid