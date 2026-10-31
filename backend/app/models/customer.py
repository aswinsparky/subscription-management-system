"""
Customer Model for Brightloop Nexus.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    billing_address: Mapped[str] = mapped_column(Text, nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    account_status: Mapped[str] = mapped_column(
        String(50), default="ACTIVE", nullable=False, index=True
    )  # ACTIVE, SUSPENDED, ARCHIVED
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
    user: Mapped[Optional["User"]] = relationship("User", back_populates="customer_profile")
    quotations: Mapped[List["Quotation"]] = relationship(
        "Quotation", back_populates="customer", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="customer", cascade="all, delete-orphan"
    )
    churn_assessments: Mapped[List["ChurnRiskAssessment"]] = relationship(
        "ChurnRiskAssessment", back_populates="customer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, code='{self.customer_code}', name='{self.full_name}')>"

