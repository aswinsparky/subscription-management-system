"""
Tax Management API Endpoints .
"""
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_admin_user, get_staff_or_admin_user, get_current_user
from app.models.user import User
from app.schemas.tax import (
    TaxCreate,
    TaxUpdate,
    TaxResponse,
    TaxCalculationRequest,
    TaxCalculationResponse,
)
from app.services.tax_service import TaxService

router = APIRouter()


@router.get("", response_model=List[TaxResponse], summary="List configured taxes")
def list_taxes(
    active_only: bool = Query(False, description="Filter only currently active taxes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TaxService.get_taxes(db, active_only=active_only)


@router.get("/{tax_id}", response_model=TaxResponse, summary="Get tax rule by ID")
def get_tax(
    tax_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TaxService.get_tax_by_id(db, tax_id)


@router.post("", response_model=TaxResponse, status_code=status.HTTP_201_CREATED, summary="Create a new tax rule")
def create_tax(
    data: TaxCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return TaxService.create_tax(db, data)


@router.put("/{tax_id}", response_model=TaxResponse, summary="Update an existing tax rule")
def update_tax(
    tax_id: int,
    data: TaxUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return TaxService.update_tax(db, tax_id, data)


@router.post("/calculate", response_model=TaxCalculationResponse, summary="Calculate tax on amount (Integration)")
def calculate_taxes(
    data: TaxCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TaxService.calculate_taxes(db, base_amount=data.base_amount, tax_ids=data.tax_ids)

