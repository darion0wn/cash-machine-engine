from dataclasses import dataclass
from datetime import datetime


@dataclass
class Analysis:
    id: int | None
    opportunity_id: int

    # Metadata
    model: str
    prompt_version: str

    # Problem Analysis
    problem: str
    customer: str
    pain_level: int
    urgency: int
    current_solution: str
    why_current_solution_fails: str

    # Market Analysis
    category: str
    market_size: str
    market_maturity: str
    competition_level: int
    competition: str

    # Business Analysis
    business_model: str
    competitive_advantage: str
    implementation_difficulty: int
    monetization_difficulty: int

    # Opportunity Analysis
    confidence: int
    opportunity_score: int
    reasoning: str
    red_flags: str
    next_steps: str

    created_at: datetime | None = None