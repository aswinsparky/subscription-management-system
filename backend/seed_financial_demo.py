"""
Demonstration Seed Script for Brightloop Nexus (Member 2: Financial Intelligence Engine).
Seeds taxes, discounts, invoices, payments, reconciliations, and guardian findings.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from app.core.database import SessionLocal, engine, Base
from app.models.user import Role, User
from app.models.customer import Customer
from app.models.product import Product
from app.models.plan import Plan
from app.models.subscription import Subscription, SubscriptionItem
from app.models.tax import Tax
from app.models.discount import Discount
from app.models.invoice import Invoice, InvoiceItem, InvoiceTaxDetail, InvoiceDiscountDetail
from app.models.payment import Payment
from app.models.reconciliation import PaymentReconciliation
from app.models.revenue_guardian import RevenueGuardianFinding, RevenueGuardianRun
from app.models.recovery import BillingRecoveryAttempt
from app.models.simulator import RevenueSimulationScenario
from app.services.auth_service import AuthService


def seed_demo_data():
    print("Initializing demo seed data...")
    from app.core import database
    from app.core.config import settings
    from sqlalchemy import create_engine, text

    active_engine = database.engine
    active_session_maker = database.SessionLocal

    try:
        with active_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
    except Exception as e:
        print(f"Notice: MySQL not reachable ({e}). Falling back to local development database (brightloop_nexus.db)...")
        sqlite_uri = "sqlite:///./brightloop_nexus.db"
        settings.DATABASE_URL = sqlite_uri
        active_engine = create_engine(sqlite_uri, connect_args={"check_same_thread": False})
        active_session_maker = database.sessionmaker(bind=active_engine, autocommit=False, autoflush=False)
        database.engine = active_engine
        database.SessionLocal = active_session_maker

    Base.metadata.create_all(bind=active_engine)
    db = active_session_maker()

    try:
        # 1. Seed Roles & Admin
        AuthService.seed_initial_roles_and_admin(db)
        admin = db.scalar(select(User).where(User.email == "admin@brightloop.io"))

        # 2. Seed Taxes
        taxes = [
            Tax(name="GST 18%", description="Goods & Services Tax", tax_type="PERCENTAGE", rate=Decimal("18.00"), applicability="ALL", is_active=True),
            Tax(name="VAT 20%", description="Value Added Tax", tax_type="PERCENTAGE", rate=Decimal("20.00"), applicability="ALL", is_active=True),
            Tax(name="State Tech Surcharge", description="Local cloud service fee", tax_type="FIXED", rate=Decimal("15.00"), applicability="ALL", is_active=True),
        ]
        for t in taxes:
            existing = db.scalar(select(Tax).where(Tax.name == t.name))
            if not existing:
                db.add(t)
        db.flush()

        # 3. Seed Discounts
        discounts = [
            Discount(name="Launch Promotion 20%", coupon_code="LAUNCH20", discount_type="PERCENTAGE", discount_value=Decimal("20.00"), min_purchase_amount=Decimal("50.00"), max_usage_limit=500, is_active=True),
            Discount(name="Annual Flat $50 Off", coupon_code="ANNUAL50", discount_type="FIXED", discount_value=Decimal("50.00"), min_purchase_amount=Decimal("200.00"), max_usage_limit=100, is_active=True),
            Discount(name="Startup Tier Boost", coupon_code="STARTUP10", discount_type="PERCENTAGE", discount_value=Decimal("10.00"), min_purchase_amount=Decimal("0.00"), is_active=True),
        ]
        for d in discounts:
            existing = db.scalar(select(Discount).where(Discount.coupon_code == d.coupon_code))
            if not existing:
                db.add(d)
        db.flush()

        # 4. Seed Sample Customers
        customers = [
            Customer(customer_code="CUST-0001", full_name="Apex Media Global", email="finance@apexmedia.io", phone="+1-555-0101", company_name="Apex Media Inc.", billing_address="100 Madison Ave, New York, NY", tax_id="US-EIN-99212"),
            Customer(customer_code="CUST-0002", full_name="HyperScale AI Labs", email="billing@hyperscale.ai", phone="+1-555-0102", company_name="HyperScale AI Corp", billing_address="450 Townsend St, San Francisco, CA", tax_id="US-EIN-44123"),
            Customer(customer_code="CUST-0003", full_name="Nordic SaaS Technologies", email="accounts@nordicsaas.se", phone="+46-8-123456", company_name="Nordic SaaS AB", billing_address="Kungsgatan 12, Stockholm, Sweden", tax_id="SE-VAT-556677"),
        ]
        for c in customers:
            existing = db.scalar(select(Customer).where(Customer.email == c.email))
            if not existing:
                db.add(c)
        db.flush()

        # 5. Seed Sample Product & Plan
        prod = db.scalar(select(Product).where(Product.product_code == "PROD-CLOUD-PRO"))
        if not prod:
            prod = Product(
                product_code="PROD-CLOUD-PRO",
                name="Cloud Platform Pro",
                product_type="SOFTWARE",
                sales_price=Decimal("199.00"),
                cost_price=Decimal("45.00"),
                is_active=True,
            )
            db.add(prod)
            db.flush()

        plan = db.scalar(select(Plan).where(Plan.plan_code == "PLAN-ENTERPRISE-MONTHLY"))
        if not plan:
            plan = Plan(
                plan_code="PLAN-ENTERPRISE-MONTHLY",
                name="Enterprise Monthly Plan",
                billing_interval="MONTHLY",
                plan_price=Decimal("499.00"),
                minimum_quantity=1,
                status="ACTIVE",
                auto_close_enabled=False,
                early_cancellation_allowed=True,
                pause_allowed=True,
                renewal_allowed=True,
            )
            db.add(plan)
            db.flush()

        # 6. Seed Subscriptions
        cust1 = db.scalar(select(Customer).where(Customer.customer_code == "CUST-0001"))
        cust2 = db.scalar(select(Customer).where(Customer.customer_code == "CUST-0002"))
        cust3 = db.scalar(select(Customer).where(Customer.customer_code == "CUST-0003"))

        now = datetime.now(timezone.utc)
        sub1 = db.scalar(select(Subscription).where(Subscription.subscription_number == "SUB-2026-0001"))
        if not sub1 and cust1 and plan:
            sub1 = Subscription(
                subscription_number="SUB-2026-0001",
                customer_id=cust1.id,
                plan_id=plan.id,
                start_date=now - timedelta(days=60),
                expiry_date=now + timedelta(days=305),
                billing_interval="MONTHLY",
                payment_terms="Net 15",
                subtotal=Decimal("499.00"),
                total_amount=Decimal("499.00"),
                status="ACTIVE",
                next_billing_date=now + timedelta(days=5),
                current_period_start=now - timedelta(days=25),
                current_period_end=now + timedelta(days=5),
                auto_renew=True,
            )
            db.add(sub1)
            db.flush()
            db.add(SubscriptionItem(subscription_id=sub1.id, product_id=prod.id, quantity=1, unit_price=Decimal("499.00"), subtotal=Decimal("499.00")))

        sub2 = db.scalar(select(Subscription).where(Subscription.subscription_number == "SUB-2026-0002"))
        if not sub2 and cust2 and plan:
            sub2 = Subscription(
                subscription_number="SUB-2026-0002",
                customer_id=cust2.id,
                plan_id=plan.id,
                start_date=now - timedelta(days=90),
                expiry_date=now + timedelta(days=275),
                billing_interval="MONTHLY",
                payment_terms="Immediate",
                subtotal=Decimal("998.00"),
                total_amount=Decimal("998.00"),
                status="ACTIVE",
                next_billing_date=now - timedelta(days=2),  # Past billing date (Leakage test)
                current_period_start=now - timedelta(days=32),
                current_period_end=now - timedelta(days=2),
                auto_renew=True,
            )
            db.add(sub2)
            db.flush()
            db.add(SubscriptionItem(subscription_id=sub2.id, product_id=prod.id, quantity=2, unit_price=Decimal("499.00"), subtotal=Decimal("998.00")))

        db.flush()

        # 7. Seed Invoices in Diverse Statuses
        inv1 = db.scalar(select(Invoice).where(Invoice.invoice_number == "INV-2026-00001"))
        if not inv1 and cust1:
            inv1 = Invoice(
                invoice_number="INV-2026-00001",
                customer_id=cust1.id,
                subscription_id=sub1.id if sub1 else None,
                created_by_user_id=admin.id if admin else None,
                invoice_date=now - timedelta(days=40),
                due_date=now - timedelta(days=25),
                status="PAID",
                subtotal=Decimal("499.00"),
                discount_amount=Decimal("50.00"),
                tax_amount=Decimal("80.82"),
                total_amount=Decimal("529.82"),
                amount_paid=Decimal("529.82"),
                amount_due=Decimal("0.00"),
                payment_terms="Net 15",
                notes="Initial onboarding invoice",
            )
            db.add(inv1)
            db.flush()
            db.add(InvoiceItem(invoice_id=inv1.id, product_id=prod.id, item_description="Enterprise Monthly Plan", quantity=1, unit_price=Decimal("499.00"), subtotal=Decimal("499.00"), tax_rate_snapshot=Decimal("18.00"), tax_amount_snapshot=Decimal("80.82"), total_amount=Decimal("579.82")))
            
            # Seed Payment for inv1
            p1 = Payment(
                payment_reference="PAY-2026-00001",
                invoice_id=inv1.id,
                customer_id=cust1.id,
                recorded_by_user_id=admin.id if admin else None,
                amount=Decimal("529.82"),
                payment_date=now - timedelta(days=26),
                payment_method="BANK_TRANSFER",
                payment_status="SUCCESSFUL",
                transaction_id="TXN-WIRE-998811",
                notes="Wire transfer received and verified",
            )
            db.add(p1)
            db.flush()
            db.add(PaymentReconciliation(payment_id=p1.id, invoice_id=inv1.id, reconciled_by_user_id=admin.id if admin else None, status="MATCHED", invoice_total=Decimal("529.82"), payment_amount=Decimal("529.82"), discrepancy_amount=Decimal("0.00"), notes="Bank statement matched."))

        # Overdue Invoice for cust3
        inv2 = db.scalar(select(Invoice).where(Invoice.invoice_number == "INV-2026-00002"))
        if not inv2 and cust3:
            inv2 = Invoice(
                invoice_number="INV-2026-00002",
                customer_id=cust3.id,
                created_by_user_id=admin.id if admin else None,
                invoice_date=now - timedelta(days=25),
                due_date=now - timedelta(days=10),
                status="OVERDUE",
                subtotal=Decimal("799.00"),
                discount_amount=Decimal("0.00"),
                tax_amount=Decimal("159.80"),
                total_amount=Decimal("958.80"),
                amount_paid=Decimal("300.00"),
                amount_due=Decimal("658.80"),
                payment_terms="Immediate",
                notes="Consulting & Custom Engineering Services",
            )
            db.add(inv2)
            db.flush()
            db.add(InvoiceItem(invoice_id=inv2.id, item_description="Custom API Architecture Consulting", quantity=1, unit_price=Decimal("799.00"), subtotal=Decimal("799.00"), tax_rate_snapshot=Decimal("20.00"), tax_amount_snapshot=Decimal("159.80"), total_amount=Decimal("958.80")))
            p2 = Payment(
                payment_reference="PAY-2026-00002",
                invoice_id=inv2.id,
                customer_id=cust3.id,
                recorded_by_user_id=admin.id if admin else None,
                amount=Decimal("300.00"),
                payment_date=now - timedelta(days=12),
                payment_method="CARD",
                payment_status="SUCCESSFUL",
                transaction_id="TXN-STRIPE-44219",
                notes="Deposit paid by corporate Visa",
            )
            db.add(p2)
            db.flush()
            db.add(PaymentReconciliation(payment_id=p2.id, invoice_id=inv2.id, status="PARTIALLY_MATCHED", invoice_total=Decimal("958.80"), payment_amount=Decimal("300.00"), discrepancy_amount=Decimal("658.80"), notes="Partial deposit reconciled; remaining balance overdue."))

        # 8. Seed Revenue Guardian Findings
        f1 = db.scalar(select(RevenueGuardianFinding).where(RevenueGuardianFinding.issue_code == "RG-SEED-OVERDUE-01"))
        if not f1 and inv2:
            db.add(RevenueGuardianFinding(
                issue_code="RG-SEED-OVERDUE-01",
                issue_title="Invoice #INV-2026-00002 has Past Due Balance ($658.80)",
                category="OVERDUE_BALANCE",
                severity="HIGH",
                customer_id=cust3.id,
                invoice_id=inv2.id,
                estimated_loss=Decimal("658.80"),
                explanation="Due date expired 10 days ago. Outstanding balance of $658.80 remains uncollected.",
                recommended_action="Dispatch automated SMS and Email dunning sequence.",
                resolution_status="OPEN",
            ))

        db.commit()
        print("Demo seed data successfully populated!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
