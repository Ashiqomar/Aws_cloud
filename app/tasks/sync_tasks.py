"""
Celery tasks for AWS data synchronization and rules-engine analysis.

Tasks:
- ``sync_aws_data``       — full data pull for a single tenant (on-demand)
- ``run_analysis``        — run the rules engine for a single tenant
- ``run_analysis_all``    — periodic: run analysis across all active tenants
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.cost_daily import CostDaily
from app.models.resource import Resource
from app.models.recommendation import Recommendation
from app.services.aws_sts import assume_role, STSError
from app.services.aws_ingestion import (
    fetch_monthly_costs,
    fetch_ec2_utilization,
    fetch_ebs_volumes,
    fetch_rds_utilization,
)
from app.services.rules_engine import run_all_rules

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  TASK 1 — Full AWS data sync (on-demand per tenant)
# ═══════════════════════════════════════════════════════════════════

@celery_app.task(
    bind=True,
    name="tasks.sync_aws_data",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def sync_aws_data(self, tenant_id: str) -> dict:
    """
    Pull cost data, EC2 utilization, EBS volumes, and RDS metrics
    from AWS, persist to PostgreSQL, then run the rules engine.

    Parameters
    ----------
    tenant_id : str
        UUID string of the tenant to sync.

    Returns
    -------
    dict
        Summary of ingested records and recommendations.
    """
    logger.info("Starting sync for tenant %s", tenant_id)
    db = SessionLocal()

    try:
        # ── 1. Load tenant ───────────────────────────────────────
        tenant = db.execute(
            select(Tenant).where(Tenant.id == uuid.UUID(tenant_id))
        ).scalar_one_or_none()

        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        if not tenant.is_active:
            raise ValueError(f"Tenant {tenant_id} is inactive")

        # ── 2. Assume IAM role ───────────────────────────────────
        try:
            session = assume_role(
                role_arn=tenant.role_arn,
                external_id=tenant.external_id,
                session_name=f"finops-sync-{tenant.account_id}",
            )
        except STSError as exc:
            logger.error("STS failed for tenant %s: %s", tenant_id, exc.message)
            raise self.retry(exc=exc)

        # ── 3. Fetch & upsert cost data (last 30 days) ──────────
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=30)).isoformat()

        cost_records = fetch_monthly_costs(session, start_date, end_date)
        cost_count = _upsert_costs(db, tenant.id, cost_records)

        # ── 4. Fetch & upsert EC2 utilization ────────────────────
        ec2_records = fetch_ec2_utilization(session)
        ec2_count = _upsert_ec2_resources(db, tenant.id, ec2_records)

        # ── 5. Fetch & upsert EBS volumes ────────────────────────
        ebs_records = fetch_ebs_volumes(session)
        ebs_count = _upsert_ebs_resources(db, tenant.id, ebs_records)

        # ── 6. Fetch & upsert RDS utilization ────────────────────
        rds_records = fetch_rds_utilization(session)
        rds_count = _upsert_rds_resources(db, tenant.id, rds_records)

        # ── 7. Run rules engine ──────────────────────────────────
        reco_summary = run_all_rules(db, tenant.id)

        db.commit()

        summary = {
            "tenant_id": tenant_id,
            "costs_upserted": cost_count,
            "ec2_upserted": ec2_count,
            "ebs_upserted": ebs_count,
            "rds_upserted": rds_count,
            "recommendations": reco_summary,
        }
        logger.info("Sync complete for tenant %s: %s", tenant_id, summary)
        return summary

    except Exception as exc:
        db.rollback()
        logger.exception("Sync failed for tenant %s", tenant_id)
        raise

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════
#  TASK 2 — Rules-engine analysis only (per tenant)
# ═══════════════════════════════════════════════════════════════════

@celery_app.task(
    bind=True,
    name="tasks.run_analysis",
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def run_analysis(self, tenant_id: str) -> dict:
    """
    Run the rules engine against existing data for one tenant.

    Useful when you want to re-analyse without re-fetching from AWS.
    """
    logger.info("Running analysis for tenant %s", tenant_id)
    db = SessionLocal()

    try:
        tenant = db.execute(
            select(Tenant).where(Tenant.id == uuid.UUID(tenant_id))
        ).scalar_one_or_none()

        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")

        summary = run_all_rules(db, tenant.id)
        db.commit()

        logger.info("Analysis complete for tenant %s: %s", tenant_id, summary)
        return {"tenant_id": tenant_id, "recommendations": summary}

    except Exception:
        db.rollback()
        logger.exception("Analysis failed for tenant %s", tenant_id)
        raise

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════
#  TASK 3 — Periodic analysis across ALL active tenants
# ═══════════════════════════════════════════════════════════════════

@celery_app.task(
    name="tasks.run_analysis_all",
    acks_late=True,
)
def run_analysis_all() -> dict:
    """
    Iterate over all active tenants and dispatch ``run_analysis`` for
    each one.  Intended to be called by Celery Beat on a schedule.
    """
    logger.info("Starting periodic analysis for all tenants")
    db = SessionLocal()

    try:
        tenants = db.execute(
            select(Tenant).where(Tenant.is_active == True)  # noqa: E712
        ).scalars().all()

        dispatched = 0
        for tenant in tenants:
            run_analysis.delay(str(tenant.id))
            dispatched += 1

        logger.info("Dispatched analysis for %d tenants", dispatched)
        return {"tenants_dispatched": dispatched}

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════
#  PRIVATE HELPERS — Upsert functions
# ═══════════════════════════════════════════════════════════════════

def _upsert_costs(db, tenant_id: uuid.UUID, records: list[dict]) -> int:
    """Upsert daily cost records using PostgreSQL ON CONFLICT."""
    if not records:
        return 0

    for record in records:
        stmt = pg_insert(CostDaily).values(
            tenant_id=tenant_id,
            date=record["date"],
            service_name=record["service"],
            amount=record["amount"],
            currency=record.get("currency", "USD"),
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_cost_daily_tenant_date_service",
            set_={
                "amount": stmt.excluded.amount,
                "currency": stmt.excluded.currency,
            },
        )
        db.execute(stmt)

    return len(records)


def _upsert_ec2_resources(db, tenant_id: uuid.UUID, records: list[dict]) -> int:
    """Upsert EC2 resources using PostgreSQL ON CONFLICT."""
    if not records:
        return 0

    for record in records:
        metrics = {
            "instance_type": record.get("instance_type"),
            "avg_cpu_percent": record.get("avg_cpu_percent"),
        }
        stmt = pg_insert(Resource).values(
            tenant_id=tenant_id,
            resource_id=record["instance_id"],
            service="EC2",
            region=record["region"],
            status=record["state"],
            metrics_json=metrics,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_resources_tenant_resource",
            set_={
                "status": stmt.excluded.status,
                "metrics_json": stmt.excluded.metrics_json,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        db.execute(stmt)

    return len(records)


def _upsert_ebs_resources(db, tenant_id: uuid.UUID, records: list[dict]) -> int:
    """Upsert EBS volume records."""
    if not records:
        return 0

    for record in records:
        metrics = {
            "volume_type": record.get("volume_type"),
            "size_gb": record.get("size_gb"),
            "attached_instance_id": record.get("attached_instance_id"),
        }
        stmt = pg_insert(Resource).values(
            tenant_id=tenant_id,
            resource_id=record["volume_id"],
            service="EBS",
            region=record["region"],
            status=record["state"],
            metrics_json=metrics,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_resources_tenant_resource",
            set_={
                "status": stmt.excluded.status,
                "metrics_json": stmt.excluded.metrics_json,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        db.execute(stmt)

    return len(records)


def _upsert_rds_resources(db, tenant_id: uuid.UUID, records: list[dict]) -> int:
    """Upsert RDS instance records."""
    if not records:
        return 0

    for record in records:
        metrics = {
            "instance_class": record.get("instance_class"),
            "engine": record.get("engine"),
            "avg_cpu_percent": record.get("avg_cpu_percent"),
            "avg_connections": record.get("avg_connections"),
        }
        # Map RDS status to a consistent value
        status = record.get("status", "unknown")
        if status == "available":
            status = "running"  # RDS "available" = running

        stmt = pg_insert(Resource).values(
            tenant_id=tenant_id,
            resource_id=record["db_instance_id"],
            service="RDS",
            region=record["region"],
            status=status,
            metrics_json=metrics,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_resources_tenant_resource",
            set_={
                "status": stmt.excluded.status,
                "metrics_json": stmt.excluded.metrics_json,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        db.execute(stmt)

    return len(records)
