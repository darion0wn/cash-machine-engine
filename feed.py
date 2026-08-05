from services.opportunity_feed import OpportunityFeed


def print_section(title, rows):

    print()

    print("=" * 80)

    print(title)

    print("=" * 80)

    print()

    if not rows:

        print("No opportunities.")

        return

    for item in rows:

        print(
            f"[{item['ranking_score']:>3}] "
            f"{item['title']}"
        )

        print(
            f"      Source : {item['source']}"
        )

        print(
            f"      Cash   : {item['cash_machine_score']}"
        )

        print()


def main():

    feed = OpportunityFeed()

    print()

    print("#" * 80)

    print(" CASH MACHINE FEED ")

    print("#" * 80)

    print_section(
        "🔥 BUILD",
        feed.builds(),
    )

    print_section(
        "👀 WATCH",
        feed.watchlist(),
    )

    print_section(
        "❌ SKIP",
        feed.skipped(),
    )


if __name__ == "__main__":

    main()