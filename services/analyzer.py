from ai.provider_factory import build_provider
from config.settings import PROMPT_VERSION
from crawler.page_fetcher import PageFetcher
from crawler.text_extractor import TextExtractor
from models.analysis import Analysis
from models.opportunity import Opportunity
from models.investment_recommendation import InvestmentRecommendation


class Analyzer:

    def __init__(self):
        self.fetcher = PageFetcher()
        self.extractor = TextExtractor()
        self.provider = build_provider()

    def analyze(
        self,
        opportunity: Opportunity,
    ):

        if not opportunity.article and opportunity.url:

            html = self.fetcher.fetch(opportunity.url)

            if html:
                opportunity.article = self.extractor.extract_html(html)

        result = self.provider.analyze(opportunity)

        result["investment_recommendation"] = (
            InvestmentRecommendation(
                result["investment_recommendation"]
            )
        )

        analysis = Analysis(
            id=None,
            opportunity_id=0,
            model=self.provider.model,
            prompt_version=PROMPT_VERSION,
            **result,
        )

        return opportunity, analysis