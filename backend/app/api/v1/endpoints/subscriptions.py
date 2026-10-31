"""
Subscription Lifecycle & State Machine Endpoints (Module 6).
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionListResponse,
    SubscriptionActionRequest,
    SubscriptionEventResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Subscription in DRAFT status",
)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = SubscriptionService.create_subscription(db, current_user, payload)
    return SubscriptionService.get_subscription(db, current_user, sub.id)


@router.get(
    "",
    response_model=SubscriptionListResponse,
    summary="List subscriptions with filtering and pagination",
)
def list_subscriptions(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, ACTIVE, etc.)"),
    plan_id: Optional[int] = Query(None, description="Filter by plan ID"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = SubscriptionService.list_subscriptions(
        db, current_user, customer_id, status, plan_id, page, size
    )
    return SubscriptionListResponse(items=items, total=total, page=page, size=size)


@router.get(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Get subscription details by ID",
)
def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SubscriptionService.get_subscription(db, current_user, subscription_id)


@router.post(
    "/{subscription_id}/confirm",
    response_model=SubscriptionResponse,
    summary="Transition subscription from DRAFT/QUOTATION to CONFIRMED",
)
def confirm_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = SubscriptionService.confirm_subscription(db, current_user, subscription_id)
    return SubscriptionService.get_subscription(db, current_user, sub.id)


@router.post(
    "/{subscription_id}/activate",
    response_model=SubscriptionResponse,
    summary="Activate a CONFIRMED subscription into ACTIVE status",
)
def activate_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = SubscriptionService.activate_subscription(db, current_user, subscription_id)
    return SubscriptionService.get_subscription(db, current_user, sub.id)


@router.post(
    "/{subscription_id}/pause",
    response_model=SubscriptionResponse,
    summary="Pause an ACTIVE subscription (policy checked)",
)
def pause_subscription(
    subscription_id: int,
    payload: Optional[SubscriptionActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reason = payload.reason if payload else None
    sub = SubscriptionService.pause_subscription(db, current_user, subscription_id, reason)
    return SubscriptionService.get_subscription(db, current_user, sub.id)


@router.post(
    "/{subscription_id}/resume",
    response_model=SubscriptionResponse,
    summary="Resume a PAUSED subscription back to ACTIVE",
)
def resume_subscription(
    subscription_id: int,
    payload: Optional[SubscriptionActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reason = payload.reason if payload else None
    sub = SubscriptionService.resume_subscription(db, current_user, subscription_id, reason)
    return SubscriptionService.get_subscription(db, current_user, sub.id)


@router.post(
    "/{subscription_id}/cancel",
    response_model=SubscriptionResponse,
    summary="Cancel subscription (checks early cancellation policy)",
)
def cancel_subscription(
    subscription_id: int,
    payload: Optional[SubscriptionActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reason = payload.reason if payload else None
    sub = SubscriptionService.cancel_subscription(db, current_user, subscription_id, reason)
    return SubscriptionService.get_subscription(db, current_user, sub.id)


@router.post(
    "/{subscription_id}/close",
    response_model=SubscriptionResponse,
    summary="Close subscription normally into CLOSED terminal status",
)
def close_subscription(
    subscription_id: int,
    payload: Optional[SubscriptionActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reason = payload.reason if payload else None
    sub = SubscriptionService.close_subscription(db, current_user, subscription_id, reason)
    return SubscriptionService.get_subscription(db, current_user, sub.id)


@router.get(
    "/{subscription_id}/events",
    response_model=List[SubscriptionEventResponse],
    summary="Get immutable audit events history for a subscription",
)
def get_subscription_events(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SubscriptionService.get_events(db, current_user, subscription_id)
