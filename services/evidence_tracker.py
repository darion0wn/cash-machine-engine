from __future__ import annotations

from typing import Any

from database.evidence_repository import EvidenceRepository


class EvidenceTracker:
    STATUS_SCORE = {"PASS": 10, "PARTIAL": 5, "FAIL": 0}

    def __init__(self) -> None:
        self.repository = EvidenceRepository()

    def add(self, opportunity_id: int, **payload: Any) -> int:
        return self.repository.add(opportunity_id, **payload)

    def get(self, opportunity_id: int) -> dict:
        evidence = self.repository.list_for_opportunity(opportunity_id)
        latest = self.repository.latest_by_key(opportunity_id)
        counts = self.repository.count_by_status(opportunity_id)
        return {
            "items": evidence,
            "latest_by_key": latest,
            "counts": counts,
            "total": len(evidence),
            "passed": counts["PASS"],
            "failed": counts["FAIL"],
            "partial": counts["PARTIAL"],
        }

    @classmethod
    def apply_to_validation(cls, validation: dict, latest_by_key: dict[str, dict]) -> dict:
        result = {**validation}
        dimensions = [dict(item) for item in validation.get("dimensions", [])]

        for item in dimensions:
            evidence = latest_by_key.get(item.get("key"))
            if evidence is None:
                continue
            score = cls.STATUS_SCORE[evidence["status"]]
            item["score"] = score
            item["status"] = "EVIDENCE"
            item["reason"] = f"Founder evidence recorded: {evidence['observation']}"
            item["basis"] = ["founder_evidence", evidence["validation_key"]]

        known = [item for item in dimensions if item.get("status") != "UNKNOWN"]
        evidence_items = [item for item in dimensions if item.get("status") == "EVIDENCE"]
        inference = [item for item in dimensions if item.get("status") == "INFERENCE"]
        unknown = [item for item in dimensions if item.get("status") == "UNKNOWN"]
        scores = [item["score"] for item in known if item.get("score") is not None]
        result["dimensions"] = dimensions
        result["evidence"] = evidence_items
        result["inference"] = inference
        result["unknown"] = unknown
        result["known_dimensions"] = len(known)
        result["validation_score"] = int(round(sum(scores) / len(scores) * 10)) if scores else 0
        result["coverage_score"] = int(round(len(known) / max(1, len(dimensions)) * 100))

        if result["coverage_score"] >= 80 and len(evidence_items) >= 5:
            result["confidence"] = "High"
        elif result["coverage_score"] >= 60 and len(evidence_items) >= 3:
            result["confidence"] = "Medium"
        else:
            result["confidence"] = "Low"

        if not unknown:
            result["summary"] = "Founder evidence covers all current validation dimensions."
        elif len(unknown) <= 2:
            result["summary"] = f"Founder evidence and existing analysis leave {len(unknown)} validation gap(s)."
        else:
            result["summary"] = f"Founder evidence is improving coverage, but {len(unknown)} important validation gaps remain."
        return result

    def close(self) -> None:
        self.repository.close()
