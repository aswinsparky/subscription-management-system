"""
Pydantic v2 Schemas for Payment Reconciliation.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ReconciliationResolveRequest(BaseModel):
    status: str = Field(..., example="RESOLVED")  # RESOLVED | MATCHED
    notes: str = Field(..., min_length=3, example="Reviewed bank transfer statement; settled discrepancy")


class ReconciliationResponse(BaseModel):
    id: int
    payment_id: Optional[int]
    invoice_id: Optional[int]
    reconciled_by_user_id: Optional[int]
    status: str
    invoice_total: Decimal
    payment_amount: Decimal
    discrepancy_amount: Decimal
    notes: Optional[str]
    reconciled_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReconciliationListResponse(BaseModel):
    items: List[ReconciliationResponse]
    total: int
    unmatched_count: int
    discrepancy_count: int
    resolved_count: int

