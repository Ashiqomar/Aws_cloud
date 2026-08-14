"""
Pydantic schemas for the /api/v1/recommendations endpoint.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
#  RESPONSE schemas
# ═══════════════════════════════════════════════════════════════════

class RecommendationItem(BaseModel):
    """Single recommendation in the list response."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    resource_id: str
    type: str = Field(description="e.g. 'idle_ec2', 'unused_ebs', 'oversized_rds'")
    detail: str | None = None
    estimated_savings_monthly: float
    status: str = Field(description="'open', 'applied', or 'dismissed'")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecommendationsListResponse(BaseModel):
    """Paginated list of recommendations."""
    success: bool = True
    count: int
    total_estimated_savings: float = Field(
        description="Sum of estimated_savings_monthly for returned items"
    )
    items: list[RecommendationItem]


class RecommendationsSummaryResponse(BaseModel):
    """Aggregated breakdown by recommendation type."""
    success: bool = True
    tenant_id: uuid.UUID
    summary: list["TypeSummary"]
    total_open: int
    total_estimated_savings: float


class TypeSummary(BaseModel):
    """Per-type aggregation."""
    type: str
    count: int
    estimated_savings: float


class AnalysisTriggerResponse(BaseModel):
    """Returned after triggering an analysis run."""
    success: bool = True
    message: str
    task_id: str


# Rebuild model to resolve forward references
RecommendationsSummaryResponse.model_rebuild()
