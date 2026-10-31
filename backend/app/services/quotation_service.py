"""
Quotation Management Domain Service (Module 5).
Handles Quotation Creation, Templates, Expiration Validation, and Safe Conversion to Subscription.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import math
from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, or_, func
from fastapi import HTTPException, status
from app.models.quotation import (
    Quotation,
    QuotationItem,
    QuotationTemplate,
    QuotationTemplateItem,
)
from app.models.customer import Customer
from app.models.plan import Plan
from app.models.product import Product, ProductVariant
from app.models.subscription import Subscription, SubscriptionItem, SubscriptionEvent
from app.models.user import User
from app.schemas.quotation import (
    QuotationCreate,
    QuotationCreateFromTemplate,
    QuotationUpdate,
    QuotationResponse,
    QuotationListResponse,
    QuotationItemResponse,
    ConvertQuotationResponse,
    QuotationTemplateCreate,
    QuotationTemplateResponse,
    QuotationTemplateItemResponse,
)


class QuotationService:
    @staticmethod
    def _generate_quotation_number(db: Session) -> str:
        year = datetime.now(timezone.utc).year
        count = db.scalar(select(func.count(Quotation.id))) or 0
        return f"QUOTE-{year}-{(count + 1):04d}"

    @staticmethod
    def _generate_subscription_number(db: Session) -> str:
        year = datetime.now(timezone.utc).year
        count = db.scalar(select(func.count(Subscription.id))) or 0
        return f"SUB-{year}-{(count + 1):04d}"

    @staticmethod
    def _to_quotation_response(q: Quotation) -> QuotationResponse:
        items = [
            QuotationItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else None,
                variant_id=item.variant_id,
                variant_name=item.variant.variant_name if item.variant else None,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in q.items
        ]

        return QuotationResponse(
            id=q.id,
            quotation_number=q.quotation_number,
            customer_id=q.customer_id,
            customer_name=q.customer.full_name if q.customer else None,
            customer_code=q.customer.customer_code if q.customer else None,
            plan_id=q.plan_id,
            plan_name=q.plan.name if q.plan else None,
            template_id=q.template_id,
            quotation_date=q.quotation_date,
            expiration_date=q.expiration_date,
            subtotal=q.subtotal,
            tax_reference=q.tax_reference,
            tax_amount=q.tax_amount,
            total=q.total,
            status=q.status,
            converted_to_subscription_id=q.converted_to_subscription_id,
            created_by_user_id=q.created_by_user_id,
            created_at=q.created_at,
            updated_at=q.updated_at,
            items=items,
        )

    @staticmethod
    def create_quotation(db: Session, req: QuotationCreate, current_user: User) -> QuotationResponse:
        """Create quotation from scratch."""
        # Validate customer
        customer = db.scalar(select(Customer).where(Customer.id == req.customer_id))
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        # Validate plan
        plan = db.scalar(select(Plan).where(Plan.id == req.plan_id))
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription Plan not found.")

        now = datetime.now(timezone.utc)
        exp_date = req.expiration_date or (now + timedelta(days=30))
        if exp_date <= now:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Expiration date must be in the future.")

        quotation_num = QuotationService._generate_quotation_number(db)
        quotation = Quotation(
            quotation_number=quotation_num,
            customer_id=customer.id,
            plan_id=plan.id,
            template_id=req.template_id,
            expiration_date=exp_date,
            tax_reference=req.tax_reference,
            tax_amount=Decimal("0.00"),
            status="DRAFT",
            created_by_user_id=current_user.id,
        )
        db.add(quotation)
        db.flush()

        # Build items and calculate subtotal
        subtotal_acc = Decimal("0.00")
        total_quantity = 0

        for line in req.items:
            product = db.scalar(select(Product).where(Product.id == line.product_id))
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product #{line.product_id} not found.")

            variant = None
            if line.variant_id:
                variant = db.scalar(
                    select(ProductVariant).where(
                        ProductVariant.id == line.variant_id, ProductVariant.product_id == line.product_id
                    )
                )
                if not variant:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Variant #{line.variant_id} does not belong to Product #{line.product_id}.",
                    )

            line_subtotal = Decimal(str(line.quantity)) * line.unit_price
            item = QuotationItem(
                quotation_id=quotation.id,
                product_id=line.product_id,
                variant_id=line.variant_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                subtotal=line_subtotal,
            )
            db.add(item)
            subtotal_acc += line_subtotal
            total_quantity += line.quantity

        # Enforce plan minimum quantity
        if total_quantity < plan.minimum_quantity:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Total items quantity ({total_quantity}) does not meet Plan minimum quantity requirement ({plan.minimum_quantity}).",
            )

        quotation.subtotal = subtotal_acc
        quotation.total = subtotal_acc + quotation.tax_amount
        db.commit()

        # Reload with relationships
        full_q = db.scalar(
            select(Quotation)
            .options(
                selectinload(Quotation.items).selectinload(QuotationItem.product),
                selectinload(Quotation.items).selectinload(QuotationItem.variant),
                selectinload(Quotation.customer),
                selectinload(Quotation.plan),
            )
            .where(Quotation.id == quotation.id)
        )
        return QuotationService._to_quotation_response(full_q)

    @staticmethod
    def create_from_template(
        db: Session, req: QuotationCreateFromTemplate, current_user: User
    ) -> QuotationResponse:
        """Create a new quotation pre-populated from a reusable template."""
        template = db.scalar(
            select(QuotationTemplate)
            .options(selectinload(QuotationTemplate.items))
            .where(QuotationTemplate.id == req.template_id)
        )
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation template not found.")
        if not template.default_plan_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Template has no default plan configured.")

        items = [
            QuotationItemCreate(
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.default_quantity,
                unit_price=item.unit_price,
            )
            for item in template.items
        ]

        now = datetime.now(timezone.utc)
        exp_date = now + timedelta(days=template.validity_duration_days)

        q_create = QuotationCreate(
            customer_id=req.customer_id,
            plan_id=template.default_plan_id,
            template_id=template.id,
            expiration_date=exp_date,
            items=items,
        )
        return QuotationService.create_quotation(db, q_create, current_user)

    @staticmethod
    def get_quotations(
        db: Session,
        current_user: User,
        query: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> QuotationListResponse:
        """List quotations with search, status filter, and pagination."""
        stmt = (
            select(Quotation)
            .options(
                selectinload(Quotation.items).selectinload(QuotationItem.product),
                selectinload(Quotation.items).selectinload(QuotationItem.variant),
                selectinload(Quotation.customer),
                selectinload(Quotation.plan),
            )
            .join(Customer)
        )

        user_role = current_user.role.name if current_user.role else "CUSTOMER"
        if user_role == "CUSTOMER":
            # Strict tenant isolation
            stmt = stmt.where(Customer.user_id == current_user.id)

        if query and query.strip():
            search = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Quotation.quotation_number.ilike(search),
                    Customer.full_name.ilike(search),
                    Customer.customer_code.ilike(search),
                )
            )

        if status_filter and status_filter.upper() != "ALL":
            stmt = stmt.where(Quotation.status == status_filter.upper())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        offset = (max(page, 1) - 1) * page_size
        stmt = stmt.order_by(Quotation.created_at.desc()).offset(offset).limit(page_size)
        items = db.scalars(stmt).all()

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return QuotationListResponse(
            items=[QuotationService._to_quotation_response(q) for q in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_quotation_by_id(db: Session, quotation_id: int, current_user: User) -> QuotationResponse:
        """Retrieve quotation by ID with tenant security check."""
        q = db.scalar(
            select(Quotation)
            .options(
                selectinload(Quotation.items).selectinload(QuotationItem.product),
                selectinload(Quotation.items).selectinload(QuotationItem.variant),
                selectinload(Quotation.customer),
                selectinload(Quotation.plan),
            )
            .where(Quotation.id == quotation_id)
        )
        if not q:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")

        user_role = current_user.role.name if current_user.role else "CUSTOMER"
        if user_role == "CUSTOMER" and q.customer.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this quotation.")

        return QuotationService._to_quotation_response(q)

    @staticmethod
    def update_quotation(
        db: Session, quotation_id: int, req: QuotationUpdate, current_user: User
    ) -> QuotationResponse:
        """Update quotation status or parameters."""
        q = db.scalar(
            select(Quotation)
            .options(selectinload(Quotation.items))
            .where(Quotation.id == quotation_id)
        )
        if not q:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")

        if req.status is not None:
            q.status = req.status.upper()
        if req.expiration_date is not None:
            q.expiration_date = req.expiration_date
        if req.tax_reference is not None:
            q.tax_reference = req.tax_reference

        q.updated_at = datetime.now(timezone.utc)
        db.commit()
        return QuotationService.get_quotation_by_id(db, quotation_id, current_user)

    @staticmethod
    def convert_to_subscription(
        db: Session, quotation_id: int, current_user: User
    ) -> ConvertQuotationResponse:
        """
        Converts an accepted quotation into an active Subscription.
        Enforces:
        - Must not be expired
        - Must not have been converted previously (IDEMPOTENCY)
        - Atomic transaction copying line items & creating initial Time Machine audit event.
        """
        q = db.scalar(
            select(Quotation)
            .options(
                selectinload(Quotation.items),
                selectinload(Quotation.customer),
                selectinload(Quotation.plan),
            )
            .where(Quotation.id == quotation_id)
        )
        if not q:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")

        # Check duplicate conversion guard
        if q.converted_to_subscription_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Quotation #{q.quotation_number} has already been converted to Subscription #{q.converted_to_subscription_id}.",
            )

        # Check expiration
        now = datetime.now(timezone.utc)
        exp = q.expiration_date.replace(tzinfo=timezone.utc) if q.expiration_date.tzinfo is None else q.expiration_date
        if now > exp:
            q.status = "EXPIRED"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quotation #{q.quotation_number} expired on {exp.strftime('%Y-%m-%d')} and cannot be converted.",
            )

        # Determine subscription period dates
        interval = q.plan.billing_interval.upper()
        if interval == "DAILY":
            period_delta = timedelta(days=1)
        elif interval == "WEEKLY":
            period_delta = timedelta(days=7)
        elif interval == "MONTHLY":
            period_delta = timedelta(days=30)
        else:  # YEARLY
            period_delta = timedelta(days=365)

        start_date = now
        expiry_date = start_date + period_delta
        next_billing_date = expiry_date

        sub_number = QuotationService._generate_subscription_number(db)
        subscription = Subscription(
            subscription_number=sub_number,
            customer_id=q.customer_id,
            plan_id=q.plan_id,
            source_quotation_id=q.id,
            start_date=start_date,
            expiry_date=expiry_date,
            billing_interval=interval,
            payment_terms="Immediate",
            subtotal=q.subtotal,
            discount_amount=Decimal("0.00"),
            tax_amount=q.tax_amount,
            total_amount=q.total,
            status="CONFIRMED",
            next_billing_date=next_billing_date,
            current_period_start=start_date,
            current_period_end=expiry_date,
            auto_renew=q.plan.renewal_allowed,
        )
        db.add(subscription)
        db.flush()

        # Copy line items to subscription_items
        for q_item in q.items:
            sub_item = SubscriptionItem(
                subscription_id=subscription.id,
                product_id=q_item.product_id,
                variant_id=q_item.variant_id,
                quantity=q_item.quantity,
                unit_price=q_item.unit_price,
                subtotal=q_item.subtotal,
            )
            db.add(sub_item)

        # Append Time Machine audit event
        audit_event = SubscriptionEvent(
            subscription_id=subscription.id,
            event_type="CREATED_FROM_QUOTATION",
            previous_state=None,
            new_state={
                "status": "CONFIRMED",
                "subscription_number": sub_number,
                "source_quotation_number": q.quotation_number,
                "total_amount": str(q.total),
                "plan": q.plan.name,
            },
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role.name if current_user.role else "STAFF",
            reason=f"Converted from accepted quotation {q.quotation_number}",
        )
        db.add(audit_event)

        # Lock quotation against re-conversion
        q.converted_to_subscription_id = subscription.id
        q.status = "ACCEPTED"
        db.commit()

        return ConvertQuotationResponse(
            message=f"Quotation #{q.quotation_number} successfully converted to Subscription #{sub_number}.",
            quotation_id=q.id,
            subscription_id=subscription.id,
            subscription_number=sub_number,
        )
