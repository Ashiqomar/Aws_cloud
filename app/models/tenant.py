"""
Tenant model — represents a customer AWS account linked to the platform.

Each tenant stores the IAM Role ARN and external ID required for
cross-account AssumeRole access.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    account_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
        comment="AWS Account ID (12-digit)",
    )
    organization_name: Mapped[str] = mapped_column(
        String(256), nullable=False,
    )
    role_arn: Mapped[str] = mapped_column(
        String(512), nullable=False,
        comment="IAM Role ARN for cross-account AssumeRole",
    )
    external_id: Mapped[str] = mapped_column(
        String(256), nullable=False,
        comment="STS external ID for the trust policy",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
    )

    # ── Timestamps ───────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Tenant {self.organization_name} ({self.account_id})>"
