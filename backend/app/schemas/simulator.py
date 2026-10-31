"""
Pydantic v2 Schemas for Future Revenue Simulator (Member 2).
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SimulationRequest(BaseModel):
    scenario_name: str = Field(default="Base Scenario", example="Aggressive Growth Q1")
    new_customers_monthly: int = Field(default=5, ge=0, example=10)
    churn_rate_percent: Decimal = Field(default=Decimal("3.0"), ge=0, le=100, example=Decimal("2.5"))
    plan_upgrade_rate_percent: Decimal = Field(default=Decimal("5.0"), ge=0, le=100, example=Decimal("8.0"))
    price_change_percent: Decimal = Field(default=Decimal("0.0"), ge=-100, le=500, example=Decimal("10.0"))
    discount_campaign_impact_percent: Decimal = Field(default=Decimal("0.0"), ge=0, le=100, example=Decimal("5.0"))
    projection_months: int = Field(default=12, ge=3, le=36, example=12)


class MonthlyForecastPoint(BaseModel):
    month_index: int
    month_label: str
    baseline_revenue: Decimal
    projected_revenue: Decimal
    new_revenue: Decimal
    churned_revenue: Decimal
    net_growth: Decimal
    active_subscriptions: int


class SimulationResponse(BaseModel):
    scenario_name: str
    baseline_mrr: Decimal
    projected_mrr: Decimal
    net_mrr_impact: Decimal
    baseline_arr: Decimal
    projected_arr: Decimal
    growth_rate_percent: Decimal
    assumptions_used: Dict[str, Any]
    monthly_forecast: List[MonthlyForecastPoint]

