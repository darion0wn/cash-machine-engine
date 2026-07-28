import requests


class PageFetcher:

    def fetch(self, url: str) -> str | None:
        try:
            response = requests.get(
                url,
                timeout=15,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/138 Safari/537.36"
                    )
                },
            )

            response.raise_for_status()

            return response.text

        except Exception as e:
            print(f"Errore durante il download della pagina: {e}")
            return None