"""Coverage for the admin-only compatibility/test-result endpoints in src/api/benchmarks.py."""

import asyncio

from fastapi.testclient import TestClient

from src.config import settings
from src.db.models import MCPServer
from src.db.session import AsyncSessionLocal, engine, init_db
from src.main import app


def _run(async_fn, *args, **kwargs):
    async def _wrapper():
        result = await async_fn(*args, **kwargs)
        await engine.dispose()
        return result

    return asyncio.run(_wrapper())


async def _seed_server(namespace: str) -> int:
    await init_db()
    async with AsyncSessionLocal() as db:
        server = MCPServer(namespace=namespace, name="Test Server")
        db.add(server)
        await db.commit()
        await db.refresh(server)
        return server.id


def test_compatibility_route_is_not_swallowed_by_server_detail_route(monkeypatch):
    """benchmarks.router must be registered before servers.router in main.py -
    otherwise POST /servers/{ns}/compatibility matches servers.py's own
    {namespace:path} route first and never reaches this handler."""
    monkeypatch.setattr(settings, "admin_api_key", "s3cret")
    ns = "routing-order.test/compat"
    _run(_seed_server, ns)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/servers/{ns}/compatibility",
            json={"client": "claude", "compatible": True},
            headers={"X-Admin-Token": "s3cret"},
        )

    assert response.status_code == 200
    assert response.json()["client"] == "claude"


def test_record_compatibility_requires_admin_token(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "s3cret")
    ns = "auth-required.test/compat"
    _run(_seed_server, ns)

    with TestClient(app) as client:
        no_token = client.post(
            f"/api/v1/servers/{ns}/compatibility",
            json={"client": "claude", "compatible": True},
        )
        wrong_token = client.post(
            f"/api/v1/servers/{ns}/compatibility",
            json={"client": "claude", "compatible": True},
            headers={"X-Admin-Token": "wrong"},
        )

    assert no_token.status_code == 401
    assert wrong_token.status_code == 401


def test_record_compatibility_fails_closed_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", None)
    ns = "unconfigured.test/compat"
    _run(_seed_server, ns)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/servers/{ns}/compatibility",
            json={"client": "claude", "compatible": True},
        )

    assert response.status_code == 503


def test_record_compatibility_rejects_unknown_client(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "s3cret")
    ns = "bad-client.test/compat"
    _run(_seed_server, ns)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/servers/{ns}/compatibility",
            json={"client": "emacs", "compatible": True},
            headers={"X-Admin-Token": "s3cret"},
        )

    assert response.status_code == 422


def test_record_compatibility_upserts_not_duplicates(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "s3cret")
    ns = "upsert-compat.test/pkg"
    _run(_seed_server, ns)

    with TestClient(app) as client:
        first = client.post(
            f"/api/v1/servers/{ns}/compatibility",
            json={"client": "cursor", "compatible": True},
            headers={"X-Admin-Token": "s3cret"},
        )
        second = client.post(
            f"/api/v1/servers/{ns}/compatibility",
            json={"client": "cursor", "compatible": False},
            headers={"X-Admin-Token": "s3cret"},
        )
        detail = client.get(f"/api/v1/servers/{ns}")

    assert first.json()["compatible"] is True
    assert second.json()["compatible"] is False
    compatibilities = detail.json()["data"]["compatibilities"]
    assert len(compatibilities) == 1
    assert compatibilities[0]["compatible"] is False


def test_record_test_result_requires_admin_token(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "s3cret")
    ns = "auth-required.test/benchmark"
    _run(_seed_server, ns)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/servers/{ns}/test-results",
            json={
                "version": "1.0.0",
                "speed_ms": 100,
                "memory_mb": 50,
                "success_rate": 1.0,
                "error_count": 0,
            },
        )

    assert response.status_code == 401


def test_record_test_result_appends_history_not_upsert(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "s3cret")
    ns = "test-result-history.test/pkg"
    _run(_seed_server, ns)

    def _post(client, version):
        return client.post(
            f"/api/v1/servers/{ns}/test-results",
            json={
                "version": version,
                "speed_ms": 100,
                "memory_mb": 50,
                "success_rate": 0.9,
                "error_count": 0,
            },
            headers={"X-Admin-Token": "s3cret"},
        )

    with TestClient(app) as client:
        for version in ("1.0.0", "1.0.1"):
            _post(client, version)
        detail = client.get(f"/api/v1/servers/{ns}")

    test_results = detail.json()["data"]["test_results"]
    assert len(test_results) == 2
    assert {r["version"] for r in test_results} == {"1.0.0", "1.0.1"}


def test_server_detail_caps_test_results_at_five_most_recent(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "s3cret")
    ns = "test-result-cap.test/pkg"
    _run(_seed_server, ns)

    with TestClient(app) as client:
        for i in range(6):
            client.post(
                f"/api/v1/servers/{ns}/test-results",
                json={
                    "version": f"1.0.{i}",
                    "speed_ms": 100,
                    "memory_mb": 50,
                    "success_rate": 0.9,
                    "error_count": 0,
                },
                headers={"X-Admin-Token": "s3cret"},
            )
        detail = client.get(f"/api/v1/servers/{ns}")

    test_results = detail.json()["data"]["test_results"]
    assert len(test_results) == 5
    assert "1.0.0" not in {r["version"] for r in test_results}


def test_record_test_result_rejects_out_of_range_success_rate(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "s3cret")
    ns = "bad-success-rate.test/pkg"
    _run(_seed_server, ns)

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/servers/{ns}/test-results",
            json={
                "version": "1.0.0",
                "speed_ms": 100,
                "memory_mb": 50,
                "success_rate": 1.5,
                "error_count": 0,
            },
            headers={"X-Admin-Token": "s3cret"},
        )

    assert response.status_code == 422
