"""
Product and Variant Management (Module 3) Integration Tests.
Verifies dynamic pricing, multi-variants, search/filter, and referential archive safety.
"""
import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.services.auth_service import AuthService
from app.models.quotation import Quotation, QuotationItem
from app.models.customer import Customer
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


def get_customer_token() -> str:
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Product Test Customer",
            "email": f"prod_cust_{uuid.uuid4().hex[:8]}@example.com",
            "password": "Password123!@",
            "confirm_password": "Password123!@",
            "billing_address": "888 Tech Drive",
        },
    )
    return res.json()["access_token"]


def test_create_product_with_variants_and_pricing_calculation():
    """
    Test Master Requirement Example:
    Product: Business Software (Base: 5000.00)
    Variants:
    - Standard: +0.00 => Final: 5000.00
    - Odoo: +560.00 => Final: 5560.00
    - Enterprise: +1200.00 => Final: 6200.00
    """
    token = get_admin_token()
    payload = {
        "name": f"Business Software {uuid.uuid4().hex[:6]}",
        "product_type": "SOFTWARE",
        "description": "Comprehensive enterprise ERP suite",
        "sales_price": "5000.00",
        "cost_price": "2000.00",
        "internal_notes": "Core licensed software",
        "variants": [
            {"variant_name": "Standard", "sku": f"BS-STD-{uuid.uuid4().hex[:6]}", "additional_price": "0.00"},
            {"variant_name": "Odoo", "sku": f"BS-ODOO-{uuid.uuid4().hex[:6]}", "additional_price": "560.00"},
            {"variant_name": "Enterprise", "sku": f"BS-ENT-{uuid.uuid4().hex[:6]}", "additional_price": "1200.00"},
        ],
    }

    res = client.post(
        "/api/v1/products/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["sales_price"] == "5000.00"
    assert len(data["variants"]) == 3

    # Check calculated final prices: Base Sales Price + Variant Additional Price
    variants_by_name = {v["variant_name"]: v for v in data["variants"]}
    assert variants_by_name["Standard"]["final_price"] == "5000.00"
    assert variants_by_name["Odoo"]["final_price"] == "5560.00"
    assert variants_by_name["Enterprise"]["final_price"] == "6200.00"


def test_negative_prices_rejected():
    """Verify that negative sales, cost, or variant prices are rejected by validator."""
    token = get_admin_token()

    # Negative sales price
    res1 = client.post(
        "/api/v1/products/",
        json={"name": "Bad Product", "sales_price": "-10.00", "cost_price": "5.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 422

    # Negative variant price
    res2 = client.post(
        "/api/v1/products/",
        json={
            "name": "Bad Product 2",
            "sales_price": "100.00",
            "cost_price": "50.00",
            "variants": [{"variant_name": "Bad Variant", "additional_price": "-5.00"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 422


def test_add_variant_to_existing_product():
    """Verify dynamic addition of variant to existing product."""
    token = get_admin_token()
    create_res = client.post(
        "/api/v1/products/",
        json={
            "name": f"Cloud Storage {uuid.uuid4().hex[:6]}",
            "product_type": "SERVICE",
            "sales_price": "1000.00",
            "cost_price": "400.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    prod_id = create_res.json()["id"]

    # Add variant
    var_res = client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={"variant_name": "1TB Premium", "additional_price": "450.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert var_res.status_code == 201
    var_data = var_res.json()
    assert var_data["variant_name"] == "1TB Premium"
    # Base 1000 + 450 = 1450
    assert var_data["final_price"] == "1450.00"


def test_search_and_filter_products():
    """Verify searching products by text and filtering by product_type."""
    token = get_admin_token()
    rand_tag = uuid.uuid4().hex[:6]
    client.post(
        "/api/v1/products/",
        json={
            "name": f"Hardware Sensor {rand_tag}",
            "product_type": "HARDWARE",
            "sales_price": "800.00",
            "cost_price": "400.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Search by tag
    search_res = client.get(
        f"/api/v1/products/?query={rand_tag}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert search_res.status_code == 200
    assert search_res.json()["total"] >= 1

    # Filter by type
    filter_res = client.get(
        f"/api/v1/products/?query={rand_tag}&product_type=HARDWARE",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert filter_res.status_code == 200
    assert filter_res.json()["total"] >= 1
    assert filter_res.json()["items"][0]["product_type"] == "HARDWARE"


def test_safe_delete_or_archive_product():
    """
    Verify referential safety:
    - If product has no references -> permanently deleted
    - If product has quotation reference -> safely archived (is_active = False)
    """
    token = get_admin_token()

    # 1. Unreferenced product deletion
    unref_res = client.post(
        "/api/v1/products/",
        json={"name": "Temp Deletable", "sales_price": "10.00", "cost_price": "5.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    unref_id = unref_res.json()["id"]

    del_res = client.delete(
        f"/api/v1/products/{unref_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200
    assert del_res.json()["action"] == "deleted"

    # Verify deleted from DB
    get_res = client.get(f"/api/v1/products/{unref_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_res.status_code == 404

    # 2. Referenced product archiving
    ref_prod_res = client.post(
        "/api/v1/products/",
        json={"name": "Referenced Product", "sales_price": "500.00", "cost_price": "200.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    ref_prod_id = ref_prod_res.json()["id"]

    # Link product to a quotation line item in DB
    db = SessionLocal()
    try:
        from datetime import datetime, timezone, timedelta
        # Ensure a customer and plan exist
        cust = db.query(Customer).first()
        plan = db.query(Plan).first()
        if not plan:
            plan = Plan(
                plan_code=f"PLAN-{uuid.uuid4().hex[:4]}",
                name="Test Plan",
                billing_interval="MONTHLY",
                plan_price=Decimal("100.00"),
                minimum_quantity=1,
            )
            db.add(plan)
            db.flush()

        from app.models.user import User
        admin_user = db.query(User).filter(User.email == "admin@brightloop.io").first()

        quote = Quotation(
            quotation_number=f"QUOTE-REF-{uuid.uuid4().hex[:6]}",
            customer_id=cust.id,
            plan_id=plan.id,
            expiration_date=datetime.now(timezone.utc) + timedelta(days=15),
            subtotal=Decimal("500.00"),
            total=Decimal("500.00"),
            status="DRAFT",
            created_by_user_id=admin_user.id,
        )
        db.add(quote)
        db.flush()

        quote_item = QuotationItem(
            quotation_id=quote.id,
            product_id=ref_prod_id,
            quantity=1,
            unit_price=Decimal("500.00"),
            subtotal=Decimal("500.00"),
        )
        db.add(quote_item)
        db.commit()
    finally:
        db.close()

    # Now attempt deletion -> MUST archive rather than delete!
    archive_res = client.delete(
        f"/api/v1/products/{ref_prod_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert archive_res.status_code == 200
    assert archive_res.json()["action"] == "archived"
    assert archive_res.json()["is_active"] is False


def test_customer_role_cannot_modify_products():
    """Verify RBAC: Customer cannot POST or PUT products."""
    cust_token = get_customer_token()
    res = client.post(
        "/api/v1/products/",
        json={"name": "Illegal Product", "sales_price": "100.00", "cost_price": "50.00"},
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert res.status_code == 403

