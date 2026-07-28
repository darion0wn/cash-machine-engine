from ai.gemini_provider import analyze
from crawler.page_fetcher import PageFetcher
from crawler.text_extractor import TextExtractor
from models.opportunity import Opportunity


class Analyzer:

    def __init__(self):
        self.fetcher = PageFetcher()
        self.extractor = TextExtractor()

    def analyze(self, source: str, title: str, url: str | None):

        article = ""

        if url:
            html = self.fetcher.fetch(url)

            if html:
                article = self.extractor.extract(html)

        result = analyze(title, article)

        opportunity = Opportunity(
            source=source,
            title=title,
            url=url,
            problem=result["problem"],
            customer=result["customer"],
            pain_level=result["pain_level"],
            market_size=result["market_size"],
            opportunity_score=result["opportunity_score"],
        )

        return opportunity, article