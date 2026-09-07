from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(
    os.getenv(
        "CASH_MACHINE_DB_PATH",
        ROOT_DIR / "database" / "opportunities.db",
    )
).resolve()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DB_BACKEND = os.getenv(
    "DB_BACKEND",
    "postgres" if DATABASE_URL.startswith(("postgres://", "postgresql://")) else "sqlite",
).strip().lower()

_SCHEMA_INIT_LOCK = threading.Lock()
_SCHEMA_INITIALIZED = False
_LOCAL_ADVISORY_LOCKS: dict[str, threading.Lock] = {}
_LOCAL_ADVISORY_LOCKS_GUARD = threading.Lock()


def _postgres_params(sql: str) -> str:
    """Translate the project's SQLite-style '?' placeholders to psycopg '%s'."""
    return sql.replace("?", "%s")


class _PostgresConnection:
    """Small DB-API compatibility wrapper so existing repositories stay simple."""

    def __init__(self, dsn: str):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL support requires psycopg. "
                "Install dependencies with: pip install -r requirements.txt"
            ) from exc

        self._conn = psycopg.connect(dsn)

    def cursor(self):
        return _PostgresCursor(self._conn.cursor())

    def execute(self, sql: str, params: Any = None):
        cursor = self.cursor()
        cursor.execute(sql, params)
        return cursor

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    @property
    def closed(self):
        return self._conn.closed


class _PostgresCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql: str, params: Any = None):
        self._cursor.execute(_postgres_params(sql), params or ())
        return self

    def executemany(self, sql: str, params_seq):
        self._cursor.executemany(_postgres_params(sql), params_seq)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self):
        return self._cursor.rowcount


