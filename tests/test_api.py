from fastapi.testclient import TestClient
from src.config import settings
from src.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to MCP Hub API" in response.json()["message"]


def test_list_servers_empty():
    response = client.get("/api/v1/servers")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["pagination"]["total"] == 0


def test_sync_registry_requires_admin_auth(monkeypatch):
    # scraper-behavior coverage (dict repository, pagination, version dedup) lives in test_regressions.py
    monkeypatch.setattr(settings, "admin_api_key", "s3cret")
    response = client.post("/api/v1/admin/sync-registry")
    assert response.status_code == 401
