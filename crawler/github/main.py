from crawler.github.client import GitHubClient
from enrichment.website_enricher import WebsiteEnricher
from models.opportunity import Opportunity
from pipeline.engine import Engine


def main():

    client = GitHubClient()

    website_enricher = WebsiteEnricher()

    engine = Engine()

    repositories = client.fetch_trending(limit=10)

    print(
        f"[INFO] Retrieved {len(repositories)} repositories."
    )

    scanned = 0
    saved = 0
    failed = 0

    for repository in repositories:

        scanned += 1

        print(
            f"[INFO] Processing: {repository.full_name}"
        )

        try:

            repository = client.fetch_repository(
                repository
            )

            repository.readme = client.fetch_readme(
                repository
            )

            website_text = website_enricher.enrich(
                repository.homepage
            )

            opportunity = Opportunity(

                source="GitHub",

                title=repository.full_name,

                url=repository.html_url,

                article=repository.readme,

                description=repository.description or "",

                homepage=repository.homepage,

                website_text=website_text,

                language=repository.language,

                topics=repository.topics,

                license=repository.license,

                stars=repository.stars,

                forks=repository.forks,

                watchers=repository.watchers,

                open_issues=repository.open_issues,
            )

            opportunity_id = engine.process(
                opportunity
            )

            if opportunity_id:

                saved += 1

                print(
                    f"[ OK ] Saved: {repository.full_name}"
                )

            else:

                print(
                    f"[INFO] Skipped: {repository.full_name}"
                )

        except Exception as e:

            failed += 1

            print(
                f"[FAIL] Failed: {repository.full_name}"
            )

            print(e)

    print()

    print("[INFO] ===== SUMMARY =====")

    print(f"[INFO] Scanned : {scanned}")

    print(f"[INFO] Saved   : {saved}")

    print(f"[INFO] Failed  : {failed}")


if __name__ == "__main__":
    main()