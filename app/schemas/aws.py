"""
Pydantic schemas for the /api/v1/aws/* endpoints.

Separates request bodies and response payloads from ORM models to keep
the API contract clean and versioned independently.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
#  REQUEST schemas
# ═══════════════════════════════════════════════════════════════════

class AWSConnectRequest(BaseModel):
    """POST /api/v1/aws/connect — link an AWS account."""
    account_id: str = Field(
        ..., min_length=12, max_length=12,
        description="12-digit AWS Account ID",
        examples=["123456789012"],
    )
    organization_name: str = Field(
        ..., min_length=1, max_length=256,
        description="Human-readable name for the tenant / org",
        examples=["Acme Corp"],
    )
    role_arn: str = Field(
        ..., pattern=r"^arn:aws:iam::\d{12}:role/.+$",
        description="Full IAM Role ARN to assume",
        examples=["arn:aws:iam::123456789012:role/FinOpsCrossAccountRole"],
    )
    external_id: str = Field(
        ..., min_length=1, max_length=256,
        description="External ID configured in the role trust policy",
        examples=["finops-ext-abc123"],
    )


class AWSSyncRequest(BaseModel):
    """POST /api/v1/aws/sync — trigger a data sync for a tenant."""
    tenant_id: uuid.UUID = Field(
        ...,
        description="UUID of the tenant to sync",
    )


# ═══════════════════════════════════════════════════════════════════
#  RESPONSE schemas
# ═══════════════════════════════════════════════════════════════════

class AWSConnectResponse(BaseModel):
    """Returned after a successful connect attempt."""
    success: bool
    message: str
    tenant_id: uuid.UUID
    account_id: str


class AWSSyncResponse(BaseModel):
    """Returned after queuing a sync task."""
    success: bool
    message: str
    task_id: str


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    success: bool = False
    error: str
    detail: str | None = None
