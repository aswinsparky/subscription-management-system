"""
Payment Processing API Endpoints (Member 2).
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentListResponse
from app.services.payment_service import PaymentService

router = APIRouter()


@router.get("", response_model=PaymentListResponse, summary="List payments with role isolation")
def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    invoice_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payments, total = PaymentService.get_payments(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        invoice_id=invoice_id,
        customer_id=customer_id,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaymentListResponse(
        items=[PaymentResponse.model_validate(p) for p in payments],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED, summary="Record payment against invoice")
def record_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = PaymentService.record_payment(db, data, current_user)
    return PaymentResponse.model_validate(payment)

