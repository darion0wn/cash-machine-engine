from abc import ABC, abstractmethod

from models.opportunity import Opportunity


class AIProvider(ABC):

    @property
    @abstractmethod
    def model(self) -> str:
        """Return provider model name."""
        pass

    @abstractmethod
    def analyze(
        self,
        opportunity: Opportunity,
    ) -> dict:
        """Analyze an opportunity and return structured data."""
        pass