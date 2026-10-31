"""
Pydantic v2 Schemas for Tax Management (Member 2).
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TaxBase(BaseModel):
    name: str = Field(..., max_length=100, example="Standard GST")
    description: Optional[str] = Field(None, example="Standard Goods & Services Tax")
    tax_type: str = Field(default="PERCENTAGE", example="PERCENTAGE")  # PERCENTAGE | FIXED
    rate: Decimal = Field(..., ge=0, example=Decimal("18.00"))
    applicability: str = Field(default="ALL", example="ALL")
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    is_active: bool = True


class TaxCreate(TaxBase):
    pass


class TaxUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    tax_type: Optional[str] = None
    rate: Optional[Decimal] = Field(None, ge=0)
    applicability: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class TaxResponse(TaxBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaxCalculationRequest(BaseModel):
    tax_ids: List[int]
    base_amount: Decimal = Field(..., ge=0)


class TaxCalculationItemResult(BaseModel):
    tax_id: int
    name: str
    tax_type: str
    rate: Decimal
    calculated_amount: Decimal


class TaxCalculationResponse(BaseModel):
    base_amount: Decimal
    total_tax_amount: Decimal
    breakdown: List[TaxCalculationItemResult]

