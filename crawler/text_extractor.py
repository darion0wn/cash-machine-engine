from bs4 import BeautifulSoup
from readability import Document


class TextExtractor:

    def extract(self, html: str) -> str:

        doc = Document(html)

        article_html = doc.summary()

        soup = BeautifulSoup(article_html, "html.parser")

        text = soup.get_text(separator="\n")

        text = "\n".join(
            line.strip()
            for line in text.splitlines()
            if line.strip()
        )

        return text