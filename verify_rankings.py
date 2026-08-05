from database.database import Database


def print_section(title):

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def main():

    db = Database()

    cursor = db.conn.cursor()

    print_section("RANKING OVERVIEW")

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM analyses
        """
    )

    total = cursor.fetchone()[0]

    print(f"Total analyses : {total}")

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM analyses
        WHERE portfolio_status='BUILD'
        """
    )

    print(
        f"BUILD          : {cursor.fetchone()[0]}"
    )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM analyses
        WHERE portfolio_status='WATCH'
        """
    )

    print(
        f"WATCH          : {cursor.fetchone()[0]}"
    )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM analyses
        WHERE portfolio_status='SKIP'
        """
    )

    print(
        f"SKIP           : {cursor.fetchone()[0]}"
    )

    cursor.execute(
        """
        SELECT ROUND(AVG(ranking_score),1)
        FROM analyses
        """
    )

    print(
        f"Average Rank   : {cursor.fetchone()[0]}"
    )

    print_section("TOP 10")

    cursor.execute(
        """
        SELECT

            opportunities.title,

            analyses.ranking_score,

            analyses.cash_machine_score,

            analyses.portfolio_status

        FROM analyses

        JOIN opportunities

        ON analyses.opportunity_id = opportunities.id

        ORDER BY analyses.ranking_score DESC

        LIMIT 10
        """
    )

    for row in cursor.fetchall():

        print(
            f"[{row[1]:>3}] "
            f"{row[3]:<6} "
            f"(Cash {row[2]:>3}) "
            f"{row[0]}"
        )

    print_section("INVALID RECORDS")

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM analyses

        WHERE ranking_score=0
        """
    )

    print(
        f"Ranking = 0 : {cursor.fetchone()[0]}"
    )

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM analyses

        WHERE cash_machine_score=0
        """
    )

    print(
        f"Cash = 0    : {cursor.fetchone()[0]}"
    )

    print()

    print("=" * 80)
    print("CHECK COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()