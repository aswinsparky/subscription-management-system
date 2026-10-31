"""
Churn Radar & Behavioral Risk Analytics Service (Module 8).
Deterministic heuristic risk scoring engine (0-100) assessing pauses, auto-renew cancellations,
overdue billings, and historical churn indicators.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Customer
from app.models.subscription import Subscription, SubscriptionEvent
from app.models.user import User
from app.schemas.churn import (
    CustomerRiskProfile,
    ChurnRiskSignal,
    ChurnDashboardMetrics,
    RetentionActionRequest,
    RetentionActionResponse,
)


class ChurnService:

    @classmethod
    def calculate_customer_risk(
        cls,
        customer: Customer,
        subscriptions: List[Subscription],
    ) -> CustomerRiskProfile:
        now = datetime.now(timezone.utc)
        score = 10  # Base natural risk
        signals: List[ChurnRiskSignal] = []

        active_subs = [s for s in subscriptions if s.status == "ACTIVE"]
        paused_subs = [s for s in subscriptions if s.status == "PAUSED"]
        cancelled_subs = [s for s in subscriptions if s.status == "CANCELLED"]

        total_mrr = sum((s.total_amount for s in active_subs), Decimal("0.00"))

        # Signal 1: Currently Paused
        if paused_subs:
            score += 30
            signals.append(
                ChurnRiskSignal(
                    signal_key="CURRENTLY_PAUSED",
                    signal_name="Subscription Currently Paused",
                    weight=30,
                    severity="CRITICAL",
                    description=f"{len(paused_subs)} subscription(s) currently paused by customer.",
                    recommended_action="Initiate personal outreach to address hiatus reason before cancellation occurs.",
                )
            )

        # Signal 2: Auto-Renew Disabled
        auto_renew_off = [s for s in (active_subs + paused_subs) if not s.auto_renew]
        if auto_renew_off:
            score += 25
            signals.append(
                ChurnRiskSignal(
                    signal_key="AUTO_RENEW_DISABLED",
                    signal_name="Auto-Renewal Turned Off",
                    weight=25,
                    severity="CRITICAL",
                    description=f"{len(auto_renew_off)} active contract(s) have auto-renewal disabled.",
                    recommended_action="Dispatch retention promotion with discount coupon to incentivize re-enabling auto-renew.",
                )
            )

        # Signal 3: Past Due / Overdue Next Billing Date
        overdue = [
            s for s in active_subs
            if (s.next_billing_date.replace(tzinfo=timezone.utc) if s.next_billing_date.tzinfo is None else s.next_billing_date) <= now
        ]
        if overdue:
            score += 20
            signals.append(
                ChurnRiskSignal(
                    signal_key="BILLING_OVERDUE",
                    signal_name="Renewal Past Due",
                    weight=20,
                    severity="WARNING",
                    description=f"{len(overdue)} subscription(s) have reached billing date without renewal.",
                    recommended_action="Review payment method validity and send urgent renewal alert.",
                )
            )

        # Signal 4: Historical Cancellations
        if cancelled_subs:
            score += 15
            signals.append(
                ChurnRiskSignal(
                    signal_key="HISTORICAL_CANCELLATIONS",
                    signal_name="History of Cancelled Contracts",
                    weight=15,
                    severity="WARNING",
                    description=f"Customer previously cancelled {len(cancelled_subs)} subscription(s).",
                    recommended_action="Conduct satisfaction survey and offer executive plan review.",
                )
            )

        # Signal 5: Zero Active Contracts or Low Engagement
        if len(active_subs) == 0 and len(paused_subs) == 0:
            score += 40
            signals.append(
                ChurnRiskSignal(
                    signal_key="ZERO_ACTIVE_SUBS",
                    signal_name="No Active Subscriptions",
                    weight=40,
                    severity="CRITICAL",
                    description="Customer has no currently active subscriptions.",
                    recommended_action="Engage in win-back campaign with special re-activation pricing.",
                )
            )
        elif len(active_subs) == 1 and total_mrr < Decimal("150.00"):
            score += 10
            signals.append(
                ChurnRiskSignal(
                    signal_key="LOW_TIER_ENGAGEMENT",
                    signal_name="Low Spend Single-Contract",
                    weight=10,
                    severity="INFO",
                    description="Customer holds only a single low-tier subscription contract.",
                    recommended_action="Present feature add-ons and cross-sell enterprise modules.",
                )
            )

        final_score = min(100, max(0, score))

        if final_score >= 70:
            tier = "HIGH"
            playbook = "Immediate High-Priority Retention Outreach with 20% Discount Playbook"
        elif final_score >= 40:
            tier = "MEDIUM"
            playbook = "Automated Re-engagement Campaign & Account Feature Review"
        else:
            tier = "LOW"
            playbook = "Standard Relationship Management & Proactive Upsell Sequence"

        return CustomerRiskProfile(
            customer_id=customer.id,
            customer_code=customer.customer_code,
            full_name=customer.full_name,
            email=customer.email,
            company_name=customer.company_name,
            risk_score=final_score,
            risk_tier=tier,
            active_subscriptions_count=len(active_subs),
            total_mrr=total_mrr,
            signals=signals,
            suggested_retention_playbook=playbook,
        )

    @classmethod
    def get_dashboard_metrics(cls, db: Session) -> ChurnDashboardMetrics:
        customers = (
            db.query(Customer)
            .options(
                joinedload(Customer.subscriptions).joinedload(Subscription.plan),
            )
            .all()
        )

        profiles: List[CustomerRiskProfile] = []
        high_count = 0
        med_count = 0
        low_count = 0
        total_score = 0
        at_risk_mrr = Decimal("0.00")

        for c in customers:
            profile = cls.calculate_customer_risk(c, c.subscriptions or [])
            profiles.append(profile)
            total_score += profile.risk_score

            if profile.risk_tier == "HIGH":
                high_count += 1
                at_risk_mrr += profile.total_mrr
            elif profile.risk_tier == "MEDIUM":
                med_count += 1
                at_risk_mrr += (profile.total_mrr * Decimal("0.5"))
            else:
                low_count += 1

        avg_score = round(total_score / len(profiles), 1) if profiles else 0.0

        # Sort top at-risk descending
        profiles.sort(key=lambda p: p.risk_score, reverse=True)

        return ChurnDashboardMetrics(
            total_customers_analyzed=len(profiles),
            avg_risk_score=avg_score,
            high_risk_count=high_count,
            medium_risk_count=med_count,
            low_risk_count=low_count,
            at_risk_mrr=at_risk_mrr,
            top_at_risk_customers=profiles[:20],
        )

    @classmethod
    def get_customer_profile(cls, db: Session, customer_id: int) -> CustomerRiskProfile:
        customer = (
            db.query(Customer)
            .options(
                joinedload(Customer.subscriptions).joinedload(Subscription.plan),
            )
            .filter(Customer.id == customer_id)
            .first()
        )
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        return cls.calculate_customer_risk(customer, customer.subscriptions or [])

    @classmethod
    def record_retention_action(
        cls,
        db: Session,
        customer_id: int,
        payload: RetentionActionRequest,
        actor: User,
    ) -> RetentionActionResponse:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        now = datetime.now(timezone.utc)
        # Log to customer active subscriptions if present
        for sub in customer.subscriptions:
            if sub.status in ("ACTIVE", "PAUSED"):
                from app.services.subscription_service import SubscriptionService
                SubscriptionService.record_event(
                    db=db,
                    subscription=sub,
                    event_type="RETENTION_ACTION",
                    actor=actor,
                    previous_state=None,
                    reason=f"Retention Action '{payload.action_type}': {payload.notes}",
                    metadata_json={
                        "action_type": payload.action_type,
                        "discount_offered": payload.discount_percent_offered,
                    },
                )
        db.commit()

        return RetentionActionResponse(
            customer_id=customer.id,
            action_type=payload.action_type,
            notes=payload.notes,
            recorded_at=now,
            recorded_by=actor.email,
            status="LOGGED_SUCCESSFULLY",
        )

