"""
Customer Management (Module 2) Integration Tests.
Verifies CRUD, search, filter, pagination, history, and strict tenant ownership checks.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.services.auth_service import AuthService

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


def get_customer_token_and_id(email_prefix: str) -> tuple[str, int]:
    email = f"{email_prefix}_{uuid.uuid4().hex[:8]}@test.com"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Customer User",
            "email": email,
            "password": "Password123!@",
            "confirm_password": "Password123!@",
            "billing_address": "777 Market Street",
        },
    )
    token = res.json()["access_token"]
    user_id = res.json()["user"]["id"]
    return token, user_id


def test_admin_can_create_customer():
    """Verify that ADMIN/STAFF can provision a new customer."""
    token = get_admin_token()
    email = f"corp_{uuid.uuid4().hex[:8]}@enterprise.com"
    payload = {
        "full_name": "Acme Global Dynamics",
        "email": email,
        "phone": "+1-800-555-0199",
        "company_name": "Acme Corp",
        "billing_address": "100 Acme Way, Silicon Valley, CA",
        "tax_id": "US-EIN-9928172",
        "account_status": "ACTIVE",
    }
    res = client.post(
        "/api/v1/customers/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == email
    assert data["full_name"] == "Acme Global Dynamics"
    assert data["customer_code"].startswith("CUST-")
    assert data["account_status"] == "ACTIVE"


def test_customer_role_cannot_create_customer():
    """Verify RBAC: CUSTOMER role cannot call POST /api/v1/customers/."""
    cust_token, _ = get_customer_token_and_id("cust_unpriv")
    res = client.post(
        "/api/v1/customers/",
        json={
            "full_name": "Illegal Creation",
            "email": f"illegal_{uuid.uuid4().hex[:8]}@test.com",
            "billing_address": "Nowhere",
        },
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert res.status_code == 403


def test_search_and_filter_customers():
    """Verify customer search by keyword and filter by account_status."""
    token = get_admin_token()
    rand_tag = uuid.uuid4().hex[:6]
    # Create 2 customers
    c1_email = f"search_{rand_tag}_alpha@searchtest.com"
    client.post(
        "/api/v1/customers/",
        json={
            "full_name": f"SearchAlpha {rand_tag}",
            "email": c1_email,
            "company_name": f"AlphaCorp {rand_tag}",
            "billing_address": "Alpha Street",
            "account_status": "ACTIVE",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    c2_email = f"search_{rand_tag}_beta@searchtest.com"
    client.post(
        "/api/v1/customers/",
        json={
            "full_name": f"SearchBeta {rand_tag}",
            "email": c2_email,
            "company_name": f"BetaCorp {rand_tag}",
            "billing_address": "Beta Street",
            "account_status": "SUSPENDED",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # 1. Search by unique tag
    search_res = client.get(
        f"/api/v1/customers/?query={rand_tag}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] >= 2

    # 2. Filter by status SUSPENDED
    filter_res = client.get(
        f"/api/v1/customers/?query={rand_tag}&account_status=SUSPENDED",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert filter_res.status_code == 200
    filter_data = filter_res.json()
    assert filter_data["total"] == 1
    assert filter_data["items"][0]["email"] == c2_email
    assert filter_data["items"][0]["account_status"] == "SUSPENDED"


def test_customer_ownership_security_checks():
    """
    CRITICAL SECURITY TEST:
    Verify that Customer A cannot view or modify Customer B's records.
    """
    cust_a_token, cust_a_id = get_customer_token_and_id("tenant_a")
    cust_b_token, cust_b_id = get_customer_token_and_id("tenant_b")

    # Fetch Customer A's own profile
    a_profile = client.get("/api/v1/customers/me", headers={"Authorization": f"Bearer {cust_a_token}"})
    assert a_profile.status_code == 200
    a_cust_id = a_profile.json()["id"]

    # Fetch Customer B's own profile
    b_profile = client.get("/api/v1/customers/me", headers={"Authorization": f"Bearer {cust_b_token}"})
    assert b_profile.status_code == 200
    b_cust_id = b_profile.json()["id"]

    # Customer A attempts to view Customer B's details -> MUST return 403 Forbidden!
    forbidden_view = client.get(
        f"/api/v1/customers/{b_cust_id}",
        headers={"Authorization": f"Bearer {cust_a_token}"},
    )
    assert forbidden_view.status_code == 403
    assert "access denied" in forbidden_view.json()["detail"].lower()

    # Customer A attempts to modify Customer B's details -> MUST return 403 Forbidden!
    forbidden_edit = client.put(
        f"/api/v1/customers/{b_cust_id}",
        json={"company_name": "Hacked Company"},
        headers={"Authorization": f"Bearer {cust_a_token}"},
    )
    assert forbidden_edit.status_code == 403


def test_update_customer_and_view_history():
    """Verify editing customer profile and retrieving subscription/quotation history."""
    token = get_admin_token()
    email = f"update_{uuid.uuid4().hex[:8]}@test.com"
    create_res = client.post(
        "/api/v1/customers/",
        json={
            "full_name": "Original Name",
            "email": email,
            "billing_address": "Original Address",
            "account_status": "ACTIVE",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    cust_id = create_res.json()["id"]

    # Update
    update_res = client.put(
        f"/api/v1/customers/{cust_id}",
        json={
            "full_name": "Updated Name Ltd",
            "company_name": "New Brand Inc",
            "account_status": "SUSPENDED",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["full_name"] == "Updated Name Ltd"
    assert updated_data["company_name"] == "New Brand Inc"
    assert updated_data["account_status"] == "SUSPENDED"

    # History
    history_res = client.get(
        f"/api/v1/customers/{cust_id}/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert history_res.status_code == 200
    hist = history_res.json()
    assert hist["customer"]["id"] == cust_id
    assert isinstance(hist["subscriptions"], list)
    assert isinstance(hist["quotations"], list)
