"""
Pydantic v2 Schemas for Self-Healing Billing (Member 2).
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class BillingRecoveryAttemptResponse(BaseModel):
    id: int
    subscription_id: int
    invoice_id: Optional[int]
    payment_id: Optional[int]
    failure_type: str
    failure_reason: str
    retry_count: int
    max_retries: int
    next_retry_at: Optional[datetime]
    recovery_status: str
    idempotency_key: str
    error_details: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ManualRetryRequest(BaseModel):
    attempt_id: int
    notes: Optional[str] = None

