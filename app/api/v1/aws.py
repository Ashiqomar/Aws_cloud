"""
AWS endpoints — /api/v1/aws/*

POST /connect  — validate IAM Role credentials and register tenant.
POST /sync     — trigger async data ingestion via Celery.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tenant import Tenant
from app.schemas.aws import (
    AWSConnectRequest,
    AWSConnectResponse,
    AWSSyncRequest,
    AWSSyncResponse,
    ErrorResponse,
)
from app.services.aws_sts import assume_role, STSError
from app.tasks.sync_tasks import sync_aws_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/aws", tags=["AWS Integration"])


# ═══════════════════════════════════════════════════════════════════
#  POST /api/v1/aws/connect
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/connect",
    response_model=AWSConnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Connect an AWS account",
    description=(
        "Validates the provided IAM Role ARN + External ID by performing "
        "an STS AssumeRole call.  On success the tenant record is created "
        "or updated in the database."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid credentials or STS failure"},
    },
)
def connect_aws_account(
    body: AWSConnectRequest,
    db: Session = Depends(get_db),
) -> AWSConnectResponse:
    """Validate AWS credentials and upsert the tenant."""

    # 1. Attempt AssumeRole to verify credentials
    try:
        session = assume_role(
            role_arn=body.role_arn,
            external_id=body.external_id,
            session_name=f"finops-connect-{body.account_id}",
        )
        logger.info("AssumeRole validated for account %s", body.account_id)
    except STSError as exc:
        logger.warning("Connect failed for %s: %s", body.account_id, exc.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    # 2. Upsert tenant record
    tenant = db.execute(
        select(Tenant).where(Tenant.account_id == body.account_id)
    ).scalar_one_or_none()

    if tenant is None:
        tenant = Tenant(
            account_id=body.account_id,
            organization_name=body.organization_name,
            role_arn=body.role_arn,
            external_id=body.external_id,
            is_active=True,
        )
        db.add(tenant)
        message = "AWS account connected and tenant created."
    else:
        tenant.organization_name = body.organization_name
        tenant.role_arn = body.role_arn
        tenant.external_id = body.external_id
        tenant.is_active = True
        message = "AWS account reconnected — tenant updated."

    db.commit()
    db.refresh(tenant)

    return AWSConnectResponse(
        success=True,
        message=message,
        tenant_id=tenant.id,
        account_id=tenant.account_id,
    )


# ═══════════════════════════════════════════════════════════════════
#  POST /api/v1/aws/sync
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/sync",
    response_model=AWSSyncResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger an async AWS data sync",
    description=(
        "Queues a Celery task that fetches Cost Explorer data, EC2 "
        "utilization metrics, and generates savings recommendations "
        "for the given tenant."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Tenant not found"},
    },
)
def trigger_sync(
    body: AWSSyncRequest,
    db: Session = Depends(get_db),
) -> AWSSyncResponse:
    """Dispatch the background sync task."""

    # Verify tenant exists
    tenant = db.execute(
        select(Tenant).where(Tenant.id == body.tenant_id)
    ).scalar_one_or_none()

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {body.tenant_id} not found.",
        )
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant {body.tenant_id} is inactive. Reconnect first.",
        )

    # Dispatch Celery task
    task = sync_aws_data.delay(str(body.tenant_id))
    logger.info(
        "Sync task %s queued for tenant %s",
        task.id, body.tenant_id,
    )

    return AWSSyncResponse(
        success=True,
        message="Sync task queued successfully.",
        task_id=task.id,
    )
