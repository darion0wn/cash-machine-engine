from ai.errors import RetryableAIError


class ErrorClassifier:

    @staticmethod
    def should_retry(exception: Exception) -> bool:
        """
        Returns True only for temporary failures.
        """

        return isinstance(
            exception,
            RetryableAIError,
        )