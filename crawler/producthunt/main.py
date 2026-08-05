from crawler.producthunt.client import ProductHuntClient
from crawler.page_fetcher import PageFetcher
from crawler.text_extractor import TextExtractor
from models.opportunity import Opportunity
from pipeline.engine import Engine


def main():

    client = ProductHuntClient()

    engine = Engine()

    fetcher = PageFetcher()

    extractor = TextExtractor()

    products = client.fetch_latest(first=10)

    print(
        f"[INFO] Retrieved {len(products)} products."
    )

    scanned = 0
    saved = 0
    failed = 0

    for product in products:

        scanned += 1

        print(
            f"[INFO] Processing: {product.name}"
        )

        try:

            website_text = ""

            if product.website:

                html = fetcher.fetch(
                    product.website
                )

                if html:

                    website_text = extractor.extract_html(
                        html
                    )

            article = "\n\n".join(
                filter(
                    None,
                    [
                        product.tagline,
                        product.description,
                    ],
                )
            )

            opportunity = Opportunity(

                source="Product Hunt",

                title=product.name,

                url=product.url,

                article=article,

                description=product.description or "",

                homepage=product.website,

                website_text=website_text,

                topics=product.topics or [],
            )

            opportunity_id = engine.process(
                opportunity
            )

            if opportunity_id:

                saved += 1

                print(
                    f"[ OK ] Saved: {product.name}"
                )

            else:

                print(
                    f"[INFO] Skipped: {product.name}"
                )

        except Exception as e:

            failed += 1

            print(
                f"[FAIL] Failed: {product.name}"
            )

            print(e)

    print()

    print("[INFO] ===== SUMMARY =====")

    print(f"[INFO] Scanned : {scanned}")

    print(f"[INFO] Saved   : {saved}")

    print(f"[INFO] Failed  : {failed}")


if __name__ == "__main__":
    main()