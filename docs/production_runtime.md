# Production Runtime

Cash Machine Engine separates the web runtime from scheduled refresh execution.

## Web service

Run Flask through Gunicorn:

```bash
gunicorn --bind 0.0.0.0:${PORT:-5000} --workers ${WEB_CONCURRENCY:-1} --threads ${WEB_THREADS:-4} --timeout ${WEB_TIMEOUT:-300} web.app:app
```

Set:

```text
RUNTIME_ROLE=web
SCHEDULER_IN_PROCESS=False
```

The in-process scheduler is disabled so a production platform can run the refresh as a separate scheduled job.

## Scheduled worker

Run one synchronous refresh and exit:

```bash
python -m web.services.refresh_service --trigger scheduled
```

The command returns the crawler exit code and records the run in `refresh_runs`.

## Health check

```text
GET /health
```

The endpoint returns a small JSON payload suitable for a cloud health check.

## Production database

Production uses PostgreSQL through `DATABASE_URL`:

```text
DATABASE_URL=postgresql://user:password@host:5432/cash_machine_engine
DB_BACKEND=postgres
```

The application automatically creates the required tables and indexes on first startup.

Local development can continue using SQLite:

```text
DB_BACKEND=sqlite
CASH_MACHINE_DB_PATH=database/opportunities.db
```

### SQLite → PostgreSQL migration

To preserve the existing local opportunity history, run the migration before switching the production runtime to PostgreSQL:

```bash
python -m database.migrate_sqlite_to_postgres   --source database/opportunities.db   --dsn "$DATABASE_URL"
```

The migration preserves primary keys and resets PostgreSQL sequences so new records continue from the correct IDs.

Use `--replace` only when the target PostgreSQL database is disposable:

```bash
python -m database.migrate_sqlite_to_postgres   --source database/opportunities.db   --dsn "$DATABASE_URL"   --replace
```

Do not put `DATABASE_URL` or any credentials in Git.

## Runtime topology

```text
Web Service
    |
    +---- PostgreSQL
    |
Cron Job (07:00 Europe/Rome)
    |
    +---- PostgreSQL
```

Both runtimes use the same database and therefore see the same opportunities, analyses, evidence, decisions, lifecycle and trend history.
