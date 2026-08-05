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
    ideal_customer: str

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
    pricing_strategy: str

    competitive_advantage: str

    mvp_description: str

    implementation_difficulty: int
    monetization_difficulty: int

    # -------------------------------------------------------------------------
    # Opportunity Scores
    # -------------------------------------------------------------------------

    problem_score: int
    market_score: int
    competition_score: int
    business_score: int
    execution_score: int

    ai_leverage_score: int
    distribution_score: int

    cash_machine_score: int

    # Compatibilità
    opportunity_score: int

    # -------------------------------------------------------------------------
    # Final Verdict
    # -------------------------------------------------------------------------

    build_verdict: str

    investment_recommendation: InvestmentRecommendation

    confidence: int
    confidence_reason: str

    # -------------------------------------------------------------------------
    # Explainability
    # -------------------------------------------------------------------------

    reasoning: str

    key_evidence: list[str]

    red_flags: list[str]

    biggest_risk: str

    next_action: str

    recommended_next_steps: str

    # -------------------------------------------------------------------------
    # Ranking Engine
    # -------------------------------------------------------------------------

    trend_score: int = 0

    ranking_score: int = 0

    portfolio_status: str = "WATCH"

    created_at: datetime | None = None