from abc import ABC, abstractmethod


class AIProvider(ABC):

    @property
    @abstractmethod
    def model(self) -> str:
        """Return provider model name."""
        pass

    @abstractmethod
    def analyze(
        self,
        title: str,
        article: str,
    ) -> dict:
        """Analyze an opportunity and return structured data."""
        pass