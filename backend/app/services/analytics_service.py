"""
Revenue Command Center and Financial Analytics Service for Brightloop Nexus (Member 2).
Aggregates live database metrics for MRR, ARR, cash collection, and churn payment signals.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.revenue_guardian import RevenueGuardianFinding


class AnalyticsService:
    @staticmethod
    def get_command_center_summary(db: Session) -> Dict[str, Any]:
        """Aggregate high-level financial KPIs directly from live database tables."""
        now = datetime.utcnow()

        # 1. Total Invoiced & Balances
        inv_totals = db.execute(
            select(
                func.coalesce(func.sum(Invoice.total_amount), 0),
                func.coalesce(func.sum(Invoice.amount_paid), 0),
                func.coalesce(func.sum(Invoice.amount_due), 0),
            ).where(Invoice.status != "CANCELLED")
        ).fetchone()

        total_invoiced = Decimal(str(inv_totals[0] or 0)).quantize(Decimal("0.01"))
        total_collected = Decimal(str(inv_totals[1] or 0)).quantize(Decimal("0.01"))
        total_outstanding = Decimal(str(inv_totals[2] or 0)).quantize(Decimal("0.01"))

        # 2. Overdue Amount
        overdue_amt = db.scalar(
            select(func.coalesce(func.sum(Invoice.amount_due), 0)).where(
                Invoice.status.in_(["OVERDUE", "CONFIRMED", "PARTIALLY_PAID"]),
                Invoice.due_date < now,
                Invoice.amount_due > 0,
            )
        ) or 0
        total_overdue = Decimal(str(overdue_amt)).quantize(Decimal("0.01"))

        # 3. Monthly Recurring Revenue (MRR) normalized from Active Subscriptions
        active_subs = db.scalars(select(Subscription).where(Subscription.status == "ACTIVE")).all()
        mrr = Decimal("0.00")
        for sub in active_subs:
            total_amt = sub.total_amount
            interval = (sub.billing_interval or "MONTHLY").upper()
            if interval == "MONTHLY":
                mrr += total_amt
            elif interval == "YEARLY":
                mrr += (total_amt / Decimal("12.00"))
            elif interval == "WEEKLY":
                mrr += (total_amt * Decimal("4.333"))
            elif interval == "DAILY":
                mrr += (total_amt * Decimal("30.00"))

        mrr = mrr.quantize(Decimal("0.01"))
        arr = (mrr * Decimal("12.00")).quantize(Decimal("0.01"))

        # 4. Payment Stats
        total_success_payments = db.scalar(
            select(func.count(Payment.id)).where(Payment.payment_status == "SUCCESSFUL")
        ) or 0
        total_failed_payments = db.scalar(
            select(func.count(Payment.id)).where(Payment.payment_status == "FAILED")
        ) or 0
        total_payment_attempts = total_success_payments + total_failed_payments
        success_rate = (
            (Decimal(str(total_success_payments)) / Decimal(str(total_payment_attempts)) * Decimal("100.00")).quantize(Decimal("0.1"))
            if total_payment_attempts > 0 else Decimal("100.0")
        )

        # 5. Subscription Counts
        active_subs_count = len(active_subs)
        cancelled_subs_count = db.scalar(
            select(func.count(Subscription.id)).where(Subscription.status == "CANCELLED")
        ) or 0

        # 6. Open Revenue Leakage Findings
        open_leakage = db.scalar(
            select(func.coalesce(func.sum(RevenueGuardianFinding.estimated_loss), 0)).where(
                RevenueGuardianFinding.resolution_status == "OPEN"
            )
        ) or 0

        return {
            "total_revenue": total_invoiced,
            "mrr": mrr,
            "arr": arr,
            "total_collected": total_collected,
            "total_outstanding": total_outstanding,
            "total_overdue": total_overdue,
            "active_subscriptions": active_subs_count,
            "cancelled_subscriptions": cancelled_subs_count,
            "payment_success_rate": success_rate,
            "revenue_leakage_at_risk": Decimal(str(open_leakage)).quantize(Decimal("0.01")),
        }

    @staticmethod
    def get_monthly_trends(db: Session, months_count: int = 6) -> List[Dict[str, Any]]:
        """Calculate monthly invoiced vs collected revenue trend for Recharts."""
        now = datetime.utcnow()
        trends: List[Dict[str, Any]] = []

        for i in range(months_count - 1, -1, -1):
            target_date = now - timedelta(days=i * 30)
            month_label = target_date.strftime("%b %Y")
            start_of_month = datetime(target_date.year, target_date.month, 1)
            if target_date.month == 12:
                end_of_month = datetime(target_date.year + 1, 1, 1)
            else:
                end_of_month = datetime(target_date.year, target_date.month + 1, 1)

            invoiced = db.scalar(
                select(func.coalesce(func.sum(Invoice.total_amount), 0)).where(
                    Invoice.invoice_date >= start_of_month,
                    Invoice.invoice_date < end_of_month,
                    Invoice.status != "CANCELLED",
                )
            ) or 0

            collected = db.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(
                    Payment.payment_date >= start_of_month,
                    Payment.payment_date < end_of_month,
                    Payment.payment_status == "SUCCESSFUL",
                )
            ) or 0

            trends.append({
                "month": month_label,
                "invoiced": float(invoiced),
                "collected": float(collected),
            })

        return trends

    @staticmethod
    def get_invoice_status_distribution(db: Session) -> List[Dict[str, Any]]:
        """Returns distribution of invoices by status."""
        rows = db.execute(
            select(Invoice.status, func.count(Invoice.id), func.coalesce(func.sum(Invoice.total_amount), 0))
            .group_by(Invoice.status)
        ).all()
        return [
            {"status": row[0], "count": row[1], "total": float(row[2])}
            for row in rows
        ]

    @staticmethod
    def get_payment_method_distribution(db: Session) -> List[Dict[str, Any]]:
        """Returns distribution of successful payments by payment method."""
        rows = db.execute(
            select(Payment.payment_method, func.count(Payment.id), func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.payment_status == "SUCCESSFUL")
            .group_by(Payment.payment_method)
        ).all()
        return [
            {"method": row[0], "count": row[1], "total": float(row[2])}
            for row in rows
        ]

    @staticmethod
    def get_customer_churn_signals(db: Session, customer_id: int) -> Dict[str, Any]:
        """
        Integration Contract with Member 1 Churn Radar:
        Provides financial health signals for a customer.
        """
        now = datetime.utcnow()
        unpaid_invoices = db.scalars(
            select(Invoice).where(
                Invoice.customer_id == customer_id,
                Invoice.status.in_(["OVERDUE", "CONFIRMED", "PARTIALLY_PAID"]),
                Invoice.amount_due > 0,
            )
        ).all()

        days_overdue_max = 0
        for inv in unpaid_invoices:
            if inv.due_date < now:
                overdue_days = (now - inv.due_date).days
                if overdue_days > days_overdue_max:
                    days_overdue_max = overdue_days

        failed_payments_count = db.scalar(
            select(func.count(Payment.id)).where(
                Payment.customer_id == customer_id,
                Payment.payment_status == "FAILED",
            )
        ) or 0

        return {
            "customer_id": customer_id,
            "unpaid_invoices_count": len(unpaid_invoices),
            "total_outstanding_balance": sum((inv.amount_due for inv in unpaid_invoices), Decimal("0.00")),
            "days_overdue_max": days_overdue_max,
            "failed_payments_count": failed_payments_count,
            "financial_risk_level": "HIGH" if (days_overdue_max > 30 or failed_payments_count >= 2) else ("MEDIUM" if days_overdue_max > 0 else "LOW"),
        }

