import os

from dotenv import load_dotenv

import requests

from crawler.producthunt.models import Product

load_dotenv()


class ProductHuntClient:

    TOKEN_URL = "https://api.producthunt.com/v2/oauth/token"

    GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"

    def __init__(self):

        self.api_key = os.getenv("PRODUCTHUNT_API_KEY")

        self.api_secret = os.getenv("PRODUCTHUNT_API_SECRET")

        self.access_token = self._authenticate()

    def _authenticate(self) -> str:

        response = requests.post(
            self.TOKEN_URL,
            json={
                "client_id": self.api_key,
                "client_secret": self.api_secret,
                "grant_type": "client_credentials",
            },
            headers={
                "Accept": "application/json",
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json()["access_token"]

    def fetch_latest(
        self,
        first: int = 10,
    ) -> list[Product]:

        query = """
        query ($first: Int!) {

          posts(first: $first) {

            edges {

              node {

                id

                name

                tagline

                description

                url

                website

                votesCount

                commentsCount

                createdAt

                topics(first: 10) {

                  edges {

                    node {

                      name

                    }

                  }

                }

              }

            }

          }

        }
        """

        response = requests.post(
            self.GRAPHQL_URL,
            json={
                "query": query,
                "variables": {
                    "first": first,
                },
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()["data"]["posts"]["edges"]

        products = []

        for edge in data:

            node = edge["node"]

            products.append(
                Product(
                    id=node["id"],
                    name=node["name"],
                    tagline=node["tagline"],
                    description=node["description"],
                    url=node["url"],
                    website=node["website"],
                    votes_count=node["votesCount"],
                    comments_count=node["commentsCount"],
                    created_at=node["createdAt"],
                    topics=[
                        topic["node"]["name"]
                        for topic in node["topics"]["edges"]
                    ],
                )
            )

        return products