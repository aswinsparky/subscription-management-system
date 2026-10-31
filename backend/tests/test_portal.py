"""
Customer Self-Service Portal (Module 10) Integration Tests.
Verifies multi-tenant isolation, customer profile self-management, quote acceptance, and lifecycle actions.
"""
import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.services.auth_service import AuthService
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


def register_customer_user(email_prefix="cust_portal"):
    suffix = uuid.uuid4().hex[:6]
    email = f"{email_prefix}_{suffix}@brightloop.io"
    password = "Customer@123456!"
    client.post(
        "/api/v1/auth/register",
        json={
            "name": f"Portal Client {suffix}",
            "email": email,
            "password": password,
            "confirm_password": password,
            "billing_address": "123 Portal Blvd",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return login_res.json()["access_token"], email


def get_admin_token() -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@brightloop.io", "password": "Admin@123456!"},
    )
    return res.json()["access_token"]


def test_customer_portal_profile_and_overview():
    """Verify customer can view portal dashboard and update profile information."""
    cust_token, email = register_customer_user("portal_prof")

    # 1. Fetch Overview
    res = client.get(
        "/api/v1/portal/overview",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "profile" in data
    assert data["profile"]["email"] == email

    # 2. Update Profile
    update_res = client.put(
        "/api/v1/portal/profile",
        json={
            "phone": "+1-555-0199",
            "billing_address": "42 Galactic Way, Suite 500",
            "company_name": "Portal Tech LLC",
        },
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["phone"] == "+1-555-0199"
    assert updated["company_name"] == "Portal Tech LLC"
    assert "42 Galactic Way" in updated["billing_address"]


def test_customer_portal_quote_acceptance_and_pause():
    """Verify customer accepts quote and manages subscription lifecycle."""
    cust_token, email = register_customer_user("portal_sub")
    admin_token = get_admin_token()

    # Get customer id
    prof_res = client.get(
        "/api/v1/portal/profile",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    cust_id = prof_res.json()["id"]

    # Admin creates product, plan, and quotation for this customer
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:6]
        product = Product(
            name=f"Portal Tool {suffix}",
            product_code=f"SKU-PORT-{suffix}",
            product_type="SOFTWARE",
            sales_price=Decimal("120.00"),
            cost_price=Decimal("30.00"),
            is_active=True,
        )
        plan = Plan(
            name=f"Portal Plan {suffix}",
            plan_code=f"PLAN-PORT-{suffix}",
            billing_interval="MONTHLY",
            plan_price=Decimal("120.00"),
            pause_allowed=True,
            early_cancellation_allowed=True,
            renewal_allowed=True,
            status="ACTIVE",
        )
        db.add(product)
        db.add(plan)
        db.commit()
        prod_id, plan_id = product.id, plan.id
    finally:
        db.close()

    quote_res = client.post(
        "/api/v1/quotations/",
        json={
            "customer_id": cust_id,
            "plan_id": plan_id,
            "billing_interval": "MONTHLY",
            "items": [{"product_id": prod_id, "quantity": 1, "unit_price": "120.00"}],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    quote_id = quote_res.json()["id"]

    # Customer accepts quote from Portal
    accept_res = client.post(
        f"/api/v1/portal/quotations/{quote_id}/accept",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert accept_res.status_code == 200
    conv_data = accept_res.json()
    sub_id = conv_data["subscription_id"]

    # Admin activates subscription so customer can pause it
    client.post(
        f"/api/v1/subscriptions/{sub_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Customer pauses subscription from Portal
    pause_res = client.post(
        f"/api/v1/portal/subscriptions/{sub_id}/pause",
        json={"reason": "Customer vacation pause"},
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"

    # Customer resumes subscription from Portal
    resume_res = client.post(
        f"/api/v1/portal/subscriptions/{sub_id}/resume",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "ACTIVE"


def test_multi_tenant_isolation_guard():
    """Verify Customer A cannot pause or cancel Customer B's subscription."""
    token_a, _ = register_customer_user("tenant_a")
    token_b, _ = register_customer_user("tenant_b")
    admin_token = get_admin_token()

    prof_a = client.get("/api/v1/portal/profile", headers={"Authorization": f"Bearer {token_a}"}).json()
    cust_a_id = prof_a["id"]

    db = SessionLocal()
    try:
        p = db.query(Product).first()
        pl = db.query(Plan).first()
        prod_id, plan_id = p.id, pl.id
    finally:
        db.close()

    # Create sub for Customer A
    sub_a_res = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": cust_a_id,
            "plan_id": plan_id,
            "items": [{"product_id": prod_id, "quantity": 1}],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    sub_a_id = sub_a_res.json()["id"]

    # Customer B attempts to pause Customer A's subscription
    res = client.post(
        f"/api/v1/portal/subscriptions/{sub_a_id}/pause",
        json={"reason": "Malicious pause attempt"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code in (403, 404)
    assert "not found in your account" in res.json()["detail"].lower()
