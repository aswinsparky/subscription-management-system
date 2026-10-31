"""
Quotation and Quotation Template Pydantic v2 Schemas (Module 5).
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class QuotationItemCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(1, ge=1, description="Line item quantity (>= 1)")
    unit_price: Decimal = Field(..., ge=0, description="Unit price per item")


class QuotationItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    variant_id: Optional[int] = None
    variant_name: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class QuotationCreate(BaseModel):
    customer_id: int
    plan_id: int
    template_id: Optional[int] = None
    expiration_date: Optional[datetime] = None
    tax_reference: Optional[str] = Field(None, description="Member 2 tax rule reference")
    items: List[QuotationItemCreate] = Field(..., min_length=1, description="At least one quotation line item is required")


class QuotationCreateFromTemplate(BaseModel):
    customer_id: int
    template_id: int


class QuotationUpdate(BaseModel):
    status: Optional[str] = Field(None, description="DRAFT | SENT | ACCEPTED | EXPIRED | REJECTED")
    expiration_date: Optional[datetime] = None
    tax_reference: Optional[str] = None
    items: Optional[List[QuotationItemCreate]] = None


class QuotationResponse(BaseModel):
    id: int
    quotation_number: str
    customer_id: int
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    plan_id: int
    plan_name: Optional[str] = None
    template_id: Optional[int] = None
    quotation_date: datetime
    expiration_date: datetime
    subtotal: Decimal
    tax_reference: Optional[str]
    tax_amount: Decimal
    total: Decimal
    status: str
    converted_to_subscription_id: Optional[int]
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    items: List[QuotationItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class QuotationListResponse(BaseModel):
    items: List[QuotationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ConvertQuotationResponse(BaseModel):
    message: str
    quotation_id: int
    subscription_id: int
    subscription_number: str


# Template Schemas
class QuotationTemplateItemCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    default_quantity: int = Field(1, ge=1)
    unit_price: Decimal = Field(..., ge=0)


class QuotationTemplateItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    variant_id: Optional[int] = None
    variant_name: Optional[str] = None
    default_quantity: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class QuotationTemplateCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    default_plan_id: Optional[int] = None
    validity_duration_days: int = Field(30, ge=1)
    items: List[QuotationTemplateItemCreate] = Field(default_factory=list)


class QuotationTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    default_plan_id: Optional[int]
    validity_duration_days: int
    is_active: bool
    created_at: datetime
    items: List[QuotationTemplateItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

