from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Opportunity:
    id: Optional[int] = None

    source: str = ""
    title: str = ""
    url: Optional[str] = None

    article: str = ""

    created_at: Optional[datetime] = None