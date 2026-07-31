import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai.errors import (
    APIError,
    ClientError,
    ServerError,
)

from ai.errors import (
    DailyQuotaExceededError,
    InvalidApiKeyError,
    InvalidPromptError,
    InvalidResponseError,
    ServiceUnavailableError,
    TemporaryRateLimitError,
)
from ai.prompt_loader import PromptLoader
from ai.provider import AIProvider
from config.settings import AI_MODEL, PROMPT_VERSION
from services.analysis_validator import AnalysisValidator

load_dotenv()


class GeminiProvider(AIProvider):

    MODEL = AI_MODEL

    @property
    def model(self) -> str:
        return self.MODEL

    def __init__(self):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
        self.prompt_loader = PromptLoader()

    def analyze(self, title: str, article: str) -> dict:

        try:

            prompt = self.prompt_loader.load(
                f"opportunity_{PROMPT_VERSION}",
                title=title,
                article=article[:12000],
            )

            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
            )

            text = response.text.strip()

            if text.startswith("```"):
                text = (
                    text.replace("```json", "")
                    .replace("```", "")
                    .strip()
                )

            start = text.find("{")
            end = text.rfind("}")

            if start == -1 or end == -1:
                raise InvalidResponseError(
                    "No JSON object found in Gemini response."
                )

            text = text[start:end + 1]

            data = json.loads(text)

            return AnalysisValidator.validate(data)

        except ServerError as e:
            raise ServiceUnavailableError(str(e)) from e

        except ClientError as e:

            message = str(e).lower()

            if (
                "resource_exhausted" in message
                or "generaterequestsperday" in message
                or "quota" in message
            ):
                raise DailyQuotaExceededError(str(e)) from e

            if "429" in message:
                raise TemporaryRateLimitError(str(e)) from e

            if "401" in message:
                raise InvalidApiKeyError(str(e)) from e

            if "400" in message:
                raise InvalidPromptError(str(e)) from e

            raise

        except APIError as e:
            raise ServiceUnavailableError(str(e)) from e