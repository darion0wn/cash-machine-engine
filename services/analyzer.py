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

    def analyze(self, source: str, title: str, url: str | None):

        article = ""

        if url:
            html = self.fetcher.fetch(url)

            if html:
                article = self.extractor.extract(html)

        result = self.provider.analyze(title, article)

        result["investment_recommendation"] = InvestmentRecommendation(result["investment_recommendation"])

        opportunity = Opportunity(
            source=source,
            title=title,
            url=url,
            article=article,
        )

        analysis = Analysis(
            id=None,
            opportunity_id=0,
            model=self.provider.MODEL,
            prompt_version=PROMPT_VERSION,
            **result,
        )

        return opportunity, analysis