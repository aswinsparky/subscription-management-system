"""
Quotation Management (Module 5) Integration Tests.
Verifies quotation creation, line pricing, expiration validation, and idempotent conversion to subscription.
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
from app.models.quotation import Quotation

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


def get_or_create_fixtures(db):
    """Ensure customer, product, and plan exist."""
    customer = db.query(Customer).first()
    if not customer:
        customer = Customer(
            customer_code=f"CUST-Q-{uuid.uuid4().hex[:4]}",
            full_name="Quotation Test Customer",
            email=f"qc_{uuid.uuid4().hex[:6]}@example.com",
            billing_address="123 Quote Road",
        )
        db.add(customer)
        db.flush()

    product = db.query(Product).first()
    if not product:
        product = Product(
            product_code=f"PROD-Q-{uuid.uuid4().hex[:4]}",
            name="Quotation Core Product",
            product_type="SOFTWARE",
            sales_price=Decimal("1500.00"),
            cost_price=Decimal("500.00"),
        )
        db.add(product)
        db.flush()

    plan = db.query(Plan).first()
    if not plan:
        plan = Plan(
            plan_code=f"PLAN-Q-{uuid.uuid4().hex[:4]}",
            name="Monthly Quote Plan",
            billing_interval="MONTHLY",
            plan_price=Decimal("1500.00"),
            minimum_quantity=1,
        )
        db.add(plan)
        db.flush()

    db.commit()
    return customer.id, product.id, plan.id


def test_create_quotation_and_line_calculation():
    """Verify quotation creation with calculated line items and subtotal."""
    token = get_admin_token()
    db = SessionLocal()
    try:
        cust_id, prod_id, plan_id = get_or_create_fixtures(db)
    finally:
        db.close()

    payload = {
        "customer_id": cust_id,
        "plan_id": plan_id,
        "items": [
            {"product_id": prod_id, "quantity": 2, "unit_price": "1500.00"}
        ],
    }

    res = client.post(
        "/api/v1/quotations/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["quotation_number"].startswith("QUOTE-")
    assert data["subtotal"] == "3000.00"  # 2 * 1500.00
    assert data["total"] == "3000.00"
    assert data["status"] == "DRAFT"
    assert len(data["items"]) == 1
    assert data["items"][0]["subtotal"] == "3000.00"


def test_convert_quotation_to_subscription_and_prevent_duplicate():
    """
    Critical Workflow:
    1. Create quotation
    2. Convert to subscription
    3. Verify subscription is created and quotation marked ACCEPTED
    4. Second conversion call MUST return 409 Conflict (Duplicate Prevention)
    """
    token = get_admin_token()
    db = SessionLocal()
    try:
        cust_id, prod_id, plan_id = get_or_create_fixtures(db)
    finally:
        db.close()

    # 1. Create quote
    q_res = client.post(
        "/api/v1/quotations/",
        json={
            "customer_id": cust_id,
            "plan_id": plan_id,
            "items": [{"product_id": prod_id, "quantity": 1, "unit_price": "2000.00"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    quote_id = q_res.json()["id"]

    # 2. Convert to subscription
    conv_res = client.post(
        f"/api/v1/quotations/{quote_id}/convert",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    assert "successfully converted" in conv_data["message"]
    assert conv_data["subscription_number"].startswith("SUB-")
    sub_id = conv_data["subscription_id"]

    # Verify quote state updated
    get_q = client.get(f"/api/v1/quotations/{quote_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_q.json()["status"] == "ACCEPTED"
    assert get_q.json()["converted_to_subscription_id"] == sub_id

    # 3. Duplicate Conversion Attempt -> MUST fail with 409 Conflict
    dup_res = client.post(
        f"/api/v1/quotations/{quote_id}/convert",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dup_res.status_code == 409
    assert "already been converted" in dup_res.json()["detail"].lower()


def test_expired_quotation_cannot_be_converted():
    """Verify that converting an expired quotation returns 400 Bad Request."""
    token = get_admin_token()
    db = SessionLocal()
    try:
        cust_id, prod_id, plan_id = get_or_create_fixtures(db)
        from app.models.user import User
        admin_user = db.query(User).filter(User.email == "admin@brightloop.io").first()

        # Insert quotation already expired
        now = datetime.now(timezone.utc)
        expired_quote = Quotation(
            quotation_number=f"QUOTE-EXP-{uuid.uuid4().hex[:6]}",
            customer_id=cust_id,
            plan_id=plan_id,
            expiration_date=now - timedelta(days=2),  # In the past
            subtotal=Decimal("1000.00"),
            total=Decimal("1000.00"),
            status="SENT",
            created_by_user_id=admin_user.id,
        )
        db.add(expired_quote)
        db.commit()
        exp_id = expired_quote.id
    finally:
        db.close()

    res = client.post(
        f"/api/v1/quotations/{exp_id}/convert",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()
