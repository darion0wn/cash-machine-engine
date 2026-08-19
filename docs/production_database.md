# Production Database

Cash Machine Engine uses SQLite for local development and PostgreSQL for production.

## Local

```text
DB_BACKEND=sqlite
CASH_MACHINE_DB_PATH=database/opportunities.db
```

## Production

Set the managed PostgreSQL connection string:

```text
DATABASE_URL=postgresql://user:password@host:5432/cash_machine_engine
DB_BACKEND=postgres
```

`DB_BACKEND` can be omitted when `DATABASE_URL` starts with `postgres://` or
`postgresql://`; PostgreSQL is selected automatically.

## Migration

The application schema is created automatically. To preserve an existing local
SQLite history, migrate it once before switching the production runtime:

```bash
python -m database.migrate_sqlite_to_postgres   --source database/opportunities.db   --dsn "$DATABASE_URL"
```

The migration preserves primary keys and resets PostgreSQL sequences so newly
generated IDs continue correctly.

Use `--replace` only against a disposable PostgreSQL database:

```bash
python -m database.migrate_sqlite_to_postgres   --source database/opportunities.db   --dsn "$DATABASE_URL"   --replace
```

Never commit `.env`, `DATABASE_URL`, or credentials.

## Runtime topology

```text
            PostgreSQL
             /                  /              Web Service   Cron Job
        Gunicorn     07:00
```

Both processes use the same PostgreSQL database, so the dashboard and scheduled
refresh operate over the same opportunities, analyses, trends, evidence,
decisions, lifecycle history and favorites.
