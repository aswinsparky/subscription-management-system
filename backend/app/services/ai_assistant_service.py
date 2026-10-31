"""
Ask Brightloop AI Assistant Service for Brightloop Nexus (Member 2).
Strictly grounds answers in validated database aggregator functions.
Supports Google Gemini API with seamless deterministic fallback.
"""
import json
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from app.core.config import settings
from app.models.invoice import Invoice
from app.models.customer import Customer
from app.models.discount import Discount
from app.models.subscription import Subscription
from app.models.revenue_guardian import RevenueGuardianFinding
from app.services.analytics_service import AnalyticsService
from app.schemas.ai_assistant import AIAssistantQueryResponse

logger = logging.getLogger(__name__)


class AIAssistantService:
    @staticmethod
    def gather_grounded_context(db: Session) -> Dict[str, Any]:
        """Collect factual, validated database metrics to ground the AI response."""
        summary = AnalyticsService.get_command_center_summary(db)

        # Top 3 customers with highest outstanding balance
        top_debtors_rows = db.execute(
            select(Customer.full_name, Customer.company_name, func.sum(Invoice.amount_due))
            .join(Invoice, Invoice.customer_id == Customer.id)
            .where(Invoice.status.in_(["OVERDUE", "CONFIRMED", "PARTIALLY_PAID"]), Invoice.amount_due > 0)
            .group_by(Customer.id, Customer.full_name, Customer.company_name)
            .order_by(desc(func.sum(Invoice.amount_due)))
            .limit(3)
        ).all()
        top_debtors = [
            {"name": row[0], "company": row[1] or "N/A", "outstanding_due": float(row[2])}
            for row in top_debtors_rows
        ]

        # Top active discounts
        discounts_rows = db.scalars(select(Discount).order_by(Discount.current_usage_count.desc()).limit(3)).all()
        top_discounts = [
            {"code": d.coupon_code, "type": d.discount_type, "value": float(d.discount_value), "usages": d.current_usage_count}
            for d in discounts_rows
        ]

        # Overdue invoice count
        overdue_count = db.scalar(
            select(func.count(Invoice.id)).where(Invoice.status == "OVERDUE")
        ) or 0

        # Critical leakage count
        critical_leakage = db.scalar(
            select(func.count(RevenueGuardianFinding.id)).where(
                RevenueGuardianFinding.resolution_status == "OPEN",
                RevenueGuardianFinding.severity == "CRITICAL",
            )
        ) or 0

        return {
            "total_revenue": float(summary["total_revenue"]),
            "mrr": float(summary["mrr"]),
            "arr": float(summary["arr"]),
            "total_collected": float(summary["total_collected"]),
            "total_outstanding": float(summary["total_outstanding"]),
            "total_overdue": float(summary["total_overdue"]),
            "overdue_invoice_count": overdue_count,
            "active_subscriptions": summary["active_subscriptions"],
            "cancelled_subscriptions": summary["cancelled_subscriptions"],
            "payment_success_rate": float(summary["payment_success_rate"]),
            "revenue_leakage_at_risk": float(summary["revenue_leakage_at_risk"]),
            "critical_leakage_findings_count": critical_leakage,
            "top_debtors": top_debtors,
            "top_discounts": top_discounts,
        }

    @staticmethod
    def answer_query(db: Session, query: str) -> AIAssistantQueryResponse:
        """Process user question using Gemini API if configured, or deterministic fallback engine."""
        grounded_data = AIAssistantService.gather_grounded_context(db)
        q_lower = query.strip().lower()

        # Follow-up suggestion pills
        followups = [
            "How much revenue is currently overdue?",
            "What is our Monthly Recurring Revenue (MRR)?",
            "Which customers have the highest outstanding balance?",
            "What is our payment success rate?",
            "Are there any critical revenue leakage risks?",
        ]

        # 1. Try Gemini API if API key is present
        if settings.GEMINI_API_KEY:
            try:
                import httpx
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                prompt = (
                    f"You are the Brightloop Nexus AI Financial Analyst. Answer the user question accurately "
                    f"using strictly the following validated database context. Do not invent numbers. "
                    f"Explain clearly in professional business language:\n\n"
                    f"DATABASE CONTEXT:\n{json.dumps(grounded_data, indent=2)}\n\n"
                    f"USER QUESTION: {query}"
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(gemini_url, json=payload)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        answer_text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                        return AIAssistantQueryResponse(
                            query=query,
                            answer=answer_text,
                            grounded_data=grounded_data,
                            provider="gemini",
                            suggested_followups=followups,
                        )
            except Exception as e:
                logger.warning(f"Gemini API request failed ({e}); falling back to deterministic engine.")

        # 2. Deterministic Grounded Fallback Engine
        if "overdue" in q_lower or "due" in q_lower or "unpaid" in q_lower:
            answer = (
                f"We currently have **${grounded_data['total_overdue']:,.2f}** in overdue invoice balances across "
                f"**{grounded_data['overdue_invoice_count']}** overdue invoice(s). Total outstanding accounts receivable "
                f"is **${grounded_data['total_outstanding']:,.2f}**."
            )
        elif "mrr" in q_lower or "monthly recurring" in q_lower:
            answer = (
                f"Our current **Monthly Recurring Revenue (MRR)** is **${grounded_data['mrr']:,.2f}**, which represents "
                f"an **Annual Recurring Revenue (ARR)** run-rate of **${grounded_data['arr']:,.2f}** across "
                f"**{grounded_data['active_subscriptions']}** active subscriptions."
            )
        elif "debtor" in q_lower or "highest balance" in q_lower or "who owes" in q_lower:
            if grounded_data["top_debtors"]:
                debtors_str = ", ".join(
                    [f"**{d['name']}** ({d['company']}) with **${d['outstanding_due']:,.2f}**" for d in grounded_data["top_debtors"]]
                )
                answer = f"The top customers with outstanding balances are: {debtors_str}."
            else:
                answer = "There are currently no customers with outstanding overdue balances."
        elif "leakage" in q_lower or "guardian" in q_lower or "risk" in q_lower:
            answer = (
                f"Revenue Guardian has detected **${grounded_data['revenue_leakage_at_risk']:,.2f}** in potential revenue leakage "
                f"with **{grounded_data['critical_leakage_findings_count']}** critical finding(s). Please review the Revenue Guardian panel."
            )
        elif "payment" in q_lower or "success" in q_lower or "collected" in q_lower:
            answer = (
                f"Total collected payments stand at **${grounded_data['total_collected']:,.2f}** with a payment collection "
                f"success rate of **{grounded_data['payment_success_rate']}%**."
            )
        elif "discount" in q_lower or "coupon" in q_lower:
            if grounded_data["top_discounts"]:
                disc_str = ", ".join([f"**{d['code']}** ({d['usages']} redemptions)" for d in grounded_data["top_discounts"]])
                answer = f"Our most redeemed discount codes are: {disc_str}."
            else:
                answer = "No coupon redemptions recorded yet."
        elif "cancel" in q_lower or "churn" in q_lower:
            answer = (
                f"We currently have **{grounded_data['cancelled_subscriptions']}** cancelled subscription(s) compared to "
                f"**{grounded_data['active_subscriptions']}** active subscriptions."
            )
        else:
            answer = (
                f"**Brightloop Nexus Snapshot:**\n"
                f"- **Total Revenue**: ${grounded_data['total_revenue']:,.2f}\n"
                f"- **MRR / ARR**: ${grounded_data['mrr']:,.2f} / ${grounded_data['arr']:,.2f}\n"
                f"- **Collected**: ${grounded_data['total_collected']:,.2f} | **Outstanding**: ${grounded_data['total_outstanding']:,.2f}\n"
                f"- **Overdue**: ${grounded_data['total_overdue']:,.2f} ({grounded_data['overdue_invoice_count']} invoices)\n"
                f"- **Active Subscriptions**: {grounded_data['active_subscriptions']}\n"
                f"- **Payment Success Rate**: {grounded_data['payment_success_rate']}%\n"
                f"- **Revenue Leakage at Risk**: ${grounded_data['revenue_leakage_at_risk']:,.2f}"
            )

        return AIAssistantQueryResponse(
            query=query,
            answer=answer,
            grounded_data=grounded_data,
            provider="deterministic_engine",
            suggested_followups=followups,
        )