class Database:
    """Database facade supporting local SQLite and production PostgreSQL.

    Selection:
      - DATABASE_URL starting with postgres:// or postgresql:// -> PostgreSQL
      - DB_BACKEND=postgres -> PostgreSQL
      - otherwise -> SQLite
    """

    def __init__(self):
        if DB_BACKEND == "postgres":
            if not DATABASE_URL:
                raise RuntimeError(
                    "DB_BACKEND=postgres requires DATABASE_URL."
                )
            self.conn = _PostgresConnection(DATABASE_URL)
            self._backend = "postgres"
        elif DB_BACKEND == "sqlite":
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(DB_PATH)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self._backend = "sqlite"
        else:
            raise ValueError(
                f"Unsupported DB_BACKEND '{DB_BACKEND}'. "
                "Use 'sqlite' or 'postgres'."
            )

        self._ensure_schema()

    def _ensure_schema(self) -> None:
        global _SCHEMA_INITIALIZED

        if _SCHEMA_INITIALIZED:
            return

        with _SCHEMA_INIT_LOCK:
            if _SCHEMA_INITIALIZED:
                return

            if self._backend == "postgres":
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT pg_advisory_lock(hashtext('cash_machine_engine:schema'))"
                )
                try:
                    self.create_tables()
                    self.migrate()
                finally:
                    cursor.execute(
                        "SELECT pg_advisory_unlock(hashtext('cash_machine_engine:schema'))"
                    )
                    self.conn.commit()
            else:
                self.create_tables()
                self.migrate()

            _SCHEMA_INITIALIZED = True

    def try_advisory_lock(self, key: str) -> bool:
        key = str(key or "").strip()
        if not key:
            raise ValueError("Advisory lock key is required.")

        if self._backend == "postgres":
            row = self.conn.execute(
                "SELECT pg_try_advisory_lock(hashtext(?))",
                (key,),
            ).fetchone()
            return bool(row and row[0])

        with _LOCAL_ADVISORY_LOCKS_GUARD:
            lock = _LOCAL_ADVISORY_LOCKS.setdefault(key, threading.Lock())
        return lock.acquire(blocking=False)

    def release_advisory_lock(self, key: str) -> None:
        key = str(key or "").strip()
        if not key:
            return

        if self._backend == "postgres":
            self.conn.execute(
                "SELECT pg_advisory_unlock(hashtext(?))",
                (key,),
            ).fetchone()
            self.conn.commit()
            return

        with _LOCAL_ADVISORY_LOCKS_GUARD:
            lock = _LOCAL_ADVISORY_LOCKS.get(key)
        if lock is not None and lock.locked():
            lock.release()

    @property
    def backend(self) -> str:
        return self._backend

    def insert_returning_id(self, sql: str, params: tuple | list = ()) -> int:
        """Execute an INSERT and return its generated integer primary key."""
        if self._backend == "postgres":
            normalized = sql.strip().rstrip(";")
            if "RETURNING" not in normalized.upper():
                normalized = f"{normalized} RETURNING id"
            cursor = self.conn.cursor()
            cursor.execute(normalized, params)
            row = cursor.fetchone()
            self.conn.commit()
            if row is None:
                raise RuntimeError("INSERT did not return a generated id.")
            return int(row[0])

        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return int(cursor.lastrowid)

    def _execute_script_sqlite(self, statements: list[str]) -> None:
        cursor = self.conn.cursor()
        for statement in statements:
            cursor.execute(statement)
        self.conn.commit()

    def _create_sqlite_tables(self) -> None:
        statements = [
            """
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
            """,
            """
            CREATE TABLE IF NOT EXISTS refresh_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at DATETIME NOT NULL,
                finished_at DATETIME,
                status TEXT NOT NULL DEFAULT 'running',
                return_code INTEGER,
                message TEXT,
                trigger TEXT NOT NULL DEFAULT 'manual'
            )
            """,
            """
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
            """,
            """
            CREATE TABLE IF NOT EXISTS favorite_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER NOT NULL UNIQUE,
                saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                cash_machine_score_at_save INTEGER DEFAULT 0,
                ranking_score_at_save INTEGER DEFAULT 0,
                portfolio_status_at_save TEXT,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS validation_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER NOT NULL,
                validation_key TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PARTIAL',
                observation TEXT NOT NULL,
                source TEXT,
                confidence TEXT NOT NULL DEFAULT 'MEDIUM',
                notes TEXT,
                captured_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS opportunity_lifecycle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'founder',
                changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS founder_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER NOT NULL,
                decision TEXT NOT NULL,
                rationale TEXT NOT NULL,
                next_action TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'engine',
                decided_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS alert_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
                UNIQUE(opportunity_id, alert_type, fingerprint)
            )
            """,
            """
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
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
            )
            """,
        ]
        self._execute_script_sqlite(statements)
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_trend_snapshots_topic_time
            ON trend_snapshots(topic, captured_at)
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_validation_evidence_opportunity
            ON validation_evidence(opportunity_id, captured_at DESC)
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_validation_evidence_step
            ON validation_evidence(opportunity_id, validation_key, captured_at DESC)
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_opportunity_lifecycle_opportunity_time
            ON opportunity_lifecycle(opportunity_id, changed_at DESC, id DESC)
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_founder_decisions_opportunity
            ON founder_decisions(opportunity_id, decided_at DESC, id DESC)
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alert_events_opportunity
            ON alert_events(opportunity_id, created_at DESC)
            """
        )
        self.conn.commit()

    def _create_postgres_tables(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id BIGSERIAL PRIMARY KEY,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS refresh_runs (
                id BIGSERIAL PRIMARY KEY,
                started_at TIMESTAMP NOT NULL,
                finished_at TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'running',
                return_code INTEGER,
                message TEXT,
                trigger TEXT NOT NULL DEFAULT 'manual'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS trend_snapshots (
                id BIGSERIAL PRIMARY KEY,
                captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                topic TEXT NOT NULL,
                frequency INTEGER NOT NULL DEFAULT 0,
                source_diversity INTEGER NOT NULL DEFAULT 0,
                average_ranking DOUBLE PRECISION NOT NULL DEFAULT 0,
                average_cash DOUBLE PRECISION NOT NULL DEFAULT 0,
                trend_score DOUBLE PRECISION NOT NULL DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS favorite_opportunities (
                id BIGSERIAL PRIMARY KEY,
                opportunity_id BIGINT NOT NULL UNIQUE REFERENCES opportunities(id) ON DELETE CASCADE,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cash_machine_score_at_save INTEGER DEFAULT 0,
                ranking_score_at_save INTEGER DEFAULT 0,
                portfolio_status_at_save TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS validation_evidence (
                id BIGSERIAL PRIMARY KEY,
                opportunity_id BIGINT NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
                validation_key TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PARTIAL',
                observation TEXT NOT NULL,
                source TEXT,
                confidence TEXT NOT NULL DEFAULT 'MEDIUM',
                notes TEXT,
                captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS opportunity_lifecycle (
                id BIGSERIAL PRIMARY KEY,
                opportunity_id BIGINT NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
                stage TEXT NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'founder',
                changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS founder_decisions (
                id BIGSERIAL PRIMARY KEY,
                opportunity_id BIGINT NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
                decision TEXT NOT NULL,
                rationale TEXT NOT NULL,
                next_action TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'engine',
                decided_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS alert_events (
                id BIGSERIAL PRIMARY KEY,
                opportunity_id BIGINT NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
                alert_type TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(opportunity_id, alert_type, fingerprint)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id BIGSERIAL PRIMARY KEY,
                opportunity_id BIGINT NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        ]
        cursor = self.conn.cursor()
        for statement in statements:
            cursor.execute(statement)
        for statement in [
            "CREATE INDEX IF NOT EXISTS idx_trend_snapshots_topic_time ON trend_snapshots(topic, captured_at)",
            "CREATE INDEX IF NOT EXISTS idx_validation_evidence_opportunity ON validation_evidence(opportunity_id, captured_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_validation_evidence_step ON validation_evidence(opportunity_id, validation_key, captured_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_opportunity_lifecycle_opportunity_time ON opportunity_lifecycle(opportunity_id, changed_at DESC, id DESC)",
            "CREATE INDEX IF NOT EXISTS idx_founder_decisions_opportunity ON founder_decisions(opportunity_id, decided_at DESC, id DESC)",
            "CREATE INDEX IF NOT EXISTS idx_alert_events_opportunity ON alert_events(opportunity_id, created_at DESC)",
        ]:
            cursor.execute(statement)
        self.conn.commit()

    def create_tables(self):
        if self._backend == "sqlite":
            self._create_sqlite_tables()
        else:
            self._create_postgres_tables()

    def _sqlite_columns(self, table: str) -> set[str]:
        rows = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {row[1] for row in rows}

    def _postgres_columns(self, table: str) -> set[str]:
        rows = self.conn.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = ?
            """,
            (table,),
        ).fetchall()
        return {row[0] for row in rows}

    def migrate(self):
        """Apply additive migrations required by older project databases."""
        if self._backend == "sqlite":
            self._migrate_sqlite()
        else:
            self._migrate_postgres()

    def _migrate_sqlite(self):
        cursor = self.conn.cursor()

        refresh_run_columns = self._sqlite_columns("refresh_runs")
        if "trigger" not in refresh_run_columns:
            cursor.execute(
                "ALTER TABLE refresh_runs ADD COLUMN trigger TEXT NOT NULL DEFAULT 'manual'"
            )

        columns = self._sqlite_columns("opportunities")
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
                cursor.execute(f"ALTER TABLE opportunities ADD COLUMN {column} {definition}")

        if "status" not in columns:
            cursor.execute("ALTER TABLE opportunities ADD COLUMN status TEXT DEFAULT 'PENDING'")
        if "updated_at" not in columns:
            cursor.execute("ALTER TABLE opportunities ADD COLUMN updated_at DATETIME")
            cursor.execute("UPDATE opportunities SET updated_at = CURRENT_TIMESTAMP")

        analysis_columns = self._sqlite_columns("analyses")
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
            "trend_score": "INTEGER DEFAULT 0",
            "ranking_score": "INTEGER DEFAULT 0",
            "portfolio_status": "TEXT DEFAULT 'WATCH'",
        }
        for column, definition in analysis_migrations.items():
            if column not in analysis_columns:
                cursor.execute(f"ALTER TABLE analyses ADD COLUMN {column} {definition}")

        self.conn.commit()

    def _migrate_postgres(self):
        cursor = self.conn.cursor()

        refresh_run_columns = self._postgres_columns("refresh_runs")
        if "trigger" not in refresh_run_columns:
            cursor.execute(
                "ALTER TABLE refresh_runs ADD COLUMN trigger TEXT NOT NULL DEFAULT 'manual'"
            )

        columns = self._postgres_columns("opportunities")
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
                cursor.execute(f"ALTER TABLE opportunities ADD COLUMN {column} {definition}")
        if "status" not in columns:
            cursor.execute(
                "ALTER TABLE opportunities ADD COLUMN status TEXT DEFAULT 'PENDING'"
            )
        if "updated_at" not in columns:
            cursor.execute(
                "ALTER TABLE opportunities ADD COLUMN updated_at TIMESTAMP"
            )
            cursor.execute(
                "UPDATE opportunities SET updated_at = CURRENT_TIMESTAMP "
                "WHERE updated_at IS NULL"
            )

        analysis_columns = self._postgres_columns("analyses")
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
            "trend_score": "INTEGER DEFAULT 0",
            "ranking_score": "INTEGER DEFAULT 0",
            "portfolio_status": "TEXT DEFAULT 'WATCH'",
        }
        for column, definition in analysis_migrations.items():
            if column not in analysis_columns:
                cursor.execute(f"ALTER TABLE analyses ADD COLUMN {column} {definition}")

        self.conn.commit()
