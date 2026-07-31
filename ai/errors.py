"""
Application-level exceptions for AI providers.

The rest of the application should only depend on these exceptions,
never on provider-specific SDK exceptions.
"""


class AIError(Exception):
    """Base exception for all AI-related errors."""


# ----------------------------------------------------------------------
# Retryable errors
# ----------------------------------------------------------------------

class RetryableAIError(AIError):
    """Temporary error. Retrying may succeed."""


class ServiceUnavailableError(RetryableAIError):
    """Provider is temporarily unavailable."""


class TemporaryRateLimitError(RetryableAIError):
    """Temporary rate limit exceeded."""


# ----------------------------------------------------------------------
# Non-retryable errors
# ----------------------------------------------------------------------

class NonRetryableAIError(AIError):
    """Permanent error. Retrying won't help."""


class DailyQuotaExceededError(NonRetryableAIError):
    """Daily quota exhausted."""


class InvalidApiKeyError(NonRetryableAIError):
    """API key is invalid."""


class InvalidPromptError(NonRetryableAIError):
    """Prompt is invalid."""


class InvalidResponseError(NonRetryableAIError):
    """Provider returned an invalid response."""


class NoAvailableProviderError(NonRetryableAIError):
    """No provider could satisfy the request."""