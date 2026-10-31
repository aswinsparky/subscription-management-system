"""
Self-Healing Billing and Failure Recovery Tracking Models for Brightloop Nexus.
Enforces safe retry attempts, exponential delays, and idempotency protection.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Integer,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BillingRecoveryAttempt(Base):
    __tablename__ = "billing_recovery_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    failure_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # PAYMENT_FAILED, INVOICE_GENERATION_FAILED, RECONCILIATION_ERROR
    failure_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recovery_status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False, index=True
    )  # PENDING, RETRYING, RECOVERED, FAILED_PERMANENTLY
    idempotency_key: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False, index=True
    )
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice")
    payment: Mapped[Optional["Payment"]] = relationship("Payment")

    def __repr__(self) -> str:
        return f"<BillingRecoveryAttempt(id={self.id}, sub={self.subscription_id}, status='{self.recovery_status}', retries={self.retry_count}/{self.max_retries})>"

