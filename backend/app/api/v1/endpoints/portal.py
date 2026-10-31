"""
Customer Self-Service Portal Endpoints (Module 10).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.portal import (
    CustomerPortalOverview,
    CustomerProfileResponse,
    CustomerProfileUpdate,
    PortalActionRequest,
)
from app.schemas.subscription import SubscriptionResponse
from app.schemas.quotation import QuotationResponse, ConvertQuotationResponse
from app.services.portal_service import PortalService

router = APIRouter(prefix="/portal", tags=["Customer Self-Service Portal"])


@router.get(
    "/overview",
    response_model=CustomerPortalOverview,
    summary="Get customer portal dashboard overview for the authenticated user",
)
def get_portal_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return PortalService.get_overview(db, current_user)


@router.get(
    "/profile",
    response_model=CustomerProfileResponse,
    summary="Get customer profile details for the authenticated user",
)
def get_portal_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cust = PortalService.get_customer_for_user(db, current_user)
    return CustomerProfileResponse.model_validate(cust)


@router.put(
    "/profile",
    response_model=CustomerProfileResponse,
    summary="Update customer profile (billing address, company, phone)",
)
def update_portal_profile(
    payload: CustomerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return PortalService.update_profile(db, current_user, payload)


@router.post(
    "/subscriptions/{subscription_id}/pause",
    response_model=SubscriptionResponse,
    summary="Self-service request to pause customer's active subscription",
)
def customer_pause_subscription(
    subscription_id: int,
    payload: Optional[PortalActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reason = payload.reason if payload else "Self-service customer pause"
    return PortalService.pause_subscription(db, current_user, subscription_id, reason)


@router.post(
    "/subscriptions/{subscription_id}/resume",
    response_model=SubscriptionResponse,
    summary="Self-service request to resume customer's paused subscription",
)
def customer_resume_subscription(
    subscription_id: int,
    payload: Optional[PortalActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reason = payload.reason if payload else "Self-service customer resume"
    return PortalService.resume_subscription(db, current_user, subscription_id, reason)


@router.post(
    "/subscriptions/{subscription_id}/cancel",
    response_model=SubscriptionResponse,
    summary="Self-service request to cancel customer's subscription",
)
def customer_cancel_subscription(
    subscription_id: int,
    payload: Optional[PortalActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reason = payload.reason if payload else "Self-service customer cancellation"
    return PortalService.cancel_subscription(db, current_user, subscription_id, reason)


@router.post(
    "/quotations/{quotation_id}/accept",
    response_model=ConvertQuotationResponse,
    summary="Self-service customer acceptance of quote into active subscription",
)
def customer_accept_quote(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return PortalService.accept_quotation(db, current_user, quotation_id)

