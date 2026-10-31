"""
Revenue Guardian Intelligence Engine for Brightloop Nexus (Member 2).
Performs deterministic anomaly detection to discover revenue leakage, billing gaps, and overdue risks.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, status
from app.models.revenue_guardian import RevenueGuardianFinding, RevenueGuardianRun
from app.models.invoice import Invoice
from app.models.subscription import Subscription
from app.models.payment import Payment
from app.models.user import User
from app.schemas.revenue_guardian import RevenueGuardianRunSummary, RevenueGuardianResolveRequest


class RevenueGuardianService:
    @staticmethod
    def get_findings(
        db: Session,
        status_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
    ) -> List[RevenueGuardianFinding]:
        stmt = select(RevenueGuardianFinding)
        if status_filter:
            stmt = stmt.where(RevenueGuardianFinding.resolution_status == status_filter.upper())
        if severity_filter:
            stmt = stmt.where(RevenueGuardianFinding.severity == severity_filter.upper())
        stmt = stmt.order_by(
            RevenueGuardianFinding.detected_at.desc(),
            RevenueGuardianFinding.id.desc(),
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def run_audit(db: Session, run_type: str = "MANUAL", user_id: Optional[int] = None) -> RevenueGuardianRunSummary:
        """
        Executes deterministic revenue leakage checks across subscriptions, invoices, and payments.
        """
        now = datetime.utcnow()
        new_findings: List[RevenueGuardianFinding] = []

        # 1. Overdue Invoices check
        overdue_invoices = db.scalars(
            select(Invoice).where(
                Invoice.due_date < now,
                Invoice.amount_due > Decimal("0.00"),
                Invoice.status.in_(["CONFIRMED", "PARTIALLY_PAID"]),
            )
        ).all()

        for inv in overdue_invoices:
            # Auto-mark status as OVERDUE
            inv.status = "OVERDUE"
            code = f"RG-OVERDUE-INV-{inv.id}"
            existing = db.scalar(select(RevenueGuardianFinding).where(RevenueGuardianFinding.issue_code == code))
            if not existing:
                finding = RevenueGuardianFinding(
                    issue_code=code,
                    issue_title=f"Invoice #{inv.invoice_number} is Overdue",
                    category="OVERDUE_BALANCE",
                    severity="HIGH",
                    customer_id=inv.customer_id,
                    subscription_id=inv.subscription_id,
                    invoice_id=inv.id,
                    estimated_loss=inv.amount_due,
                    explanation=f"Invoice due date was {inv.due_date.strftime('%Y-%m-%d')}. Outstanding balance: ${inv.amount_due:.2f}.",
                    recommended_action="Send automated overdue dunning notice or initiate payment recovery.",
                    resolution_status="OPEN",
                )
                db.add(finding)
                new_findings.append(finding)

        # 2. Missing Invoices check (Active subscriptions past billing date with no current invoice)
        active_subs = db.scalars(
            select(Subscription).where(
                Subscription.status == "ACTIVE",
                Subscription.next_billing_date < now,
            )
        ).all()

        for sub in active_subs:
            # Check if invoice exists for this period
            has_invoice = db.scalar(
                select(Invoice.id).where(
                    Invoice.subscription_id == sub.id,
                    Invoice.invoice_date >= sub.next_billing_date,
                    Invoice.status != "CANCELLED",
                )
            )
            if not has_invoice:
                code = f"RG-MISSING-SUB-{sub.id}-{sub.next_billing_date.strftime('%Y%m%d')}"
                existing = db.scalar(select(RevenueGuardianFinding).where(RevenueGuardianFinding.issue_code == code))
                if not existing:
                    finding = RevenueGuardianFinding(
                        issue_code=code,
                        issue_title=f"Missing Invoice for Active Subscription {sub.subscription_number}",
                        category="MISSING_INVOICE",
                        severity="CRITICAL",
                        customer_id=sub.customer_id,
                        subscription_id=sub.id,
                        estimated_loss=sub.total_amount,
                        explanation=f"Subscription {sub.subscription_number} was due for billing on {sub.next_billing_date.strftime('%Y-%m-%d')}, but no invoice has been generated.",
                        recommended_action="Trigger automatic invoice generation service for this subscription.",
                        resolution_status="OPEN",
                    )
                    db.add(finding)
                    new_findings.append(finding)

        # 3. Calculation Discrepancies check
        all_active_invoices = db.scalars(
            select(Invoice).where(Invoice.status.notin_(["CANCELLED", "DRAFT"]))
        ).all()

        for inv in all_active_invoices:
            expected_total = max(Decimal("0.00"), inv.subtotal - inv.discount_amount + inv.tax_amount)
            if abs(inv.total_amount - expected_total) > Decimal("0.02"):
                code = f"RG-MATH-INV-{inv.id}"
                existing = db.scalar(select(RevenueGuardianFinding).where(RevenueGuardianFinding.issue_code == code))
                if not existing:
                    diff = abs(inv.total_amount - expected_total)
                    finding = RevenueGuardianFinding(
                        issue_code=code,
                        issue_title=f"Calculation Discrepancy on Invoice #{inv.invoice_number}",
                        category="INCORRECT_TOTAL",
                        severity="MEDIUM",
                        customer_id=inv.customer_id,
                        invoice_id=inv.id,
                        estimated_loss=diff,
                        explanation=f"Stored total ${inv.total_amount:.2f} differs from Subtotal (${inv.subtotal:.2f}) - Discount (${inv.discount_amount:.2f}) + Tax (${inv.tax_amount:.2f}) = ${expected_total:.2f}.",
                        recommended_action="Recalculate invoice totals and review tax/discount lines.",
                        resolution_status="OPEN",
                    )
                    db.add(finding)
                    new_findings.append(finding)

        # 4. Failed Payments check without subsequent resolution
        failed_payments = db.scalars(
            select(Payment).where(Payment.payment_status == "FAILED")
        ).all()

        for pay in failed_payments:
            # Check if invoice is still unpaid
            if pay.invoice and pay.invoice.status != "PAID":
                code = f"RG-FAILED-PAY-{pay.id}"
                existing = db.scalar(select(RevenueGuardianFinding).where(RevenueGuardianFinding.issue_code == code))
                if not existing:
                    finding = RevenueGuardianFinding(
                        issue_code=code,
                        issue_title=f"Failed Payment {pay.payment_reference} on Invoice #{pay.invoice.invoice_number}",
                        category="FAILED_PAYMENT",
                        severity="HIGH",
                        customer_id=pay.customer_id,
                        invoice_id=pay.invoice_id,
                        payment_id=pay.id,
                        estimated_loss=pay.amount,
                        explanation=f"Payment attempt for ${pay.amount:.2f} failed on {pay.payment_date.strftime('%Y-%m-%d')}. Invoice remains unsettled.",
                        recommended_action="Initiate self-healing retry or request updated customer payment method.",
                        resolution_status="OPEN",
                    )
                    db.add(finding)
                    new_findings.append(finding)

        # 5. Log Run Record
        db.flush()
        all_open_findings = list(db.scalars(select(RevenueGuardianFinding).where(RevenueGuardianFinding.resolution_status == "OPEN")).all())

        critical_count = sum(1 for f in all_open_findings if f.severity == "CRITICAL")
        high_count = sum(1 for f in all_open_findings if f.severity == "HIGH")
        medium_count = sum(1 for f in all_open_findings if f.severity == "MEDIUM")
        low_count = sum(1 for f in all_open_findings if f.severity == "LOW")
        total_leakage = sum((f.estimated_loss for f in all_open_findings), Decimal("0.00"))

        run_log = RevenueGuardianRun(
            run_type=run_type,
            triggered_by_user_id=user_id,
            issues_found_count=len(all_open_findings),
            critical_count=critical_count,
            high_count=high_count,
            estimated_leakage_total=total_leakage,
            started_at=now,
            completed_at=datetime.utcnow(),
        )
        db.add(run_log)
        db.commit()

        return RevenueGuardianRunSummary(
            total_findings=len(all_open_findings),
            critical_findings=critical_count,
            high_findings=high_count,
            medium_findings=medium_count,
            low_findings=low_count,
            total_estimated_leakage=total_leakage,
            findings=all_open_findings,
        )

    @staticmethod
    def resolve_finding(
        db: Session,
        finding_id: int,
        data: RevenueGuardianResolveRequest,
        current_user: User,
    ) -> RevenueGuardianFinding:
        finding = db.scalar(select(RevenueGuardianFinding).where(RevenueGuardianFinding.id == finding_id))
        if not finding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Finding with ID {finding_id} not found.",
            )

        finding.resolution_status = data.resolution_status.upper()
        finding.resolved_at = datetime.utcnow()
        finding.resolved_by_user_id = current_user.id
        finding.resolution_notes = data.resolution_notes.strip()

        db.commit()
        db.refresh(finding)
        return finding

