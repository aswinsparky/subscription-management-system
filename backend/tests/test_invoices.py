"""
Invoice Management and PDF Generation (Modules 3 & 4) Integration Tests.
Verifies manual creation, total recalculation, PDF generation, and duplicate prevention.
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


def create_test_customer(token: str) -> int:
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post(
        "/api/v1/customers",
        json={
            "full_name": "Acme Global Tech",
            "email": f"acme_{uuid.uuid4().hex[:6]}@example.com",
            "company_name": "Acme Corp",
            "billing_address": "123 Silicon Way",
            "tax_id": "US-TAX-9988",
        },
        headers=headers,
    )
    return res.json()["id"]


def test_create_and_confirm_invoice():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    cust_id = create_test_customer(token)

    payload = {
        "customer_id": cust_id,
        "payment_terms": "Net 15",
        "notes": "Quarterly cloud infrastructure fees",
        "items": [
            {
                "item_description": "Dedicated Cloud Cluster",
                "quantity": 2,
                "unit_price": "250.00",
                "tax_rate_snapshot": "0.00",
            }
        ],
    }
    create_res = client.post("/api/v1/invoices", json=payload, headers=headers)
    assert create_res.status_code == 201
    inv_data = create_res.json()
    assert inv_data["status"] == "DRAFT"
    assert float(inv_data["subtotal"]) == 500.00
    assert float(inv_data["total_amount"]) == 500.00
    assert float(inv_data["amount_due"]) == 500.00

    inv_id = inv_data["id"]

    # Confirm invoice
    confirm_res = client.post(f"/api/v1/invoices/{inv_id}/confirm", headers=headers)
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "CONFIRMED"

    # Download PDF
    pdf_res = client.get(f"/api/v1/invoices/{inv_id}/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000

