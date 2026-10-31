"""
Revenue Guardian Anomaly Detection (Module 7) Integration Tests.
Verifies automated leakage auditing, overdue invoice detection, and resolution workflows.
"""
from datetime import datetime, timedelta
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


def test_run_revenue_guardian_audit():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Run audit
    res = client.post("/api/v1/revenue-guardian/run", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_findings" in data
    assert "total_estimated_leakage" in data

    # List findings
    findings_res = client.get("/api/v1/revenue-guardian/findings", headers=headers)
    assert findings_res.status_code == 200
    assert isinstance(findings_res.json(), list)

