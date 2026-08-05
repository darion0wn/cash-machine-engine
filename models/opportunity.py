from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models.opportunity_status import OpportunityStatus


@dataclass
class Opportunity:

    id: Optional[int] = None

    source: str = ""

    title: str = ""

    url: Optional[str] = None

    article: str = ""

    # Metadata
    description: str = ""

    homepage: Optional[str] = None

    language: Optional[str] = None

    topics: list[str] | None = None

    license: Optional[str] = None

    stars: int = 0

    forks: int = 0

    watchers: int = 0

    open_issues: int = 0

    status: OpportunityStatus = OpportunityStatus.PENDING

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None