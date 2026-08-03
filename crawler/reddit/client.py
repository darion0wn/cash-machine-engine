from __future__ import annotations

import requests

from .models import RedditPost


class RedditClient:

    BASE_URL = "https://www.reddit.com"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/138.0 Safari/537.36"
        )
    }

    def fetch_subreddit(
        self,
        subreddit: str,
        limit: int = 25,
    ) -> list[RedditPost]:

        url = (
            f"{self.BASE_URL}/r/{subreddit}/new.json"
            f"?limit={limit}"
        )

        response = requests.get(
            url,
            headers=self.HEADERS,
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()

        posts = []

        for child in payload["data"]["children"]:

            data = child["data"]

            posts.append(
                RedditPost(
                    id=data["id"],
                    subreddit=data["subreddit"],
                    title=data["title"],
                    author=data["author"],
                    score=data["score"],
                    num_comments=data["num_comments"],
                    created_utc=data["created_utc"],
                    url=f'https://reddit.com{data["permalink"]}',
                    selftext=data["selftext"],
                )
            )

        return posts