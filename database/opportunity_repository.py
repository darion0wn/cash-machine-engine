import json

from database.database import Database
from models.opportunity import Opportunity
from models.opportunity_status import OpportunityStatus


class OpportunityRepository:

    def __init__(self, db: Database | None = None):
        self.db = db or Database()
        self._owns_db = db is None

    def exists(
        self,
        opportunity: Opportunity,
    ) -> bool:

        cursor = self.db.conn.cursor()

        if opportunity.url:

            cursor.execute(
                """
                SELECT 1
                FROM opportunities
                WHERE source = ?
                  AND url = ?
                LIMIT 1
                """,
                (
                    opportunity.source,
                    opportunity.url,
                ),
            )

        else:

            cursor.execute(
                """
                SELECT 1
                FROM opportunities
                WHERE source = ?
                  AND title = ?
                LIMIT 1
                """,
                (
                    opportunity.source,
                    opportunity.title,
                ),
            )

        return cursor.fetchone() is not None

    def save(
        self,
        opportunity: Opportunity,
    ) -> int | None:

        if self.exists(opportunity):
            return None

        return self.db.insert_returning_id(
            """
            INSERT INTO opportunities (

                source,
                title,
                url,
                article,

                description,
                homepage,
                website_text,

                language,
                topics,
                license,

                stars,
                forks,
                watchers,
                open_issues,

                status

            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity.source,
                opportunity.title,
                opportunity.url,
                opportunity.article,

                opportunity.description,
                opportunity.homepage,
                opportunity.website_text,

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

    def next_pending(
        self,
    ) -> Opportunity | None:

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
                website_text,

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
            website_text=row[7] or "",

            language=row[8],
            topics=json.loads(row[9]) if row[9] else [],
            license=row[10],

            stars=row[11],
            forks=row[12],
            watchers=row[13],
            open_issues=row[14],

            status=OpportunityStatus(row[15]),
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
    def close(self):
        if self._owns_db:
            self.db.conn.close()
