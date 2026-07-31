import time
from collections.abc import Callable

from ai.error_classifier import ErrorClassifier


class Retry:

    @staticmethod
    def run(
        func: Callable,
        attempts: int = 3,
        delay: float = 2,
        backoff: float = 2,
    ):

        current_delay = delay
        last_exception = None

        for attempt in range(1, attempts + 1):

            try:
                return func()

            except Exception as e:

                last_exception = e

                if not ErrorClassifier.should_retry(e):
                    raise

                if attempt == attempts:
                    break

                print(
                    f"[Retry {attempt}/{attempts}] "
                    f"{e} "
                    f"- retrying in {current_delay:.0f}s..."
                )

                time.sleep(current_delay)

                current_delay *= backoff

        raise last_exception