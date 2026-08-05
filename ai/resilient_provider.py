from ai.provider import AIProvider
from models.opportunity import Opportunity
from services.retry import Retry


class ResilientProvider(AIProvider):

    def __init__(self, provider: AIProvider):
        self._provider = provider

    @property
    def model(self) -> str:
        return self._provider.model

    def analyze(
        self,
        opportunity: Opportunity,
    ) -> dict:

        return Retry.run(
            lambda: self._provider.analyze(
                opportunity
            )
        )