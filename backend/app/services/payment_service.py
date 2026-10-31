"""
Payment Processing and Balance Recalculation Service for Brightloop Nexus (Member 2).
Enforces transactional safety, partial payments, idempotency, and audit trails.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.customer import Customer
from app.models.reconciliation import PaymentReconciliation
from app.models.user import User
from app.schemas.payment import PaymentCreate


class PaymentService:
    @staticmethod
    def generate_payment_reference(db: Session) -> str:
        """Generate unique payment sequence e.g. PAY-2026-00001."""
        year = datetime.utcnow().year
        prefix = f"PAY-{year}-"
        count = db.scalar(
            select(func.count(Payment.id)).where(Payment.payment_reference.like(f"{prefix}%"))
        ) or 0
        return f"{prefix}{count + 1:05d}"

    @staticmethod
    def get_payments(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        invoice_id: Optional[int] = None,
        customer_id: Optional[int] = None,
    ) -> Tuple[List[Payment], int]:
        stmt = select(Payment)

        user_role = current_user.role.name if current_user.role else "CUSTOMER"
        if user_role == "CUSTOMER":
            linked_customer = db.scalar(select(Customer).where(Customer.user_id == current_user.id))
            if not linked_customer:
                return [], 0
            stmt = stmt.where(Payment.customer_id == linked_customer.id)
        elif customer_id:
            stmt = stmt.where(Payment.customer_id == customer_id)

        if invoice_id:
            stmt = stmt.where(Payment.invoice_id == invoice_id)

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(Payment.payment_date.desc(), Payment.id.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        payments = list(db.scalars(stmt).all())
        return payments, total

    @staticmethod
    def record_payment(
        db: Session,
        data: PaymentCreate,
        current_user: User,
    ) -> Payment:
        """Record payment against invoice, update balance, and auto-generate reconciliation record."""
        # 1. Check idempotency key if provided
        if data.idempotency_key:
            existing = db.scalar(select(Payment).where(Payment.idempotency_key == data.idempotency_key))
            if existing:
                return existing

        # 2. Lock invoice row for update in transaction
        invoice = db.scalar(
            select(Invoice).where(Invoice.id == data.invoice_id).with_for_update()
        )
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {data.invoice_id} not found.",
            )

        if invoice.status in ["CANCELLED", "DRAFT"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot record payment for invoice in status '{invoice.status}'. Invoice must be CONFIRMED or OVERDUE.",
            )

        # 3. RBAC customer verification
        user_role = current_user.role.name if current_user.role else "CUSTOMER"
        if user_role == "CUSTOMER":
            linked_customer = db.scalar(select(Customer).where(Customer.user_id == current_user.id))
            if not linked_customer or invoice.customer_id != linked_customer.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Cannot pay an invoice belonging to another customer.",
                )

        # 4. Overpayment prevention
        if data.amount > invoice.amount_due:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount (${data.amount:.2f}) exceeds outstanding invoice balance (${invoice.amount_due:.2f}).",
            )

        payment_status = "FAILED" if data.simulate_failure else "SUCCESSFUL"
        payment_date = data.payment_date or datetime.utcnow()

        payment = Payment(
            payment_reference=PaymentService.generate_payment_reference(db),
            invoice_id=invoice.id,
            customer_id=invoice.customer_id,
            recorded_by_user_id=current_user.id,
            amount=data.amount,
            payment_date=payment_date,
            payment_method=data.payment_method.upper(),
            payment_status=payment_status,
            transaction_id=data.transaction_id or f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            notes=data.notes,
            idempotency_key=data.idempotency_key,
        )
        db.add(payment)
        db.flush()

        # 5. If successful, update invoice balances and status
        if payment_status == "SUCCESSFUL":
            invoice.amount_paid = (invoice.amount_paid + data.amount).quantize(Decimal("0.01"))
            invoice.amount_due = max(Decimal("0.00"), invoice.total_amount - invoice.amount_paid).quantize(Decimal("0.01"))

            if invoice.amount_due == Decimal("0.00"):
                invoice.status = "PAID"
            elif invoice.amount_paid > Decimal("0.00"):
                invoice.status = "PARTIALLY_PAID"

            recon_status = "MATCHED" if invoice.amount_due == Decimal("0.00") else "PARTIALLY_MATCHED"
        else:
            recon_status = "DISCREPANCY"

        # 6. Automatic reconciliation record
        reconciliation = PaymentReconciliation(
            payment_id=payment.id,
            invoice_id=invoice.id,
            reconciled_by_user_id=current_user.id,
            status=recon_status,
            invoice_total=invoice.total_amount,
            payment_amount=data.amount,
            discrepancy_amount=invoice.amount_due,
            notes=f"Auto-reconciled on payment receipt {payment.payment_reference}. Status: {payment_status}",
        )
        db.add(reconciliation)

        db.commit()
        db.refresh(payment)
        return payment

