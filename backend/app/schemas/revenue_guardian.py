"""
Pydantic v2 Schemas for Revenue Guardian Anomaly Detection (Member 2).
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class RevenueGuardianFindingResponse(BaseModel):
    id: int
    issue_code: str
    issue_title: str
    category: str
    severity: str
    customer_id: Optional[int]
    subscription_id: Optional[int]
    invoice_id: Optional[int]
    payment_id: Optional[int]
    estimated_loss: Decimal
    explanation: str
    recommended_action: str
    resolution_status: str
    detected_at: datetime
    resolved_at: Optional[datetime]
    resolved_by_user_id: Optional[int]
    resolution_notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class RevenueGuardianResolveRequest(BaseModel):
    resolution_status: str = Field(..., example="RESOLVED")  # RESOLVED | DISMISSED | IN_REVIEW
    resolution_notes: str = Field(..., min_length=3, example="Generated missing invoice manually")


class RevenueGuardianRunSummary(BaseModel):
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    total_estimated_leakage: Decimal
    findings: List[RevenueGuardianFindingResponse]

