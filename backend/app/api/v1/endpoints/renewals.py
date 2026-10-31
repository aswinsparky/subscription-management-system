"""
Automated Renewal Scheduler & Member 2 Billing Integration Endpoints (Module 7).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, get_staff_or_admin_user
from app.models.user import User
from app.schemas.renewal import (
    RenewalBillingRequestResponse,
    DueSubscriptionResponse,
    BatchRenewalResult,
    Member2WebhookPayload,
)
from app.services.renewal_service import RenewalService

router = APIRouter(prefix="/renewals", tags=["Automated Renewal Scheduler"])


@router.get(
    "/due",
    response_model=List[DueSubscriptionResponse],
    summary="List subscriptions due for renewal within horizon days",
)
def get_due_subscriptions(
    horizon_days: int = Query(7, ge=0, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return RenewalService.get_due_subscriptions(db, horizon_days=horizon_days)


@router.get(
    "/requests",
    summary="List all Renewal Billing Requests (Admin/Staff)",
)
def list_renewal_requests(
    status: Optional[str] = Query(None, description="PENDING, PROCESSED, FAILED"),
    subscription_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    items, total = RenewalService.list_requests(db, status, subscription_id, page, size)
    return {"items": items, "total": total, "page": page, "size": size}


@router.post(
    "/trigger/{subscription_id}",
    response_model=RenewalBillingRequestResponse,
    summary="Trigger renewal for a specific subscription",
)
def trigger_subscription_renewal(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return RenewalService.trigger_renewal(db, subscription_id, actor=current_user, simulate_member2=True)


@router.post(
    "/batch-run",
    response_model=BatchRenewalResult,
    summary="Execute automated batch renewal cycle",
)
def run_batch_renewals(
    horizon_days: int = Query(0, ge=0, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return RenewalService.batch_process_due(db, horizon_days=horizon_days)


@router.post(
    "/member2-webhook",
    response_model=RenewalBillingRequestResponse,
    summary="Member 2 Billing Engine asynchronous invoice callback",
)
def member2_invoice_webhook(
    payload: Member2WebhookPayload,
    db: Session = Depends(get_db),
):
    return RenewalService.handle_member2_webhook(db, payload)

