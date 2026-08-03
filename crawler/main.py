from crawler.github.main import main as github_main
from crawler.hackernews.main import main as hackernews_main


def main():

    print("\n" + "=" * 80)
    print(" CASH MACHINE ENGINE")
    print("=" * 80)

    print("\n[1/2] Running Hacker News crawler...\n")
    hackernews_main()

    print("\n[2/2] Running GitHub crawler...\n")
    github_main()

    print("\n" + "=" * 80)
    print(" ALL SOURCES COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()