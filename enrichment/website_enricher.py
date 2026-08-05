from crawler.page_fetcher import PageFetcher
from crawler.text_extractor import TextExtractor


class WebsiteEnricher:

    def __init__(self):

        self.fetcher = PageFetcher()

        self.extractor = TextExtractor()

    def enrich(
        self,
        url: str | None,
    ) -> str:

        if not url:
            return ""

        html = self.fetcher.fetch(url)

        if not html:
            return ""

        try:
            return self.extractor.extract_html(html)

        except Exception:
            return ""