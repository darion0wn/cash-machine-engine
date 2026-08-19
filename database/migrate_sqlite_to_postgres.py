from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
import os


TABLES = [
    "opportunities",
    "refresh_runs",
    "trend_snapshots",
    "favorite_opportunities",
    "validation_evidence",
    "opportunity_lifecycle",
    "founder_decisions",
    "analyses",
]

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Copy an existing Cash Machine Engine SQLite database into PostgreSQL."
    )
    parser.add_argument(
        "--source",
        default="database/opportunities.db",
        help="Path to the source SQLite database.",
    )
    parser.add_argument(
        "--dsn",
        default=os.getenv("DATABASE_URL"),
        help="PostgreSQL DSN. Defaults to DATABASE_URL.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Clear target tables before copying data.",
    )
    return parser.parse_args()


def _load_rows(sqlite_conn, table: str):
    cursor = sqlite_conn.execute(f"SELECT * FROM {table}")
    columns = [item[0] for item in cursor.description]
    rows = cursor.fetchall()
    return columns, rows


def main() -> int:
    args = _parse_args()
    if not args.dsn:
        raise SystemExit("PostgreSQL DSN is required via --dsn or DATABASE_URL.")

    source = Path(args.source).resolve()
    if not source.exists():
        raise SystemExit(f"SQLite database not found: {source}")

    import psycopg
    from database.database import Database

    # Create the production schema using the application's own schema builder.
    previous_url = os.environ.get("DATABASE_URL")
    previous_backend = os.environ.get("DB_BACKEND")
    os.environ["DATABASE_URL"] = args.dsn
    os.environ["DB_BACKEND"] = "postgres"

    try:
        production_db = Database()
        production_db.conn.close()
    finally:
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url

        if previous_backend is None:
            os.environ.pop("DB_BACKEND", None)
        else:
            os.environ["DB_BACKEND"] = previous_backend

    sqlite_conn = sqlite3.connect(source)
    pg_conn = psycopg.connect(args.dsn)

    try:
        pg_conn.autocommit = False

        if args.replace:
            with pg_conn.cursor() as cursor:
                for table in reversed(TABLES):
                    cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")

        with pg_conn.cursor() as cursor:
            for table in TABLES:
                columns, rows = _load_rows(sqlite_conn, table)
                if not rows:
                    continue

                quoted_columns = ", ".join(f'"{column}"' for column in columns)
                placeholders = ", ".join(["%s"] * len(columns))
                statement = (
                    f'INSERT INTO "{table}" ({quoted_columns}) '
                    f"VALUES ({placeholders})"
                )
                cursor.executemany(statement, rows)

                # Preserve future generated IDs after explicit historical IDs.
                cursor.execute(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', 'id'),
                        COALESCE((SELECT MAX(id) FROM "{table}"), 1),
                        (SELECT COUNT(*) > 0 FROM "{table}")
                    )
                    """
                )

        pg_conn.commit()
        print(f"Migration completed successfully: {source} -> PostgreSQL")
        return 0
    except Exception:
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
