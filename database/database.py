import sqlite3
from pathlib import Path

from models.opportunity import Opportunity

DB_PATH = Path("database/opportunities.db")


class Database:

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()

    def create_tables(self):

        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT UNIQUE,

            article TEXT,

            problem TEXT,
            customer TEXT,

            pain_level INTEGER,
            market_size TEXT,
            opportunity_score INTEGER,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()

    def save(self, opportunity: Opportunity, article: str = ""):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO opportunities (
                source,
                title,
                url,
                article,
                problem,
                customer,
                pain_level,
                market_size,
                opportunity_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity.source,
                opportunity.title,
                opportunity.url,
                article,
                opportunity.problem,
                opportunity.customer,
                opportunity.pain_level,
                opportunity.market_size,
                opportunity.opportunity_score,
            ),
        )

        self.conn.commit()

        return cursor.rowcount > 0