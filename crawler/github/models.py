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