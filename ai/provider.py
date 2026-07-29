from abc import ABC, abstractmethod


class AIProvider(ABC):

    @abstractmethod
    def analyze(self, title: str, article: str) -> dict:
        """Analyze an opportunity and return structured data."""
        pass