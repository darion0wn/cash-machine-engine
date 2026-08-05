import json

from database.database import Database
from models.opportunity import Opportunity
from models.opportunity_status import OpportunityStatus


class OpportunityRepository:

    def __init__(self):
        self.db = Database()

    def save(
        self,
        opportunity: Opportunity,
    ) -> int | None:

        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO opportunities (

                source,
                title,
                url,
                article,

                description,
                homepage,
                language,
                topics,
                license,

                stars,
                forks,
                watchers,
                open_issues,

                status

            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity.source,
                opportunity.title,
                opportunity.url,
                opportunity.article,

                opportunity.description,
                opportunity.homepage,
                opportunity.language,
                json.dumps(opportunity.topics or []),
                opportunity.license,

                opportunity.stars,
                opportunity.forks,
                opportunity.watchers,
                opportunity.open_issues,

                opportunity.status.value,
            ),
        )

        self.db.conn.commit()

        if cursor.rowcount == 0:
            return None

        return cursor.lastrowid

    def next_pending(self) -> Opportunity | None:

        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                source,
                title,
                url,
                article,

                description,
                homepage,
                language,
                topics,
                license,

                stars,
                forks,
                watchers,
                open_issues,

                status

            FROM opportunities

            WHERE status = ?

            ORDER BY id

            LIMIT 1
            """,
            (
                OpportunityStatus.PENDING.value,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return Opportunity(
            id=row[0],
            source=row[1],
            title=row[2],
            url=row[3],
            article=row[4],

            description=row[5] or "",
            homepage=row[6],
            language=row[7],
            topics=json.loads(row[8]) if row[8] else [],
            license=row[9],

            stars=row[10],
            forks=row[11],
            watchers=row[12],
            open_issues=row[13],

            status=OpportunityStatus(row[14]),
        )

    def update_status(
        self,
        opportunity_id: int,
        status: OpportunityStatus,
    ):

        cursor = self.db.conn.cursor()

        cursor.execute(
            """
            UPDATE opportunities
            SET
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                status.value,
                opportunity_id,
            ),
        )

        self.db.conn.commit()