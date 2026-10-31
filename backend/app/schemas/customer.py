"""
Customer Pydantic v2 Schemas for CRUD, Search, Filter, and Pagination.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class CustomerCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255, description="Customer or primary contact name")
    email: EmailStr = Field(..., description="Customer billing and contact email")
    phone: Optional[str] = Field(None, max_length=50)
    company_name: Optional[str] = Field(None, max_length=255)
    billing_address: str = Field(..., min_length=5, description="Full billing address for invoices")
    tax_id: Optional[str] = Field(None, max_length=100, description="Tax identification / GST / VAT number")
    account_status: str = Field("ACTIVE", description="ACTIVE | SUSPENDED | ARCHIVED")


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    billing_address: Optional[str] = None
    tax_id: Optional[str] = None
    account_status: Optional[str] = Field(None, description="ACTIVE | SUSPENDED | ARCHIVED")


class CustomerResponse(BaseModel):
    id: int
    customer_code: str
    user_id: Optional[int]
    full_name: str
    email: str
    phone: Optional[str]
    company_name: Optional[str]
    billing_address: str
    tax_id: Optional[str]
    account_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    items: List[CustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SubscriptionSummary(BaseModel):
    id: int
    subscription_number: str
    status: str
    billing_interval: str
    total_amount: str
    start_date: datetime
    expiry_date: datetime
    next_billing_date: datetime


class QuotationSummary(BaseModel):
    id: int
    quotation_number: str
    status: str
    total: str
    quotation_date: datetime
    expiration_date: datetime


class CustomerHistoryResponse(BaseModel):
    customer: CustomerResponse
    subscriptions: List[SubscriptionSummary]
    quotations: List[QuotationSummary]

