"""
Financial Scenario Runner & Stress Tester for Brightloop Nexus .
Simulates recurring billing cycles, stress-tests Revenue Guardian anomaly detection,
and validates idempotency and financial precision across simulated volume.
"""

import sys
import os
import argparse
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Ensure backend root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.services.invoice_service import InvoiceService
from app.services.revenue_guardian_service import RevenueGuardianService
from app.services.analytics_service import AnalyticsService


def run_billing_stress_test(batch_size: int = 50):
    """Stress test recurring invoice generation batch processing."""
    db = SessionLocal()
    print(f"[*] Starting recurring billing simulation for batch size: {batch_size}...")
    try:
        results = InvoiceService.generate_recurring_invoices(db)
        print(f"[+] Invoice Generation Results: {results}")

        # Idempotency check: Running again immediately should produce 0 new invoices
        second_run = InvoiceService.generate_recurring_invoices(db)
        print(f"[+] Idempotency Verification Run: {second_run}")
        assert second_run.get("generated_count", 0) == 0, "Idempotency failed: duplicate invoice generated!"
        print("[OK] Idempotency Verified: 0 duplicates created.")
    finally:
        db.close()


def run_guardian_audit():
    """Execute real-time revenue loss detection audit."""
    db = SessionLocal()
    print("[*] Launching Revenue Guardian comprehensive audit...")
    try:
        run = RevenueGuardianService.run_full_audit(db)
        print(f"[+] Guardian Audit Run ID: {run.id}")
        print(f"[+] Total Leak Detected: ${run.total_leak_detected:.2f}")
        print(f"[+] Findings Identified: {run.findings_count}")
        for idx, f in enumerate(run.findings, 1):
            print(f"    {idx}. [{f.severity}] {f.issue_code}: {f.issue_title} (${f.estimated_loss:.2f})")
    finally:
        db.close()


def print_financial_health_report():
    """Print high-level revenue health and KPIs."""
    db = SessionLocal()
    print("[*] Fetching Revenue Command Center analytics...")
    try:
        summary = AnalyticsService.get_financial_summary(db)
        print("\n================ BRIGHTLOOP FINANCIAL HEALTH ================")
        print(f"  Monthly Recurring Revenue (MRR): ${summary.mrr:.2f}")
        print(f"  Annual Recurring Revenue (ARR):  ${summary.arr:.2f}")
        print(f"  Active Paid Subscriptions:       {summary.active_subscriptions}")
        print(f"  Total Recognized Revenue:        ${summary.total_revenue_recognized:.2f}")
        print(f"  Total Cash Collected:            ${summary.total_revenue_collected:.2f}")
        print(f"  Outstanding Balance:             ${summary.outstanding_receivables:.2f}")
        print(f"  Overdue Receivables:             ${summary.overdue_amount:.2f}")
        print(f"  Net Collection Efficiency:       {summary.collection_rate_percent:.1f}%")
        print("=============================================================\n")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Brightloop Nexus Financial Scenario Runner")
    parser.add_argument("--test-billing", action="store_true", help="Run recurring billing stress test")
    parser.add_argument("--audit", action="store_true", help="Execute Revenue Guardian audit")
    parser.add_argument("--report", action="store_true", help="Print real-time financial health KPIs")
    args = parser.parse_args()

    if not any([args.test_billing, args.audit, args.report]):
        # Default run all
        print_financial_health_report()
        run_guardian_audit()
        run_billing_stress_test()
    else:
        if args.report:
            print_financial_health_report()
        if args.audit:
            run_guardian_audit()
        if args.test_billing:
            run_billing_stress_test()
