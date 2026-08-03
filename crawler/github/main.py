from crawler.github.client import GitHubClient
from pipeline.engine import Engine


def main():

    client = GitHubClient()

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

            repository.readme = client.fetch_readme(
                repository
            )

            opportunity_id = engine.process(
                source="GitHub",
                title=repository.full_name,
                url=repository.html_url,
                article=repository.readme,
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