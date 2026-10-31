"""
Quotation Management API Endpoints (Module 5).
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import (
    get_current_user,
    get_staff_or_admin_user,
)
from app.models.user import User
from app.schemas.quotation import (
    QuotationCreate,
    QuotationCreateFromTemplate,
    QuotationUpdate,
    QuotationResponse,
    QuotationListResponse,
    ConvertQuotationResponse,
)
from app.services.quotation_service import QuotationService

router = APIRouter(prefix="/quotations", tags=["Quotation Management"])


@router.post(
    "/",
    response_model=QuotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Quotation from Scratch (Admin/Staff)",
)
def create_quotation(
    req: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    """
    Generate a new quotation with product lines, quantities, and agreed prices.
    """
    return QuotationService.create_quotation(db, req, current_user)


@router.post(
    "/from-template",
    response_model=QuotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Quotation from Template (Admin/Staff)",
)
def create_quotation_from_template(
    req: QuotationCreateFromTemplate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    """
    Generate a quotation populated from a pre-configured quotation template.
    """
    return QuotationService.create_from_template(db, req, current_user)


@router.get(
    "/",
    response_model=QuotationListResponse,
    summary="List Quotations with Search, Filter & Pagination",
)
def list_quotations(
    query: Optional[str] = Query(None, description="Search quotation number or customer name"),
    status: Optional[str] = Query("ALL", description="Filter: ALL, DRAFT, SENT, ACCEPTED, EXPIRED, REJECTED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List quotations. Customers only see their own quotations.
    """
    return QuotationService.get_quotations(
        db=db,
        current_user=current_user,
        query=query,
        status_filter=status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{quotation_id}",
    response_model=QuotationResponse,
    summary="Get Quotation Details",
)
def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve quotation lines, calculated subtotal, and expiration dates.
    """
    return QuotationService.get_quotation_by_id(db, quotation_id, current_user)


@router.put(
    "/{quotation_id}",
    response_model=QuotationResponse,
    summary="Update Quotation Status",
)
def update_quotation(
    quotation_id: int,
    req: QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update quotation status (e.g. SENT, ACCEPTED, REJECTED).
    """
    return QuotationService.update_quotation(db, quotation_id, req, current_user)


@router.post(
    "/{quotation_id}/convert",
    response_model=ConvertQuotationResponse,
    summary="Convert Accepted Quotation into Subscription",
)
def convert_to_subscription(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    """
    Converts an accepted quotation into an active subscription.
    Enforces idempotency: Duplicate conversions are strictly rejected.
    """
    return QuotationService.convert_to_subscription(db, quotation_id, current_user)
