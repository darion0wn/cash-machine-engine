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

    status: OpportunityStatus = OpportunityStatus.PENDING

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None