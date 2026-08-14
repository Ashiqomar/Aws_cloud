"""
Cost analytics and Tenant endpoints — /api/v1/costs/* & /api/v1/tenants

Endpoints:
GET  /api/v1/costs/summary  — Aggregated monthly spending, cost-by-service breakdown, & daily trends.
GET  /api/v1/tenants        — List active tenants for tenant switcher.
POST /api/v1/demo/seed      — Seed realistic FinOps demo data for immediate UI visualization.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.cost_daily import CostDaily
from app.models.resource import Resource
from app.models.recommendation import Recommendation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Cost Analytics & Tenants"])


# ═══════════════════════════════════════════════════════════════════
#  GET /api/v1/costs/summary
# ═══════════════════════════════════════════════════════════════════

@router.get("/costs/summary")
def get_cost_summary(
    tenant_id: Optional[uuid.UUID] = Query(None, description="Optional Tenant UUID filter"),
    days: int = Query(30, ge=7, le=90, description="Lookback window in days"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns cost overview metrics for the dashboard:
    - total_monthly_cost
    - service_breakdown (for Donut Chart)
    - daily_trends (for Area / Trend Chart)
    """
    start_date = date.today() - timedelta(days=days)

    # 1. Base filter
    filters = [CostDaily.date >= start_date]
    if tenant_id:
        filters.append(CostDaily.tenant_id == tenant_id)

    # 2. Total spending
    total_cost_res = db.execute(
        select(func.coalesce(func.sum(CostDaily.amount), 0)).where(*filters)
    ).scalar_one()

    # 3. Service Breakdown
    service_rows = db.execute(
        select(
            CostDaily.service_name,
            func.sum(CostDaily.amount).label("total_amount")
        )
        .where(*filters)
        .group_by(CostDaily.service_name)
        .order_by(func.sum(CostDaily.amount).desc())
    ).all()

    total_cost_val = float(total_cost_res)
    service_breakdown = []
    for row in service_rows:
        amt = float(row.total_amount)
        pct = (amt / total_cost_val * 100) if total_cost_val > 0 else 0
        service_breakdown.append({
            "service_name": row.service_name,
            "amount": round(amt, 2),
            "percentage": round(pct, 1)
        })

    # 4. Daily Spending Trend
    daily_rows = db.execute(
        select(
            CostDaily.date,
            func.sum(CostDaily.amount).label("daily_amount")
        )
        .where(*filters)
        .group_by(CostDaily.date)
        .order_by(CostDaily.date.asc())
    ).all()

    daily_trends = [
        {"date": row.date.strftime("%Y-%m-%d"), "amount": round(float(row.daily_amount), 2)}
        for row in daily_rows
    ]

    return {
        "success": True,
        "total_monthly_cost": round(total_cost_val, 2),
        "currency": "USD",
        "lookback_days": days,
        "service_breakdown": service_breakdown,
        "daily_trends": daily_trends
    }


# ═══════════════════════════════════════════════════════════════════
#  GET /api/v1/tenants
# ═══════════════════════════════════════════════════════════════════

