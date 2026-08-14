"""
Resource model — cloud asset inventory.

Tracks every AWS resource discovered during a sync (EC2 instances, RDS
databases, etc.) along with flexible JSON metrics.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "resource_id",
            name="uq_resources_tenant_resource",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[str] = mapped_column(
        String(256), nullable=False,
        comment="AWS resource identifier, e.g. i-0abc123def456",
    )
    service: Mapped[str] = mapped_column(
        String(128), nullable=False,
        comment="AWS service, e.g. 'EC2', 'RDS', 'Lambda'",
    )
    region: Mapped[str] = mapped_column(
        String(64), nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unknown",
        comment="e.g. 'running', 'stopped', 'terminated'",
    )
    metrics_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=None,
        comment="Flexible store for CloudWatch metrics, tags, etc.",
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
        return f"<Resource {self.service}/{self.resource_id} ({self.status})>"
