from google.genai.errors import (
    APIError,
    ClientError,
    ServerError,
)

from ai.errors import (
    InvalidApiKeyError,
    InvalidPromptError,
    RateLimitError,
    ServiceUnavailableError,
)


class ExceptionMapper:

    @staticmethod
    def map(exception: Exception) -> Exception:

        if isinstance(exception, ServerError):
            return ServiceUnavailableError(str(exception))

        if isinstance(exception, ClientError):

            message = str(exception).lower()

            if "429" in message:
                return RateLimitError(str(exception))

            if "401" in message:
                return InvalidApiKeyError(str(exception))

            if "400" in message:
                return InvalidPromptError(str(exception))

        if isinstance(exception, APIError):
            return ServiceUnavailableError(str(exception))

        return exception