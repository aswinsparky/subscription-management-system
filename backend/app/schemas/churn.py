"""
Churn Radar & Behavioral Risk Analytics Schemas (Module 8).
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ChurnRiskSignal(BaseModel):
    signal_key: str
    signal_name: str
    weight: int
    severity: str  # INFO, WARNING, CRITICAL
    description: str
    recommended_action: str


class CustomerRiskProfile(BaseModel):
    customer_id: int
    customer_code: str
    full_name: str
    email: str
    company_name: Optional[str] = None
    risk_score: int  # 0 to 100
    risk_tier: str  # LOW, MEDIUM, HIGH
    active_subscriptions_count: int
    total_mrr: Decimal
    signals: List[ChurnRiskSignal]
    suggested_retention_playbook: str


class ChurnDashboardMetrics(BaseModel):
    total_customers_analyzed: int
    avg_risk_score: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    at_risk_mrr: Decimal
    top_at_risk_customers: List[CustomerRiskProfile]


class RetentionActionRequest(BaseModel):
    action_type: str  # DISCOUNT_OFFER, PLAN_CONSULTATION, SUPPORT_OUTREACH, PAUSE_EXTENDED
    notes: str
    discount_percent_offered: Optional[int] = None


class RetentionActionResponse(BaseModel):
    customer_id: int
    action_type: str
    notes: str
    recorded_at: datetime
    recorded_by: str
    status: str

