"""
Payment Reconciliation API Endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_staff_or_admin_user
from app.models.user import User
from app.schemas.reconciliation import (
    ReconciliationResponse,
    ReconciliationListResponse,
    ReconciliationResolveRequest,
)
from app.services.reconciliation_service import ReconciliationService

router = APIRouter()


@router.get("", response_model=ReconciliationListResponse, summary="List payment reconciliations and discrepancies")
def list_reconciliations(
    status: Optional[str] = Query(None, description="Filter by status (MATCHED, DISCREPANCY, UNMATCHED, RESOLVED)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    items, total, unmatched, discrepancy, resolved = ReconciliationService.get_reconciliations(
        db=db,
        status_filter=status,
        page=page,
        page_size=page_size,
    )
    return ReconciliationListResponse(
        items=[ReconciliationResponse.model_validate(r) for r in items],
        total=total,
        unmatched_count=unmatched,
        discrepancy_count=discrepancy,
        resolved_count=resolved,
    )


@router.post("/{reconciliation_id}/resolve", response_model=ReconciliationResponse, summary="Resolve reconciliation mismatch")
def resolve_reconciliation(
    reconciliation_id: int,
    data: ReconciliationResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    recon = ReconciliationService.resolve_reconciliation(db, reconciliation_id, data, current_user)
    return ReconciliationResponse.model_validate(recon)

