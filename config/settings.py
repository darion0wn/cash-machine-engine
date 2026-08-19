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

MAX_ANALYSIS_PER_RUN = 10

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
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "Europe/Rome")
SCHEDULER_CHECK_SECONDS = int(os.getenv("SCHEDULER_CHECK_SECONDS", "30"))
SCHEDULER_CATCH_UP = _env_bool("SCHEDULER_CATCH_UP", True)
