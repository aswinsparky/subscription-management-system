"""
Authentication and Role-Based Access Control (RBAC) Integration Tests.
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
    """Ensure database has initial roles and admin before running tests."""
    db = SessionLocal()
    try:
        AuthService.seed_initial_roles_and_admin(db)
    finally:
        db.close()


def test_admin_login_success():
    """Verify that default administrator can authenticate and obtain an ADMIN JWT token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@brightloop.io", "password": "Admin@123456!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@brightloop.io"
    assert data["user"]["role"] == "ADMIN"


def test_customer_registration_success():
    """Verify that customer registration creates account, linked customer profile, and returns token."""
    unique_email = f"customer_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Jane Doe Enterprises",
        "email": unique_email,
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "phone": "+1-555-0199",
        "company_name": "Doe Cloud Solutions",
        "billing_address": "456 Innovation Way, Tech Park",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["role"] == "CUSTOMER"


def test_customer_registration_duplicate_email_fails():
    """Verify that registering with an existing email returns 409 Conflict."""
    payload = {
        "name": "Duplicate Tester",
        "email": "admin@brightloop.io",
        "password": "ValidPassword123!",
        "confirm_password": "ValidPassword123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_customer_registration_weak_password_fails():
    """Verify password complexity rules (>8 chars, uppercase, lowercase, special char)."""
    # Too short
    res1 = client.post(
        "/api/v1/auth/register",
        json={"name": "Weak", "email": "w1@test.com", "password": "Short1!", "confirm_password": "Short1!"},
    )
    assert res1.status_code == 422

    # No special character
    res2 = client.post(
        "/api/v1/auth/register",
        json={"name": "Weak", "email": "w2@test.com", "password": "NoSpecialChar123", "confirm_password": "NoSpecialChar123"},
    )
    assert res2.status_code == 422

    # No uppercase
    res3 = client.post(
        "/api/v1/auth/register",
        json={"name": "Weak", "email": "w3@test.com", "password": "nouppercase123!", "confirm_password": "nouppercase123!"},
    )
    assert res3.status_code == 422


def test_admin_can_create_staff():
    """Verify that an ADMIN can create a STAFF account."""
    # 1. Login as Admin
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@brightloop.io", "password": "Admin@123456!"},
    )
    admin_token = admin_login.json()["access_token"]

    # 2. Create staff
    staff_email = f"staff_{uuid.uuid4().hex[:8]}@brightloop.io"
    staff_payload = {
        "full_name": "Operations Specialist",
        "email": staff_email,
        "password": "StaffPassword123!",
    }
    res = client.post(
        "/api/v1/auth/create-staff",
        json=staff_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["role"] == "STAFF"
    assert data["email"] == staff_email


def test_non_admin_cannot_create_staff():
    """Verify RBAC: non-admin (Customer) gets 403 Forbidden when trying to create staff."""
    # 1. Register customer
    cust_email = f"regular_{uuid.uuid4().hex[:8]}@example.com"
    cust_res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Regular User",
            "email": cust_email,
            "password": "RegularUserPass123!",
            "confirm_password": "RegularUserPass123!",
        },
    )
    cust_token = cust_res.json()["access_token"]

    # 2. Try creating staff
    res = client.post(
        "/api/v1/auth/create-staff",
        json={
            "full_name": "Unauthorized Staff",
            "email": f"unauth_{uuid.uuid4().hex[:8]}@brightloop.io",
            "password": "StaffPassword123!",
        },
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert res.status_code == 403
    assert "operation not permitted" in res.json()["detail"].lower()


def test_password_reset_flow():
    """Verify end-to-end single-use password reset flow."""
    email = f"reset_{uuid.uuid4().hex[:8]}@example.com"
    # 1. Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Reset Test User",
            "email": email,
            "password": "InitialPassword123!",
            "confirm_password": "InitialPassword123!",
        },
    )

    # 2. Request reset token
    req_res = client.post("/api/v1/auth/password-reset/request", json={"email": email})
    assert req_res.status_code == 200
    token = req_res.json()["reset_token"]
    assert token is not None

    # 3. Confirm password reset with new password
    confirm_res = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": token,
            "new_password": "NewUpdatedPassword123!",
            "confirm_password": "NewUpdatedPassword123!",
        },
    )
    assert confirm_res.status_code == 200

    # 4. Old password should fail
    old_login = client.post("/api/v1/auth/login", json={"email": email, "password": "InitialPassword123!"})
    assert old_login.status_code == 401

    # 5. New password should succeed
    new_login = client.post("/api/v1/auth/login", json={"email": email, "password": "NewUpdatedPassword123!"})
    assert new_login.status_code == 200
    assert new_login.json()["user"]["email"] == email

    # 6. Reusing consumed token must fail
    reuse_res = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": token,
            "new_password": "AnotherPassword123!",
            "confirm_password": "AnotherPassword123!",
        },
    )
    assert reuse_res.status_code == 400
