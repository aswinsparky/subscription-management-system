"""
Revenue Command Center and Analytics API Endpoints (Member 2).
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_staff_or_admin_user, get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/summary", response_model=Dict[str, Any], summary="Get Revenue Command Center high-level KPIs")
def get_command_center_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return AnalyticsService.get_command_center_summary(db)


@router.get("/trends", response_model=List[Dict[str, Any]], summary="Get monthly revenue trend (invoiced vs collected)")
def get_monthly_trends(
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return AnalyticsService.get_monthly_trends(db, months_count=months)


@router.get("/status-distribution", response_model=List[Dict[str, Any]], summary="Get invoice status distribution")
def get_invoice_status_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return AnalyticsService.get_invoice_status_distribution(db)


@router.get("/payment-methods", response_model=List[Dict[str, Any]], summary="Get payment method distribution")
def get_payment_methods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return AnalyticsService.get_payment_method_distribution(db)


@router.get("/churn-signals/{customer_id}", response_model=Dict[str, Any], summary="Get customer payment churn signals (Member 1 integration)")
def get_churn_signals(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return AnalyticsService.get_customer_churn_signals(db, customer_id)

