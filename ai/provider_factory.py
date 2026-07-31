from ai.gemini_provider import GeminiProvider
from ai.resilient_provider import ResilientProvider
from config.settings import AI_PROVIDER


def build_provider():

    if AI_PROVIDER == "gemini":
        return ResilientProvider(GeminiProvider())

    raise ValueError(
        f"Unsupported AI provider: {AI_PROVIDER}"
    )