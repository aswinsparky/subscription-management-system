"""
Invoice, Invoice Items, Tax Details, Discount Details, and Generation Logs.
Monetary precision strictly adheres to DECIMAL(12, 2).
Provides idempotent recurring generation and audit trail snapshots.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
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


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="chk_inv_subtotal_non_negative"),
        CheckConstraint("discount_amount >= 0", name="chk_inv_discount_non_negative"),
        CheckConstraint("tax_amount >= 0", name="chk_inv_tax_non_negative"),
        CheckConstraint("total_amount >= 0", name="chk_inv_total_non_negative"),
        CheckConstraint("amount_paid >= 0", name="chk_inv_paid_non_negative"),
        CheckConstraint("amount_due >= 0", name="chk_inv_due_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    subscription_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    invoice_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="DRAFT", nullable=False, index=True
    )  # DRAFT, CONFIRMED, PAID, PARTIALLY_PAID, OVERDUE, CANCELLED
    billing_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    billing_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    amount_due: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    payment_terms: Mapped[str] = mapped_column(
        String(100), default="Immediate", nullable=False
    )  # Immediate, Net 15, Net 30, Net 60
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(120), unique=True, nullable=True, index=True
    )
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
    customer: Mapped["Customer"] = relationship("Customer")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription")
    items: Mapped[List["InvoiceItem"]] = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )
    tax_details: Mapped[List["InvoiceTaxDetail"]] = relationship(
        "InvoiceTaxDetail", back_populates="invoice", cascade="all, delete-orphan"
    )
    discount_details: Mapped[List["InvoiceDiscountDetail"]] = relationship(
        "InvoiceDiscountDetail", back_populates="invoice", cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="invoice"
    )

    def recalculate_totals(self) -> None:
        """Deterministically recalculate subtotal, taxes, discounts, totals, and balances."""
        item_subtotal = sum((item.subtotal for item in self.items), Decimal("0.00"))
        self.subtotal = item_subtotal.quantize(Decimal("0.01"))
        
        # Calculate discount sum
        total_discount = sum((d.calculated_discount_amount for d in self.discount_details), Decimal("0.00"))
        self.discount_amount = min(total_discount, self.subtotal).quantize(Decimal("0.01"))
        
        # Calculate tax sum
        total_tax = sum((t.calculated_tax_amount for t in self.tax_details), Decimal("0.00"))
        self.tax_amount = total_tax.quantize(Decimal("0.01"))
        
        # Final amount = Subtotal - Discount + Tax
        final_total = max(Decimal("0.00"), self.subtotal - self.discount_amount + self.tax_amount)
        self.total_amount = final_total.quantize(Decimal("0.01"))
        
        # Balance = Total - Paid
        self.amount_due = max(Decimal("0.00"), self.total_amount - self.amount_paid).quantize(Decimal("0.01"))

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', status='{self.status}', total={self.total_amount}, due={self.amount_due})>"


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="chk_inv_item_qty_positive"),
        CheckConstraint("unit_price >= 0", name="chk_inv_item_price_non_negative"),
        CheckConstraint("subtotal >= 0", name="chk_inv_item_subtotal_non_negative"),
        CheckConstraint("total_amount >= 0", name="chk_inv_item_total_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    product_variant_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True
    )
    subscription_item_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("subscription_items.id", ondelete="SET NULL"), nullable=True
    )
    item_description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    tax_rate_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    tax_amount_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")


class InvoiceTaxDetail(Base):
    __tablename__ = "invoice_tax_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tax_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("taxes.id", ondelete="SET NULL"), nullable=True
    )
    tax_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_rate_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    calculated_tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="tax_details")


class InvoiceDiscountDetail(Base):
    __tablename__ = "invoice_discount_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    discount_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("discounts.id", ondelete="SET NULL"), nullable=True
    )
    coupon_code_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    discount_type_snapshot: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_rate_or_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    calculated_discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="discount_details")


class InvoiceGenerationLog(Base):
    __tablename__ = "invoice_generation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    billing_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    billing_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # SUCCESS, FAILED, SKIPPED
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invoice_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

