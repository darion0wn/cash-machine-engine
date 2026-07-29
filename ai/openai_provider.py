import json
import os

from dotenv import load_dotenv
from google import genai

from ai.prompt_loader import PromptLoader
from ai.provider import AIProvider
from config.settings import AI_MODEL, PROMPT_VERSION

load_dotenv()


class GeminiProvider(AIProvider):

    MODEL = AI_MODEL

    def __init__(self):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
        self.prompt_loader = PromptLoader()

    def analyze(self, title: str, article: str) -> dict:

        prompt = self.prompt_loader.load(
            PROMPT_VERSION,
            title=title,
            article=article[:12000],
        )

        response = self.client.models.generate_content(
            model=self.MODEL,
            contents=prompt,
        )

        text = response.text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)