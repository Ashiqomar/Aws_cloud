"""
CostDaily model — one row per (tenant, date, service).

Stores daily cost data ingested from AWS Cost Explorer, grouped by
AWS service name.
"""

import uuid
from datetime import date as date_type, datetime, timezone

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CostDaily(Base):
    __tablename__ = "cost_daily"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "date", "service_name",
            name="uq_cost_daily_tenant_date_service",
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
    date: Mapped[date_type] = mapped_column(
        Date, nullable=False,
    )
    service_name: Mapped[str] = mapped_column(
        String(256), nullable=False,
        comment="AWS service name, e.g. 'Amazon EC2', 'Amazon S3'",
    )
    amount: Mapped[float] = mapped_column(
        Numeric(14, 4), nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, default="USD",
    )

    # ── Timestamps ───────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<CostDaily {self.date} | {self.service_name} | ${self.amount}>"
