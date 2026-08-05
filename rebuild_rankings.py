from database.analysis_repository import AnalysisRepository
from services.ranking_engine import RankingEngine


def main():

    repository = AnalysisRepository()

    ranking_engine = RankingEngine()

    analyses = repository.find_all()

    print()

    print("=" * 80)
    print(" REBUILDING RANKINGS ")
    print("=" * 80)

    updated = 0

    for analysis in analyses:

        ranking_engine.calculate(analysis)

        repository.update_ranking(
            analysis.id,
            analysis.ranking_score,
            analysis.portfolio_status,
        )

        updated += 1

        print(
            f"[ OK ] {analysis.id} -> "
            f"{analysis.ranking_score} "
            f"({analysis.portfolio_status})"
        )

    print()

    print("=" * 80)
    print(f"Updated: {updated}")
    print("=" * 80)


if __name__ == "__main__":
    main()