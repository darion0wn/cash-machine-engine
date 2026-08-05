from dataclasses import dataclass


@dataclass
class Product:

    id: str

    name: str

    tagline: str | None = None

    description: str | None = None

    url: str | None = None

    website: str | None = None

    votes_count: int = 0

    comments_count: int = 0

    created_at: str = ""

    topics: list[str] | None = None