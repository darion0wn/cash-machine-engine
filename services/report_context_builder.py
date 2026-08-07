from models.investment_recommendation import InvestmentRecommendation


class ReportContextBuilder:

    def build(self, opportunity, analysis):

        recommendation = analysis.investment_recommendation

        if recommendation == InvestmentRecommendation.STRONG_BUY:
            recommendation_badge = "🟢 STRONG BUY"

        elif recommendation == InvestmentRecommendation.BUY:
            recommendation_badge = "🟢 BUY"

        elif recommendation == InvestmentRecommendation.WATCH:
            recommendation_badge = "🟡 WATCH"

        else:
            recommendation_badge = "❌ PASS"

        generated_at = (
            analysis.created_at.strftime("%Y-%m-%d %H:%M UTC")
            if analysis.created_at
            else "Unknown"
        )

        return {
            # ------------------------------------------------------------------
            # Header
            # ------------------------------------------------------------------

            "opportunity_score": analysis.opportunity_score,
            "cash_machine_score": analysis.cash_machine_score,
            "build_verdict": analysis.build_verdict,

            "investment_recommendation": recommendation_badge,

            "confidence": f"{analysis.confidence}/10",

            # ------------------------------------------------------------------
            # Source
            # ------------------------------------------------------------------

            "source": opportunity.source,
            "title": opportunity.title,
            "url": opportunity.url or "N/A",

            # ------------------------------------------------------------------
            # Problem Analysis
            # ------------------------------------------------------------------

            "problem_analysis": (
                "### Problem\n\n"
                f"{analysis.problem}\n\n"
                "### Customer\n\n"
                f"{analysis.customer}\n\n"
                "### Ideal Customer\n\n"
                f"{analysis.ideal_customer}\n\n"
                "| Metric | Value |\n"
                "|-------|------:|\n"
                f"| Pain Level | {analysis.pain_level}/10 |\n"
                f"| Urgency | {analysis.urgency}/10 |\n\n"
                "### Current Solution\n\n"
                f"{analysis.current_solution}\n\n"
                "### Why Current Solution Fails\n\n"
                f"{analysis.why_current_solution_fails}"
            ),

            # ------------------------------------------------------------------
            # Market Analysis
            # ------------------------------------------------------------------

            "market_analysis": (
                f"**Category:** {analysis.category}\n\n"
                f"**Market Size:** {analysis.market_size}\n\n"
                f"**Market Maturity:** {analysis.market_maturity}\n\n"
                f"**Competition Level:** {analysis.competition_level}/10\n\n"
                "### Competitors\n\n"
                f"{analysis.competition}"
            ),

            # ------------------------------------------------------------------
            # Business Analysis
            # ------------------------------------------------------------------

            "business_analysis": (
                "### Business Model\n\n"
                f"{analysis.business_model}\n\n"
                "### Pricing Strategy\n\n"
                f"{analysis.pricing_strategy}\n\n"
                "### Competitive Advantage\n\n"
                f"{analysis.competitive_advantage}\n\n"
                "### MVP Description\n\n"
                f"{analysis.mvp_description}\n\n"
                "| Metric | Value |\n"
                "|-------|------:|\n"
                f"| Implementation Difficulty | {analysis.implementation_difficulty}/10 |\n"
                f"| Monetization Difficulty | {analysis.monetization_difficulty}/10 |"
            ),

            # ------------------------------------------------------------------
            # Investment Evaluation
            # ------------------------------------------------------------------

            "investment_evaluation": (
                "| Category | Score |\n"
                "|----------|------:|\n"
                f"| Problem | {analysis.problem_score}/10 |\n"
                f"| Market | {analysis.market_score}/10 |\n"
                f"| Competition | {analysis.competition_score}/10 |\n"
                f"| Business | {analysis.business_score}/10 |\n"
                f"| Execution | {analysis.execution_score}/10 |\n"
                f"| AI Leverage | {analysis.ai_leverage_score}/10 |\n"
                f"| Distribution | {analysis.distribution_score}/10 |\n\n"
                f"## Cash Machine Score\n\n"
                f"**{analysis.cash_machine_score}/100**\n\n"
                f"**Build Verdict:** {analysis.build_verdict}\n\n"
                f"**Confidence:** {analysis.confidence}%\n\n"
                "### Confidence Reason\n\n"
                f"{analysis.confidence_reason}\n\n"
                "### Full Reasoning\n\n"
                f"{analysis.reasoning}"
            ),

            # ------------------------------------------------------------------
            # New Sections
            # ------------------------------------------------------------------

            "ideal_customer": analysis.ideal_customer,

            "pricing_strategy": analysis.pricing_strategy,

            "mvp_description": analysis.mvp_description,

            "biggest_risk": analysis.biggest_risk,

            "next_action": analysis.next_action,

            "topics": "\n".join(
                f"- {topic}" for topic in analysis.topics
            ) if analysis.topics else "Unknown",

            # ------------------------------------------------------------------
            # Lists
            # ------------------------------------------------------------------

            "key_evidence": "\n".join(
                f"- {item}" for item in analysis.key_evidence
            ),

            "red_flags": "\n".join(
                f"- {item}" for item in analysis.red_flags
            ),

            "recommended_next_steps": analysis.recommended_next_steps,

            # ------------------------------------------------------------------
            # Metadata
            # ------------------------------------------------------------------

            "opportunity_id": opportunity.id,
            "generated_at": generated_at,
            "model": analysis.model,
            "prompt_version": analysis.prompt_version,
        }