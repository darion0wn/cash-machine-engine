class ReportContextBuilder:

    def build(self, analysis):

        return {
            "opportunity_score": analysis.opportunity_score,
            "investment_recommendation": analysis.investment_recommendation.value,
            "confidence": f"{analysis.confidence}%",

            "problem_analysis": (
                f"Problem: {analysis.problem}\n\n"
                f"Customer: {analysis.customer}\n\n"
                f"Pain Level: {analysis.pain_level}/10\n"
                f"Urgency: {analysis.urgency}/10\n\n"
                f"Current Solution:\n{analysis.current_solution}\n\n"
                f"Why Current Solution Fails:\n"
                f"{analysis.why_current_solution_fails}"
            ),

            "market_analysis": (
                f"Category: {analysis.category}\n\n"
                f"Market Size: {analysis.market_size}\n\n"
                f"Market Maturity: {analysis.market_maturity}\n\n"
                f"Competition Level: {analysis.competition_level}/10\n\n"
                f"Competitors:\n{analysis.competition}"
            ),

            "business_analysis": (
                f"Business Model:\n{analysis.business_model}\n\n"
                f"Competitive Advantage:\n"
                f"{analysis.competitive_advantage}\n\n"
                f"Implementation Difficulty: "
                f"{analysis.implementation_difficulty}/10\n\n"
                f"Monetization Difficulty: "
                f"{analysis.monetization_difficulty}/10"
            ),

            "investment_evaluation": (
                "| Category | Score |\n"
                "|----------|------:|\n"
                f"| Problem | {analysis.problem_score}/10 |\n"
                f"| Market | {analysis.market_score}/10 |\n"
                f"| Competition | {analysis.competition_score}/10 |\n"
                f"| Business | {analysis.business_score}/10 |\n"
                f"| Execution | {analysis.execution_score}/10 |\n\n"
                f"**Confidence:** {analysis.confidence}%\n\n"
                f"### Confidence Reason\n"
                f"{analysis.confidence_reason}\n\n"
                f"### Full Reasoning\n"
                f"{analysis.reasoning}"
            ),

            "key_evidence": "\n".join(
                f"- {item}" for item in analysis.key_evidence
            ),

            "red_flags": "\n".join(
                f"- {item}" for item in analysis.red_flags
            ),

            "recommended_next_steps": analysis.recommended_next_steps,

            "model": analysis.model,
            "prompt_version": analysis.prompt_version,
        }