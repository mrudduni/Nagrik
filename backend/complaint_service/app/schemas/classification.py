from enum import Enum, IntEnum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ComplaintCategory(str, Enum):
    POTHOLE = "POTHOLE"
    WATER_SUPPLY = "WATER_SUPPLY"
    DRAINAGE = "DRAINAGE"
    GARBAGE = "GARBAGE"
    STREETLIGHT = "STREETLIGHT"
    POLLUTION = "POLLUTION"
    NOISE = "NOISE"
    ENCROACHMENT = "ENCROACHMENT"
    TRAFFIC = "TRAFFIC"
    ELECTRICITY = "ELECTRICITY"
    PUBLIC_TRANSPORT = "PUBLIC_TRANSPORT"
    SANITATION = "SANITATION"
    OTHER = "OTHER"


class SeverityLevel(IntEnum):
    MINOR = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    CRITICAL = 5


class PriorityTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplaintStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLUTION_CLAIMED = "RESOLUTION_CLAIMED"
    CITIZEN_VERIFIED = "CITIZEN_VERIFIED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class ClassificationResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: ComplaintCategory
    sub_category: Optional[str] = None
    severity: int = Field(ge=1, le=5, default=3)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    keywords: List[str] = Field(default_factory=list)
    department_code: Optional[str] = None
    reasoning: Optional[str] = None
