"""
Self-Healing Billing and Failure Recovery API Endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_staff_or_admin_user
from app.models.user import User
from app.schemas.recovery import BillingRecoveryAttemptResponse, ManualRetryRequest
from app.services.recovery_service import BillingRecoveryService

router = APIRouter()


@router.get("", response_model=List[BillingRecoveryAttemptResponse], summary="List billing recovery attempts")
def list_recovery_attempts(
    status: Optional[str] = Query(None, description="Filter by recovery status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    attempts, _ = BillingRecoveryService.get_recovery_attempts(
        db=db,
        status_filter=status,
        page=page,
        page_size=page_size,
    )
    return [BillingRecoveryAttemptResponse.model_validate(a) for a in attempts]


@router.post("/retry", response_model=BillingRecoveryAttemptResponse, summary="Manually trigger safe recovery retry")
def trigger_retry(
    data: ManualRetryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    attempt = BillingRecoveryService.process_recovery_attempt(
        db=db,
        attempt_id=data.attempt_id,
        current_user=current_user,
    )
    return BillingRecoveryAttemptResponse.model_validate(attempt)

