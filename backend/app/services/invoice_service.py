"""
Invoice Generation and Lifecycle Domain Service for Brightloop Nexus (Member 2).
Enforces transactional consistency, idempotency, duplicate prevention, and historical snapshots.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status
from app.models.invoice import (
    Invoice,
    InvoiceItem,
    InvoiceTaxDetail,
    InvoiceDiscountDetail,
    InvoiceGenerationLog,
)
from app.models.subscription import Subscription, SubscriptionItem
from app.models.customer import Customer
from app.models.tax import Tax
from app.models.discount import Discount
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate
from app.services.discount_service import DiscountService


class InvoiceService:
    @staticmethod
    def generate_next_invoice_number(db: Session) -> str:
        """Generate contiguous unique invoice sequence e.g. INV-2026-00001."""
        year = datetime.utcnow().year
        prefix = f"INV-{year}-"

        # Count existing invoices with this year's prefix
        count = db.scalar(
            select(func.count(Invoice.id)).where(Invoice.invoice_number.like(f"{prefix}%"))
        ) or 0
        sequence = count + 1
        return f"{prefix}{sequence:05d}"

    @staticmethod
    def calculate_due_date(invoice_date: datetime, payment_terms: str) -> datetime:
        """Calculate due date from payment terms."""
        terms_lower = payment_terms.strip().lower()
        if "15" in terms_lower:
            return invoice_date + timedelta(days=15)
        elif "30" in terms_lower:
            return invoice_date + timedelta(days=30)
        elif "60" in terms_lower:
            return invoice_date + timedelta(days=60)
        # Immediate or default
        return invoice_date + timedelta(days=1)

    @staticmethod
    def get_invoices(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        customer_id: Optional[int] = None,
    ) -> Tuple[List[Invoice], int]:
        """Fetch invoices with role-based isolation (Customers only see their own)."""
        stmt = select(Invoice)

        # Enforce Customer tenant isolation
        user_role = current_user.role.name if current_user.role else "CUSTOMER"
        if user_role == "CUSTOMER":
            # Find customer linked to current user
            linked_customer = db.scalar(select(Customer).where(Customer.user_id == current_user.id))
            if not linked_customer:
                return [], 0
            stmt = stmt.where(Invoice.customer_id == linked_customer.id)
        elif customer_id:
            stmt = stmt.where(Invoice.customer_id == customer_id)

        if status_filter:
            stmt = stmt.where(Invoice.status == status_filter.upper())

        if search:
            search_term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Invoice.invoice_number.ilike(search_term),
                    Invoice.notes.ilike(search_term),
                )
            )

        # Total count
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        # Pagination
        stmt = stmt.order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        invoices = list(db.scalars(stmt).all())

        return invoices, total

    @staticmethod
    def get_invoice_by_id(db: Session, invoice_id: int, current_user: User) -> Invoice:
        invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id))
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found.",
            )

        # RBAC ownership check
        user_role = current_user.role.name if current_user.role else "CUSTOMER"
        if user_role == "CUSTOMER":
            linked_customer = db.scalar(select(Customer).where(Customer.user_id == current_user.id))
            if not linked_customer or invoice.customer_id != linked_customer.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You do not have permission to view this invoice.",
                )

        return invoice

    @staticmethod
    def create_invoice(
        db: Session,
        data: InvoiceCreate,
        user_id: Optional[int] = None,
    ) -> Invoice:
        """Create manual or ad-hoc invoice in DRAFT state."""
        # Check idempotency key if provided
        if data.idempotency_key:
            existing = db.scalar(
                select(Invoice).where(Invoice.idempotency_key == data.idempotency_key)
            )
            if existing:
                return existing

        customer = db.scalar(select(Customer).where(Customer.id == data.customer_id))
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {data.customer_id} not found.",
            )

        invoice_date = data.invoice_date or datetime.utcnow()
        due_date = data.due_date or InvoiceService.calculate_due_date(invoice_date, data.payment_terms)

        invoice = Invoice(
            invoice_number=InvoiceService.generate_next_invoice_number(db),
            customer_id=customer.id,
            subscription_id=data.subscription_id,
            created_by_user_id=user_id,
            invoice_date=invoice_date,
            due_date=due_date,
            status="DRAFT",
            payment_terms=data.payment_terms,
            notes=data.notes,
            idempotency_key=data.idempotency_key,
        )
        db.add(invoice)
        db.flush()

        # Build items
        for item_in in data.items:
            item_subtotal = (Decimal(str(item_in.quantity)) * item_in.unit_price).quantize(Decimal("0.01"))
            tax_amt = (item_subtotal * (item_in.tax_rate_snapshot / Decimal("100.00"))).quantize(Decimal("0.01"))
            item_total = item_subtotal + tax_amt

            inv_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=item_in.product_id,
                product_variant_id=item_in.product_variant_id,
                subscription_item_id=item_in.subscription_item_id,
                item_description=item_in.item_description,
                quantity=item_in.quantity,
                unit_price=item_in.unit_price,
                subtotal=item_subtotal,
                tax_rate_snapshot=item_in.tax_rate_snapshot,
                tax_amount_snapshot=tax_amt,
                total_amount=item_total,
            )
            db.add(inv_item)

        db.flush()

        # Process Discounts
        if data.coupon_code:
            discount = DiscountService.get_discount_by_code(db, data.coupon_code)
            if discount:
                item_subtotal = sum((i.subtotal for i in invoice.items), Decimal("0.00"))
                calc_discount = discount.calculate_discount_amount(item_subtotal)
                discount_detail = InvoiceDiscountDetail(
                    invoice_id=invoice.id,
                    discount_id=discount.id,
                    coupon_code_snapshot=discount.coupon_code,
                    discount_type_snapshot=discount.discount_type,
                    discount_rate_or_value=discount.discount_value,
                    calculated_discount_amount=calc_discount,
                )
                db.add(discount_detail)
                DiscountService.record_usage(
                    db=db,
                    discount=discount,
                    customer_id=customer.id,
                    invoice_id=invoice.id,
                    amount_applied=calc_discount,
                )

        # Process Taxes
        if data.tax_ids:
            active_taxes = db.scalars(select(Tax).where(Tax.id.in_(data.tax_ids), Tax.is_active == True)).all()
            item_subtotal = sum((i.subtotal for i in invoice.items), Decimal("0.00"))
            for tax in active_taxes:
                tax_amt = tax.calculate_tax(item_subtotal)
                tax_detail = InvoiceTaxDetail(
                    invoice_id=invoice.id,
                    tax_id=tax.id,
                    tax_name_snapshot=tax.name,
                    tax_rate_snapshot=tax.rate,
                    calculated_tax_amount=tax_amt,
                )
                db.add(tax_detail)

        db.flush()
        invoice.recalculate_totals()
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def generate_invoice_from_subscription(
        db: Session,
        subscription_id: int,
        user_id: Optional[int] = None,
        billing_period_start: Optional[datetime] = None,
        billing_period_end: Optional[datetime] = None,
        coupon_code: Optional[str] = None,
        tax_ids: Optional[List[int]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Invoice:
        """
        Module 3: Automatic Invoice Generation.
        Generates invoice from active subscription line items with duplicate billing prevention.
        """
        subscription = db.scalar(select(Subscription).where(Subscription.id == subscription_id))
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription with ID {subscription_id} not found.",
            )

        if subscription.status not in ["ACTIVE", "CONFIRMED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot generate invoice for subscription in status '{subscription.status}'. Only ACTIVE subscriptions are eligible.",
            )

        period_start = billing_period_start or subscription.current_period_start or subscription.start_date
        period_end = billing_period_end or subscription.current_period_end or subscription.expiry_date

        # Check for duplicate invoice for same subscription & period
        existing_dup = db.scalar(
            select(Invoice).where(
                Invoice.subscription_id == subscription_id,
                Invoice.billing_period_start == period_start,
                Invoice.billing_period_end == period_end,
                Invoice.status != "CANCELLED",
            )
        )
        if existing_dup:
            # Log skipped attempt
            log = InvoiceGenerationLog(
                subscription_id=subscription_id,
                billing_period_start=period_start,
                billing_period_end=period_end,
                status="SKIPPED",
                message=f"Duplicate invoice prevented. Existing invoice: {existing_dup.invoice_number}",
                invoice_id=existing_dup.id,
            )
            db.add(log)
            db.commit()
            return existing_dup

        # Verify idempotency key if provided
        key = idempotency_key or f"SUB_{subscription_id}_{period_start.strftime('%Y%m%d')}_{period_end.strftime('%Y%m%d')}"
        existing_key = db.scalar(select(Invoice).where(Invoice.idempotency_key == key))
        if existing_key:
            return existing_key

        invoice_date = datetime.utcnow()
        due_date = InvoiceService.calculate_due_date(invoice_date, subscription.payment_terms)

        invoice = Invoice(
            invoice_number=InvoiceService.generate_next_invoice_number(db),
            customer_id=subscription.customer_id,
            subscription_id=subscription.id,
            created_by_user_id=user_id,
            invoice_date=invoice_date,
            due_date=due_date,
            status="CONFIRMED",  # Recurring auto invoices are immediately confirmed
            billing_period_start=period_start,
            billing_period_end=period_end,
            payment_terms=subscription.payment_terms,
            notes=f"Recurring billing cycle for subscription {subscription.subscription_number} ({subscription.billing_interval})",
            idempotency_key=key,
        )
        db.add(invoice)
        db.flush()

        # Generate line items from subscription items
        for sub_item in subscription.items:
            unit_price = sub_item.unit_price
            qty = sub_item.quantity
            item_subtotal = (Decimal(str(qty)) * unit_price).quantize(Decimal("0.01"))

            inv_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=sub_item.product_id,
                product_variant_id=sub_item.variant_id,
                subscription_item_id=sub_item.id,
                item_description=f"Subscription Item: Product #{sub_item.product_id}",
                quantity=qty,
                unit_price=unit_price,
                subtotal=item_subtotal,
                tax_rate_snapshot=Decimal("0.00"),
                tax_amount_snapshot=Decimal("0.00"),
                total_amount=item_subtotal,
            )
            db.add(inv_item)

        db.flush()

        # Apply subscription discount reference if any, or coupon_code
        code_to_apply = coupon_code or subscription.discount_reference
        if code_to_apply:
            discount = DiscountService.get_discount_by_code(db, code_to_apply)
            if discount:
                item_subtotal = sum((i.subtotal for i in invoice.items), Decimal("0.00"))
                calc_discount = discount.calculate_discount_amount(item_subtotal)
                discount_detail = InvoiceDiscountDetail(
                    invoice_id=invoice.id,
                    discount_id=discount.id,
                    coupon_code_snapshot=discount.coupon_code,
                    discount_type_snapshot=discount.discount_type,
                    discount_rate_or_value=discount.discount_value,
                    calculated_discount_amount=calc_discount,
                )
                db.add(discount_detail)
                DiscountService.record_usage(
                    db=db,
                    discount=discount,
                    customer_id=subscription.customer_id,
                    invoice_id=invoice.id,
                    amount_applied=calc_discount,
                )

        # Apply applicable taxes
        if tax_ids:
            active_taxes = db.scalars(select(Tax).where(Tax.id.in_(tax_ids), Tax.is_active == True)).all()
            item_subtotal = sum((i.subtotal for i in invoice.items), Decimal("0.00"))
            for tax in active_taxes:
                tax_amt = tax.calculate_tax(item_subtotal)
                tax_detail = InvoiceTaxDetail(
                    invoice_id=invoice.id,
                    tax_id=tax.id,
                    tax_name_snapshot=tax.name,
                    tax_rate_snapshot=tax.rate,
                    calculated_tax_amount=tax_amt,
                )
                db.add(tax_detail)

        db.flush()
        invoice.recalculate_totals()

        # Log generation event
        gen_log = InvoiceGenerationLog(
            subscription_id=subscription.id,
            billing_period_start=period_start,
            billing_period_end=period_end,
            status="SUCCESS",
            message=f"Generated invoice {invoice.invoice_number} successfully.",
            invoice_id=invoice.id,
        )
        db.add(gen_log)

        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def confirm_invoice(db: Session, invoice_id: int, user_id: Optional[int] = None) -> Invoice:
        invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id))
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

        if invoice.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot confirm invoice in status '{invoice.status}'. Only DRAFT invoices can be confirmed.",
            )

        invoice.status = "CONFIRMED"
        invoice.recalculate_totals()
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def cancel_invoice(db: Session, invoice_id: int, user_id: Optional[int] = None) -> Invoice:
        invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id))
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

        if invoice.status == "PAID":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel a fully PAID invoice. Issue a refund or credit note instead.",
            )

        invoice.status = "CANCELLED"
        db.commit()
        db.refresh(invoice)
        return invoice

