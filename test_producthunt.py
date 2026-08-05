from dotenv import load_dotenv
load_dotenv()

import os

print("API KEY:", repr(os.getenv("PRODUCTHUNT_API_KEY")))
print("API SECRET:", repr(os.getenv("PRODUCTHUNT_API_SECRET")))

from crawler.producthunt.client import ProductHuntClient

client = ProductHuntClient()

products = client.fetch_latest(5)

for product in products:
    print(product.name)