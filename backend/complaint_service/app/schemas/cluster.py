from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .classification import ComplaintCategory


class SimilarComplaint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: UUID
    title: str
    category: ComplaintCategory
    similarity_score: float
    created_at: datetime


class DuplicateCheckResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_duplicate: bool
    similar_complaints: List[SimilarComplaint]
    suggested_cluster_id: Optional[UUID] = None


class ClusterInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: ComplaintCategory
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    complaint_count: int
    avg_severity: float
    status: str
    representative_complaint: Optional[UUID] = None


class ClusterDetail(ClusterInfo):
    model_config = ConfigDict(from_attributes=True)

    member_complaints: List[SimilarComplaint]
