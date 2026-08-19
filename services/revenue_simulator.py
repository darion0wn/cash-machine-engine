from __future__ import annotations

import math
import re
from typing import Any


class RevenueSimulator:
    """
    Deterministic €500/month planning simulator for the private founder workspace.

    The simulator separates:
      - explicit pricing evidence from the analysis;
      - mathematical customer-count paths when the price is EUR;
      - planning scenarios that are useful for validation but are NOT forecasts.

    It never invents an FX rate and never presents customer acquisition as a
    probability without real evidence.
    """

    TARGET_MRR = 500.0
    PLANNING_CUSTOMER_TARGETS = (5, 10, 20, 30, 50)

    _RANGE_PATTERNS = (
        re.compile(r"(?i)(?:€|eur)\s*(\d+(?:[.,]\d+)?)\s*(?:-|–|to)\s*(?:€|eur)?\s*(\d+(?:[.,]\d+)?)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)"),
        re.compile(r"(?i)(?:\$|usd)\s*(\d+(?:[.,]\d+)?)\s*(?:-|–|to)\s*(?:\$|usd)?\s*(\d+(?:[.,]\d+)?)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)"),
        re.compile(r"(?i)(?:£|gbp)\s*(\d+(?:[.,]\d+)?)\s*(?:-|–|to)\s*(?:£|gbp)?\s*(\d+(?:[.,]\d+)?)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)"),
    )

    _MONTHLY_PATTERNS = (
        re.compile(r"(?i)(?:€|eur\s*)(\d+(?:[.,]\d+)?)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)"),
        re.compile(r"(?i)(?:\$|usd\s*)(\d+(?:[.,]\d+)?)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)"),
        re.compile(r"(?i)(?:£|gbp\s*)(\d+(?:[.,]\d+)?)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)"),
        re.compile(r"(?i)\b(\d+(?:[.,]\d+)?)\s*(?:€|eur)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)"),
        re.compile(r"(?i)\b(\d+(?:[.,]\d+)?)\s*(?:\$|usd|£|gbp)\s*(?:/|per\s+)?(?:mo(?:nth)?|month)"),
    )

    @staticmethod
    def _currency(text: str) -> str:
        lowered = text.lower()
        if "€" in text or "eur" in lowered:
            return "EUR"
        if "$" in text or "usd" in lowered:
            return "USD"
        if "£" in text or "gbp" in lowered:
            return "GBP"
        return ""

    @classmethod
    def _extract_price(cls, pricing_strategy: str | None) -> dict[str, Any]:
        text = str(pricing_strategy or "").strip()
        if not text:
            return {
                "known": False,
                "low": None,
                "high": None,
                "currency": None,
                "evidence": None,
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
                    "currency": cls._currency(match.group(0)),
                    "evidence": match.group(0),
                }

        for pattern in cls._MONTHLY_PATTERNS:
            match = pattern.search(text)
            if match:
                price = float(match.group(1).replace(",", "."))
                return {
                    "known": price > 0,
                    "low": price if price > 0 else None,
                    "high": price if price > 0 else None,
                    "currency": cls._currency(match.group(0)),
                    "evidence": match.group(0),
                }

        return {
            "known": False,
            "low": None,
            "high": None,
            "currency": None,
            "evidence": None,
        }

    @staticmethod
    def _price_label(currency: str, value: float) -> str:
        symbol = {"EUR": "€", "USD": "$", "GBP": "£"}.get(currency, currency + " ")
        return f"{symbol}{value:g}/month"

    @classmethod
    def _eur_price_points(cls, low: float, high: float) -> list[float]:
        if low <= 0:
            return []
        if math.isclose(low, high):
            candidates = [low]
        else:
            midpoint = (low + high) / 2
            candidates = [low, midpoint, high]

        deduped: list[float] = []
        for value in candidates:
            rounded = round(value, 2)
            if rounded > 0 and all(not math.isclose(rounded, existing) for existing in deduped):
                deduped.append(rounded)
        return deduped[:3]

    @classmethod
    def _planning_scenarios(cls, currency: str | None, prices: list[float]) -> list[dict[str, Any]]:
        clean_prices = [price for price in prices if price and price > 0]
        if not clean_prices:
            return []

        scenarios: list[dict[str, Any]] = []
        for price in clean_prices:
            for customers in cls.PLANNING_CUSTOMER_TARGETS:
                scenarios.append(
                    {
                        "price": price,
                        "price_label": cls._price_label(currency or "", price),
                        "customers": customers,
                        "monthly_revenue": round(price * customers, 2),
                        "monthly_revenue_label": cls._price_label(currency or "", price * customers).replace(
                            "/month", ""
                        ),
                        "target_reached": currency == "EUR" and price * customers >= cls.TARGET_MRR,
                    }
                )
        return scenarios

    @classmethod
    def simulate(cls, analysis: dict[str, Any] | None) -> dict[str, Any]:
        pricing = cls._extract_price((analysis or {}).get("pricing_strategy"))
        validation = (analysis or {}).get("validation") or {}
        validation_score = int(validation.get("validation_score") or 0)
        coverage_score = int(validation.get("coverage_score") or 0)

        if not pricing["known"]:
            return {
                "target_mrr": cls.TARGET_MRR,
                "pricing_known": False,
                "pricing_currency": None,
                "pricing_evidence": None,
                "monthly_price_low": None,
                "monthly_price_high": None,
                "mathematical_path": "Cannot calculate a customer path until monthly pricing is explicit.",
                "customers_required": None,
                "customers_required_min": None,
                "customers_required_max": None,
                "planning_scenarios": [],
                "planning_note": "No pricing forecast is shown because the analysis does not contain explicit monthly pricing.",
                "readiness": "EARLY",
                "readiness_reason": "Pricing must be validated before a €500/month path can be quantified.",
            }

        currency = pricing["currency"]
        low = pricing["low"]
        high = pricing["high"]

        exact_customers = None
        mathematical_path = ""
        planning_prices = [low]

        customers_required_min = None
        customers_required_max = None

        if currency == "EUR":
            customers_at_low = max(1, int(math.ceil(cls.TARGET_MRR / high)))
            customers_at_high = max(1, int(math.ceil(cls.TARGET_MRR / low)))
            customers_required_min = customers_at_low
            customers_required_max = customers_at_high
            exact_customers = customers_at_low if math.isclose(low, high) else None
            if math.isclose(low, high):
                price_label = cls._price_label(currency, low)
                mathematical_path = (
                    f"{price_label} → about {customers_at_low} customer"
                    f"{'s' if customers_at_low != 1 else ''} for the €{int(cls.TARGET_MRR)}/month target."
                )
            else:
                price_label = f"€{low:g}–€{high:g}/month"
                mathematical_path = (
                    f"{price_label} → roughly {customers_at_low}–{customers_at_high} customers "
                    f"for the €{int(cls.TARGET_MRR)}/month target, depending on the chosen price point."
                )
                midpoint = round((low + high) / 2, 2)
                planning_prices = [low, midpoint, high]
        else:
            mathematical_path = (
                f"Pricing evidence is available in {currency}, but the €{int(cls.TARGET_MRR)}/month customer count cannot be calculated without an explicit FX source."
            )

        planning_scenarios = cls._planning_scenarios(currency, planning_prices)
        readiness_score = min(100, int(round((validation_score * 0.6) + (coverage_score * 0.4))))
        if readiness_score >= 75:
            readiness = "STRONGER CASE"
        elif readiness_score >= 55:
            readiness = "DEVELOPING"
        else:
            readiness = "EARLY"

        readiness_reason = (
            f"Planning readiness uses the current validation evidence ({validation_score}/100 validation score, {coverage_score}% coverage); it is not a forecast of customer acquisition."
        )

        return {
            "target_mrr": cls.TARGET_MRR,
            "pricing_known": True,
            "pricing_currency": currency,
            "pricing_evidence": pricing["evidence"],
            "monthly_price_low": low,
            "monthly_price_high": high,
            "mathematical_path": mathematical_path,
            "customers_required": exact_customers,
            "customers_required_min": customers_required_min,
            "customers_required_max": customers_required_max,
            "planning_scenarios": planning_scenarios,
            "planning_note": "Planning scenarios show what revenue looks like at selected customer counts; they are not acquisition forecasts.",
            "readiness": readiness,
            "readiness_reason": readiness_reason,
        }
