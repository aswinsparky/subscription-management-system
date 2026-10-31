"""
Payment Reconciliation Service for Brightloop Nexus (Member 2).
Audits financial mismatches, unlinked payments, and discrepancy resolutions.
"""
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.reconciliation import PaymentReconciliation
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.reconciliation import ReconciliationResolveRequest


class ReconciliationService:
    @staticmethod
    def get_reconciliations(
        db: Session,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[PaymentReconciliation], int, int, int, int]:
        stmt = select(PaymentReconciliation)
        if status_filter:
            stmt = stmt.where(PaymentReconciliation.status == status_filter.upper())

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        unmatched_count = db.scalar(
            select(func.count(PaymentReconciliation.id)).where(PaymentReconciliation.status == "UNMATCHED")
        ) or 0
        discrepancy_count = db.scalar(
            select(func.count(PaymentReconciliation.id)).where(PaymentReconciliation.status == "DISCREPANCY")
        ) or 0
        resolved_count = db.scalar(
            select(func.count(PaymentReconciliation.id)).where(PaymentReconciliation.status == "RESOLVED")
        ) or 0

        stmt = stmt.order_by(PaymentReconciliation.reconciled_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        items = list(db.scalars(stmt).all())

        return items, total, unmatched_count, discrepancy_count, resolved_count

    @staticmethod
    def resolve_reconciliation(
        db: Session,
        reconciliation_id: int,
        data: ReconciliationResolveRequest,
        current_user: User,
    ) -> PaymentReconciliation:
        recon = db.scalar(
            select(PaymentReconciliation).where(PaymentReconciliation.id == reconciliation_id)
        )
        if not recon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reconciliation record with ID {reconciliation_id} not found.",
            )

        recon.status = data.status.upper()
        recon.reconciled_by_user_id = current_user.id
        recon.notes = f"{recon.notes or ''}\nResolution by {current_user.full_name}: {data.notes}".strip()

        db.commit()
        db.refresh(recon)
        return recon

