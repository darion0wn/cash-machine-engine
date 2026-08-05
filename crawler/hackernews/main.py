import requests

from config.settings import MAX_STORIES
from core.logger import Logger
from models.opportunity import Opportunity
from pipeline.engine import Engine

BASE_URL = "https://hacker-news.firebaseio.com/v0"


def main():

    Logger.info("Downloading top Hacker News stories...")

    story_ids = requests.get(
        f"{BASE_URL}/topstories.json"
    ).json()

    Logger.info(f"Retrieved {len(story_ids)} stories.")

    engine = Engine()

    scanned = 0
    inserted = 0
    skipped = 0
    failed = 0

    for story_id in story_ids[:MAX_STORIES]:

        story = requests.get(
            f"{BASE_URL}/item/{story_id}.json"
        ).json()

        title = story.get("title", "")

        if not (
            title.startswith("Show HN")
            or title.startswith("Ask HN")
        ):
            continue

        scanned += 1

        Logger.info(f"Processing: {title}")

        try:

            opportunity = Opportunity(

                source="Hacker News",

                title=title,

                url=story.get("url"),

                article=story.get("text", ""),
            )

            saved = engine.process(
                opportunity
            )

            if saved:

                inserted += 1

                Logger.success(f"Saved: {title}")

            else:

                skipped += 1

                Logger.warning(
                    f"Already exists: {title}"
                )

        except Exception as e:

            failed += 1

            Logger.error(f"Failed: {title}")

            Logger.error(str(e))

    print()

    Logger.info("========== SUMMARY ==========")

    Logger.info(f"Scanned : {scanned}")

    Logger.info(f"Saved   : {inserted}")

    Logger.info(f"Skipped : {skipped}")

    Logger.info(f"Failed  : {failed}")


if __name__ == "__main__":
    main()