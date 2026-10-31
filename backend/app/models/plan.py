"""
Subscription Plan Model.
Defines plan pricing, intervals, availability dates, and lifecycle permissions.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    Boolean,
    Numeric,
    DateTime,
    Integer,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        CheckConstraint("plan_price >= 0", name="chk_plan_price_non_negative"),
        CheckConstraint("minimum_quantity >= 1", name="chk_plan_min_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    billing_interval: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # DAILY, WEEKLY, MONTHLY, YEARLY
    plan_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    minimum_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    available_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_close_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    early_cancellation_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pause_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    renewal_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="ACTIVE", nullable=False, index=True
    )  # DRAFT, ACTIVE, ARCHIVED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Plan(id={self.id}, code='{self.plan_code}', interval='{self.billing_interval}', price={self.plan_price})>"

