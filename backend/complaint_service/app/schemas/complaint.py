from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .classification import ComplaintCategory, ComplaintStatus, PriorityTier, SeverityLevel


class ComplaintCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    citizen_id: str
    title: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    text: Optional[str] = None  # Interop with Navya's person3_client
    raw_input: Optional[str] = None
    location: Optional[Dict[str, Any]] = None  # Interop with Navya's location dict
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ward: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    evidence_urls: Optional[List[str]] = None
    media_refs: Optional[List[str]] = None  # Interop with Navya's media_refs list


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    citizen_id: str
    title: str
    description: str
    raw_input: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ward: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    evidence_urls: List[str] = Field(default_factory=list)

    category: ComplaintCategory
    sub_category: Optional[str] = None
    severity: SeverityLevel
    priority_tier: PriorityTier
    priority_score: Optional[float] = None
    status: ComplaintStatus
    department_code: Optional[str] = None
    assigned_officer: Optional[str] = None
    cluster_id: Optional[UUID] = None

    escalation_level: int = 0
    created_at: datetime
    updated_at: datetime
    sla_deadline: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class ComplaintStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: UUID
    status: ComplaintStatus
    department: Optional[str] = None
    priority_tier: PriorityTier
    escalation_level: int = 0
    created_at: datetime
    sla_deadline: Optional[datetime] = None
    last_event: Optional[str] = None


class ComplaintUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: Optional[ComplaintStatus] = None
    assigned_officer: Optional[str] = None
    resolution_notes: Optional[str] = None


class ComplaintVerification(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    accepted: bool
    feedback: Optional[str] = None
    evidence_urls: Optional[List[str]] = None


class ComplaintListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[ComplaintResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
