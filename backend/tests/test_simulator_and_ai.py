"""
Future Revenue Simulator & Ask Brightloop AI (Modules 8 & 9) Tests.
Verifies forecasting scenarios, grounded metric answers, and analytics endpoints.
"""
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


def test_revenue_simulation():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "scenario_name": "Q2 Growth Plan",
        "new_customers_monthly": 10,
        "churn_rate_percent": "2.0",
        "plan_upgrade_rate_percent": "5.0",
        "price_change_percent": "5.0",
        "projection_months": 12,
    }
    res = client.post("/api/v1/revenue-simulator/simulate", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_name"] == "Q2 Growth Plan"
    assert len(data["monthly_forecast"]) == 12
    assert "baseline_mrr" in data
    assert "projected_mrr" in data


def test_ai_assistant_grounded_query():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    query_res = client.post(
        "/api/v1/ai-assistant/query",
        json={"query": "How much money is overdue?"},
        headers=headers,
    )
    assert query_res.status_code == 200
    data = query_res.json()
    assert "answer" in data
    assert "grounded_data" in data
    assert "total_overdue" in data["grounded_data"]


def test_analytics_summary():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_revenue" in data
    assert "mrr" in data
    assert "arr" in data
    assert "total_collected" in data
    assert "total_outstanding" in data

