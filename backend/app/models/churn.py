"""
Churn Risk Assessment Model for Churn Radar (Module 8).
Stores deterministic churn risk scores (0-100), classifications, and signal breakdowns.
"""
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ChurnRiskAssessment(Base):
    __tablename__ = "churn_risk_assessments"
    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="chk_churn_risk_score_0_to_100"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 0 to 100
    risk_classification: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # LOW, MEDIUM, HIGH
    risk_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    signal_breakdown: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="churn_assessments")

    def __repr__(self) -> str:
        return f"<ChurnRiskAssessment(customer_id={self.customer_id}, score={self.risk_score}, class='{self.risk_classification}')>"

