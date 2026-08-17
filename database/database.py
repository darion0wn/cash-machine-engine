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

            website_text TEXT,

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
        CREATE TABLE IF NOT EXISTS refresh_runs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            started_at DATETIME NOT NULL,

            finished_at DATETIME,

            status TEXT NOT NULL DEFAULT 'running',

            return_code INTEGER,

            message TEXT,

            trigger TEXT NOT NULL DEFAULT 'manual'
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trend_snapshots (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            captured_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

            topic TEXT NOT NULL,

            frequency INTEGER NOT NULL DEFAULT 0,

            source_diversity INTEGER NOT NULL DEFAULT 0,

            average_ranking REAL NOT NULL DEFAULT 0,

            average_cash REAL NOT NULL DEFAULT 0,

            trend_score REAL NOT NULL DEFAULT 0
        )
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_trend_snapshots_topic_time
        ON trend_snapshots(topic, captured_at)
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorite_opportunities (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            opportunity_id INTEGER NOT NULL UNIQUE,

            saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            cash_machine_score_at_save INTEGER DEFAULT 0,

            ranking_score_at_save INTEGER DEFAULT 0,

            portfolio_status_at_save TEXT,

            FOREIGN KEY (opportunity_id)
                REFERENCES opportunities(id)
                ON DELETE CASCADE
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
            ideal_customer TEXT,

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
            pricing_strategy TEXT,

            competitive_advantage TEXT NOT NULL,

            mvp_description TEXT,

            implementation_difficulty INTEGER NOT NULL,
            monetization_difficulty INTEGER NOT NULL,

            problem_score INTEGER NOT NULL,
            market_score INTEGER NOT NULL,
            competition_score INTEGER NOT NULL,
            business_score INTEGER NOT NULL,
            execution_score INTEGER NOT NULL,

            ai_leverage_score INTEGER DEFAULT 0,
            distribution_score INTEGER DEFAULT 0,

            cash_machine_score INTEGER DEFAULT 0,

            opportunity_score INTEGER NOT NULL,

            build_verdict TEXT,

            investment_recommendation TEXT NOT NULL,

            confidence INTEGER NOT NULL,
            confidence_reason TEXT NOT NULL,

            reasoning TEXT NOT NULL,

            key_evidence TEXT NOT NULL,

            red_flags TEXT NOT NULL,

            biggest_risk TEXT,

            next_action TEXT,

            recommended_next_steps TEXT NOT NULL,

            topics TEXT NOT NULL DEFAULT '[]',

            trend_score INTEGER DEFAULT 0,

            ranking_score INTEGER DEFAULT 0,

            portfolio_status TEXT DEFAULT 'WATCH',

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (opportunity_id)
                REFERENCES opportunities(id)
                ON DELETE CASCADE
        )
        """)

        self.conn.commit()

    def migrate(self):

        cursor = self.conn.cursor()

        # ---------------------------------------------------------
        # Refresh runs
        # ---------------------------------------------------------

        cursor.execute(
            "PRAGMA table_info(refresh_runs)"
        )

        refresh_run_columns = {
            row[1]
            for row in cursor.fetchall()
        }

        if "trigger" not in refresh_run_columns:

            cursor.execute(
                "ALTER TABLE refresh_runs "
                "ADD COLUMN trigger TEXT NOT NULL DEFAULT 'manual'"
            )

        # ---------------------------------------------------------
        # Opportunities
        # ---------------------------------------------------------

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
            "website_text": "TEXT",
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

        # ---------------------------------------------------------
        # Analyses
        # ---------------------------------------------------------

        cursor.execute(
            "PRAGMA table_info(analyses)"
        )

        analysis_columns = {
            row[1]
            for row in cursor.fetchall()
        }

        analysis_migrations = {
            "ideal_customer": "TEXT",
            "pricing_strategy": "TEXT",
            "mvp_description": "TEXT",
            "ai_leverage_score": "INTEGER DEFAULT 0",
            "distribution_score": "INTEGER DEFAULT 0",
            "cash_machine_score": "INTEGER DEFAULT 0",
            "build_verdict": "TEXT",
            "biggest_risk": "TEXT",
            "next_action": "TEXT",
            "topics": "TEXT NOT NULL DEFAULT '[]'",
        }

        for column, definition in analysis_migrations.items():

            if column not in analysis_columns:

                cursor.execute(
                    f"""
                    ALTER TABLE analyses
                    ADD COLUMN {column} {definition}
                    """
                )

        cursor.execute(
            "PRAGMA table_info(analyses)"
        )

        columns = {
            row[1]
            for row in cursor.fetchall()
        }

        migrations = {
            "trend_score": "INTEGER DEFAULT 0",
            "ranking_score": "INTEGER DEFAULT 0",
            "portfolio_status": "TEXT DEFAULT 'WATCH'",
        }

        for column, definition in migrations.items():

            if column not in columns:

                cursor.execute(
                    f"""
                    ALTER TABLE analyses
                    ADD COLUMN {column} {definition}
                    """
                )

        self.conn.commit()