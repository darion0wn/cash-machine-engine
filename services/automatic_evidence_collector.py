from __future__ import annotations

import re
from typing import Any

from database.evidence_repository import EvidenceRepository


class AutomaticEvidenceCollector:
    """Collect deterministic evidence from data already gathered by the engine.

    This component never calls an LLM and never performs a second analysis. It
    converts concrete fields already present on an opportunity/analysis into
    structured evidence records that can improve validation coverage without
    pretending to prove real-world customer behaviour.
    """

    SOURCE = "engine:automatic"
    VALID_CONFIDENCE = "HIGH"
    _PRICE_PATTERN = re.compile(
        r"(?i)(?:€|eur|\$|usd|£|gbp)\s*\d+(?:[.,]\d+)?"
        r"|\d+(?:[.,]\d+)?\s*(?:€|eur|\$|usd|£|gbp)"
    )

    def __init__(self) -> None:
        self.repository = EvidenceRepository()

    @staticmethod
    def _known(value: Any) -> bool:
        if value is None:
            return False
        return str(value).strip().lower() not in {
            "",
            "unknown",
            "n/a",
            "na",
            "not available",
            "none",
        }

    @classmethod
    def _has_price(cls, value: Any) -> bool:
        return bool(cls._PRICE_PATTERN.search(str(value or "")))

    @classmethod
    def _signal(
        cls,
        key: str,
        status: str,
        observation: str,
        *,
        confidence: str = "HIGH",
        notes: str = "",
    ) -> dict[str, str]:
        return {
            "validation_key": key,
            "status": status,
            "observation": observation,
            "source": cls.SOURCE,
            "confidence": confidence,
            "notes": notes,
        }

    def collect(
        self,
        opportunity: Any,
        analysis: dict[str, Any],
    ) -> list[dict[str, str]]:
        analysis = analysis or {}
        signals: list[dict[str, str]] = []

        problem = analysis.get("problem")
        pain = int(float(analysis.get("pain_level") or 0))
        urgency = int(float(analysis.get("urgency") or 0))
        if self._known(problem) and pain > 0 and urgency > 0:
            signals.append(self._signal(
                "problem_severity",
                "PASS",
                f"The stored analysis contains a concrete problem with pain {pain}/10 and urgency {urgency}/10.",
                notes="Automatic evidence derived from completed AI analysis fields.",
            ))
        elif self._known(problem):
            signals.append(self._signal(
                "problem_severity",
                "PARTIAL",
                "A concrete problem is present in the stored analysis, but pain and urgency are incomplete.",
                notes="Automatic evidence derived from completed AI analysis fields.",
            ))

        customer = analysis.get("customer")
        ideal_customer = analysis.get("ideal_customer")
        if self._known(customer) and self._known(ideal_customer):
            signals.append(self._signal(
                "target_customer_clarity",
                "PASS",
                "Both customer and ideal-customer descriptions are explicitly present in the analysis.",
            ))
        elif self._known(customer) or self._known(ideal_customer):
            signals.append(self._signal(
                "target_customer_clarity",
                "PARTIAL",
                "A customer segment is present, but the profile is only partially specified.",
            ))

        pricing = analysis.get("pricing_strategy")
        business_model = analysis.get("business_model")
        if self._known(pricing) and self._has_price(pricing):
            signals.append(self._signal(
                "willingness_to_pay",
                "PARTIAL",
                "The stored analysis contains explicit pricing information. This supports a monetization signal but does not prove willingness to pay.",
                notes="Pricing is evidence of a price point, not evidence of customer willingness to pay.",
            ))
        elif self._known(pricing) or self._known(business_model):
            signals.append(self._signal(
                "willingness_to_pay",
                "PARTIAL",
                "A monetization model is described, but no explicit willingness-to-pay evidence is present.",
                confidence="MEDIUM",
            ))

        market_size = analysis.get("market_size")
        market_maturity = analysis.get("market_maturity")
        if self._known(market_size) and self._known(market_maturity):
            signals.append(self._signal(
                "market_size",
                "PASS",
                "Market size and market maturity are both present in the completed analysis.",
            ))
        elif self._known(market_size) or self._known(market_maturity):
            signals.append(self._signal(
                "market_size",
                "PARTIAL",
                "The analysis contains part of the market assessment, but not the full market-size/maturity context.",
                confidence="MEDIUM",
            ))

        competition = analysis.get("competition")
        competition_level = int(float(analysis.get("competition_level") or 0))
        if self._known(competition) and competition_level > 0:
            signals.append(self._signal(
                "competition",
                "PASS",
                f"Competition is described and a competition level of {competition_level}/10 is stored.",
            ))
        elif self._known(competition) or competition_level > 0:
            signals.append(self._signal(
                "competition",
                "PARTIAL",
                "The analysis contains only part of the competitive assessment.",
                confidence="MEDIUM",
            ))

        business_model = analysis.get("business_model")
        mvp_description = analysis.get("mvp_description")
        implementation = int(float(analysis.get("implementation_difficulty") or 0))
        if self._known(mvp_description) and implementation > 0:
            # This is explicitly a model-backed signal, not a real execution test.
            signals.append(self._signal(
                "time_to_mvp",
                "PARTIAL",
                "A concrete MVP description and implementation-difficulty assessment are present in the completed analysis.",
                confidence="MEDIUM",
                notes="Model-backed execution signal; no real-world build test is implied.",
            ))

        if self._known(business_model) and self._known(pricing):
            signals.append(self._signal(
                "monetization_potential",
                "PASS",
                "The analysis contains both a business model and pricing strategy.",
            ))
        elif self._known(business_model) or self._known(pricing):
            signals.append(self._signal(
                "monetization_potential",
                "PARTIAL",
                "The monetization section contains a partial business or pricing signal.",
                confidence="MEDIUM",
            ))

        source = str(getattr(opportunity, "source", "") or "")
        if source.lower() == "github":
            stars = int(getattr(opportunity, "stars", 0) or 0)
            forks = int(getattr(opportunity, "forks", 0) or 0)
            watchers = int(getattr(opportunity, "watchers", 0) or 0)
            issues = int(getattr(opportunity, "open_issues", 0) or 0)
            if stars or forks or watchers:
                signals.append(self._signal(
                    "source_adoption",
                    "PASS",
                    f"GitHub metadata records {stars} stars, {forks} forks and {watchers} watchers; open issues: {issues}.",
                    notes="Direct source metadata. This is an adoption/activity signal, not proof of willingness to pay.",
                ))

        return signals

    def persist(self, opportunity_id: int, signals: list[dict[str, str]]) -> list[int]:
        ids: list[int] = []
        for signal in signals:
            ids.append(
                self.repository.upsert_automatic(
                    opportunity_id,
                    validation_key=signal["validation_key"],
                    status=signal["status"],
                    observation=signal["observation"],
                    source=signal["source"],
                    confidence=signal["confidence"],
                    notes=signal.get("notes") or None,
                )
            )
        return ids

    def close(self) -> None:
        self.repository.close()
