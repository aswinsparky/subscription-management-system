"""
Health Check and Diagnostics Integration Tests.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that root endpoint returns operational status and documentation link."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "/api/v1/docs" in data["documentation"]


def test_health_check_database_connectivity():
    """Verify that /api/v1/health returns online status and active database connection."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["database"]["status"] == "connected"
    assert bool(data["database"]["version"])
