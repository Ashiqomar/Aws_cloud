"""
AI Endpoints — /api/v1/ai/*

GET /api/v1/ai/summary — Returns Gemini AI FinOps consultant insights.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.cost_daily import CostDaily
from app.models.recommendation import Recommendation
from app.services.ai_advisor import generate_cost_summary
from app.schemas.aws import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Advisor"])


@router.get(
    "/summary",
    summary="Get Gemini AI FinOps consultant summary",
    description=(
        "Queries monthly cost records and open recommendations, passes them "
        "to the Gemini AI Advisor, and returns executive FinOps insights."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Tenant not found"},
    },
)
def get_ai_cost_summary(
    tenant_id: Optional[uuid.UUID] = Query(None, description="Optional Tenant UUID filter"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Generate AI FinOps summary for a tenant."""

    # 1. If tenant_id provided, verify tenant exists
    if tenant_id:
        tenant = db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        ).scalar_one_or_none()
        if tenant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found.",
            )

    # 2. Gather Cost Breakdown (past 30 days)
    start_date = date.today() - timedelta(days=30)
    filters = [CostDaily.date >= start_date]
    if tenant_id:
        filters.append(CostDaily.tenant_id == tenant_id)

    total_cost_res = db.execute(
        select(func.coalesce(func.sum(CostDaily.amount), 0)).where(*filters)
    ).scalar_one()

    total_cost_val = float(total_cost_res)

    service_rows = db.execute(
        select(
            CostDaily.service_name,
            func.sum(CostDaily.amount).label("total_amount")
        )
        .where(*filters)
        .group_by(CostDaily.service_name)
        .order_by(func.sum(CostDaily.amount).desc())
    ).all()

    service_breakdown = []
    for row in service_rows:
        amt = float(row.total_amount)
        pct = (amt / total_cost_val * 100) if total_cost_val > 0 else 0
        service_breakdown.append({
            "service_name": row.service_name,
            "amount": round(amt, 2),
            "percentage": round(pct, 1),
        })

    # 3. Gather Recommendations
    reco_filters = [Recommendation.status == "open"]
    if tenant_id:
        reco_filters.append(Recommendation.tenant_id == tenant_id)

    reco_rows = db.execute(
        select(Recommendation)
        .where(*reco_filters)
        .order_by(Recommendation.estimated_savings_monthly.desc())
        .limit(10)
    ).scalars().all()

    recommendations = [
        {
            "resource_id": r.resource_id,
            "type": r.type,
            "detail": r.detail,
            "estimated_savings_monthly": float(r.estimated_savings_monthly),
            "status": r.status,
        }
        for r in reco_rows
    ]

    # 4. Invoke AI Advisor Service
    tenant_data = {
        "total_cost": total_cost_val,
        "currency": "USD",
        "service_breakdown": service_breakdown,
        "recommendations": recommendations,
    }

    ai_result = generate_cost_summary(tenant_data)
    ai_result["timestamp"] = datetime.now(timezone.utc).isoformat()

    return ai_result
