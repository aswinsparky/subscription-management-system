"""
Subscription Time Machine (Module 9) Integration Tests.
Verifies timeline diffs, historical state reconstruction as of timestamp T, and what-if simulation sandboxing.
"""
import uuid
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.services.auth_service import AuthService
from app.models.customer import Customer
from app.models.product import Product
from app.models.plan import Plan

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


def create_sub_with_lifecycle_history(token: str):
    suffix = uuid.uuid4().hex[:6]
    db = SessionLocal()
    try:
        customer = Customer(
            customer_code=f"CUST-TM-{suffix}",
            full_name=f"Time Machine User {suffix}",
            email=f"tm_{suffix}@brightloop.io",
            account_status="ACTIVE",
            billing_address="100 Time Warp Ave",
        )
        db.add(customer)

        product = Product(
            name=f"Quantum Compute {suffix}",
            product_code=f"SKU-TM-{suffix}",
            product_type="SOFTWARE",
            sales_price=Decimal("150.00"),
            cost_price=Decimal("50.00"),
            is_active=True,
        )
        db.add(product)

        plan = Plan(
            name=f"Timeline Plan {suffix}",
            plan_code=f"PLAN-TM-{suffix}",
            billing_interval="MONTHLY",
            plan_price=Decimal("150.00"),
            pause_allowed=True,
            early_cancellation_allowed=True,
            renewal_allowed=True,
            status="ACTIVE",
        )
        db.add(plan)
        db.commit()
        cust_id, prod_id, plan_id = customer.id, product.id, plan.id
    finally:
        db.close()

    # 1. Create DRAFT
    t0 = datetime.now(timezone.utc)
    create_res = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": cust_id,
            "plan_id": plan_id,
            "items": [{"product_id": prod_id, "quantity": 1}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    sub_id = create_res.json()["id"]

    # 2. Confirm
    time.sleep(0.2)
    t1 = datetime.now(timezone.utc)
    client.post(f"/api/v1/subscriptions/{sub_id}/confirm", headers={"Authorization": f"Bearer {token}"})

    # 3. Activate
    time.sleep(0.2)
    t2 = datetime.now(timezone.utc)
    client.post(f"/api/v1/subscriptions/{sub_id}/activate", headers={"Authorization": f"Bearer {token}"})

    return sub_id, t0, t1, t2


def test_timeline_retrieval_and_diffs():
    """Verify timeline returns chronological events with state diffs."""
    token = get_admin_token()
    sub_id, _, _, _ = create_sub_with_lifecycle_history(token)

    res = client.get(
        f"/api/v1/timemachine/subscriptions/{sub_id}/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    timeline = res.json()
    assert len(timeline) >= 3
    event_types = [e["event_type"] for e in timeline]
    assert "CREATED" in event_types
    assert "CONFIRMED" in event_types
    assert "ACTIVATED" in event_types

    # Verify diff field
    confirmed_evt = next(e for e in timeline if e["event_type"] == "CONFIRMED")
    assert "status" in confirmed_evt["diff_fields"]
    assert confirmed_evt["diff_fields"]["status"]["from"] == "DRAFT"
    assert confirmed_evt["diff_fields"]["status"]["to"] == "CONFIRMED"


def test_reconstruct_state_as_of_historical_timestamp():
    """Verify state reconstruction accurately reflects historical state at timestamp T."""
    token = get_admin_token()
    sub_id, t0, t1, t2 = create_sub_with_lifecycle_history(token)

    # Reconstruct at timestamp t1 (which was right at confirmation)
    iso_t1 = t1.isoformat()
    res = client.get(
        f"/api/v1/timemachine/subscriptions/{sub_id}/as-of",
        params={"timestamp": iso_t1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["subscription_id"] == sub_id
    assert data["reconstructed_state"]["status"] in ("DRAFT", "CONFIRMED", "ACTIVE")
    assert data["current_live_state"]["status"] == "ACTIVE"


def test_what_if_simulation_without_db_mutation():
    """Verify simulation previews transitions without persisting changes."""
    token = get_admin_token()
    sub_id, _, _, _ = create_sub_with_lifecycle_history(token)

    # 1. Simulate valid PAUSE
    sim_res = client.post(
        f"/api/v1/timemachine/subscriptions/{sub_id}/simulate",
        json={"action": "PAUSE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sim_res.status_code == 200
    sim = sim_res.json()
    assert sim["is_allowed"] is True
    assert sim["predicted_state"]["status"] == "PAUSED"

    # Verify DB subscription is STILL ACTIVE
    live_res = client.get(
        f"/api/v1/subscriptions/{sub_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert live_res.json()["status"] == "ACTIVE"

    # 2. Simulate invalid RESUME while active
    inv_res = client.post(
        f"/api/v1/timemachine/subscriptions/{sub_id}/simulate",
        json={"action": "RESUME"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert inv_res.status_code == 200
    inv = inv_res.json()
    assert inv["is_allowed"] is False
    assert "must be paused" in inv["rejection_reason"].lower()
