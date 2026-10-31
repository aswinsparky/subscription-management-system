"""
Pydantic v2 Schemas for Payment Processing.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: Decimal = Field(..., gt=0, example=Decimal("99.00"))
    payment_method: str = Field(default="CARD", example="CARD")  # CASH, BANK_TRANSFER, CARD, UPI, SIMULATED
    payment_date: Optional[datetime] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    idempotency_key: Optional[str] = None
    simulate_failure: bool = False  # For demo testing


class PaymentResponse(BaseModel):
    id: int
    payment_reference: str
    invoice_id: int
    customer_id: int
    recorded_by_user_id: Optional[int]
    amount: Decimal
    payment_date: datetime
    payment_method: str
    payment_status: str
    transaction_id: Optional[str]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentListResponse(BaseModel):
    items: List[PaymentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

