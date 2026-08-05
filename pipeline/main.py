from config.settings import MAX_ANALYSIS_PER_RUN
from pipeline.analysis_worker import AnalysisWorker


def main():

    worker = AnalysisWorker()

    processed = 0

    while processed < MAX_ANALYSIS_PER_RUN:

        if not worker.run_once():
            break

        processed += 1

    print()
    print("=" * 80)
    print(f"Processed: {processed}")
    print("=" * 80)


if __name__ == "__main__":
    main()