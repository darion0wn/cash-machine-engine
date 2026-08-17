from config.settings import MAX_ANALYSIS_PER_RUN
from pipeline.analysis_worker import AnalysisWorker


def main():
    worker = AnalysisWorker()
    processed = 0
    failed = False

    while processed < MAX_ANALYSIS_PER_RUN:
        result = worker.run_once()

        if result is None:
            break

        if result is False:
            failed = True
            break

        processed += 1

    print()
    print("=" * 80)
    print(f"Processed: {processed}")
    print("=" * 80)

    return not failed


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
