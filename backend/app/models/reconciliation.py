"""
Payment Reconciliation Model for Brightloop Nexus (Member 2).
Audits financial matching between invoices and payment receipts.
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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PaymentReconciliation(Base):
    __tablename__ = "payment_reconciliations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    invoice_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reconciled_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="MATCHED", nullable=False, index=True
    )  # MATCHED, PARTIALLY_MATCHED, UNMATCHED, DISCREPANCY, RESOLVED
    invoice_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    payment_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    discrepancy_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reconciled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    payment: Mapped[Optional["Payment"]] = relationship("Payment")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice")

    def __repr__(self) -> str:
        return f"<PaymentReconciliation(id={self.id}, status='{self.status}', discrepancy={self.discrepancy_amount})>"

