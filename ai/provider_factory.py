from ai.gemini_provider import GeminiProvider
from config.settings import AI_PROVIDER


def build_provider():

    if AI_PROVIDER == "gemini":
        return GeminiProvider()

    raise ValueError(f"Unsupported AI provider: {AI_PROVIDER}")