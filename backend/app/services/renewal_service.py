"""
Automated Renewal Scheduler & Member 2 Billing Integration Service (Module 7).
Enforces idempotency keys, billing period advancement, and Member 2 invoice synchronization.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.subscription import Subscription, RenewalBillingRequest
from app.models.customer import Customer
from app.models.plan import Plan
from app.models.user import User
from app.services.subscription_service import SubscriptionService
from app.schemas.renewal import (
    RenewalBillingRequestResponse,
    DueSubscriptionResponse,
    BatchRenewalResult,
    Member2WebhookPayload,
)


class RenewalService:

    @staticmethod
    def generate_idempotency_key(sub: Subscription, period_start: datetime, period_end: datetime) -> str:
        s_str = period_start.strftime("%Y%m%d")
        e_str = period_end.strftime("%Y%m%d")
        return f"REN-SUB{sub.id}-{s_str}-{e_str}"

    @classmethod
    def get_due_subscriptions(
        cls,
        db: Session,
        horizon_days: int = 7,
    ) -> List[DueSubscriptionResponse]:
        now = datetime.now(timezone.utc)
        horizon_cutoff = now + timedelta(days=horizon_days)

        subs = (
            db.query(Subscription)
            .options(
                joinedload(Subscription.customer),
                joinedload(Subscription.plan),
            )
            .filter(
                Subscription.status == "ACTIVE",
                Subscription.auto_renew.is_(True),
                Subscription.next_billing_date <= horizon_cutoff,
            )
            .order_by(Subscription.next_billing_date.asc())
            .all()
        )

        due_list = []
        for s in subs:
            # Skip if plan explicitly prohibits renewal
            if s.plan and not s.plan.renewal_allowed:
                continue

            delta = SubscriptionService._get_interval_delta(s.billing_interval)
            next_start = s.current_period_end
            next_end = next_start + delta
            key = cls.generate_idempotency_key(s, next_start, next_end)

            next_bill = s.next_billing_date.replace(tzinfo=timezone.utc) if s.next_billing_date.tzinfo is None else s.next_billing_date
            days_until = (next_bill - now).days

            due_list.append(
                DueSubscriptionResponse(
                    subscription_id=s.id,
                    subscription_number=s.subscription_number,
                    customer_id=s.customer_id,
                    customer_name=s.customer.full_name if s.customer else f"Customer #{s.customer_id}",
                    plan_name=s.plan.name if s.plan else f"Plan #{s.plan_id}",
                    billing_interval=s.billing_interval,
                    amount=s.total_amount,
                    current_period_end=s.current_period_end,
                    next_billing_date=s.next_billing_date,
                    days_until_due=days_until,
                    idempotency_key=key,
                )
            )
        return due_list

    @classmethod
    def list_requests(
        cls,
        db: Session,
        status_filter: Optional[str] = None,
        subscription_id: Optional[int] = None,
        page: int = 1,
        size: int = 50,
    ) -> Tuple[List[RenewalBillingRequestResponse], int]:
        query = (
            db.query(RenewalBillingRequest)
            .options(
                joinedload(RenewalBillingRequest.subscription).joinedload(Subscription.customer)
            )
        )

        if status_filter:
            query = query.filter(RenewalBillingRequest.status == status_filter.upper())
        if subscription_id:
            query = query.filter(RenewalBillingRequest.subscription_id == subscription_id)

        total = query.count()
        reqs = (
            query.order_by(RenewalBillingRequest.id.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        resp = []
        for r in reqs:
            sub = r.subscription
            cust_name = sub.customer.full_name if (sub and sub.customer) else None
            sub_num = sub.subscription_number if sub else None
            resp.append(
                RenewalBillingRequestResponse(
                    id=r.id,
                    idempotency_key=r.idempotency_key,
                    subscription_id=r.subscription_id,
                    subscription_number=sub_num,
                    customer_id=r.customer_id,
                    customer_name=cust_name,
                    billing_period_start=r.billing_period_start,
                    billing_period_end=r.billing_period_end,
                    amount=r.amount,
                    status=r.status,
                    invoice_reference=r.invoice_reference,
                    retry_count=r.retry_count,
                    last_error=r.last_error,
                    created_at=r.created_at,
                )
            )
        return resp, total

    @classmethod
    def trigger_renewal(
        cls,
        db: Session,
        subscription_id: int,
        actor: Optional[User] = None,
        simulate_member2: bool = True,
    ) -> RenewalBillingRequestResponse:
        sub = (
            db.query(Subscription)
            .options(
                joinedload(Subscription.plan),
                joinedload(Subscription.customer),
            )
            .filter(Subscription.id == subscription_id)
            .first()
        )
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        if sub.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subscription is in status '{sub.status}'. Only ACTIVE subscriptions can be renewed.",
            )

        if not sub.auto_renew:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription auto_renew flag is disabled.",
            )

        if sub.plan and not sub.plan.renewal_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan '{sub.plan.name}' policy prohibits renewals.",
            )

        delta = SubscriptionService._get_interval_delta(sub.billing_interval)
        next_period_start = sub.current_period_end
        next_period_end = next_period_start + delta
        idempotency_key = cls.generate_idempotency_key(sub, next_period_start, next_period_end)

        # Check existing request with idempotency key
        existing = (
            db.query(RenewalBillingRequest)
            .filter(RenewalBillingRequest.idempotency_key == idempotency_key)
            .first()
        )
        if existing and existing.status == "PROCESSED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate renewal prevented. Period already processed with key {idempotency_key} (Invoice: {existing.invoice_reference}).",
            )

        req = existing
        if not req:
            req = RenewalBillingRequest(
                idempotency_key=idempotency_key,
                subscription_id=sub.id,
                customer_id=sub.customer_id,
                billing_period_start=next_period_start,
                billing_period_end=next_period_end,
                amount=sub.total_amount,
                status="PENDING",
            )
            db.add(req)
            db.flush()

        if simulate_member2:
            # Synchronous simulated dispatch to Member 2 Billing Engine
            inv_ref = f"INV-M2-{uuid.uuid4().hex[:8].upper()}"
            req.status = "PROCESSED"
            req.invoice_reference = inv_ref

            # Advance subscription periods
            prev_state = SubscriptionService._snapshot_state(sub)
            now = datetime.now(timezone.utc)
            sub.current_period_start = next_period_start
            sub.current_period_end = next_period_end
            sub.next_billing_date = next_period_end
            sub.expiry_date = next_period_end
            sub.last_renewed_at = now

            # Record event in immutable ledger
            SubscriptionService.record_event(
                db=db,
                subscription=sub,
                event_type="RENEWED",
                actor=actor,
                previous_state=prev_state,
                reason=f"Renewed for period {next_period_start.strftime('%Y-%m-%d')} to {next_period_end.strftime('%Y-%m-%d')} via Member 2 invoice {inv_ref}",
                metadata_json={
                    "idempotency_key": idempotency_key,
                    "invoice_reference": inv_ref,
                    "amount": str(sub.total_amount),
                },
            )

        db.commit()
        db.refresh(req)

        return RenewalBillingRequestResponse(
            id=req.id,
            idempotency_key=req.idempotency_key,
            subscription_id=req.subscription_id,
            subscription_number=sub.subscription_number,
            customer_id=req.customer_id,
            customer_name=sub.customer.full_name if sub.customer else None,
            billing_period_start=req.billing_period_start,
            billing_period_end=req.billing_period_end,
            amount=req.amount,
            status=req.status,
            invoice_reference=req.invoice_reference,
            retry_count=req.retry_count,
            last_error=req.last_error,
            created_at=req.created_at,
        )

    @classmethod
    def batch_process_due(cls, db: Session, horizon_days: int = 0) -> BatchRenewalResult:
        due = cls.get_due_subscriptions(db, horizon_days=horizon_days)
        processed = []
        failed = 0

        for d in due:
            try:
                res = cls.trigger_renewal(db, d.subscription_id, actor=None, simulate_member2=True)
                processed.append(res)
            except Exception:
                failed += 1

        return BatchRenewalResult(
            total_due=len(due),
            processed_count=len(processed),
            failed_count=failed,
            details=processed,
        )

    @classmethod
    def handle_member2_webhook(
        cls, db: Session, payload: Member2WebhookPayload
    ) -> RenewalBillingRequestResponse:
        req = (
            db.query(RenewalBillingRequest)
            .options(
                joinedload(RenewalBillingRequest.subscription).joinedload(Subscription.customer)
            )
            .filter(RenewalBillingRequest.idempotency_key == payload.idempotency_key)
            .first()
        )
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Renewal request not found for key {payload.idempotency_key}",
            )

        if payload.status == "SUCCESS":
            req.status = "PROCESSED"
            req.invoice_reference = payload.invoice_reference
            sub = req.subscription
            if sub:
                prev_state = SubscriptionService._snapshot_state(sub)
                now = datetime.now(timezone.utc)
                sub.current_period_start = req.billing_period_start
                sub.current_period_end = req.billing_period_end
                sub.next_billing_date = req.billing_period_end
                sub.expiry_date = req.billing_period_end
                sub.last_renewed_at = now

                SubscriptionService.record_event(
                    db=db,
                    subscription=sub,
                    event_type="RENEWED",
                    actor=None,
                    previous_state=prev_state,
                    reason=f"Member 2 Webhook confirmed invoice {payload.invoice_reference}",
                    metadata_json={
                        "idempotency_key": payload.idempotency_key,
                        "invoice_reference": payload.invoice_reference,
                    },
                )
        else:
            req.status = "FAILED"
            req.last_error = payload.error_message or "Member 2 invoice generation failed"
            req.retry_count += 1

        db.commit()
        db.refresh(req)

        sub = req.subscription
        return RenewalBillingRequestResponse(
            id=req.id,
            idempotency_key=req.idempotency_key,
            subscription_id=req.subscription_id,
            subscription_number=sub.subscription_number if sub else None,
            customer_id=req.customer_id,
            customer_name=sub.customer.full_name if (sub and sub.customer) else None,
            billing_period_start=req.billing_period_start,
            billing_period_end=req.billing_period_end,
            amount=req.amount,
            status=req.status,
            invoice_reference=req.invoice_reference,
            retry_count=req.retry_count,
            last_error=req.last_error,
            created_at=req.created_at,
        )
