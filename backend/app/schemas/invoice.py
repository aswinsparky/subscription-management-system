"""
Pydantic v2 Schemas for Invoices & Line Items (Member 2).
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class InvoiceItemBase(BaseModel):
    product_id: Optional[int] = None
    product_variant_id: Optional[int] = None
    subscription_item_id: Optional[int] = None
    item_description: str = Field(..., max_length=255, example="Pro SaaS Plan (Monthly)")
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate_snapshot: Decimal = Field(default=Decimal("0.00"), ge=0)


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemResponse(InvoiceItemBase):
    id: int
    invoice_id: int
    subtotal: Decimal
    tax_amount_snapshot: Decimal
    total_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class InvoiceTaxDetailResponse(BaseModel):
    id: int
    tax_id: Optional[int]
    tax_name_snapshot: str
    tax_rate_snapshot: Decimal
    calculated_tax_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class InvoiceDiscountDetailResponse(BaseModel):
    id: int
    discount_id: Optional[int]
    coupon_code_snapshot: str
    discount_type_snapshot: str
    discount_rate_or_value: Decimal
    calculated_discount_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
    customer_id: int
    subscription_id: Optional[int] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    payment_terms: str = Field(default="Immediate")
    notes: Optional[str] = None
    coupon_code: Optional[str] = None
    tax_ids: Optional[List[int]] = None
    items: List[InvoiceItemCreate]
    idempotency_key: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    subscription_id: Optional[int]
    created_by_user_id: Optional[int]
    invoice_date: datetime
    due_date: datetime
    status: str
    billing_period_start: Optional[datetime]
    billing_period_end: Optional[datetime]
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    payment_terms: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[InvoiceItemResponse] = []
    tax_details: List[InvoiceTaxDetailResponse] = []
    discount_details: List[InvoiceDiscountDetailResponse] = []

    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class GenerateInvoiceFromSubscriptionRequest(BaseModel):
    subscription_id: int
    billing_period_start: Optional[datetime] = None
    billing_period_end: Optional[datetime] = None
    coupon_code: Optional[str] = None
    tax_ids: Optional[List[int]] = None
    idempotency_key: Optional[str] = None

