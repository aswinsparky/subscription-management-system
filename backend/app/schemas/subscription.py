"""
Subscription and Subscription Events Pydantic Schemas.
Monetary fields use Decimal(12, 2).
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SubscriptionItemCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(default=1, ge=1)


class SubscriptionItemResponse(BaseModel):
    id: int
    subscription_id: int
    product_id: int
    variant_id: Optional[int] = None
    product_name: Optional[str] = None
    variant_name: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class SubscriptionEventResponse(BaseModel):
    id: int
    subscription_id: int
    event_type: str
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Dict[str, Any]
    actor_id: Optional[int] = None
    actor_email: Optional[str] = None
    actor_role: Optional[str] = None
    reason: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionCreate(BaseModel):
    customer_id: int
    plan_id: int
    billing_interval: Optional[str] = None  # If omitted, uses plan default
    payment_terms: str = "Immediate"
    auto_renew: bool = True
    items: List[SubscriptionItemCreate] = Field(min_length=1)


class SubscriptionActionRequest(BaseModel):
    reason: Optional[str] = None


class CustomerSimpleResponse(BaseModel):
    id: int
    customer_code: str
    full_name: str
    email: str
    company_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PlanSimpleResponse(BaseModel):
    id: int
    plan_code: str
    name: str
    billing_interval: str
    plan_price: Decimal
    pause_allowed: bool
    early_cancellation_allowed: bool
    auto_close_enabled: bool

    model_config = ConfigDict(from_attributes=True)


class SubscriptionResponse(BaseModel):
    id: int
    subscription_number: str
    customer_id: int
    plan_id: int
    source_quotation_id: Optional[int] = None
    start_date: datetime
    expiry_date: datetime
    billing_interval: str
    payment_terms: str
    subtotal: Decimal
    discount_reference: Optional[str] = None
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    next_billing_date: datetime
    current_period_start: datetime
    current_period_end: datetime
    auto_renew: bool
    last_renewed_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    customer: Optional[CustomerSimpleResponse] = None
    plan: Optional[PlanSimpleResponse] = None
    items: List[SubscriptionItemResponse] = []
    events: List[SubscriptionEventResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SubscriptionListResponse(BaseModel):
    items: List[SubscriptionResponse]
    total: int
    page: int
    size: int
