from __future__ import annotations

import os

from dotenv import load_dotenv
from ai.provider import AIProvider

load_dotenv()


class OpenAIProvider(AIProvider):
    """Placeholder provider isolated from the supported Gemini production path."""

    def __init__(self):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("OpenAI support requires the openai package.") from exc
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @property
    def model(self) -> str:
        return os.getenv("OPENAI_MODEL", "gpt-5")

    def analyze(self, opportunity):
        raise NotImplementedError(
            "OpenAI is not the configured production provider; AI_PROVIDER=gemini is currently supported."
        )
