import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def analyze(title: str):

    prompt = f"""
You are a startup analyst.

Analyze this title:

{title}

Return ONLY JSON.

{{
    "problem": "...",
    "customer": "...",
    "pain_level": 1,
    "market_size": "...",
    "opportunity_score": 1
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content