@router.get("/tenants")
def list_tenants(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Returns list of registered AWS tenants."""
    tenants = db.execute(
        select(Tenant).order_by(Tenant.created_at.desc())
    ).scalars().all()

    items = [
        {
            "id": str(t.id),
            "account_id": t.account_id,
            "organization_name": t.organization_name,
            "role_arn": t.role_arn,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tenants
    ]
    return {"success": True, "count": len(items), "tenants": items}


# ═══════════════════════════════════════════════════════════════════
#  POST /api/v1/demo/seed
# ═══════════════════════════════════════════════════════════════════

@router.post("/demo/seed", status_code=status.HTTP_201_CREATED)
def seed_demo_data(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Seeds rich demo FinOps data into PostgreSQL if no tenant exists.
    Enables instant dashboard visualization without needing live AWS credentials.
    """
    existing_tenant = db.execute(select(Tenant)).scalars().first()
    if existing_tenant is not None:
        tenant_id = existing_tenant.id
        account_id = existing_tenant.account_id
    else:
        tenant = Tenant(
            account_id="123456789012",
            organization_name="Acme Cloud Enterprise",
            role_arn="arn:aws:iam::123456789012:role/FinOpsCrossAccountRole",
            external_id="finops-demo-123",
            is_active=True,
        )
        db.add(tenant)
        db.flush()
        tenant_id = tenant.id
        account_id = tenant.account_id

    # 1. Seed 30 days of daily cost records across services
    services_cost_weights = {
        "Amazon EC2": 145.50,
        "Amazon RDS": 88.20,
        "Amazon S3": 34.10,
        "Amazon EBS": 28.40,
        "AWS Lambda": 12.80,
        "Amazon ElastiCache": 19.50,
    }

    today = date.today()
    cost_records_count = 0
    for day_offset in range(30):
        current_date = today - timedelta(days=day_offset)
        for srv, base_amount in services_cost_weights.items():
            variation = (day_offset % 5 - 2) * 2.5
            amount = max(5.0, base_amount + variation)

            existing = db.execute(
                select(CostDaily).where(
                    CostDaily.tenant_id == tenant_id,
                    CostDaily.date == current_date,
                    CostDaily.service_name == srv,
                )
            ).scalar_one_or_none()

            if not existing:
                cd = CostDaily(
                    tenant_id=tenant_id,
                    date=current_date,
                    service_name=srv,
                    amount=round(amount, 2),
                    currency="USD",
                )
                db.add(cd)
                cost_records_count += 1

    # 2. Seed demo Resources
    demo_resources = [
        {"id": "i-0a8f912bc41", "srv": "EC2", "st": "running", "m": {"instance_type": "m5.2xlarge", "avg_cpu_percent": 3.2}},
        {"id": "i-03d419bf8e2", "srv": "EC2", "st": "running", "m": {"instance_type": "c5.xlarge", "avg_cpu_percent": 4.1}},
        {"id": "vol-01824ab7cd91", "srv": "EBS", "st": "available", "m": {"volume_type": "gp2", "size_gb": 500, "attached_instance_id": None}},
        {"id": "vol-0f12984cd12a", "srv": "EBS", "st": "available", "m": {"volume_type": "io1", "size_gb": 1000, "attached_instance_id": None}},
        {"id": "db-prod-analytics", "srv": "RDS", "st": "running", "m": {"instance_class": "db.m5.2xlarge", "engine": "aurora-postgresql", "avg_cpu_percent": 8.5, "avg_connections": 2}},
        {"id": "db-staging-mysql", "srv": "RDS", "st": "running", "m": {"instance_class": "db.t3.large", "engine": "mysql", "avg_cpu_percent": 11.2, "avg_connections": 1}},
    ]

    for r in demo_resources:
        existing_res = db.execute(
            select(Resource).where(
                Resource.tenant_id == tenant_id,
                Resource.resource_id == r["id"],
            )
        ).scalar_one_or_none()

        if not existing_res:
            res_obj = Resource(
                tenant_id=tenant_id,
                resource_id=r["id"],
                service=r["srv"],
                region="us-east-1",
                status=r["st"],
                metrics_json=r["m"],
            )
            db.add(res_obj)

    # 3. Seed demo Recommendations
    demo_recos = [
        {
            "resource_id": "i-0a8f912bc41",
            "type": "idle_ec2",
            "detail": "EC2 instance i-0a8f912bc41 (m5.2xlarge) in us-east-1 has avg CPU of 3.2% over past 14 days. Stopping or terminating will save ~$221.92/mo.",
            "savings": 221.92,
        },
        {
            "resource_id": "i-03d419bf8e2",
            "type": "idle_ec2",
            "detail": "EC2 instance i-03d419bf8e2 (c5.xlarge) in us-east-1 has avg CPU of 4.1%. Downsizing or stopping will save ~$98.55/mo.",
            "savings": 98.55,
        },
        {
            "resource_id": "vol-0f12984cd12a",
            "type": "unused_ebs",
            "detail": "EBS volume vol-0f12984cd12a (io1, 1000 GB) is unattached in us-east-1. Deleting will save ~$125.00/mo.",
            "savings": 125.00,
        },
        {
            "resource_id": "vol-01824ab7cd91",
            "type": "unused_ebs",
            "detail": "EBS volume vol-01824ab7cd91 (gp2, 500 GB) is unattached in us-east-1. Deleting will save ~$50.00/mo.",
            "savings": 50.00,
        },
        {
            "resource_id": "db-prod-analytics",
            "type": "oversized_rds",
            "detail": "RDS db-prod-analytics (db.m5.2xlarge) shows low utilization (avg CPU 8.5%, 2 connections). Downsizing to db.m5.xlarge saves ~$251.12/mo.",
            "savings": 251.12,
        },
    ]

    for reco in demo_recos:
        existing = db.execute(
            select(Recommendation).where(
                Recommendation.tenant_id == tenant_id,
                Recommendation.resource_id == reco["resource_id"],
                Recommendation.type == reco["type"],
            )
        ).first()
        if not existing:
            rec_obj = Recommendation(
                tenant_id=tenant_id,
                resource_id=reco["resource_id"],
                type=reco["type"],
                detail=reco["detail"],
                estimated_savings_monthly=reco["savings"],
                status="open",
            )
            db.add(rec_obj)

    db.commit()

    return {
        "success": True,
        "message": f"Demo FinOps data seeded successfully for tenant {account_id}",
        "tenant_id": str(tenant_id),
    }
