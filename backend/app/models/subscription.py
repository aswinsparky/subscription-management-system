"""
Subscription, Subscription Items, Time Machine Events, and Renewal Billing Models.
Monetary values use DECIMAL(12, 2). Events are append-only.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    String,
    Text,
    Boolean,
    Numeric,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="chk_sub_subtotal_non_negative"),
        CheckConstraint("total_amount >= 0", name="chk_sub_total_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_quotation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    billing_interval: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # DAILY, WEEKLY, MONTHLY, YEARLY
    payment_terms: Mapped[str] = mapped_column(String(100), default="Immediate", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Applied discount rule reference
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="DRAFT", nullable=False, index=True
    )  # DRAFT, QUOTATION, CONFIRMED, ACTIVE, PAUSED, CANCELLED, CLOSED
    next_billing_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_renewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship("Plan")
    items: Mapped[List["SubscriptionItem"]] = relationship(
        "SubscriptionItem", back_populates="subscription", cascade="all, delete-orphan"
    )
    events: Mapped[List["SubscriptionEvent"]] = relationship(
        "SubscriptionEvent", back_populates="subscription", cascade="all, delete-orphan", order_by="SubscriptionEvent.created_at"
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, number='{self.subscription_number}', status='{self.status}', total={self.total_amount})>"


class SubscriptionItem(Base):
    __tablename__ = "subscription_items"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="chk_sub_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="chk_sub_item_unit_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    variant_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="items")
    product: Mapped["Product"] = relationship("Product")
    variant: Mapped[Optional["ProductVariant"]] = relationship("ProductVariant")


class SubscriptionEvent(Base):
    """
    Time Machine Event Store: Append-only ledger of all subscription transitions.
    Never update or delete records in this table.
    """
    __tablename__ = "subscription_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # CREATED, QUOTATION_ACCEPTED, CONFIRMED, ACTIVATED, PAUSED, RESUMED, RENEWED, CANCELLED, CLOSED, PLAN_CHANGED, QUANTITY_CHANGED
    previous_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    new_state: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    actor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="events")
    actor: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<SubscriptionEvent(id={self.id}, sub_id={self.subscription_id}, event='{self.event_type}')>"


class RenewalBillingRequest(Base):
    """
    Renewal Billing Requests tracking table.
    Uses idempotency keys to ensure duplicate renewals are prevented.
    """
    __tablename__ = "renewal_billing_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    billing_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    billing_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False, index=True
    )  # PENDING, PROCESSED, FAILED
    invoice_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Generated Invoice reference
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

