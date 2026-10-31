"""
Invoice Management and PDF Generation API Endpoints (Member 2).
Enforces customer data isolation, pagination, status transitions, and PDF streaming.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, get_staff_or_admin_user
from app.models.user import User
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceListResponse,
    GenerateInvoiceFromSubscriptionRequest,
)
from app.services.invoice_service import InvoiceService
from app.services.pdf_service import PDFInvoiceService

router = APIRouter()


@router.get("", response_model=InvoiceListResponse, summary="List invoices with filters & role isolation")
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by invoice number or notes"),
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, CONFIRMED, PAID, OVERDUE, etc.)"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID (Staff/Admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoices, total = InvoiceService.get_invoices(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status,
        customer_id=customer_id,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return InvoiceListResponse(
        items=[InvoiceResponse.model_validate(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse, summary="Get invoice details by ID")
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = InvoiceService.get_invoice_by_id(db, invoice_id, current_user)
    return InvoiceResponse.model_validate(invoice)


@router.get("/{invoice_id}/pdf", summary="Download official PDF invoice")
def download_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = InvoiceService.get_invoice_by_id(db, invoice_id, current_user)
    pdf_buffer = PDFInvoiceService.generate_invoice_pdf(invoice)
    pdf_bytes = pdf_buffer.getvalue()

    filename = f"{invoice.invoice_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED, summary="Create a manual invoice")
def create_manual_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    invoice = InvoiceService.create_invoice(db, data, user_id=current_user.id)
    return InvoiceResponse.model_validate(invoice)


@router.post("/generate-from-subscription", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED, summary="Generate recurring invoice from active subscription")
def generate_invoice_from_subscription(
    data: GenerateInvoiceFromSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    invoice = InvoiceService.generate_invoice_from_subscription(
        db=db,
        subscription_id=data.subscription_id,
        user_id=current_user.id,
        billing_period_start=data.billing_period_start,
        billing_period_end=data.billing_period_end,
        coupon_code=data.coupon_code,
        tax_ids=data.tax_ids,
        idempotency_key=data.idempotency_key,
    )
    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/confirm", response_model=InvoiceResponse, summary="Confirm a DRAFT invoice")
def confirm_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    invoice = InvoiceService.confirm_invoice(db, invoice_id, user_id=current_user.id)
    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse, summary="Cancel an unpaid invoice")
def cancel_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    invoice = InvoiceService.cancel_invoice(db, invoice_id, user_id=current_user.id)
    return InvoiceResponse.model_validate(invoice)

