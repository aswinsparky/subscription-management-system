"""
Tax Model for Brightloop Nexus.
Supports percentage-based and fixed-amount taxes with historical snapshot preservation.
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


class Tax(Base):
    __tablename__ = "taxes"
    __table_args__ = (
        CheckConstraint("rate >= 0", name="chk_tax_rate_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tax_type: Mapped[str] = mapped_column(
        String(20), default="PERCENTAGE", nullable=False
    )  # PERCENTAGE | FIXED
    rate: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    applicability: Mapped[str] = mapped_column(
        String(50), default="ALL", nullable=False
    )  # ALL | PRODUCT_SPECIFIC | SERVICE_SPECIFIC
    effective_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    effective_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
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

    def is_currently_effective(self, as_of: Optional[datetime] = None) -> bool:
        """Check if tax rule is effective at given timestamp."""
        if not self.is_active:
            return False
        now = as_of or datetime.utcnow()
        if self.effective_from and now < self.effective_from:
            return False
        if self.effective_until and now > self.effective_until:
            return False
        return True

    def calculate_tax(self, amount: Decimal) -> Decimal:
        """Calculate tax on given base amount."""
        if self.tax_type == "PERCENTAGE":
            return (amount * (self.rate / Decimal("100.00"))).quantize(Decimal("0.01"))
        return self.rate.quantize(Decimal("0.01"))

    def __repr__(self) -> str:
        return f"<Tax(id={self.id}, name='{self.name}', type='{self.tax_type}', rate={self.rate}, active={self.is_active})>"

