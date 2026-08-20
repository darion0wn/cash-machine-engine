from __future__ import annotations

import json
import urllib.request

from config.settings import (
    TELEGRAM_ALERTS_ENABLED,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TIMEOUT_SECONDS,
)


def main() -> int:
    if not TELEGRAM_ALERTS_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "Telegram alerts are not fully configured. "
            "Set TELEGRAM_ALERTS_ENABLED=true, TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
        )
        return 2

    endpoint = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": (
            "<b>Cash Machine Engine Telegram Test</b>\\n\\n"
            "Telegram delivery is configured correctly."
        ),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=TELEGRAM_TIMEOUT_SECONDS,
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"Telegram test failed: {exc}")
        return 1

    print({"sent": bool(body.get("ok"))})
    if not body.get("ok"):
        print(body.get("description") or "Telegram API returned ok=false.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
