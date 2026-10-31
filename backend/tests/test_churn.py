"""
Churn Radar & Behavioral Risk Analytics (Module 8) Integration Tests.
Verifies heuristic churn risk scoring, signal identification, and proactive retention logging.
"""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.services.auth_service import AuthService
from app.models.customer import Customer
from app.models.plan import Plan
from app.models.subscription import Subscription

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_roles_and_admin():
    db = SessionLocal()
    try:
        AuthService.seed_initial_roles_and_admin(db)
    finally:
        db.close()


def get_admin_token() -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@brightloop.io", "password": "Admin@123456!"},
    )
    return res.json()["access_token"]


def create_churn_fixtures(db):
    suffix = uuid.uuid4().hex[:6]
    customer = Customer(
        customer_code=f"CUST-CHURN-{suffix}",
        full_name=f"Churn Risk Customer {suffix}",
        email=f"churn_{suffix}@brightloop.io",
        account_status="ACTIVE",
        billing_address="789 Churn Radar St",
    )
    db.add(customer)

    plan = Plan(
        name=f"Churn Plan {suffix}",
        plan_code=f"PLAN-CHURN-{suffix}",
        billing_interval="MONTHLY",
        plan_price=Decimal("250.00"),
        pause_allowed=True,
        early_cancellation_allowed=True,
        status="ACTIVE",
    )
    db.add(plan)
    db.commit()
    db.refresh(customer)
    db.refresh(plan)

    now = datetime.now(timezone.utc)
    # Create a PAUSED subscription with auto_renew=False to trigger multiple critical risk signals
    sub = Subscription(
        subscription_number=f"SUB-CHURN-{suffix}",
        customer_id=customer.id,
        plan_id=plan.id,
        start_date=now - timedelta(days=20),
        expiry_date=now + timedelta(days=10),
        billing_interval="MONTHLY",
        payment_terms="Immediate",
        subtotal=Decimal("250.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("250.00"),
        status="PAUSED",
        next_billing_date=now + timedelta(days=10),
        current_period_start=now - timedelta(days=20),
        current_period_end=now + timedelta(days=10),
        auto_renew=False,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return customer.id, sub.id


def test_churn_dashboard_aggregation():
    """Verify aggregated metrics endpoint returns customer counts and averages."""
    token = get_admin_token()
    res = client.get(
        "/api/v1/churn/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "total_customers_analyzed" in data
    assert "avg_risk_score" in data
    assert "high_risk_count" in data
    assert "top_at_risk_customers" in data
    assert isinstance(data["top_at_risk_customers"], list)


def test_customer_risk_profile_signals():
    """Verify heuristic signals: PAUSED and AUTO_RENEW_DISABLED elevate risk score."""
    token = get_admin_token()
    db = SessionLocal()
    try:
        cust_id, sub_id = create_churn_fixtures(db)
    finally:
        db.close()

    res = client.get(
        f"/api/v1/churn/customer/{cust_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    profile = res.json()
    assert profile["customer_id"] == cust_id
    assert profile["risk_score"] >= 60  # Paused (+30) + AutoRenewOff (+25) + Base (+10) = 65+
    assert profile["risk_tier"] in ("MEDIUM", "HIGH")
    
    signal_keys = [s["signal_key"] for s in profile["signals"]]
    assert "CURRENTLY_PAUSED" in signal_keys
    assert "AUTO_RENEW_DISABLED" in signal_keys


def test_retention_action_logging():
    """Verify logging a proactive retention intervention."""
    token = get_admin_token()
    db = SessionLocal()
    try:
        cust_id, sub_id = create_churn_fixtures(db)
    finally:
        db.close()

    payload = {
        "action_type": "DISCOUNT_OFFER",
        "notes": "Offered 20% discount if customer resumes subscription within 7 days",
        "discount_percent_offered": 20,
    }

    res = client.post(
        f"/api/v1/churn/customer/{cust_id}/retention-action",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "LOGGED_SUCCESSFULLY"
    assert data["action_type"] == "DISCOUNT_OFFER"
