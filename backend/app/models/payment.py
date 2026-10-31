"""
Payment Model for Brightloop Nexus (Member 2).
Enforces transactional balance updates, partial payments, and audit histories.
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


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_payment_amount_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_reference: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    recorded_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    payment_method: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # CASH, BANK_TRANSFER, CARD, UPI, SIMULATED
    payment_status: Mapped[str] = mapped_column(
        String(50), default="SUCCESSFUL", nullable=False, index=True
    )  # PENDING, SUCCESSFUL, FAILED, REFUNDED
    transaction_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(120), unique=True, nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")
    customer: Mapped["Customer"] = relationship("Customer")

    def __repr__(self) -> str:
        return f"<Payment(ref='{self.payment_reference}', inv={self.invoice_id}, amount={self.amount}, status='{self.payment_status}')>"

