from datetime import date
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

from .classification import ComplaintCategory, PriorityTier


class OverviewStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_complaints: int
    open: int
    resolved: int
    avg_resolution_hours: float
    sla_compliance_pct: float
    active_clusters: int
    by_priority_tier: Dict[PriorityTier, int]


class DepartmentPerformance(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    department_name: str
    total: int
    resolved: int
    pending: int
    avg_resolution_hours: float
    sla_compliance_pct: float


class CategoryBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: ComplaintCategory
    count: int
    percentage: float
    avg_severity: float
    avg_resolution_hours: float


class TrendDataPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    count: int
    category: Optional[ComplaintCategory] = None


class SLAReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    department: str
    total: int
    within_sla: int
    breached: int
    compliance_pct: float
