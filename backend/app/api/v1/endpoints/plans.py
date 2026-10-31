"""
Subscription Plan Management API Endpoints (Module 4).
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import (
    get_current_user,
    get_admin_user,
)
from app.models.user import User
from app.schemas.plan import (
    PlanCreate,
    PlanUpdate,
    PlanResponse,
    PlanListResponse,
)
from app.services.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["Subscription Plan Management"])


@router.post(
    "/",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Subscription Plan (Admin Only)",
)
def create_plan(
    req: PlanCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """
    Create a new subscription plan.
    Restricted exclusively to ADMIN role.
    """
    return PlanService.create_plan(db, req, admin_user)


@router.get(
    "/",
    response_model=PlanListResponse,
    summary="List Plans with Search & Filters",
)
def list_plans(
    query: Optional[str] = Query(None, description="Search plan name, code, or description"),
    billing_interval: Optional[str] = Query("ALL", description="Filter: ALL, DAILY, WEEKLY, MONTHLY, YEARLY"),
    status: Optional[str] = Query("ALL", description="Filter: ALL, DRAFT, ACTIVE, ARCHIVED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all configured subscription plans.
    """
    return PlanService.get_plans(
        db=db,
        query=query,
        billing_interval=billing_interval,
        status_filter=status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
    summary="Get Subscription Plan Details",
)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed plan configurations and lifecycle permission flags.
    """
    return PlanService.get_plan_by_id(db, plan_id)


@router.put(
    "/{plan_id}",
    response_model=PlanResponse,
    summary="Update Subscription Plan (Admin Only)",
)
def update_plan(
    plan_id: int,
    req: PlanUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """
    Update plan pricing, intervals, availability, or lifecycle permissions.
    """
    return PlanService.update_plan(db, plan_id, req, admin_user)


@router.delete(
    "/{plan_id}",
    summary="Safe Delete or Archive Plan (Admin Only)",
)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """
    Safely delete or archive a plan.
    If referenced in subscriptions or quotations, marks ARCHIVED instead of deleting.
    """
    return PlanService.archive_or_delete_plan(db, plan_id, admin_user)

