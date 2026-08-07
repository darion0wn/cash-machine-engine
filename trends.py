from services.trend_engine import TrendEngine


def separator():

    print()
    print("=" * 100)
    print()


def main():

    engine = TrendEngine()

    try:
        trends = engine.top(30)
    finally:
        engine.repository.db.conn.close()

    print()

    print("#" * 100)
    print(" CASH MACHINE TOP TOPICS ")
    print("#" * 100)

    if not trends:

        print()
        print("No trends detected.")
        return

    separator()

    print(
        f"{'Topic':28}"
        f"{'Freq':>8}"
        f"{'Srcs':>8}"
        f"{'Avg Rank':>12}"
        f"{'Avg Cash':>12}"
        f"{'Latest':>14}"
        f"{'Trend':>12}"
    )

    print("-" * 100)

    for trend in trends:

        score = trend["trend_score"]

        if score >= 80:
            icon = "🔥"
        elif score >= 65:
            icon = "🚀"
        elif score >= 50:
            icon = "📈"
        else:
            icon = "•"

        print(
            f"{icon} {trend['topic'][:26]:26}"
            f"{trend['frequency']:>8}"
            f"{trend['source_diversity']:>8}"
            f"{trend['average_ranking']:>12.1f}"
            f"{trend['average_cash']:>12.1f}"
            f"{trend['latest_seen']:>14}"
            f"{score:>12.1f}"
        )

    separator()

    print(f"Tracked topics : {len(trends)}")

    print(f"Top displayed  : {min(30, len(trends))}")

    separator()


if __name__ == "__main__":
    main()
