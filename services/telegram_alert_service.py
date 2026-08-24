from __future__ import annotations

import hashlib
from typing import Any

import requests

from config.settings import (
    TELEGRAM_ALERTS_ENABLED,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_MIN_CASH_SCORE,
    TELEGRAM_MIN_CONFIDENCE,
    TELEGRAM_PUBLIC_URL,
    TELEGRAM_TIMEOUT_SECONDS,
)
from database.alert_repository import AlertRepository


class TelegramAlertService:
    """Send high-signal, idempotent opportunity alerts to Telegram.

    Telegram delivery is best-effort: a notification failure must never fail
    the analysis/refresh pipeline.
    """

    API_BASE = "https://api.telegram.org"

    def __init__(self, repository: AlertRepository | None = None) -> None:
        # Reuse the pipeline's existing database connection when one is supplied.
        # This prevents a second PostgreSQL initialization (CREATE TABLE/INDEX)
        # from competing for schema locks during refresh/backfill runs.
        self.repository = repository or AlertRepository()

    @property
    def configured(self) -> bool:
        return bool(
            TELEGRAM_ALERTS_ENABLED
            and TELEGRAM_BOT_TOKEN
            and TELEGRAM_CHAT_ID
        )

    @staticmethod
    def _text(value: Any, fallback: str = "Unknown") -> str:
        text = str(value or "").strip()
        return text if text else fallback

    @staticmethod
    def _fingerprint(*parts: Any) -> str:
        raw = "|".join(str(part or "").strip() for part in parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    @classmethod
    def _should_alert(
        cls,
        analysis: dict[str, Any],
        validation: dict[str, Any],
        decision: dict[str, Any],
        previous_decision: dict[str, Any] | None,
    ) -> tuple[str | None, str]:
        # Support both the in-memory FounderDecision recommendation shape
        # (effective_decision/recommended_decision) and the persisted decision
        # row shape (decision). This keeps alert eligibility consistent for
        # pipeline runs, backfills, and direct/manual replays.
        effective = str(
            decision.get("effective_decision")
            or decision.get("recommended_decision")
            or decision.get("decision")
            or analysis.get("build_verdict")
            or analysis.get("portfolio_status")
            or "WATCH"
        ).upper()

        cash_score = int(analysis.get("cash_machine_score", 0) or 0)
        validation_score = int(validation.get("validation_score", 0) or 0)
        confidence_raw = analysis.get("confidence", 0)
        confidence = int(confidence_raw or 0)

        qualifies = (
            effective == "BUILD"
            and cash_score >= TELEGRAM_MIN_CASH_SCORE
            and confidence >= TELEGRAM_MIN_CONFIDENCE
        )
        if not qualifies:
            return None, ""

        # Alert delivery is idempotent at the repository layer. Validation is
        # informative here, not a second decision gate: the AI build verdict,
        # cash score and analysis confidence determine whether the opportunity
        # is worth interrupting the founder for. Returning an
        # alert candidate whenever the thresholds are met allows a newly
        # qualifying BUILD to notify even when the persisted decision was
        # already BUILD before the alert system saw it. The alert fingerprint
        # prevents duplicate sends when nothing materially changed.
        return "BUILD_SIGNAL", "L'opportunità ha superato le soglie per un segnale BUILD ad alta priorità."

    @staticmethod
    def _message(
        opportunity: Any,
        analysis: dict[str, Any],
        validation: dict[str, Any],
        decision: dict[str, Any],
        lifecycle: dict[str, Any],
        reason: str,
    ) -> str:
        title = TelegramAlertService._text(getattr(opportunity, "title", None))
        source = TelegramAlertService._text(getattr(opportunity, "source", None))
        cash_score = int(analysis.get("cash_machine_score", 0) or 0)
        validation_score = int(validation.get("validation_score", 0) or 0)
        confidence = int(analysis.get("confidence", 0) or 0)
        trend_score = int(analysis.get("trend_score", 0) or 0)
        decision_label = TelegramAlertService._text(
            decision.get("decision_label")
            or decision.get("effective_decision")
            or decision.get("recommended_decision")
            or decision.get("decision")
            or analysis.get("build_verdict"),
            "BUILD",
        )
        next_action = TelegramAlertService._text(
            decision.get("next_action") or analysis.get("next_action"),
            "Review the opportunity.",
        )
        lifecycle_stage = TelegramAlertService._text(
            lifecycle.get("current_label"),
            "In analisi",
        )
        lifecycle_labels = {
            "BUILDING": "In costruzione",
            "BUILDING NOW": "In costruzione",
            "ANALYZED": "Analizzata",
            "VALIDATING": "In validazione",
            "VALIDATED": "Validata",
            "WATCH": "Da monitorare",
            "SKIP": "Da scartare",
            "KILLED": "Archiviata",
        }
        lifecycle_stage = lifecycle_labels.get(lifecycle_stage.upper(), lifecycle_stage)
        problem = TelegramAlertService._text(
            analysis.get("problem"),
            "No problem summary available.",
        )
        risk = TelegramAlertService._text(
            analysis.get("biggest_risk"),
            "Unknown",
        )

        lines = [
            "🚨 <b>Segnale Cash Machine</b>",
            "",
            f"<b>{TelegramAlertService._escape_html(title)}</b>",
            f"Fonte: {TelegramAlertService._escape_html(source)}",
            "",
            f"💰 Cash Score: <b>{cash_score}/100</b>",
            f"✅ Validazione: <b>{validation_score}/100</b>",
            f"🎯 Affidabilità: <b>{confidence}/10</b>",
            f"📈 Punteggio trend: <b>{trend_score}</b>",
            f"🧠 Decisione: <b>{TelegramAlertService._escape_html(decision_label)}</b>",
            f"🔄 Ciclo: {TelegramAlertService._escape_html(lifecycle_stage)}",
            "",
            f"<b>Perché è interessante</b>\n{TelegramAlertService._escape_html(problem)}",
            "",
            f"<b>Rischio principale</b>\n{TelegramAlertService._escape_html(risk)}",
            "",
            f"<b>Prossima azione</b>\n{TelegramAlertService._escape_html(next_action)}",
            "",
            f"<i>{TelegramAlertService._escape_html(reason)}</i>",
        ]
        return "\n".join(lines)

    @staticmethod
    def _escape_html(value: str) -> str:
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _send(self, message: str, url: str | None = None) -> dict[str, Any]:
        endpoint = f"{self.API_BASE}/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload: dict[str, Any] = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if url:
            payload["reply_markup"] = {
                "inline_keyboard": [
                    [{"text": "Apri opportunità", "url": url}]
                ]
            }

        response = requests.post(
            endpoint,
            json=payload,
            timeout=TELEGRAM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        body = response.json()
        if not body.get("ok"):
            raise RuntimeError(body.get("description") or "Telegram API returned ok=false.")
        return body

    def notify(
        self,
        opportunity: Any,
        analysis: dict[str, Any],
        validation: dict[str, Any],
        decision: dict[str, Any],
        lifecycle: dict[str, Any],
        previous_decision: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.configured:
            return {"sent": False, "reason": "telegram_not_configured"}

        alert_type, reason = self._should_alert(
            analysis,
            validation,
            decision,
            previous_decision,
        )
        if not alert_type:
            return {"sent": False, "reason": "threshold_not_met"}

        opportunity_id = int(getattr(opportunity, "id"))
        current_score = int(analysis.get("cash_machine_score", 0) or 0)
        current_validation = int(validation.get("validation_score", 0) or 0)
        previous = str((previous_decision or {}).get("decision") or "NONE").upper()

        fingerprint = self._fingerprint(
            alert_type,
            previous,
            decision.get("effective_decision"),
            current_score,
            current_validation,
            analysis.get("id"),
        )
        if self.repository.exists(opportunity_id, alert_type, fingerprint):
            return {"sent": False, "reason": "duplicate"}

        message = self._message(
            opportunity,
            analysis,
            validation,
            decision,
            lifecycle,
            reason,
        )

        url = None
        if TELEGRAM_PUBLIC_URL:
            url = f"{TELEGRAM_PUBLIC_URL}/opportunities/{opportunity_id}"

        try:
            self._send(message, url=url)
        except Exception as exc:
            # Do not record failed delivery, allowing a future run to retry.
            print(f"[WARN] Telegram alert failed: {exc}")
            return {"sent": False, "reason": "delivery_failed"}

        self.repository.record(opportunity_id, alert_type, fingerprint)
        print(
            f"[INFO] Telegram alert sent for opportunity {opportunity_id} "
            f"({alert_type})."
        )
        return {
            "sent": True,
            "alert_type": alert_type,
            "fingerprint": fingerprint,
        }

    def close(self) -> None:
        self.repository.close()
