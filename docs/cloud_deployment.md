# Cloud Deployment

This document describes the production runtime for Cash Machine Engine.

## Topology

```text
Cloud provider
├── Web Service
│   └── Gunicorn → Flask
├── Cron Job
│   └── python -m web.services.refresh_service --trigger scheduled
└── PostgreSQL
    ├── Web Service
    └── Cron Job
```

## Cloud deployment configuration

The repository contains a `render.yaml` Blueprint for legacy Render deployments; the active production platform can use its own service/job configuration.

It creates:

- `cash-machine-engine-web`
- `cash-machine-engine-refresh`
- `cash-machine-engine-db`

Both application services use the same PostgreSQL connection string.

The web service exposes `/health`. The health endpoint checks both the application process and database connectivity; The cloud platform should only consider the deployment healthy when both are available.

## Scheduled refresh

The production Cron/Job should run three times per day:

```text
0 5,11,17 * * *
```

If the active scheduler uses UTC, configure the three desired UTC slots.

That is approximately:

- 07:00 / 13:00 / 19:00 Europe/Rome while daylight saving time is active;
- 06:00 / 12:00 / 18:00 Europe/Rome during standard time.

This seasonal one-hour shift is intentional because the Render cron schedule is UTC.

## Analysis volume

Production currently uses:

```text
MAX_ANALYSIS_PER_RUN=10
```

With three refreshes per day, the theoretical upper bound is 30 Gemini analyses/day.

The limit is an upper bound only: the existing pipeline may analyze fewer items if fewer new eligible opportunities are available.

## Secrets

Do not commit `.env` or secret values to Git.

The deployment should provide these shared secret environment variables:

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `GITHUB_TOKEN`
- `PRODUCTHUNT_API_KEY`
- `PRODUCTHUNT_API_SECRET`

Populate these values in the active cloud platform.

## One-time data migration

The local SQLite database is intentionally excluded from the Docker image.

Before the first production run, migrate the existing local database once:

```bash
python -m database.migrate_sqlite_to_postgres   --source database/opportunities.db   --dsn "$DATABASE_URL"
```

Use the production PostgreSQL connection string from the managed database.

Do not place that connection string in Git.

Do not add the migration command to the regular deploy path: it is a one-time data migration, not a recurring startup task.

## First production smoke test

After the first deploy:

1. Open the Web Service URL.
2. Open `/health`.
3. Confirm:

```json
{
  "status": "ok",
  "database": "ok"
}
```

4. Trigger one Cron run manually.
5. Confirm a new `refresh_runs` entry.
6. Confirm the Dashboard shows the new refresh time.
7. Confirm the number of analyzed opportunities is at most `MAX_ANALYSIS_PER_RUN`.

## Ongoing operation

Once the first smoke test succeeds, the founder computer does not need to stay online.

The cloud Web Service hosts the Founder Workspace and the external refresh job runs the pipeline independently.