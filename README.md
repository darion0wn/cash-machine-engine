# Cash Machine Engine

Cash Machine Engine is an AI Founder Workspace that helps you discover, analyze, organize and act on software opportunities worth building.

It scans public sources, enriches each opportunity with AI, scores the business case, tracks market momentum and turns the result into a decision-ready workspace.

## What it does

- Crawls opportunities from Hacker News, GitHub and Product Hunt
- Enriches each item with structured AI analysis
- Scores problem fit, market fit, execution difficulty and monetization potential
- Builds a founder-friendly dashboard, feed, trend radar, portfolio view and reports
- Highlights what to build, what to watch and what to skip

## Founder workflow

1. **Dashboard** — get an instant overview of the workspace.
2. **Feed** — review build/watch/skip opportunities.
3. **Opportunity detail** — inspect the full analysis before making a decision.
4. **Trend intelligence** — spot themes gaining momentum.
5. **Portfolio** — organize opportunities into actionable buckets.
6. **Reports** — read generated CEO-style briefs.

## Founder playbook

Use the private founder playbook when reviewing opportunities or walking through the workspace yourself.

1. **Dashboard** — see the current state of the workspace.
2. **Feed** — pick an opportunity worth exploring.
3. **Opportunity detail** — inspect the full analysis and risks.
4. **Trends** — confirm whether the market is heating up.
5. **Portfolio** — see how the ideas are bucketed.
6. **Reports** — finish with the CEO-style briefing and recommendation.

Open the dedicated playbook at `/demo`.

## Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Feed
![Feed](docs/screenshots/feed.png)

### Trends
![Trends](docs/screenshots/trends.png)

### Portfolio
![Portfolio](docs/screenshots/portfolio.png)

### Reports
![Reports](docs/screenshots/reports.png)

### Opportunity detail
![Opportunity detail](docs/screenshots/opportunity.png)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
python web/app.py
```

Open the local server at `http://127.0.0.1:5000`.

## Configuration

The web app reads a few optional environment variables:

- `APP_VERSION` — shown in the footer and About page
- `APP_COMMIT` / `GIT_COMMIT` — shown in the footer
- `BUILD_DATE` — shown in the footer
- `PORT` — Flask port
- `FLASK_DEBUG` — set to `1` for debug mode

### Automatic daily refresh

The private Founder Workspace starts an in-process scheduler when the Flask app is running.

Defaults:

- `SCHEDULER_ENABLED = True`
- `SCHEDULER_TIME = 07:00`
- `SCHEDULER_TIMEZONE = Europe/Rome`
- `SCHEDULER_CHECK_SECONDS = 30`
- `SCHEDULER_CATCH_UP = True`

The scheduler runs at most one automatic refresh per calendar day. If the app starts after the configured time and no successful refresh has happened that day, it performs a catch-up refresh automatically.

A failed scheduled run is not retried repeatedly in a tight loop. A manual refresh remains available from the Dashboard.

For local development, the scheduler can run in-process. In production, the web process keeps the scheduler disabled and a separate daily Cron Job runs:

```bash
python -m web.services.refresh_service --trigger scheduled
```

The production web service and Cron Job share the same PostgreSQL database.

## Production deployment

Production is designed as two separate services sharing PostgreSQL:

```text
Web Service
    |
    +---- PostgreSQL
    |
Cron Job (07:00 Europe/Rome)
    |
    +---- PostgreSQL
```

Set:

```text
DATABASE_URL=postgresql://...
DB_BACKEND=postgres
RUNTIME_ROLE=web
SCHEDULER_IN_PROCESS=False
```

Migrate the existing local database once before switching to production:

```bash
python -m database.migrate_sqlite_to_postgres   --source database/opportunities.db   --dsn "$DATABASE_URL"
```

Never commit database credentials or `.env` files.

## How it works

The pipeline is split into three main layers:

- **Crawler** — collects fresh opportunities from public sources
- **AI Engine** — extracts problem, market, business and evidence signals
- **Founder Workspace** — presents the information in a decision-ready UI

## Roadmap

- **Sprint 17** — founder memory, watchlists and follow-up workflows
- **Sprint 18** — notifications, compare mode and opportunity similarity
- **Sprint 19** — automated founder briefs and recurring exports

## Stack

- Python
- Flask
- PostgreSQL (production)
- SQLite (local development)
- Jinja
- Bootstrap 5
- Gemini

## License

Internal project.
