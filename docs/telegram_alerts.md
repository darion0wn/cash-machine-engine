# Telegram Alerts

Telegram alerts are optional and best-effort. A Telegram delivery failure never
fails an opportunity analysis or a scheduled refresh.

## Environment variables

```text
TELEGRAM_ALERTS_ENABLED=true
TELEGRAM_BOT_TOKEN=<bot token>
TELEGRAM_CHAT_ID=<target chat id>
TELEGRAM_PUBLIC_URL=https://<public app domain>
TELEGRAM_MIN_CASH_SCORE=80
TELEGRAM_MIN_VALIDATION_SCORE=75
TELEGRAM_MIN_CONFIDENCE=7
TELEGRAM_TIMEOUT_SECONDS=10
```

`TELEGRAM_PUBLIC_URL` is optional on Railway. If it is omitted, the service uses
`RAILWAY_PUBLIC_DOMAIN` when available.

## What is considered alert-worthy

An opportunity is sent to Telegram when the automatic engine decision is
`BUILD` and all three thresholds are met:

- Cash Machine Score >= 80
- Validation Score >= 75
- Analysis confidence >= 7/10

The same opportunity is not repeatedly notified while it remains `BUILD`. If it
leaves `BUILD` and later re-enters `BUILD`, the alert is eligible again.

Alerts are persisted in `alert_events`, which makes delivery idempotent across
restarts and multiple refresh workers.

## Message

The bot sends a concise HTML-formatted message containing the opportunity title,
source, Cash Machine score, validation score, confidence, trend score, automatic
decision, lifecycle stage, problem summary, biggest risk and next action.

When `TELEGRAM_PUBLIC_URL` is available, the message includes an inline `Open
opportunity` URL button.

## Configure the bot

1. Create a bot with BotFather and keep the token secret.
2. Open the bot chat and send it a message such as `/start`.
3. Retrieve the chat ID using Telegram's `getUpdates` method.
4. Put the token and chat ID in the Railway service variables. Do not commit
   them to Git.
5. Set `TELEGRAM_ALERTS_ENABLED=true`.

Telegram's Bot API uses HTTPS requests to
`https://api.telegram.org/bot<token>/METHOD_NAME`; `sendMessage` accepts a
`chat_id`, formatted text and optional inline keyboard. The `getUpdates` method
can be used for development/testing when no outgoing webhook is configured.
