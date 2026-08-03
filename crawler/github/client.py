import base64

import requests

from .models import GitHubRepository


class GitHubClient:

    BASE_URL = "https://api.github.com"

    HEADERS = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "CashMachineEngine",
    }

    def fetch_trending(
        self,
        limit: int = 10,
    ) -> list[GitHubRepository]:

        url = (
            f"{self.BASE_URL}/search/repositories"
            "?q=created:>2026-07-01 stars:>50"
            "&sort=stars"
            "&order=desc"
            f"&per_page={limit}"
        )

        response = requests.get(
            url,
            headers=self.HEADERS,
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()

        repositories = []

        for repo in payload["items"]:

            repositories.append(
                GitHubRepository(
                    id=repo["id"],
                    name=repo["name"],
                    full_name=repo["full_name"],
                    description=repo["description"],
                    language=repo["language"],
                    stars=repo["stargazers_count"],
                    forks=repo["forks_count"],
                    open_issues=repo["open_issues_count"],
                    html_url=repo["html_url"],
                    default_branch=repo["default_branch"],
                    updated_at=repo["updated_at"],
                )
            )

        return repositories

    def fetch_readme(
        self,
        repository: GitHubRepository,
    ) -> str | None:

        url = (
            f"{self.BASE_URL}/repos/"
            f"{repository.full_name}"
            "/readme"
        )

        response = requests.get(
            url,
            headers=self.HEADERS,
            timeout=30,
        )

        if response.status_code != 200:
            return None

        payload = response.json()

        if payload.get("encoding") != "base64":
            return None

        return base64.b64decode(
            payload["content"]
        ).decode(
            "utf-8",
            errors="ignore",
        )