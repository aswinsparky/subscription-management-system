"""
Customer Self-Service Portal Schemas (Module 10).
Strict multi-tenant customer-scoped operations.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.subscription import SubscriptionResponse
from app.schemas.quotation import QuotationResponse


class CustomerProfileUpdate(BaseModel):
    phone: Optional[str] = None
    company_name: Optional[str] = None
    billing_address: Optional[str] = None
    tax_id: Optional[str] = None


class CustomerProfileResponse(BaseModel):
    id: int
    customer_code: str
    user_id: Optional[int] = None
    full_name: str
    email: str
    phone: Optional[str] = None
    company_name: Optional[str] = None
    billing_address: str
    tax_id: Optional[str] = None
    account_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerPortalOverview(BaseModel):
    profile: CustomerProfileResponse
    active_subscriptions: List[SubscriptionResponse]
    pending_quotations: List[QuotationResponse]
    total_active_mrr: Decimal


class PortalActionRequest(BaseModel):
    reason: Optional[str] = None
