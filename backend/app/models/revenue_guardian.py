"""
Revenue Guardian Anomaly Detection & Financial Leakage Audit Models.
Stores audit findings, severity classifications, and authorized resolution workflows.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    Numeric,
    DateTime,
    Integer,
    ForeignKey,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class RevenueGuardianFinding(Base):
    __tablename__ = "revenue_guardian_findings"
    __table_args__ = (
        CheckConstraint("estimated_loss >= 0", name="chk_guardian_loss_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    issue_title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # MISSING_INVOICE, DUPLICATE_INVOICE, INCORRECT_TOTAL, TAX_MISMATCH, OVERDUE_BALANCE, UNMATCHED_PAYMENT, FAILED_PAYMENT, BILLING_CYCLE_GAP
    severity: Mapped[str] = mapped_column(
        String(20), default="MEDIUM", nullable=False, index=True
    )  # CRITICAL, HIGH, MEDIUM, LOW
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subscription_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    invoice_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    estimated_loss: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_status: Mapped[str] = mapped_column(
        String(50), default="OPEN", nullable=False, index=True
    )  # OPEN, IN_REVIEW, RESOLVED, DISMISSED
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship("Customer")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice")
    payment: Mapped[Optional["Payment"]] = relationship("Payment")

    def __repr__(self) -> str:
        return f"<RevenueGuardianFinding(id={self.id}, code='{self.issue_code}', severity='{self.severity}', status='{self.resolution_status}')>"


class RevenueGuardianRun(Base):
    __tablename__ = "revenue_guardian_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_type: Mapped[str] = mapped_column(String(50), default="MANUAL", nullable=False)
    triggered_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    issues_found_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    critical_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_leakage_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

