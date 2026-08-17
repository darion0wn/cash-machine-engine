"""Manual Product Hunt connectivity check.

Run explicitly with:
    python test_producthunt.py
"""

import os

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    from crawler.producthunt.client import ProductHuntClient

    if not os.getenv("PRODUCTHUNT_API_KEY") or not os.getenv("PRODUCTHUNT_API_SECRET"):
        raise RuntimeError(
            "PRODUCTHUNT_API_KEY and PRODUCTHUNT_API_SECRET are required."
        )

    client = ProductHuntClient()
    products = client.fetch_latest(5)

    for product in products:
        print(product.name)


if __name__ == "__main__":
    main()
