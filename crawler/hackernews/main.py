import requests

from pipeline.engine import Engine

BASE_URL = "https://hacker-news.firebaseio.com/v0"

story_ids = requests.get(f"{BASE_URL}/topstories.json").json()

engine = Engine()

for story_id in story_ids[:50]:

    story = requests.get(f"{BASE_URL}/item/{story_id}.json").json()

    title = story.get("title", "")

    if not (
        title.startswith("Show HN")
        or title.startswith("Ask HN")
    ):
        continue

    try:

        inserted = engine.process(
            source="Hacker News",
            title=title,
            url=story.get("url")
        )

        if inserted:
            print(f"✅ Salvata: {title}")
        else:
            print(f"⏭️ Già presente: {title}")

    except Exception as e:
        print(f"❌ Errore su '{title}'")
        print(e)