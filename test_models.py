"""Manual Gemini model listing check.

Run explicitly with:
    python test_models.py
"""

import os

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required.")

    client = genai.Client(api_key=api_key)

    for model in client.models.list():
        print(model.name)

        methods = getattr(model, "supported_actions", None)
        if methods:
            print("   ", methods)


if __name__ == "__main__":
    main()
