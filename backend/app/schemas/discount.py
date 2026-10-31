"""
Pydantic v2 Schemas for Discount and Coupon Management.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class DiscountBase(BaseModel):
    name: str = Field(..., max_length=100, example="Early Adopter Special")
    coupon_code: str = Field(..., max_length=50, example="SAVE20")
    discount_type: str = Field(default="PERCENTAGE", example="PERCENTAGE")  # PERCENTAGE | FIXED
    discount_value: Decimal = Field(..., ge=0, example=Decimal("20.00"))
    min_purchase_amount: Decimal = Field(default=Decimal("0.00"), ge=0, example=Decimal("50.00"))
    min_quantity: int = Field(default=1, ge=1, example=1)
    max_usage_limit: Optional[int] = Field(None, ge=1, example=100)
    usage_per_customer_limit: Optional[int] = Field(default=1, ge=1, example=1)
    applicable_product_ids: Optional[List[int]] = None
    applicable_plan_ids: Optional[List[int]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True


class DiscountCreate(DiscountBase):
    pass


class DiscountUpdate(BaseModel):
    name: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[Decimal] = Field(None, ge=0)
    min_purchase_amount: Optional[Decimal] = Field(None, ge=0)
    min_quantity: Optional[int] = Field(None, ge=1)
    max_usage_limit: Optional[int] = None
    usage_per_customer_limit: Optional[int] = None
    applicable_product_ids: Optional[List[int]] = None
    applicable_plan_ids: Optional[List[int]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class DiscountResponse(DiscountBase):
    id: int
    current_usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiscountValidateRequest(BaseModel):
    coupon_code: str = Field(..., example="SAVE20")
    customer_id: int
    subtotal: Decimal = Field(..., ge=0)
    quantity: int = Field(default=1, ge=1)
    product_ids: Optional[List[int]] = None
    plan_id: Optional[int] = None


class DiscountValidateResponse(BaseModel):
    is_valid: bool
    coupon_code: str
    discount_type: Optional[str] = None
    discount_value: Optional[Decimal] = None
    calculated_discount: Decimal = Decimal("0.00")
    message: str

