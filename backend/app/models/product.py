"""
Product and Product Variant Models.
Monetary values use DECIMAL(12, 2) to eliminate rounding errors.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Boolean,
    Numeric,
    DateTime,
    ForeignKey,
    Integer,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("sales_price >= 0", name="chk_product_sales_price_non_negative"),
        CheckConstraint("cost_price >= 0", name="chk_product_cost_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    product_type: Mapped[str] = mapped_column(
        String(50), default="SOFTWARE", nullable=False, index=True
    )  # SERVICE, SOFTWARE, HARDWARE, CONSUMABLE
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sales_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
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
    variants: Mapped[List["ProductVariant"]] = relationship(
        "ProductVariant", back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, code='{self.product_code}', name='{self.name}', price={self.sales_price})>"


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        CheckConstraint("additional_price >= 0", name="chk_variant_additional_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. Standard, Odoo, Enterprise
    sku: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    additional_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="variants")

    def __repr__(self) -> str:
        return f"<ProductVariant(id={self.id}, product_id={self.product_id}, name='{self.variant_name}', +{self.additional_price})>"

