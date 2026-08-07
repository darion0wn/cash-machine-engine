from services.opportunity_feed import OpportunityFeed
from services.trend_engine import TrendEngine


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



def print_hot_topics():
    engine = TrendEngine()
    try:
        topics = engine.top(5)
    finally:
        engine.repository.db.conn.close()

    print()
    print("=" * 80)
    print("🔥 HOT TOPICS")
    print("=" * 80)
    print()

    if not topics:
        print("No topics.")
        return

    for t in topics:
        print(f"- {t['topic']} ({t['trend_score']:.1f})")


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

    print_hot_topics()


if __name__ == "__main__":

    main()