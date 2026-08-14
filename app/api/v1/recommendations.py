"""
Recommendations endpoints — /api/v1/recommendations/*

GET  /                 — list recommendations (filterable)
GET  /summary          — aggregated breakdown by type
POST /analyze          — trigger rules-engine analysis
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.recommendation import Recommendation
from app.schemas.recommendations import (
    AnalysisTriggerResponse,
    RecommendationItem,
    RecommendationsListResponse,
    RecommendationsSummaryResponse,
    TypeSummary,
)
from app.schemas.aws import ErrorResponse
from app.tasks.sync_tasks import run_analysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


# ═══════════════════════════════════════════════════════════════════
#  GET /api/v1/recommendations
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "",
    response_model=RecommendationsListResponse,
    summary="List cost-saving recommendations",
    description=(
        "Returns recommendations for a tenant, optionally filtered by "
        "type and/or status.  Results include the total estimated savings."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Tenant not found"},
    },
)
def list_recommendations(
    tenant_id: uuid.UUID = Query(..., description="Tenant UUID"),
    type: Optional[str] = Query(
        None,
        description="Filter by recommendation type (e.g. 'idle_ec2', 'unused_ebs', 'oversized_rds')",
    ),
    rec_status: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status: 'open', 'applied', 'dismissed'",
    ),
    limit: int = Query(100, ge=1, le=500, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> RecommendationsListResponse:
    """Fetch filtered recommendations with total savings."""

    # Verify tenant
    tenant = db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    ).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found.",
        )

    # Build query
    query = select(Recommendation).where(Recommendation.tenant_id == tenant_id)

    if type is not None:
        query = query.where(Recommendation.type == type)
    if rec_status is not None:
        query = query.where(Recommendation.status == rec_status)

    query = query.order_by(
        Recommendation.estimated_savings_monthly.desc(),
        Recommendation.created_at.desc(),
    )

    # Count + paginate
    total_query = select(func.count()).select_from(query.subquery())
    # We don't use total_count for now but it's available for future pagination metadata

    items = db.execute(query.offset(offset).limit(limit)).scalars().all()

    total_savings = sum(
        float(item.estimated_savings_monthly) for item in items
    )

    return RecommendationsListResponse(
        success=True,
        count=len(items),
        total_estimated_savings=round(total_savings, 2),
        items=[RecommendationItem.model_validate(item) for item in items],
    )


# ═══════════════════════════════════════════════════════════════════
#  GET /api/v1/recommendations/summary
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/summary",
    response_model=RecommendationsSummaryResponse,
    summary="Recommendations breakdown by type",
    description=(
        "Returns an aggregated summary of open recommendations grouped "
        "by type, with counts and estimated savings per category."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Tenant not found"},
    },
)
def recommendations_summary(
    tenant_id: uuid.UUID = Query(..., description="Tenant UUID"),
    db: Session = Depends(get_db),
) -> RecommendationsSummaryResponse:
    """Aggregated recommendation summary."""

    tenant = db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    ).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found.",
        )

    # Group open recommendations by type
    rows = db.execute(
        select(
            Recommendation.type,
            func.count(Recommendation.id).label("count"),
            func.coalesce(
                func.sum(Recommendation.estimated_savings_monthly), 0
            ).label("estimated_savings"),
        )
        .where(
            Recommendation.tenant_id == tenant_id,
            Recommendation.status == "open",
        )
        .group_by(Recommendation.type)
    ).all()

    summary = [
        TypeSummary(type=row.type, count=row.count, estimated_savings=float(row.estimated_savings))
        for row in rows
    ]
    total_open = sum(s.count for s in summary)
    total_savings = sum(s.estimated_savings for s in summary)

    return RecommendationsSummaryResponse(
        success=True,
        tenant_id=tenant_id,
        summary=summary,
        total_open=total_open,
        total_estimated_savings=round(total_savings, 2),
    )


# ═══════════════════════════════════════════════════════════════════
#  POST /api/v1/recommendations/analyze
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/analyze",
    response_model=AnalysisTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger rules-engine analysis",
    description=(
        "Queues a Celery task that runs the rules engine against the "
        "tenant's existing resource data and generates new recommendations."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Tenant not found"},
    },
)
def trigger_analysis(
    tenant_id: uuid.UUID = Query(..., description="Tenant UUID"),
    db: Session = Depends(get_db),
) -> AnalysisTriggerResponse:
    """Dispatch the analysis background task."""

    tenant = db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    ).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found.",
        )

    task = run_analysis.delay(str(tenant_id))
    logger.info("Analysis task %s queued for tenant %s", task.id, tenant_id)

    return AnalysisTriggerResponse(
        success=True,
        message="Analysis task queued successfully.",
        task_id=task.id,
    )
