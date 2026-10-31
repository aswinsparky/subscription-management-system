"""
Subscription Plan Pydantic v2 Schemas (Module 4).
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class PlanBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Plan title (e.g. Starter Monthly, Enterprise Annual)")
    description: Optional[str] = None
    billing_interval: str = Field("MONTHLY", description="DAILY | WEEKLY | MONTHLY | YEARLY")
    plan_price: Decimal = Field(..., ge=0, description="Base recurring plan price (non-negative)")
    minimum_quantity: int = Field(1, ge=1, description="Minimum quantity required (>= 1)")
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    auto_close_enabled: bool = False
    early_cancellation_allowed: bool = True
    pause_allowed: bool = True
    renewal_allowed: bool = True
    status: str = Field("ACTIVE", description="DRAFT | ACTIVE | ARCHIVED")

    @field_validator("billing_interval")
    @classmethod
    def validate_billing_interval(cls, v: str) -> str:
        valid_intervals = ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]
        upper_v = v.upper()
        if upper_v not in valid_intervals:
            raise ValueError(f"Invalid billing interval '{v}'. Must be one of: {', '.join(valid_intervals)}")
        return upper_v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = ["DRAFT", "ACTIVE", "ARCHIVED"]
        upper_v = v.upper()
        if upper_v not in valid_statuses:
            raise ValueError(f"Invalid status '{v}'. Must be one of: {', '.join(valid_statuses)}")
        return upper_v

    @model_validator(mode="after")
    def validate_date_range(self) -> "PlanBase":
        if self.available_from and self.available_until:
            if self.available_until < self.available_from:
                raise ValueError("available_until date must be greater than or equal to available_from date.")
        return self


class PlanCreate(PlanBase):
    plan_code: Optional[str] = Field(None, max_length=50, description="Custom plan code or auto-generated")


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    billing_interval: Optional[str] = None
    plan_price: Optional[Decimal] = Field(None, ge=0)
    minimum_quantity: Optional[int] = Field(None, ge=1)
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    auto_close_enabled: Optional[bool] = None
    early_cancellation_allowed: Optional[bool] = None
    pause_allowed: Optional[bool] = None
    renewal_allowed: Optional[bool] = None
    status: Optional[str] = None

    @field_validator("billing_interval")
    @classmethod
    def validate_billing_interval(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_intervals = ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]
        upper_v = v.upper()
        if upper_v not in valid_intervals:
            raise ValueError(f"Invalid billing interval '{v}'. Must be one of: {', '.join(valid_intervals)}")
        return upper_v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_statuses = ["DRAFT", "ACTIVE", "ARCHIVED"]
        upper_v = v.upper()
        if upper_v not in valid_statuses:
            raise ValueError(f"Invalid status '{v}'. Must be one of: {', '.join(valid_statuses)}")
        return upper_v


class PlanResponse(PlanBase):
    id: int
    plan_code: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlanListResponse(BaseModel):
    items: List[PlanResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

