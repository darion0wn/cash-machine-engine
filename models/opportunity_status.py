from enum import Enum


class OpportunityStatus(str, Enum):

    PENDING = "PENDING"

    PROCESSING = "PROCESSING"

    DONE = "DONE"

    FAILED = "FAILED"