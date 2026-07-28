from dataclasses import dataclass
from datetime import datetime


@dataclass
class Analysis:
    id: int | None
    opportunity_id: int

    model: str
    prompt_version: str

    problem: str
    customer: str

    pain_level: int
    market_size: str
    opportunity_score: int

    created_at: datetime | None = None