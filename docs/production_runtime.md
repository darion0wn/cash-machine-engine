# Production Runtime

Cash Machine Engine runs in production as two separate services sharing PostgreSQL:

```text
                    Render
                      |
          +-----------+-----------+
          |                       |
      Web Service             Cron Job
      Gunicorn                 3x/day
          |                       |
          +-----------+-----------+
                      |
                  PostgreSQL
```

## Web service

The web service runs:

```bash
gunicorn --bind 0.0.0.0:${PORT:-5000} --workers ${WEB_CONCURRENCY:-1} --threads ${WEB_THREADS:-4} --timeout ${WEB_TIMEOUT:-300} web.app:app
```

Production web settings:

```text
RUNTIME_ROLE=web
SCHEDULER_ENABLED=false
SCHEDULER_IN_PROCESS=false
DB_BACKEND=postgres
```

The Flask health endpoint is:

```text
GET /health
```

## Autonomous refresh

The cloud scheduler runs the existing one-shot refresh command:

```bash
python -m web.services.refresh_service --trigger scheduled
```

Render uses this cron expression as the production source of truth:

```text
0 5,11,17 * * *
```

Render cron schedules are UTC. Therefore this runs at:

- 07:00, 13:00 and 19:00 Europe/Rome during daylight-saving time (CEST)
- 06:00, 12:00 and 18:00 Europe/Rome during standard time (CET)

The Render Cron schedule is intentionally independent from the local in-process `SCHEDULER_TIMES` setting. The local setting is used only when the in-process scheduler is enabled.

The important property is that the refresh runs independently of the founder's computer, browser, VS Code, or Codespace.

## PostgreSQL

Both services point to the same managed PostgreSQL database through:

```text
DATABASE_URL
DB_BACKEND=postgres
```

The existing local SQLite database is not used by the production services.

## First deployment

1. Push this repository to the configured branch.
2. Create the Render Blueprint from `render.yaml`.
3. Enter the secret environment variables when prompted.
4. Wait for the PostgreSQL database and web service to become healthy.
5. Migrate the existing local SQLite data once:

```bash
python -m database.migrate_sqlite_to_postgres   --source database/opportunities.db   --dsn "$DATABASE_URL"
```

6. Trigger one manual production refresh and verify a successful `refresh_runs` entry.
7. Confirm the first scheduled execution from the Render Cron logs.

Do not run the SQLite-to-PostgreSQL migration automatically on every deploy; the migration script is designed as a one-time data migration and would duplicate rows on repeated deployment.

## Local development

Local development remains unchanged:

```bash
python web/app.py
```

SQLite remains the default when no PostgreSQL backend is configured.
