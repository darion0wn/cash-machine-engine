from __future__ import annotations

import math
import re
from typing import Any


class DecisionEngine:
    """
    Deterministic decision layer focused on the private €500/month target.

    It does not overwrite the existing AI/ranking verdict. It adds a second,
    founder-oriented interpretation based only on fields already present in
    the analysis.
    """

    TARGET_MRR = 500.0

    _MONTHLY_PATTERNS = (
        re.compile(
            r"(?i)(?:€|eur\s*)\s*(\d+(?:[.,]\d+)?)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)",
        ),
        re.compile(
            r"(?i)(?:\$|usd\s*)\s*(\d+(?:[.,]\d+)?)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)",
        ),
        re.compile(
            r"(?i)(?:£|gbp\s*)\s*(\d+(?:[.,]\d+)?)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)",
        ),
        re.compile(
            r"(?i)\b(\d+(?:[.,]\d+)?)\s*(?:€|eur)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)",
        ),
        re.compile(
            r"(?i)\b(\d+(?:[.,]\d+)?)\s*(?:\$|usd|£|gbp)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)",
        ),
    )

    _RANGE_PATTERNS = (
        re.compile(
            r"(?i)(?:€|eur\s*)\s*(\d+(?:[.,]\d+)?)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(?:€|eur)?\s*(?:/|per\s+)?(?:mo(?:nth)?|month)",
        ),
        re.compile(
            r"(?i)(?:\$|usd\s*)\s*(\d+(?:[.,]\d+)?)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(?:\$|usd)?\s*(?:/|per\s+)?(?:mo(?:nth)?|month)",
        ),
        re.compile(
            r"(?i)(?:£|gbp\s*)\s*(\d+(?:[.,]\d+)?)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(?:£|gbp)?\s*(?:/|per\s+)?(?:mo(?:nth)?|month)",
        ),
    )

    @staticmethod
    def _number(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _extract_monthly_price(cls, pricing_strategy: str | None) -> dict[str, Any]:
        text = (pricing_strategy or "").strip()

        if not text:
            return {
                "known": False,
                "low": None,
                "high": None,
                "currency": None,
                "source": None,
            }

        for pattern in cls._RANGE_PATTERNS:
            match = pattern.search(text)
            if match:
                low = float(match.group(1).replace(",", "."))
                high = float(match.group(2).replace(",", "."))
                return {
                    "known": low > 0 and high > 0,
                    "low": min(low, high),
                    "high": max(low, high),
                    "currency": cls._currency_from_text(match.group(0)),
                    "source": match.group(0),
                }

        for pattern in cls._MONTHLY_PATTERNS:
            match = pattern.search(text)
            if match:
                price = float(match.group(1).replace(",", "."))
                return {
                    "known": price > 0,
                    "low": price if price > 0 else None,
                    "high": price if price > 0 else None,
                    "currency": cls._currency_from_text(match.group(0)),
                    "source": match.group(0),
                }

        return {
            "known": False,
            "low": None,
            "high": None,
            "currency": None,
            "source": None,
        }

    @staticmethod
    def _currency_from_text(text: str) -> str:
        lowered = text.lower()
        if "€" in text or "eur" in lowered:
            return "EUR"
        if "$" in text or "usd" in lowered:
            return "USD"
        if "£" in text or "gbp" in lowered:
            return "GBP"
        return ""

    @staticmethod
    def _score(analysis: dict[str, Any]) -> int:
        problem = DecisionEngine._number(analysis.get("problem_score"))
        market = DecisionEngine._number(analysis.get("market_score"))
        business = DecisionEngine._number(analysis.get("business_score"))
        execution_difficulty = DecisionEngine._number(
            analysis.get("implementation_difficulty")
        )
        competition_level = DecisionEngine._number(
            analysis.get("competition_level")
        )
        monetization_difficulty = DecisionEngine._number(
            analysis.get("monetization_difficulty")
        )
        distribution = DecisionEngine._number(
            analysis.get("distribution_score")
        )

        score = (
            problem * 10 * 0.20
            + market * 10 * 0.15
            + business * 10 * 0.15
            + max(0.0, 10.0 - execution_difficulty) * 10 * 0.15
            + max(0.0, 10.0 - competition_level) * 10 * 0.10
            + max(0.0, 10.0 - monetization_difficulty) * 10 * 0.10
            + distribution * 10 * 0.15
        )

        return int(round(max(0.0, min(100.0, score))))

    @classmethod
    def evaluate(cls, analysis: dict[str, Any] | None) -> dict[str, Any]:
        if not analysis:
            return {
                "target_mrr": cls.TARGET_MRR,
                "decision_score": 0,
                "decision_label": "NO DATA",
                "five_hundred_path": "No analysis available yet.",
                "pricing_known": False,
                "monthly_price_low": None,
                "monthly_price_high": None,
                "customers_required": None,
                "customers_required_label": "Unknown",
                "pricing_evidence": None,
                "potential": "Unknown",
                "confidence": "Low",
                "reasoning": "A decision assessment requires a completed analysis.",
            }

        pricing = cls._extract_monthly_price(
            analysis.get("pricing_strategy")
        )
        score = cls._score(analysis)

        status = str(
            analysis.get("portfolio_status")
            or analysis.get("build_verdict")
            or "WATCH"
        ).upper()

        if pricing["known"]:
            customers_required = int(
                math.ceil(cls.TARGET_MRR / pricing["low"])
            )
            if pricing["low"] >= cls.TARGET_MRR:
                customers_required = 1

            if pricing["low"] == pricing["high"]:
                price_label = (
                    f"{pricing['currency'] or 'currency'} "
                    f"{pricing['low']:g}/month"
                )
            else:
                price_label = (
                    f"{pricing['currency'] or 'currency'} "
                    f"{pricing['low']:g}–{pricing['high']:g}/month"
                )

            path = (
                f"{price_label} → about {customers_required} "
                f"customer{'s' if customers_required != 1 else ''} "
                f"for €{int(cls.TARGET_MRR)}/month target"
            )
        else:
            customers_required = None
            path = (
                "Pricing is not explicit enough in the source analysis "
                "to calculate a reliable €500/month customer path."
            )

        if score >= 75 and pricing["known"] and customers_required <= 25:
            potential = "HIGH"
        elif score >= 60 or pricing["known"]:
            potential = "MEDIUM"
        else:
            potential = "LOW"

        if status == "BUILD" and score >= 70:
            label = "BUILD CANDIDATE"
        elif status == "WATCH":
            label = "VALIDATE"
        else:
            label = "WATCH"

        reasons = [
            f"Founder decision score: {score}/100.",
            f"Existing portfolio status: {status}.",
        ]

        if pricing["known"]:
            reasons.append(
                f"Pricing evidence supports a concrete customer-count path."
            )
        else:
            reasons.append(
                "Pricing evidence is insufficient, so monetization still needs validation."
            )

        return {
            "target_mrr": cls.TARGET_MRR,
            "decision_score": score,
            "decision_label": label,
            "five_hundred_path": path,
            "pricing_known": pricing["known"],
            "monthly_price_low": pricing["low"],
            "monthly_price_high": pricing["high"],
            "pricing_currency": pricing["currency"],
            "customers_required": customers_required,
            "customers_required_label": (
                str(customers_required)
                if customers_required is not None
                else "Unknown"
            ),
            "pricing_evidence": pricing["source"],
            "potential": potential,
            "confidence": (
                "High"
                if pricing["known"] and score >= 75
                else "Medium"
                if score >= 60 or pricing["known"]
                else "Low"
            ),
            "reasoning": " ".join(reasons),
            "next_action": (
                analysis.get("next_action")
                or "Validate the weakest decision signal with real users."
            ),
        }
