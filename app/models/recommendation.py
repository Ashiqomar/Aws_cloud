"""
Recommendation model — detected savings opportunities.

Each recommendation links to a specific resource and includes the
estimated monthly savings and a lifecycle status.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

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
        comment="AWS resource identifier the recommendation targets",
    )
    type: Mapped[str] = mapped_column(
        String(128), nullable=False,
        comment="Category: 'rightsizing', 'idle_resource', 'reserved_instance', etc.",
    )
    detail: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Human-readable explanation of the recommendation",
    )
    estimated_savings_monthly: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="open",
        comment="Lifecycle: 'open', 'applied', 'dismissed'",
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
        return f"<Recommendation {self.type} | ${self.estimated_savings_monthly}/mo ({self.status})>"
