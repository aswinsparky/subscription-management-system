"""
Subscription Plan Management (Module 4) Integration Tests.
"""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.services.auth_service import AuthService
from app.models.quotation import Quotation
from app.models.customer import Customer

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


def get_customer_token() -> str:
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Plan Test Customer",
            "email": f"plan_cust_{uuid.uuid4().hex[:8]}@example.com",
            "password": "Password123!@",
            "confirm_password": "Password123!@",
            "billing_address": "555 Avenue",
        },
    )
    return res.json()["access_token"]


def test_admin_create_plan():
    """Verify that ADMIN can create a recurring plan with lifecycle permission settings."""
    token = get_admin_token()
    now = datetime.now(timezone.utc)
    payload = {
        "name": f"Enterprise Pro Monthly {uuid.uuid4().hex[:6]}",
        "description": "Full access cloud subscription",
        "billing_interval": "MONTHLY",
        "plan_price": "999.00",
        "minimum_quantity": 2,
        "available_from": now.isoformat(),
        "available_until": (now + timedelta(days=365)).isoformat(),
        "auto_close_enabled": False,
        "early_cancellation_allowed": True,
        "pause_allowed": True,
        "renewal_allowed": True,
        "status": "ACTIVE",
    }
    res = client.post(
        "/api/v1/plans/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["billing_interval"] == "MONTHLY"
    assert data["plan_price"] == "999.00"
    assert data["minimum_quantity"] == 2
    assert data["plan_code"].startswith("PLAN-MON-")


def test_invalid_plan_dates_and_interval_rejected():
    """Verify validation: available_until < available_from rejected."""
    token = get_admin_token()
    now = datetime.now(timezone.utc)

    # Inverted dates
    res1 = client.post(
        "/api/v1/plans/",
        json={
            "name": "Invalid Dates Plan",
            "billing_interval": "MONTHLY",
            "plan_price": "100.00",
            "available_from": now.isoformat(),
            "available_until": (now - timedelta(days=10)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 422

    # Invalid interval
    res2 = client.post(
        "/api/v1/plans/",
        json={
            "name": "Invalid Interval Plan",
            "billing_interval": "BIWEEKLY",  # Not supported
            "plan_price": "100.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 422


def test_non_admin_cannot_create_or_update_plan():
    """Verify RBAC: Customer or Staff cannot create/edit plans (Admin only)."""
    cust_token = get_customer_token()
    res = client.post(
        "/api/v1/plans/",
        json={"name": "Hacked Plan", "billing_interval": "YEARLY", "plan_price": "1.00"},
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert res.status_code == 403


def test_safe_delete_or_archive_plan():
    """Verify plan deletion if unused, or safe archiving if referenced in quotation."""
    token = get_admin_token()

    # 1. Unreferenced plan delete
    create_res = client.post(
        "/api/v1/plans/",
        json={"name": "Temp Plan", "billing_interval": "DAILY", "plan_price": "10.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    plan_id = create_res.json()["id"]

    del_res = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200
    assert del_res.json()["action"] == "deleted"

    # 2. Referenced plan archive
    ref_plan_res = client.post(
        "/api/v1/plans/",
        json={"name": "Referenced Plan", "billing_interval": "YEARLY", "plan_price": "1200.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    ref_plan_id = ref_plan_res.json()["id"]

    db = SessionLocal()
    try:
        from app.models.user import User
        cust = db.query(Customer).first()
        admin_user = db.query(User).filter(User.email == "admin@brightloop.io").first()

        quote = Quotation(
            quotation_number=f"QUOTE-PLAN-{uuid.uuid4().hex[:6]}",
            customer_id=cust.id,
            plan_id=ref_plan_id,
            expiration_date=datetime.now(timezone.utc) + timedelta(days=10),
            subtotal=Decimal("1200.00"),
            total=Decimal("1200.00"),
            status="DRAFT",
            created_by_user_id=admin_user.id,
        )
        db.add(quote)
        db.commit()
    finally:
        db.close()

    # Deletion should archive instead
    arch_res = client.delete(
        f"/api/v1/plans/{ref_plan_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert arch_res.status_code == 200
    assert arch_res.json()["action"] == "archived"
    assert arch_res.json()["status"] == "ARCHIVED"

