"""
Pydantic v2 Schemas for Product and Product Variant Management.
Includes validation for monetary amounts and computed final variant prices.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class VariantBase(BaseModel):
    variant_name: str = Field(..., min_length=1, max_length=100, description="Variant name, e.g. Standard, Odoo, Enterprise")
    sku: Optional[str] = Field(None, max_length=100, description="Optional unique SKU")
    additional_price: Decimal = Field(Decimal("0.00"), ge=0, description="Additional price added to base product sales price")
    is_active: bool = Field(True, description="Variant active status")


class VariantCreate(VariantBase):
    pass


class VariantUpdate(BaseModel):
    variant_name: Optional[str] = Field(None, min_length=1, max_length=100)
    sku: Optional[str] = None
    additional_price: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class VariantResponse(VariantBase):
    id: int
    product_id: int
    created_at: datetime
    final_price: Decimal = Field(..., description="Computed: Base Sales Price + Variant Additional Price")

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Product title")
    product_type: str = Field("SOFTWARE", description="SERVICE | SOFTWARE | HARDWARE | CONSUMABLE")
    description: Optional[str] = None
    sales_price: Decimal = Field(..., ge=0, description="Base sales price (non-negative)")
    cost_price: Decimal = Field(..., ge=0, description="Product cost price (non-negative)")
    internal_notes: Optional[str] = None
    is_active: bool = True

    @field_validator("product_type")
    @classmethod
    def validate_product_type(cls, v: str) -> str:
        valid_types = ["SERVICE", "SOFTWARE", "HARDWARE", "CONSUMABLE"]
        upper_v = v.upper()
        if upper_v not in valid_types:
            raise ValueError(f"Invalid product type '{v}'. Must be one of: {', '.join(valid_types)}")
        return upper_v


class ProductCreate(ProductBase):
    product_code: Optional[str] = Field(None, max_length=50, description="Optional custom product code")
    variants: Optional[List[VariantCreate]] = Field(default_factory=list, description="Initial product variants")


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    product_type: Optional[str] = None
    description: Optional[str] = None
    sales_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    internal_notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("product_type")
    @classmethod
    def validate_product_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_types = ["SERVICE", "SOFTWARE", "HARDWARE", "CONSUMABLE"]
        upper_v = v.upper()
        if upper_v not in valid_types:
            raise ValueError(f"Invalid product type '{v}'. Must be one of: {', '.join(valid_types)}")
        return upper_v


class ProductResponse(ProductBase):
    id: int
    product_code: str
    created_at: datetime
    updated_at: datetime
    variants: List[VariantResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

