import sqlite3
from pathlib import Path

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

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
            market_size TEXT NOT NULL,
            opportunity_score INTEGER NOT NULL,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (opportunity_id)
                REFERENCES opportunities(id)
        )
        """)

        self.conn.commit()