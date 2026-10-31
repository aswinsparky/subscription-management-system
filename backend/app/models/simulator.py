"""
Revenue Simulator Scenarios and Historical Projections Model for Brightloop Nexus (Member 2).
Persists forecasting scenarios, assumptions, and comparisons against actual baselines.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from sqlalchemy import (
    String,
    Text,
    Numeric,
    DateTime,
    Integer,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RevenueSimulationScenario(Base):
    __tablename__ = "revenue_simulation_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    baseline_mrr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    projected_mrr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    net_mrr_impact: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    baseline_arr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    projected_arr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    assumptions_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    monthly_forecast_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<RevenueSimulationScenario(id={self.id}, name='{self.scenario_name}', impact={self.net_mrr_impact})>"

