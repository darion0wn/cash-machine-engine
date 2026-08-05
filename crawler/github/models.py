from dataclasses import dataclass


@dataclass(slots=True)
class GitHubRepository:
    id: int

    name: str
    full_name: str

    description: str | None

    language: str | None

    stars: int
    forks: int
    open_issues: int

    html_url: str

    default_branch: str

    updated_at: str

    readme: str | None = None

    homepage: str | None = None

    topics: list[str] | None = None

    license: str | None = None

    watchers: int = 0

    default_branch: str = ""

    updated_at: str = ""