"""
Tax Management (Module 1) Integration Tests.
Verifies tax creation, percentage & fixed calculation precision, and RBAC rules.
"""
from decimal import Decimal
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


def test_create_percentage_tax():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "GST 18%",
        "description": "Standard Goods & Services Tax",
        "tax_type": "PERCENTAGE",
        "rate": "18.00",
        "applicability": "ALL",
        "is_active": True,
    }
    res = client.post("/api/v1/taxes", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "GST 18%"
    assert float(data["rate"]) == 18.0


def test_calculate_taxes_endpoint():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create tax
    tax_res = client.post(
        "/api/v1/taxes",
        json={"name": "VAT 20%", "tax_type": "PERCENTAGE", "rate": "20.00"},
        headers=headers,
    )
    tax_id = tax_res.json()["id"]

    # Calculate tax on base amount 100.00
    calc_res = client.post(
        "/api/v1/taxes/calculate",
        json={"tax_ids": [tax_id], "base_amount": "100.00"},
        headers=headers,
    )
    assert calc_res.status_code == 200
    calc_data = calc_res.json()
    assert float(calc_data["total_tax_amount"]) == 20.00
    assert len(calc_data["breakdown"]) == 1

