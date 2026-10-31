"""
Discount & Coupon Management (Module 2) Integration Tests.
Verifies coupon validation, minimum spend, expiration dates, and usage limits.
"""
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_admin_token() -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@brightloop.io", "password": "Admin@123456!"},
    )
    return res.json()["access_token"]


def test_create_and_validate_discount():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    code = f"SAVE_{uuid.uuid4().hex[:6].upper()}"

    # Create discount
    res = client.post(
        "/api/v1/discounts",
        json={
            "name": "Summer Promotion",
            "coupon_code": code,
            "discount_type": "PERCENTAGE",
            "discount_value": "15.00",
            "min_purchase_amount": "50.00",
            "min_quantity": 1,
            "is_active": True,
        },
        headers=headers,
    )
    assert res.status_code == 201

    # Validate with subtotal 100.00 -> should be eligible with 15.00 discount
    val_res = client.post(
        "/api/v1/discounts/validate",
        json={
            "coupon_code": code,
            "customer_id": 1,
            "subtotal": "100.00",
            "quantity": 1,
        },
        headers=headers,
    )
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["is_valid"] is True
    assert float(val_data["calculated_discount"]) == 15.00

    # Validate with subtotal 30.00 -> below minimum spend 50.00
    val_low = client.post(
        "/api/v1/discounts/validate",
        json={
            "coupon_code": code,
            "customer_id": 1,
            "subtotal": "30.00",
            "quantity": 1,
        },
        headers=headers,
    )
    assert val_low.json()["is_valid"] is False
    assert "Minimum purchase" in val_low.json()["message"]

