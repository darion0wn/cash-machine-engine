from dataclasses import dataclass
from typing import Optional


@dataclass
class Opportunity:
    source: str
    title: str
    url: Optional[str]

    problem: Optional[str] = None
    customer: Optional[str] = None

    pain_level: Optional[int] = None
    market_size: Optional[str] = None

    opportunity_score: Optional[int] = None