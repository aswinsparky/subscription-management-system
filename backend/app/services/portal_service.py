"""
Customer Self-Service Portal Service (Module 10).
Guarantees tenant isolation where end-users with role CUSTOMER can only interact
with their own subscriptions, quotations, and profile.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Customer
from app.models.subscription import Subscription
from app.models.quotation import Quotation
from app.models.user import User
from app.services.subscription_service import SubscriptionService
from app.services.quotation_service import QuotationService
from app.schemas.portal import (
    CustomerProfileResponse,
    CustomerProfileUpdate,
    CustomerPortalOverview,
)
from app.schemas.subscription import SubscriptionResponse
from app.schemas.quotation import QuotationResponse, ConvertQuotationResponse


class PortalService:

    @classmethod
    def get_customer_for_user(cls, db: Session, current_user: User) -> Customer:
        customer = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not customer:
            customer = db.query(Customer).filter(Customer.email == current_user.email).first()
            if customer:
                customer.user_id = current_user.id
                db.commit()
                db.refresh(customer)
            else:
                # Seed a default customer record for newly registered customer user
                import uuid
                customer = Customer(
                    customer_code=f"CUST-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:4].upper()}",
                    user_id=current_user.id,
                    full_name=current_user.full_name,
                    email=current_user.email,
                    billing_address="Default Registered Address",
                    account_status="ACTIVE",
                )
                db.add(customer)
                db.commit()
                db.refresh(customer)
        return customer

    @classmethod
    def get_overview(cls, db: Session, current_user: User) -> CustomerPortalOverview:
        customer = cls.get_customer_for_user(db, current_user)

        subs, _ = SubscriptionService.list_subscriptions(
            db=db,
            current_user=current_user,
            customer_id=customer.id,
            size=100,
        )

        quotes_db = (
            db.query(Quotation)
            .options(
                joinedload(Quotation.items),
                joinedload(Quotation.customer),
                joinedload(Quotation.plan),
            )
            .filter(Quotation.customer_id == customer.id)
            .order_by(Quotation.id.desc())
            .all()
        )
        quotes_resp = [QuotationService._format_response(q) for q in quotes_db]

        active_subs = [s for s in subs if s.status == "ACTIVE"]
        total_mrr = sum((s.total_amount for s in active_subs), Decimal("0.00"))

        return CustomerPortalOverview(
            profile=CustomerProfileResponse.model_validate(customer),
            active_subscriptions=subs,
            pending_quotations=quotes_resp,
            total_active_mrr=total_mrr,
        )

    @classmethod
    def update_profile(
        cls, db: Session, current_user: User, data: CustomerProfileUpdate
    ) -> CustomerProfileResponse:
        customer = cls.get_customer_for_user(db, current_user)

        if data.phone is not None:
            customer.phone = data.phone
        if data.company_name is not None:
            customer.company_name = data.company_name
        if data.billing_address is not None:
            customer.billing_address = data.billing_address
        if data.tax_id is not None:
            customer.tax_id = data.tax_id

        db.commit()
        db.refresh(customer)
        return CustomerProfileResponse.model_validate(customer)

    @classmethod
    def pause_subscription(
        cls, db: Session, current_user: User, subscription_id: int, reason: Optional[str] = None
    ) -> SubscriptionResponse:
        customer = cls.get_customer_for_user(db, current_user)
        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub or sub.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found in your account.",
            )
        SubscriptionService.pause_subscription(db, current_user, subscription_id, reason)
        return SubscriptionService.get_subscription(db, current_user, subscription_id)

    @classmethod
    def resume_subscription(
        cls, db: Session, current_user: User, subscription_id: int, reason: Optional[str] = None
    ) -> SubscriptionResponse:
        customer = cls.get_customer_for_user(db, current_user)
        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub or sub.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found in your account.",
            )
        SubscriptionService.resume_subscription(db, current_user, subscription_id, reason)
        return SubscriptionService.get_subscription(db, current_user, subscription_id)

    @classmethod
    def cancel_subscription(
        cls, db: Session, current_user: User, subscription_id: int, reason: Optional[str] = None
    ) -> SubscriptionResponse:
        customer = cls.get_customer_for_user(db, current_user)
        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub or sub.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found in your account.",
            )
        SubscriptionService.cancel_subscription(db, current_user, subscription_id, reason)
        return SubscriptionService.get_subscription(db, current_user, subscription_id)

    @classmethod
    def accept_quotation(
        cls, db: Session, current_user: User, quotation_id: int
    ) -> ConvertQuotationResponse:
        customer = cls.get_customer_for_user(db, current_user)
        quote = db.query(Quotation).filter(Quotation.id == quotation_id).first()
        if not quote or quote.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quotation not found in your account.",
            )
        return QuotationService.convert_to_subscription(db, quotation_id, current_user)
