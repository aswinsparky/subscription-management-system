"""
Churn Radar & Behavioral Risk Analytics Endpoints (Module 8).
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_staff_or_admin_user
from app.models.user import User
from app.schemas.churn import (
    CustomerRiskProfile,
    ChurnDashboardMetrics,
    RetentionActionRequest,
    RetentionActionResponse,
)
from app.services.churn_service import ChurnService

router = APIRouter(prefix="/churn", tags=["Churn Radar & Analytics"])


@router.get(
    "/dashboard",
    response_model=ChurnDashboardMetrics,
    summary="Get aggregated churn risk dashboard metrics (Staff/Admin)",
)
def get_churn_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return ChurnService.get_dashboard_metrics(db)


@router.get(
    "/customer/{customer_id}",
    response_model=CustomerRiskProfile,
    summary="Get detailed churn risk profile and signals for a customer",
)
def get_customer_churn_profile(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return ChurnService.get_customer_profile(db, customer_id)


@router.post(
    "/customer/{customer_id}/retention-action",
    response_model=RetentionActionResponse,
    summary="Log a proactive retention outreach action for a customer",
)
def record_retention_action(
    customer_id: int,
    payload: RetentionActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return ChurnService.record_retention_action(db, customer_id, payload, current_user)
