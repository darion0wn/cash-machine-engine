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
- SQLite
- Jinja
- Bootstrap 5
- Gemini

## License

Internal project.
