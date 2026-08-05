from crawler.github.main import main as github_main
from crawler.hackernews.main import main as hackernews_main
from crawler.producthunt.main import main as producthunt_main

from pipeline.main import main as pipeline_main


def run_step(name, func):

    print(f"\n{name}\n")

    try:

        func()

    except Exception as e:

        print(f"[ERROR] {name} failed")

        print(e)


def main():

    print("\n" + "=" * 80)
    print(" CASH MACHINE ENGINE ")
    print("=" * 80)

    run_step(
        "[1/4] Hacker News",
        hackernews_main,
    )

    run_step(
        "[2/4] GitHub",
        github_main,
    )

    run_step(
        "[3/4] Product Hunt",
        producthunt_main,
    )

    run_step(
        "[4/4] Analysis Worker",
        pipeline_main,
    )

    print("\n" + "=" * 80)
    print(" COMPLETED ")
    print("=" * 80)


if __name__ == "__main__":
    main()