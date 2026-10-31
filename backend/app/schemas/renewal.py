"""
Automated Renewal Scheduler & Billing Integration Schemas (Module 7).
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class RenewalBillingRequestResponse(BaseModel):
    id: int
    idempotency_key: str
    subscription_id: int
    subscription_number: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    billing_period_start: datetime
    billing_period_end: datetime
    amount: Decimal
    status: str  # PENDING, PROCESSED, FAILED
    invoice_reference: Optional[str] = None
    retry_count: int
    last_error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DueSubscriptionResponse(BaseModel):
    subscription_id: int
    subscription_number: str
    customer_id: int
    customer_name: str
    plan_name: str
    billing_interval: str
    amount: Decimal
    current_period_end: datetime
    next_billing_date: datetime
    days_until_due: int
    idempotency_key: str

    model_config = ConfigDict(from_attributes=True)


class BatchRenewalResult(BaseModel):
    total_due: int
    processed_count: int
    failed_count: int
    details: List[RenewalBillingRequestResponse]


class Member2WebhookPayload(BaseModel):
    idempotency_key: str
    invoice_reference: str
    status: str = "SUCCESS"  # SUCCESS or FAILED
    error_message: Optional[str] = None

