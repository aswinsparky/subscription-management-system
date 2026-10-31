"""
Subscription Management and State Machine Service (Module 6).
Handles lifecycle transitions: DRAFT -> CONFIRMED -> ACTIVE -> PAUSED -> CLOSED / CANCELLED.
Enforces plan policy rules (pause_allowed, early_cancellation_allowed).
Maintains append-only audit ledger in subscription_events.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.subscription import Subscription, SubscriptionItem, SubscriptionEvent
from app.models.customer import Customer
from app.models.plan import Plan
from app.models.product import Product, ProductVariant
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionItemResponse,
    SubscriptionEventResponse,
    CustomerSimpleResponse,
    PlanSimpleResponse,
)


class SubscriptionService:

    @staticmethod
    def _get_interval_delta(interval: str) -> timedelta:
        interval_norm = interval.upper()
        if interval_norm == "DAILY":
            return timedelta(days=1)
        elif interval_norm == "WEEKLY":
            return timedelta(days=7)
        elif interval_norm == "MONTHLY":
            return timedelta(days=30)
        elif interval_norm == "YEARLY":
            return timedelta(days=365)
        return timedelta(days=30)

    @staticmethod
    def generate_subscription_number(db: Session) -> str:
        current_year = datetime.now(timezone.utc).year
        prefix = f"SUB-{current_year}-"
        last_sub = (
            db.query(Subscription)
            .filter(Subscription.subscription_number.like(f"{prefix}%"))
            .order_by(Subscription.id.desc())
            .first()
        )
        if last_sub:
            try:
                seq = int(last_sub.subscription_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @staticmethod
    def _snapshot_state(sub: Subscription) -> dict:
        return {
            "status": sub.status,
            "total_amount": str(sub.total_amount),
            "billing_interval": sub.billing_interval,
            "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            "next_billing_date": sub.next_billing_date.isoformat() if sub.next_billing_date else None,
            "auto_renew": sub.auto_renew,
        }

    @staticmethod
    def _get_role_name(user: Optional[User]) -> str:
        if not user or not user.role:
            return "CUSTOMER"
        if isinstance(user.role, str):
            return user.role
        return user.role.name

    @classmethod
    def record_event(
        cls,
        db: Session,
        subscription: Subscription,
        event_type: str,
        actor: Optional[User],
        previous_state: Optional[dict] = None,
        reason: Optional[str] = None,
        metadata_json: Optional[dict] = None,
    ) -> SubscriptionEvent:
        event = SubscriptionEvent(
            subscription_id=subscription.id,
            event_type=event_type,
            previous_state=previous_state,
            new_state=cls._snapshot_state(subscription),
            actor_id=actor.id if actor else None,
            actor_email=actor.email if actor else "system@brightloop.io",
            actor_role=cls._get_role_name(actor) if actor else "SYSTEM",
            reason=reason,
            metadata_json=metadata_json,
        )
        db.add(event)
        return event

    @classmethod
    def _verify_tenant_access(cls, current_user: User, customer_id: int, db: Session):
        """Enforces that CUSTOMER role can only access their own linked customer entity."""
        role_name = cls._get_role_name(current_user)
        if role_name in ("ADMIN", "STAFF"):
            return
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer or customer.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only view or manage your own subscriptions.",
            )

    @classmethod
    def create_subscription(
        cls,
        db: Session,
        current_user: User,
        data: SubscriptionCreate,
    ) -> Subscription:
        cls._verify_tenant_access(current_user, data.customer_id, db)

        customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
        if not customer or customer.account_status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or inactive customer.",
            )

        plan = db.query(Plan).filter(Plan.id == data.plan_id).first()
        if not plan or plan.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or inactive subscription plan.",
            )

        billing_interval = data.billing_interval or plan.billing_interval
        now = datetime.now(timezone.utc)
        delta = cls._get_interval_delta(billing_interval)
        period_end = now + delta
        expiry_date = period_end

        subtotal = Decimal("0.00")
        items_to_add = []

        for item_in in data.items:
            product = db.query(Product).filter(Product.id == item_in.product_id).first()
            if not product or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product ID {item_in.product_id} does not exist or is inactive.",
                )

            unit_price = product.sales_price
            variant = None
            if item_in.variant_id:
                variant = (
                    db.query(ProductVariant)
                    .filter(
                        ProductVariant.id == item_in.variant_id,
                        ProductVariant.product_id == product.id,
                        ProductVariant.is_active.is_(True),
                    )
                    .first()
                )
                if not variant:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Variant ID {item_in.variant_id} is invalid for product '{product.name}'.",
                    )
                unit_price += variant.additional_price

            line_subtotal = unit_price * item_in.quantity
            subtotal += line_subtotal

            sub_item = SubscriptionItem(
                product_id=product.id,
                variant_id=variant.id if variant else None,
                quantity=item_in.quantity,
                unit_price=unit_price,
                subtotal=line_subtotal,
            )
            items_to_add.append(sub_item)

        total_amount = subtotal  # Tax/discount handled by Member 2

        subscription = Subscription(
            subscription_number=cls.generate_subscription_number(db),
            customer_id=customer.id,
            plan_id=plan.id,
            start_date=now,
            expiry_date=expiry_date,
            billing_interval=billing_interval,
            payment_terms=data.payment_terms,
            subtotal=subtotal,
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=total_amount,
            status="DRAFT",
            next_billing_date=period_end,
            current_period_start=now,
            current_period_end=period_end,
            auto_renew=data.auto_renew,
        )
        db.add(subscription)
        db.flush()

        for item in items_to_add:
            item.subscription_id = subscription.id
            db.add(item)

        # Log creation event
        cls.record_event(
            db=db,
            subscription=subscription,
            event_type="CREATED",
            actor=current_user,
            previous_state=None,
            reason="Subscription created in DRAFT status",
        )

        db.commit()
        db.refresh(subscription)
        return subscription

    @classmethod
    def confirm_subscription(
        cls,
        db: Session,
        current_user: User,
        subscription_id: int,
    ) -> Subscription:
        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        cls._verify_tenant_access(current_user, sub.customer_id, db)

        if sub.status not in ("DRAFT", "QUOTATION"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot confirm subscription with status '{sub.status}'. Allowed from DRAFT or QUOTATION.",
            )

        prev_state = cls._snapshot_state(sub)
        sub.status = "CONFIRMED"

        cls.record_event(
            db=db,
            subscription=sub,
            event_type="CONFIRMED",
            actor=current_user,
            previous_state=prev_state,
            reason="Subscription confirmed and ready for activation",
        )

        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def activate_subscription(
        cls,
        db: Session,
        current_user: User,
        subscription_id: int,
    ) -> Subscription:
        sub = (
            db.query(Subscription)
            .options(joinedload(Subscription.plan))
            .filter(Subscription.id == subscription_id)
            .first()
        )
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        cls._verify_tenant_access(current_user, sub.customer_id, db)

        if sub.status != "CONFIRMED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot activate subscription with status '{sub.status}'. Must be in CONFIRMED status.",
            )

        now = datetime.now(timezone.utc)
        delta = cls._get_interval_delta(sub.billing_interval)
        sub.start_date = now
        sub.current_period_start = now
        sub.current_period_end = now + delta
        sub.next_billing_date = now + delta
        sub.expiry_date = now + delta

        prev_state = cls._snapshot_state(sub)
        sub.status = "ACTIVE"

        cls.record_event(
            db=db,
            subscription=sub,
            event_type="ACTIVATED",
            actor=current_user,
            previous_state=prev_state,
            reason="Subscription officially activated",
        )

        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def pause_subscription(
        cls,
        db: Session,
        current_user: User,
        subscription_id: int,
        reason: Optional[str] = None,
    ) -> Subscription:
        sub = (
            db.query(Subscription)
            .options(joinedload(Subscription.plan))
            .filter(Subscription.id == subscription_id)
            .first()
        )
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        cls._verify_tenant_access(current_user, sub.customer_id, db)

        if sub.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot pause subscription with status '{sub.status}'. Must be ACTIVE.",
            )

        if sub.plan and not sub.plan.pause_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan '{sub.plan.name}' policy prohibits pausing subscriptions.",
            )

        prev_state = cls._snapshot_state(sub)
        sub.status = "PAUSED"

        cls.record_event(
            db=db,
            subscription=sub,
            event_type="PAUSED",
            actor=current_user,
            previous_state=prev_state,
            reason=reason or "Subscription paused by user request",
        )

        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def resume_subscription(
        cls,
        db: Session,
        current_user: User,
        subscription_id: int,
        reason: Optional[str] = None,
    ) -> Subscription:
        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        cls._verify_tenant_access(current_user, sub.customer_id, db)

        if sub.status != "PAUSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resume subscription with status '{sub.status}'. Must be PAUSED.",
            )

        prev_state = cls._snapshot_state(sub)
        sub.status = "ACTIVE"

        cls.record_event(
            db=db,
            subscription=sub,
            event_type="RESUMED",
            actor=current_user,
            previous_state=prev_state,
            reason=reason or "Subscription resumed back to ACTIVE",
        )

        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def cancel_subscription(
        cls,
        db: Session,
        current_user: User,
        subscription_id: int,
        reason: Optional[str] = None,
    ) -> Subscription:
        sub = (
            db.query(Subscription)
            .options(joinedload(Subscription.plan))
            .filter(Subscription.id == subscription_id)
            .first()
        )
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        cls._verify_tenant_access(current_user, sub.customer_id, db)

        if sub.status in ("CANCELLED", "CLOSED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subscription is already in terminal status '{sub.status}'.",
            )

        # Check early cancellation policy if active/paused and cancelling before expiry
        now = datetime.now(timezone.utc)
        if sub.status in ("ACTIVE", "PAUSED"):
            expiry = sub.expiry_date.replace(tzinfo=timezone.utc) if sub.expiry_date.tzinfo is None else sub.expiry_date
            if now < expiry and sub.plan and not sub.plan.early_cancellation_allowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Plan '{sub.plan.name}' policy prohibits early cancellation.",
                )

        prev_state = cls._snapshot_state(sub)
        sub.status = "CANCELLED"
        sub.cancellation_reason = reason or "Cancelled by user"

        cls.record_event(
            db=db,
            subscription=sub,
            event_type="CANCELLED",
            actor=current_user,
            previous_state=prev_state,
            reason=reason or "Subscription cancelled",
        )

        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def close_subscription(
        cls,
        db: Session,
        current_user: User,
        subscription_id: int,
        reason: Optional[str] = None,
    ) -> Subscription:
        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        cls._verify_tenant_access(current_user, sub.customer_id, db)

        if sub.status in ("CLOSED", "CANCELLED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subscription is already in terminal status '{sub.status}'.",
            )

        prev_state = cls._snapshot_state(sub)
        sub.status = "CLOSED"

        cls.record_event(
            db=db,
            subscription=sub,
            event_type="CLOSED",
            actor=current_user,
            previous_state=prev_state,
            reason=reason or "Subscription closed normally",
        )

        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def get_subscription(
        cls,
        db: Session,
        current_user: User,
        subscription_id: int,
    ) -> SubscriptionResponse:
        sub = (
            db.query(Subscription)
            .options(
                joinedload(Subscription.customer),
                joinedload(Subscription.plan),
                joinedload(Subscription.items).joinedload(SubscriptionItem.product),
                joinedload(Subscription.items).joinedload(SubscriptionItem.variant),
                joinedload(Subscription.events),
            )
            .filter(Subscription.id == subscription_id)
            .first()
        )
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        cls._verify_tenant_access(current_user, sub.customer_id, db)
        return cls._format_response(sub)

    @classmethod
    def list_subscriptions(
        cls,
        db: Session,
        current_user: User,
        customer_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        plan_id: Optional[int] = None,
        page: int = 1,
        size: int = 10,
    ) -> Tuple[List[SubscriptionResponse], int]:
        query = (
            db.query(Subscription)
            .options(
                joinedload(Subscription.customer),
                joinedload(Subscription.plan),
                joinedload(Subscription.items).joinedload(SubscriptionItem.product),
                joinedload(Subscription.items).joinedload(SubscriptionItem.variant),
                joinedload(Subscription.events),
            )
        )

        # Customer role can only see their own subscriptions
        if cls._get_role_name(current_user) not in ("ADMIN", "STAFF"):
            customer = db.query(Customer).filter(Customer.user_id == current_user.id).first()
            if not customer:
                return [], 0
            query = query.filter(Subscription.customer_id == customer.id)
        elif customer_id:
            query = query.filter(Subscription.customer_id == customer_id)

        if status_filter:
            query = query.filter(Subscription.status == status_filter.upper())

        if plan_id:
            query = query.filter(Subscription.plan_id == plan_id)

        total = query.count()
        subs = (
            query.order_by(Subscription.id.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return [cls._format_response(s) for s in subs], total

    @classmethod
    def get_events(
        cls,
        db: Session,
        current_user: User,
        subscription_id: int,
    ) -> List[SubscriptionEventResponse]:
        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        cls._verify_tenant_access(current_user, sub.customer_id, db)

        events = (
            db.query(SubscriptionEvent)
            .filter(SubscriptionEvent.subscription_id == subscription_id)
            .order_by(SubscriptionEvent.created_at.asc())
            .all()
        )
        return [SubscriptionEventResponse.model_validate(e) for e in events]

    @classmethod
    def _format_response(cls, sub: Subscription) -> SubscriptionResponse:
        items_resp = []
        for it in sub.items:
            items_resp.append(
                SubscriptionItemResponse(
                    id=it.id,
                    subscription_id=it.subscription_id,
                    product_id=it.product_id,
                    variant_id=it.variant_id,
                    product_name=it.product.name if it.product else None,
                    variant_name=it.variant.name if it.variant else None,
                    quantity=it.quantity,
                    unit_price=it.unit_price,
                    subtotal=it.subtotal,
                )
            )

        events_resp = [SubscriptionEventResponse.model_validate(e) for e in sub.events]

        return SubscriptionResponse(
            id=sub.id,
            subscription_number=sub.subscription_number,
            customer_id=sub.customer_id,
            plan_id=sub.plan_id,
            source_quotation_id=sub.source_quotation_id,
            start_date=sub.start_date,
            expiry_date=sub.expiry_date,
            billing_interval=sub.billing_interval,
            payment_terms=sub.payment_terms,
            subtotal=sub.subtotal,
            discount_reference=sub.discount_reference,
            discount_amount=sub.discount_amount,
            tax_amount=sub.tax_amount,
            total_amount=sub.total_amount,
            status=sub.status,
            next_billing_date=sub.next_billing_date,
            current_period_start=sub.current_period_start,
            current_period_end=sub.current_period_end,
            auto_renew=sub.auto_renew,
            last_renewed_at=sub.last_renewed_at,
            cancellation_reason=sub.cancellation_reason,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
            customer=CustomerSimpleResponse.model_validate(sub.customer) if sub.customer else None,
            plan=PlanSimpleResponse.model_validate(sub.plan) if sub.plan else None,
            items=items_resp,
            events=events_resp,
        )
