"""
Subscription Lifecycle & State Machine (Module 6) Integration Tests.
Verifies creation, full state transitions (DRAFT -> CONFIRMED -> ACTIVE -> PAUSED -> CLOSED),
plan policy constraints (pause_allowed, early_cancellation_allowed), and event auditing.
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


def get_or_create_fixtures(db, pause_allowed=True, early_cancellation_allowed=True):
    suffix = uuid.uuid4().hex[:6]
    customer = db.query(Customer).first()
    if not customer:
        customer = Customer(
            customer_code=f"CUST-SUB-{suffix}",
            full_name=f"Sub Customer {suffix}",
            email=f"sub_{suffix}@brightloop.io",
            account_status="ACTIVE",
            billing_address="123 Nexus Way",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    product = Product(
        name=f"Sub SaaS Cloud {suffix}",
        product_code=f"SKU-SUB-{suffix}",
        product_type="SOFTWARE",
        sales_price=Decimal("499.00"),
        cost_price=Decimal("150.00"),
        is_active=True,
    )
    db.add(product)

    plan = Plan(
        name=f"Sub Enterprise Plan {suffix}",
        plan_code=f"PLAN-SUB-{suffix}",
        billing_interval="MONTHLY",
        plan_price=Decimal("499.00"),
        pause_allowed=pause_allowed,
        early_cancellation_allowed=early_cancellation_allowed,
        auto_close_enabled=True,
        status="ACTIVE",
    )
    db.add(plan)
    db.commit()
    db.refresh(product)
    db.refresh(plan)

    return customer.id, product.id, plan.id


def test_subscription_creation_and_events():
    """Verify subscription draft creation with line calculation and audit log."""
    token = get_admin_token()
    db = SessionLocal()
    try:
        cust_id, prod_id, plan_id = get_or_create_fixtures(db)
    finally:
        db.close()

    payload = {
        "customer_id": cust_id,
        "plan_id": plan_id,
        "billing_interval": "MONTHLY",
        "payment_terms": "Immediate",
        "auto_renew": True,
        "items": [{"product_id": prod_id, "quantity": 2}],
    }

    res = client.post(
        "/api/v1/subscriptions",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["subscription_number"].startswith("SUB-")
    assert data["status"] == "DRAFT"
    assert Decimal(str(data["total_amount"])) == Decimal("998.00")
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2

    # Verify event audit trail
    events_res = client.get(
        f"/api/v1/subscriptions/{data['id']}/events",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 1
    assert events[0]["event_type"] == "CREATED"


def test_subscription_lifecycle_full_flow():
    """Verify state transitions: DRAFT -> CONFIRMED -> ACTIVE -> PAUSED -> ACTIVE -> CLOSED."""
    token = get_admin_token()
    db = SessionLocal()
    try:
        cust_id, prod_id, plan_id = get_or_create_fixtures(db)
    finally:
        db.close()

    # 1. Create DRAFT
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
    conf_res = client.post(
        f"/api/v1/subscriptions/{sub_id}/confirm",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert conf_res.status_code == 200
    assert conf_res.json()["status"] == "CONFIRMED"

    # 3. Activate
    act_res = client.post(
        f"/api/v1/subscriptions/{sub_id}/activate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "ACTIVE"

    # 4. Pause
    pause_res = client.post(
        f"/api/v1/subscriptions/{sub_id}/pause",
        json={"reason": "Customer going on seasonal hiatus"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"

    # 5. Resume
    resume_res = client.post(
        f"/api/v1/subscriptions/{sub_id}/resume",
        json={"reason": "Returning from hiatus"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "ACTIVE"

    # 6. Close
    close_res = client.post(
        f"/api/v1/subscriptions/{sub_id}/close",
        json={"reason": "Contract complete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"

    # Verify all 6 events were captured in order
    events_res = client.get(
        f"/api/v1/subscriptions/{sub_id}/events",
        headers={"Authorization": f"Bearer {token}"},
    )
    event_types = [e["event_type"] for e in events_res.json()]
    assert event_types == ["CREATED", "CONFIRMED", "ACTIVATED", "PAUSED", "RESUMED", "CLOSED"]


def test_pause_rejected_if_plan_disallows():
    """Verify 400 Bad Request when attempting to pause if plan pause_allowed=False."""
    token = get_admin_token()
    db = SessionLocal()
    try:
        cust_id, prod_id, plan_id = get_or_create_fixtures(db, pause_allowed=False)
    finally:
        db.close()

    # Create & activate
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
    client.post(f"/api/v1/subscriptions/{sub_id}/confirm", headers={"Authorization": f"Bearer {token}"})
    client.post(f"/api/v1/subscriptions/{sub_id}/activate", headers={"Authorization": f"Bearer {token}"})

    # Attempt Pause
    pause_res = client.post(
        f"/api/v1/subscriptions/{sub_id}/pause",
        json={"reason": "Try pause"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pause_res.status_code == 400
    assert "prohibits pausing" in pause_res.json()["detail"].lower()


def test_early_cancellation_rejected_if_plan_disallows():
    """Verify 400 Bad Request when cancelling before expiry if plan early_cancellation_allowed=False."""
    token = get_admin_token()
    db = SessionLocal()
    try:
        cust_id, prod_id, plan_id = get_or_create_fixtures(db, early_cancellation_allowed=False)
    finally:
        db.close()

    # Create & activate
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
    client.post(f"/api/v1/subscriptions/{sub_id}/confirm", headers={"Authorization": f"Bearer {token}"})
    client.post(f"/api/v1/subscriptions/{sub_id}/activate", headers={"Authorization": f"Bearer {token}"})

    # Attempt Cancel
    cancel_res = client.post(
        f"/api/v1/subscriptions/{sub_id}/cancel",
        json={"reason": "Early cancellation attempt"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cancel_res.status_code == 400
    assert "prohibits early cancellation" in cancel_res.json()["detail"].lower()


def test_terminal_state_guard():
    """Verify that closed subscriptions cannot be modified or activated."""
    token = get_admin_token()
    db = SessionLocal()
    try:
        cust_id, prod_id, plan_id = get_or_create_fixtures(db)
    finally:
        db.close()

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
    client.post(f"/api/v1/subscriptions/{sub_id}/close", headers={"Authorization": f"Bearer {token}"})

    # Attempt to activate
    res = client.post(
        f"/api/v1/subscriptions/{sub_id}/activate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
