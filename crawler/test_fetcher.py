"""Manual page extraction check.

Run explicitly with:
    python crawler/test_fetcher.py
"""


def main() -> None:
    from crawler.page_fetcher import PageFetcher
    from crawler.text_extractor import TextExtractor

    url = "https://infrawrench.com"

    fetcher = PageFetcher()
    html = fetcher.fetch(url)

    extractor = TextExtractor()
    text = extractor.extract(html)

    print(text[:3000])


if __name__ == "__main__":
    main()
