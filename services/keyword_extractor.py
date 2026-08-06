import re
from collections import Counter


class KeywordExtractor:

    MIN_WORD_LENGTH = 3

    STOP_WORDS = {

        # generic
        "the",
        "and",
        "for",
        "with",
        "from",
        "into",
        "using",
        "show",
        "ask",
        "hn",
        "new",
        "use",
        "used",
        "using",
        "build",
        "built",
        "tool",
        "tools",
        "software",
        "platform",
        "service",
        "application",
        "system",
        "solution",
        "project",
        "projects",
        "product",
        "products",

        # english
        "this",
        "that",
        "these",
        "those",
        "there",
        "their",
        "they",
        "them",
        "have",
        "has",
        "had",
        "will",
        "would",
        "could",
        "should",
        "about",
        "after",
        "before",
        "through",
        "over",
        "under",
        "more",
        "most",
        "very",
        "also",
        "than",
        "then",
        "when",
        "where",
        "what",
        "which",
        "while",
        "into",

        # articles
        "a",
        "an",
        "of",
        "to",
        "on",
        "in",
        "at",
        "by",
        "is",
        "are",
        "be",
        "as",

        # generic AI noise
        "unknown",
        "github",
        "producthunt",
        "hacker",
        "news",
        "repository",
        "repositories",

        # useless frequent words
        "management",
        "application",
        "support",
        "feature",
        "features",
        "technology",
        "technologies",

        # remove generic AI word
        "ai",
    }

    def extract(self, *texts):

        counter = Counter()

        for text in texts:

            if not text:
                continue

            words = re.findall(
                r"[A-Za-z][A-Za-z0-9\-]+",
                str(text).lower(),
            )

            for word in words:

                if len(word) < self.MIN_WORD_LENGTH:
                    continue

                if word in self.STOP_WORDS:
                    continue

                if word.isnumeric():
                    continue

                counter[word] += 1

        return counter