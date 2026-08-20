from __future__ import annotations

from types import SimpleNamespace

from config.settings import (
    TELEGRAM_ALERTS_ENABLED,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from services.telegram_alert_service import TelegramAlertService


def main() -> int:
    if not TELEGRAM_ALERTS_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "Telegram alerts are not fully configured. "
            "Set TELEGRAM_ALERTS_ENABLED=true, TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
        )
        return 2

    service = TelegramAlertService()
    try:
        result = service._send(
            "<b>Cash Machine Engine Telegram Test</b>\\n\\n"
            "Telegram delivery is configured correctly."
        )
        print({"sent": bool(result.get("ok"))})
        return 0 if result.get("ok") else 1
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
