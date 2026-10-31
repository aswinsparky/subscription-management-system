"""
Payment Processing & Reconciliation (Modules 5 & 6) Integration Tests.
Verifies balance adjustments, partial payments, overpayment rejection, and discrepancy tracking.
"""
import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_admin_token() -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@brightloop.io", "password": "Admin@123456!"},
    )
    return res.json()["access_token"]


def create_confirmed_invoice(token: str, amount: str = "200.00") -> int:
    headers = {"Authorization": f"Bearer {token}"}
    cust_res = client.post(
        "/api/v1/customers",
        json={
            "full_name": "Starlight Ventures",
            "email": f"star_{uuid.uuid4().hex[:6]}@example.com",
            "company_name": "Starlight Ltd",
            "billing_address": "888 Galaxy Blvd",
        },
        headers=headers,
    )
    cust_id = cust_res.json()["id"]

    inv_res = client.post(
        "/api/v1/invoices",
        json={
            "customer_id": cust_id,
            "payment_terms": "Immediate",
            "items": [
                {
                    "item_description": "Enterprise Subscription",
                    "quantity": 1,
                    "unit_price": amount,
                    "tax_rate_snapshot": "0.00",
                }
            ],
        },
        headers=headers,
    )
    inv_id = inv_res.json()["id"]
    client.post(f"/api/v1/invoices/{inv_id}/confirm", headers=headers)
    return inv_id


def test_partial_payment_and_full_payment_flow():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    inv_id = create_confirmed_invoice(token, "200.00")

    # 1. Record partial payment of 50.00
    p1 = client.post(
        "/api/v1/payments",
        json={"invoice_id": inv_id, "amount": "50.00", "payment_method": "BANK_TRANSFER"},
        headers=headers,
    )
    assert p1.status_code == 201
    assert p1.json()["payment_status"] == "SUCCESSFUL"

    # Verify invoice status is PARTIALLY_PAID and balance is 150.00
    inv = client.get(f"/api/v1/invoices/{inv_id}", headers=headers).json()
    assert inv["status"] == "PARTIALLY_PAID"
    assert float(inv["amount_paid"]) == 50.00
    assert float(inv["amount_due"]) == 150.00

    # 2. Overpayment attempt (200.00 when only 150.00 is due) should fail
    p_over = client.post(
        "/api/v1/payments",
        json={"invoice_id": inv_id, "amount": "200.00", "payment_method": "CARD"},
        headers=headers,
    )
    assert p_over.status_code == 400
    assert "exceeds outstanding" in p_over.json()["detail"]

    # 3. Pay remaining 150.00
    p2 = client.post(
        "/api/v1/payments",
        json={"invoice_id": inv_id, "amount": "150.00", "payment_method": "CARD"},
        headers=headers,
    )
    assert p2.status_code == 201

    # Verify invoice status is now fully PAID and balance is 0.00
    inv_final = client.get(f"/api/v1/invoices/{inv_id}", headers=headers).json()
    assert inv_final["status"] == "PAID"
    assert float(inv_final["amount_due"]) == 0.00


def test_payment_reconciliation_list():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/reconciliation", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "items" in data

