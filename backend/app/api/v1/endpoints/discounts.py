"""
Discount & Coupon Management API Endpoints (Member 2).
"""
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_admin_user, get_staff_or_admin_user, get_current_user
from app.models.user import User
from app.schemas.discount import (
    DiscountCreate,
    DiscountUpdate,
    DiscountResponse,
    DiscountValidateRequest,
    DiscountValidateResponse,
)
from app.services.discount_service import DiscountService

router = APIRouter()


@router.get("", response_model=List[DiscountResponse], summary="List discounts and coupon codes")
def list_discounts(
    active_only: bool = Query(False, description="Filter only active coupons"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DiscountService.get_discounts(db, active_only=active_only)


@router.get("/{discount_id}", response_model=DiscountResponse, summary="Get discount by ID")
def get_discount(
    discount_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DiscountService.get_discount_by_id(db, discount_id)


@router.post("", response_model=DiscountResponse, status_code=status.HTTP_201_CREATED, summary="Create a new discount code")
def create_discount(
    data: DiscountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return DiscountService.create_discount(db, data)


@router.put("/{discount_id}", response_model=DiscountResponse, summary="Update discount code parameters")
def update_discount(
    discount_id: int,
    data: DiscountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return DiscountService.update_discount(db, discount_id, data)


@router.post("/validate", response_model=DiscountValidateResponse, summary="Validate coupon eligibility and calculate reduction")
def validate_discount(
    data: DiscountValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DiscountService.validate_coupon(
        db=db,
        coupon_code=data.coupon_code,
        customer_id=data.customer_id,
        subtotal=data.subtotal,
        quantity=data.quantity,
        product_ids=data.product_ids,
        plan_id=data.plan_id,
    )

