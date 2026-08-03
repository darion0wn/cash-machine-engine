from dataclasses import dataclass

@dataclass
class RedditPost:
    id: str
    subreddit: str
    title: str
    author: str
    score: int
    num_comments: int
    created_utc: float
    url: str
    selftext: str