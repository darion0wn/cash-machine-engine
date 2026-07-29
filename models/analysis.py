from dataclasses import dataclass
from datetime import datetime

from models.investment_recommendation import InvestmentRecommendation


@dataclass
class Analysis:
    id: int | None
    opportunity_id: int

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------

    model: str
    prompt_version: str

    # -------------------------------------------------------------------------
    # Problem Analysis
    # -------------------------------------------------------------------------

    problem: str
    customer: str

    pain_level: int
    urgency: int

    current_solution: str
    why_current_solution_fails: str

    # -------------------------------------------------------------------------
    # Market Analysis
    # -------------------------------------------------------------------------

    category: str
    market_size: str
    market_maturity: str

    competition_level: int
    competition: str

    # -------------------------------------------------------------------------
    # Business Analysis
    # -------------------------------------------------------------------------

    business_model: str
    competitive_advantage: str

    implementation_difficulty: int
    monetization_difficulty: int

    # -------------------------------------------------------------------------
    # Investment Evaluation
    # -------------------------------------------------------------------------

    problem_score: int
    market_score: int
    competition_score: int
    business_score: int
    execution_score: int

    opportunity_score: int

    investment_recommendation: InvestmentRecommendation

    confidence: int
    confidence_reason: str

    # -------------------------------------------------------------------------
    # Explainability
    # -------------------------------------------------------------------------

    reasoning: str

    key_evidence: list[str]

    red_flags: list[str]

    recommended_next_steps: str

    created_at: datetime | None = None