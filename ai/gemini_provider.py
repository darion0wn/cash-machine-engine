import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = "gemini-3.6-flash"

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def analyze(title: str, article: str):

    prompt = f"""
You are a world-class startup analyst.

Your job is to identify real business opportunities.

Analyze the following startup.

TITLE:
{title}

CONTENT:
{article[:12000]}

Return ONLY valid JSON.

{{
    "problem": "",
    "customer": "",
    "pain_level": 1,
    "market_size": "",
    "opportunity_score": 1
}}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)