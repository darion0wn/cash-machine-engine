import sqlite3
from pathlib import Path

DB_PATH = Path("database/opportunities.db")


class Database:

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()
        self.migrate()

    def create_tables(self):

        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT UNIQUE,

            article TEXT,

            description TEXT,

            homepage TEXT,

            language TEXT,

            topics TEXT,

            license TEXT,

            stars INTEGER DEFAULT 0,

            forks INTEGER DEFAULT 0,

            watchers INTEGER DEFAULT 0,

            open_issues INTEGER DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'PENDING',

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            opportunity_id INTEGER NOT NULL,

            model TEXT NOT NULL,
            prompt_version TEXT NOT NULL,

            problem TEXT NOT NULL,
            customer TEXT NOT NULL,
            pain_level INTEGER NOT NULL,
            urgency INTEGER NOT NULL,
            current_solution TEXT NOT NULL,
            why_current_solution_fails TEXT NOT NULL,

            category TEXT NOT NULL,
            market_size TEXT NOT NULL,
            market_maturity TEXT NOT NULL,
            competition_level INTEGER NOT NULL,
            competition TEXT NOT NULL,

            business_model TEXT NOT NULL,
            competitive_advantage TEXT NOT NULL,
            implementation_difficulty INTEGER NOT NULL,
            monetization_difficulty INTEGER NOT NULL,

            problem_score INTEGER NOT NULL,
            market_score INTEGER NOT NULL,
            competition_score INTEGER NOT NULL,
            business_score INTEGER NOT NULL,
            execution_score INTEGER NOT NULL,

            opportunity_score INTEGER NOT NULL,
            investment_recommendation TEXT NOT NULL,

            confidence INTEGER NOT NULL,
            confidence_reason TEXT NOT NULL,

            reasoning TEXT NOT NULL,
            key_evidence TEXT NOT NULL,
            red_flags TEXT NOT NULL,
            recommended_next_steps TEXT NOT NULL,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (opportunity_id)
                REFERENCES opportunities(id)
                ON DELETE CASCADE
        )
        """)

        self.conn.commit()

    def migrate(self):

        cursor = self.conn.cursor()

        cursor.execute(
            "PRAGMA table_info(opportunities)"
        )

        columns = {
            row[1]
            for row in cursor.fetchall()
        }

        migrations = {
            "description": "TEXT",
            "homepage": "TEXT",
            "language": "TEXT",
            "topics": "TEXT",
            "license": "TEXT",
            "stars": "INTEGER DEFAULT 0",
            "forks": "INTEGER DEFAULT 0",
            "watchers": "INTEGER DEFAULT 0",
            "open_issues": "INTEGER DEFAULT 0",
        }

        for column, definition in migrations.items():

            if column not in columns:

                cursor.execute(
                    f"""
                    ALTER TABLE opportunities
                    ADD COLUMN {column} {definition}
                    """
                )

        if "status" not in columns:

            cursor.execute(
                """
                ALTER TABLE opportunities
                ADD COLUMN status TEXT
                DEFAULT 'PENDING'
                """
            )

        if "updated_at" not in columns:

            cursor.execute(
                """
                ALTER TABLE opportunities
                ADD COLUMN updated_at DATETIME
                """
            )

            cursor.execute(
                """
                UPDATE opportunities
                SET updated_at = CURRENT_TIMESTAMP
                """
            )

        self.conn.commit()