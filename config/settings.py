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

MAX_ANALYSIS_PER_RUN = 3

# Runtime
RUNTIME_ROLE = os.getenv("RUNTIME_ROLE", "local").strip().lower()
SCHEDULER_IN_PROCESS = _env_bool(
    "SCHEDULER_IN_PROCESS",
    RUNTIME_ROLE in {"local", "web-local"},
)

# Daily Scheduler
SCHEDULER_ENABLED = _env_bool("SCHEDULER_ENABLED", True)
SCHEDULER_TIME = os.getenv("SCHEDULER_TIME", "07:00")
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "Europe/Rome")
SCHEDULER_CHECK_SECONDS = int(os.getenv("SCHEDULER_CHECK_SECONDS", "30"))
SCHEDULER_CATCH_UP = _env_bool("SCHEDULER_CATCH_UP", True)
