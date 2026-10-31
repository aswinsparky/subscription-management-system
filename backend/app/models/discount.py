"""
Discount and Coupon Management Models for Brightloop Nexus.
Enforces coupon rules, redemption limits, per-customer limits, and minimum spend.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any
from sqlalchemy import (
    String,
    Text,
    Boolean,
    Numeric,
    DateTime,
    Integer,
    ForeignKey,
    JSON,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Discount(Base):
    __tablename__ = "discounts"
    __table_args__ = (
        CheckConstraint("discount_value >= 0", name="chk_discount_value_non_negative"),
        CheckConstraint("min_purchase_amount >= 0", name="chk_discount_min_purchase_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    coupon_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    discount_type: Mapped[str] = mapped_column(
        String(20), default="PERCENTAGE", nullable=False
    )  # PERCENTAGE | FIXED
    discount_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    min_purchase_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    min_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usage_per_customer_limit: Mapped[Optional[int]] = mapped_column(Integer, default=1, nullable=True)
    current_usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applicable_product_ids: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)
    applicable_plan_ids: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Usages relationship
    usages: Mapped[List["DiscountUsage"]] = relationship(
        "DiscountUsage", back_populates="discount", cascade="all, delete-orphan"
    )

    def calculate_discount_amount(self, subtotal: Decimal) -> Decimal:
        """Calculate discount on eligible subtotal without exceeding subtotal."""
        if self.discount_type == "PERCENTAGE":
            discount = (subtotal * (self.discount_value / Decimal("100.00"))).quantize(Decimal("0.01"))
        else:
            discount = self.discount_value.quantize(Decimal("0.01"))
        return min(discount, subtotal)

    def is_eligible(
        self,
        subtotal: Decimal,
        quantity: int = 1,
        customer_usage_count: int = 0,
        product_ids: Optional[List[int]] = None,
        plan_id: Optional[int] = None,
        as_of: Optional[datetime] = None,
    ) -> tuple[bool, str]:
        """Validate coupon eligibility and return (is_valid, reason)."""
        if not self.is_active:
            return False, "Coupon is inactive."

        now = as_of or datetime.utcnow()
        if self.start_date and now < self.start_date:
            return False, "Coupon is not yet active."
        if self.end_date and now > self.end_date:
            return False, "Coupon has expired."

        if self.max_usage_limit is not None and self.current_usage_count >= self.max_usage_limit:
            return False, "Coupon maximum overall usage limit has been reached."

        if self.usage_per_customer_limit is not None and customer_usage_count >= self.usage_per_customer_limit:
            return False, f"Coupon usage limit per customer ({self.usage_per_customer_limit}) exceeded."

        if subtotal < self.min_purchase_amount:
            return False, f"Minimum purchase amount of {self.min_purchase_amount} required."

        if quantity < self.min_quantity:
            return False, f"Minimum quantity of {self.min_quantity} required."

        if self.applicable_plan_ids and plan_id is not None:
            if plan_id not in self.applicable_plan_ids:
                return False, "Coupon is not applicable to this subscription plan."

        if self.applicable_product_ids and product_ids:
            if not any(pid in self.applicable_product_ids for pid in product_ids):
                return False, "Coupon is not applicable to the selected items."

        return True, "Eligible"

    def __repr__(self) -> str:
        return f"<Discount(code='{self.coupon_code}', type='{self.discount_type}', val={self.discount_value})>"


class DiscountUsage(Base):
    __tablename__ = "discount_usages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    discount_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("discounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True
    )
    discount_amount_applied: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    discount: Mapped["Discount"] = relationship("Discount", back_populates="usages")

    def __repr__(self) -> str:
        return f"<DiscountUsage(id={self.id}, discount_id={self.discount_id}, customer_id={self.customer_id}, amount={self.discount_amount_applied})>"

