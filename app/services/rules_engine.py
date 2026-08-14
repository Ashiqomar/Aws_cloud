"""
Rules Engine — heuristic analysis for cost-saving recommendations.

Scans the ``resources`` table in PostgreSQL and applies three detection
heuristics to identify waste:

1. **Idle EC2**       — avg CPU < threshold over 14 days
2. **Unused EBS**     — volumes in ``available`` state (unattached)
3. **Oversized RDS**  — low CPU *or* low connection count

Results are written to the ``recommendations`` table with estimated
monthly savings derived from the pricing reference.

All functions accept a SQLAlchemy ``Session`` and a ``tenant_id`` and
return the count of new recommendations created.  Existing open
recommendations for the same resource+type are skipped to avoid
duplicates.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.resource import Resource
from app.models.recommendation import Recommendation
from app.services.pricing import (
    ec2_monthly_cost,
    ec2_downsize_savings,
    ebs_monthly_cost,
    rds_monthly_cost,
    rds_downsize_savings,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
#  THRESHOLDS  (tune per org requirements)
# ═══════════════════════════════════════════════════════════════════
IDLE_EC2_CPU_THRESHOLD = 5.0          # percent
OVERSIZED_RDS_CPU_THRESHOLD = 15.0    # percent
OVERSIZED_RDS_CONN_THRESHOLD = 5      # avg connections


# ═══════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════

def _safe_float(metrics: dict | None, key: str) -> float | None:
    """Extract a float from metrics_json, returning None on any failure."""
    if not metrics:
        return None
    val = metrics.get(key)
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(metrics: dict | None, key: str) -> int | None:
    """Extract an int from metrics_json, returning None on any failure."""
    if not metrics:
        return None
    val = metrics.get(key)
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _safe_str(metrics: dict | None, key: str) -> str | None:
    """Extract a string from metrics_json, returning None on any failure."""
    if not metrics:
        return None
    val = metrics.get(key)
    return str(val) if val is not None else None


def _recommendation_exists(
    db: Session,
    tenant_id: uuid.UUID,
    resource_id: str,
    reco_type: str,
) -> bool:
    """Return True if an open recommendation of this type already exists."""
    row = db.execute(
        select(Recommendation.id).where(
            Recommendation.tenant_id == tenant_id,
            Recommendation.resource_id == resource_id,
            Recommendation.type == reco_type,
            Recommendation.status == "open",
        )
    ).first()
    return row is not None


# ═══════════════════════════════════════════════════════════════════
#  RULE 1 — Idle EC2 Instances
# ═══════════════════════════════════════════════════════════════════

def detect_idle_ec2(db: Session, tenant_id: uuid.UUID) -> int:
    """
    Flag EC2 instances whose average CPU utilization is below
    ``IDLE_EC2_CPU_THRESHOLD`` over the past 14 days.

    Savings estimate:
    - For **idle** instances (CPU < threshold): full monthly cost
      of the instance (assumption: it can be stopped entirely).

    Returns the number of *new* recommendations created.
    """
    resources = db.execute(
        select(Resource).where(
            Resource.tenant_id == tenant_id,
            Resource.service == "EC2",
            Resource.status == "running",
        )
    ).scalars().all()

    created = 0
    for res in resources:
        avg_cpu = _safe_float(res.metrics_json, "avg_cpu_percent")

        # Skip if no CPU data available
        if avg_cpu is None:
            logger.debug(
                "Skipping %s — no CPU metric available", res.resource_id
            )
            continue

        if avg_cpu >= IDLE_EC2_CPU_THRESHOLD:
            continue

        if _recommendation_exists(db, tenant_id, res.resource_id, "idle_ec2"):
            continue

        # Estimate savings — full instance cost (stop it)
        instance_type = _safe_str(res.metrics_json, "instance_type") or "unknown"
        monthly_cost = ec2_monthly_cost(instance_type) or 0.0

        reco = Recommendation(
            tenant_id=tenant_id,
            resource_id=res.resource_id,
            type="idle_ec2",
            detail=(
                f"EC2 instance {res.resource_id} ({instance_type}) in "
                f"{res.region} has an average CPU of {avg_cpu:.1f}% — "
                f"below the {IDLE_EC2_CPU_THRESHOLD}% threshold. "
                f"Consider stopping or terminating this instance to "
                f"save ~${monthly_cost:.2f}/month."
            ),
            estimated_savings_monthly=monthly_cost,
            status="open",
        )
        db.add(reco)
        created += 1
        logger.info(
            "Recommendation: idle_ec2 for %s (CPU=%.1f%%, save=$%.2f/mo)",
            res.resource_id, avg_cpu, monthly_cost,
        )

    return created


# ═══════════════════════════════════════════════════════════════════
#  RULE 2 — Unused EBS Volumes
# ═══════════════════════════════════════════════════════════════════

def detect_unused_ebs(db: Session, tenant_id: uuid.UUID) -> int:
    """
    Flag EBS volumes whose status is ``available`` (not attached to
    any instance).

    Savings estimate: full monthly storage cost based on volume type
    and size.

    Returns the number of *new* recommendations created.
    """
    resources = db.execute(
        select(Resource).where(
            Resource.tenant_id == tenant_id,
            Resource.service == "EBS",
            Resource.status == "available",
        )
    ).scalars().all()

    created = 0
    for res in resources:
        if _recommendation_exists(db, tenant_id, res.resource_id, "unused_ebs"):
            continue

        volume_type = _safe_str(res.metrics_json, "volume_type") or "gp2"
        size_gb = _safe_int(res.metrics_json, "size_gb") or 0
        monthly_cost = ebs_monthly_cost(volume_type, size_gb)

        reco = Recommendation(
            tenant_id=tenant_id,
            resource_id=res.resource_id,
            type="unused_ebs",
            detail=(
                f"EBS volume {res.resource_id} ({volume_type}, {size_gb} GB) "
                f"in {res.region} is unattached. "
                f"Delete or snapshot-and-delete to save ~${monthly_cost:.2f}/month."
            ),
            estimated_savings_monthly=monthly_cost,
            status="open",
        )
        db.add(reco)
        created += 1
        logger.info(
            "Recommendation: unused_ebs for %s (%s, %dGB, save=$%.2f/mo)",
            res.resource_id, volume_type, size_gb, monthly_cost,
        )

    return created


# ═══════════════════════════════════════════════════════════════════
#  RULE 3 — Oversized RDS Instances
# ═══════════════════════════════════════════════════════════════════

def detect_oversized_rds(db: Session, tenant_id: uuid.UUID) -> int:
    """
    Flag RDS instances that appear over-provisioned based on:
    - avg CPU < ``OVERSIZED_RDS_CPU_THRESHOLD``  **OR**
    - avg connection count < ``OVERSIZED_RDS_CONN_THRESHOLD``

    Savings estimate: cost delta between the current instance class
    and the next smaller class in the downsize map.

    Returns the number of *new* recommendations created.
    """
    resources = db.execute(
        select(Resource).where(
            Resource.tenant_id == tenant_id,
            Resource.service == "RDS",
            Resource.status.in_(["available", "running"]),
        )
    ).scalars().all()

    created = 0
    for res in resources:
        avg_cpu = _safe_float(res.metrics_json, "avg_cpu_percent")
        avg_conns = _safe_float(res.metrics_json, "avg_connections")
        instance_class = _safe_str(res.metrics_json, "instance_class") or "unknown"

        # Need at least one metric to evaluate
        if avg_cpu is None and avg_conns is None:
            logger.debug(
                "Skipping RDS %s — no CPU or connection metrics", res.resource_id
            )
            continue

        is_low_cpu = avg_cpu is not None and avg_cpu < OVERSIZED_RDS_CPU_THRESHOLD
        is_low_conns = avg_conns is not None and avg_conns < OVERSIZED_RDS_CONN_THRESHOLD

        if not (is_low_cpu or is_low_conns):
            continue

        if _recommendation_exists(db, tenant_id, res.resource_id, "oversized_rds"):
            continue

        # Determine savings
        smaller_class, savings = rds_downsize_savings(instance_class)

        # Build reason parts
        reasons: list[str] = []
        if is_low_cpu:
            reasons.append(f"avg CPU {avg_cpu:.1f}%")
        if is_low_conns:
            reasons.append(f"avg connections {avg_conns:.0f}")
        reason_str = " and ".join(reasons)

        if smaller_class:
            detail = (
                f"RDS instance {res.resource_id} ({instance_class}) in "
                f"{res.region} shows low utilization ({reason_str}). "
                f"Downsize to {smaller_class} to save ~${savings:.2f}/month."
            )
        else:
            # No downsize path known — still flag, savings = 0
            detail = (
                f"RDS instance {res.resource_id} ({instance_class}) in "
                f"{res.region} shows low utilization ({reason_str}). "
                f"Review workload and consider downsizing."
            )

        reco = Recommendation(
            tenant_id=tenant_id,
            resource_id=res.resource_id,
            type="oversized_rds",
            detail=detail,
            estimated_savings_monthly=savings,
            status="open",
        )
        db.add(reco)
        created += 1
        logger.info(
            "Recommendation: oversized_rds for %s (%s, save=$%.2f/mo)",
            res.resource_id, reason_str, savings,
        )

    return created


# ═══════════════════════════════════════════════════════════════════
#  AGGREGATE RUNNER
# ═══════════════════════════════════════════════════════════════════

def run_all_rules(db: Session, tenant_id: uuid.UUID) -> dict[str, int]:
    """
    Execute every heuristic rule for a tenant and return a summary.

    Returns
    -------
    dict
        ``{"idle_ec2": N, "unused_ebs": N, "oversized_rds": N, "total": N}``
    """
    idle = detect_idle_ec2(db, tenant_id)
    ebs = detect_unused_ebs(db, tenant_id)
    rds = detect_oversized_rds(db, tenant_id)

    summary = {
        "idle_ec2": idle,
        "unused_ebs": ebs,
        "oversized_rds": rds,
        "total": idle + ebs + rds,
    }
    logger.info(
        "Rules engine complete for tenant %s: %s",
        tenant_id, summary,
    )
    return summary
