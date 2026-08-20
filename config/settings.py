import os


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# AI Configuration

AI_PROVIDER = "gemini"

AI_MODEL = "gemini-3.6-flash"

PROMPT_VERSION = "v3"

MAX_STORIES = 100

MAX_ANALYSIS_PER_RUN = int(os.getenv("MAX_ANALYSIS_PER_RUN", "10"))

# Runtime
RUNTIME_ROLE = os.getenv("RUNTIME_ROLE", "local").strip().lower()
SCHEDULER_IN_PROCESS = _env_bool(
    "SCHEDULER_IN_PROCESS",
    RUNTIME_ROLE in {"local", "web-local"},
)

# Daily Scheduler
SCHEDULER_ENABLED = _env_bool("SCHEDULER_ENABLED", True)
def _env_times(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [value.strip() for value in raw.split(",") if value.strip()]


SCHEDULER_TIMES = _env_times(
    "SCHEDULER_TIMES",
    "07:00,13:00,19:00",
)

# Backwards-compatible single-time setting for the legacy in-process
# scheduler. Production scheduling is handled by Railway Cron.
SCHEDULER_TIME = SCHEDULER_TIMES[0] if SCHEDULER_TIMES else "07:00"

SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "Europe/Rome")
SCHEDULER_CHECK_SECONDS = int(os.getenv("SCHEDULER_CHECK_SECONDS", "30"))
SCHEDULER_CATCH_UP = _env_bool("SCHEDULER_CATCH_UP", True)


# Telegram Alerts
TELEGRAM_ALERTS_ENABLED = _env_bool("TELEGRAM_ALERTS_ENABLED", False)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
_telegram_public_url = os.getenv("TELEGRAM_PUBLIC_URL", "").strip().rstrip("/")
if not _telegram_public_url:
    _railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if _railway_public_domain:
        _telegram_public_url = f"https://{_railway_public_domain}"
TELEGRAM_PUBLIC_URL = _telegram_public_url
TELEGRAM_MIN_CASH_SCORE = int(os.getenv("TELEGRAM_MIN_CASH_SCORE", "80"))
TELEGRAM_MIN_VALIDATION_SCORE = int(
    os.getenv("TELEGRAM_MIN_VALIDATION_SCORE", "75")
)
TELEGRAM_MIN_CONFIDENCE = int(os.getenv("TELEGRAM_MIN_CONFIDENCE", "7"))
TELEGRAM_TIMEOUT_SECONDS = float(os.getenv("TELEGRAM_TIMEOUT_SECONDS", "10"))
