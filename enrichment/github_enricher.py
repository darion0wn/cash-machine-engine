from models.context import Context


class GitHubEnricher:

    def enrich(
        self,
        repository,
        readme: str | None,
        website: str | None = None,
    ) -> Context:

        return Context(

            title=repository.full_name,

            article="",

            readme=readme or "",

            website=website or "",

            source_description=repository.description or "",
        )