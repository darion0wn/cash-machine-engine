from bs4 import BeautifulSoup
from readability import Document

import re


class TextExtractor:

    def extract_html(
        self,
        html: str,
    ) -> str:

        doc = Document(html)

        article_html = doc.summary()

        soup = BeautifulSoup(
            article_html,
            "html.parser",
        )

        text = soup.get_text(separator="\n")

        return self._normalize(text)

    def extract_markdown(
        self,
        markdown: str,
    ) -> str:

        markdown = re.sub(
            r"```.*?```",
            "",
            markdown,
            flags=re.DOTALL,
        )

        markdown = re.sub(
            r"`.*?`",
            "",
            markdown,
        )

        markdown = re.sub(
            r"!\[.*?\]\(.*?\)",
            "",
            markdown,
        )

        markdown = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            markdown,
        )

        markdown = re.sub(
            r"<[^>]+>",
            "",
            markdown,
        )

        return self._normalize(markdown)

    def _normalize(
        self,
        text: str,
    ) -> str:

        return "\n".join(
            line.strip()
            for line in text.splitlines()
            if line.strip()
        )