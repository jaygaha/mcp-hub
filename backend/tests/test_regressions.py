"""
Regression coverage for bugs found in the codebase audit, each drawn from
the live official registry schema.

`_run` deliberately keeps async DB setup and TestClient's HTTP calls in
separate event loops (disposing the shared engine's pool between them) -
mixing pytest-asyncio's loop with TestClient's own anyio portal loop
against one asyncpg pool raises spurious "different loop" errors.
"""

import asyncio

import httpx2
from fastapi.testclient import TestClient

from src.config import settings
from src.db.session import AsyncSessionLocal, engine, init_db
from src.main import app
from src.services import registry_scraper as scraper_module
from src.services.registry_scraper import RegistryScraper


def _run(async_fn, *args, **kwargs):
    async def _wrapper():
        result = await async_fn(*args, **kwargs)
        await engine.dispose()
        return result

    return asyncio.run(_wrapper())


def _mock_client_factory(handler):
    real_async_client = httpx2.AsyncClient

    def make_client(*args, **kwargs):
        kwargs["transport"] = httpx2.MockTransport(handler)
        return real_async_client(*args, **kwargs)

    return make_client


async def _seed(namespace, name, description=None):
    from src.db.models import MCPServer

    await init_db()
    async with AsyncSessionLocal() as db:
        db.add(MCPServer(namespace=namespace, name=name, description=description))
        await db.commit()


async def _run_sync_all_servers(db_factory=AsyncSessionLocal):
    await init_db()
    async with db_factory() as db:
        return await RegistryScraper().sync_all_servers(db)


async def _seed_full_detail(namespace):
    from src.db.models import Compatibility, MCPServer, Rating, TestResult, User

    await init_db()
    async with AsyncSessionLocal() as db:
        server = MCPServer(namespace=namespace, name="Full Detail Server")
        user = User(github_id="gh-1", username="audit-user")
        db.add(server)
        db.add(user)
        await db.flush()
        db.add(
            TestResult(
                mcp_server_id=server.id,
                version="1.0.0",
                speed_ms=42.5,
                memory_mb=128.0,
                success_rate=0.95,
                error_count=1,
            )
        )
        db.add(Compatibility(mcp_server_id=server.id, client="claude", compatible=True))
        db.add(Rating(mcp_server_id=server.id, user_id=user.id, score=4))
        await db.commit()


def test_get_server_supports_namespaces_containing_a_slash():
    """Every real registry namespace is "<scope>/<name>" - the route must
    accept the slash instead of 404ing before the handler ever runs."""
    ns = "audit-test.scope/pkg"
    _run(_seed, ns, "Audit Test Server")

    with TestClient(app) as client:
        resp = client.get(f"/api/v1/servers/{ns}")

    assert resp.status_code == 200
    assert resp.json()["data"]["server"]["namespace"] == ns


def test_list_servers_total_matches_namespace_only_search():
    """The count query must use the same filter as the row query, so a
    namespace-only match reports a consistent total instead of 0."""
    ns = "zzz-audit-unique/pkg"
    _run(_seed, ns, "Totally Different Name", "no overlap")

    with TestClient(app) as client:
        resp = client.get("/api/v1/servers", params={"search": "zzz-audit-unique"})

    data = resp.json()
    assert len(data["data"]) == 1
    assert data["pagination"]["total"] == 1


def test_sync_handles_dict_shaped_repository_and_website_url(monkeypatch):
    """The registry's `repository` field is an object, not a string, and the
    real URL usually lives in `websiteUrl`. Both must be handled without
    crashing the whole sync batch."""
    payload = {
        "servers": [
            {
                "server": {
                    "name": "audit.fixture/dict-repo",
                    "title": "Dict Repo",
                    "repository": {
                        "url": "https://github.com/example/one",
                        "source": "github",
                    },
                }
            },
            {
                "server": {
                    "name": "audit.fixture/website-url",
                    "title": "Website URL",
                    "websiteUrl": "https://example.com",
                    "repository": {"url": "https://github.com/example/two"},
                }
            },
        ],
        "metadata": {"count": 2},
    }

    def handler(request):
        return httpx2.Response(200, json=payload)

    monkeypatch.setattr(
        scraper_module.httpx2, "AsyncClient", _mock_client_factory(handler)
    )

    result = _run(_run_sync_all_servers)
    assert result["status"] == "success"
    assert result["created"] == 2

    with TestClient(app) as client:
        resp = client.get("/api/v1/servers/audit.fixture/dict-repo")
        assert (
            resp.json()["data"]["server"]["repository_url"]
            == "https://github.com/example/one"
        )

        resp = client.get("/api/v1/servers/audit.fixture/website-url")
        # websiteUrl wins over the repository object when both are present
        assert resp.json()["data"]["server"]["repository_url"] == "https://example.com"


def test_sync_retries_transient_network_failures(monkeypatch):
    """A single ReadTimeout mid-walk used to discard every page already
    fetched and fail the whole sync. Transient errors must be retried
    instead."""
    payload = {
        "servers": [{"server": {"name": "audit.fixture/retry-me"}}],
        "metadata": {"count": 1},
    }
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx2.ReadTimeout("simulated transient failure")
        return httpx2.Response(200, json=payload)

    async def _no_sleep(_seconds):
        pass

    monkeypatch.setattr(scraper_module.asyncio, "sleep", _no_sleep)
    monkeypatch.setattr(
        scraper_module.httpx2, "AsyncClient", _mock_client_factory(handler)
    )

    result = _run(_run_sync_all_servers)

    assert result["status"] == "success"
    assert result["created"] == 1
    assert calls == 2


def test_sync_retries_429_honoring_retry_after(monkeypatch):
    """The registry rate-limits sustained pagination with a 429. That must
    be retried too (not treated as a fatal client error), honoring
    Retry-After when the server sends one."""
    payload = {
        "servers": [{"server": {"name": "audit.fixture/rate-limited"}}],
        "metadata": {"count": 1},
    }
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx2.Response(429, headers={"Retry-After": "7"}, text="slow down")
        return httpx2.Response(200, json=payload)

    sleeps = []

    async def _record_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(scraper_module.asyncio, "sleep", _record_sleep)
    monkeypatch.setattr(
        scraper_module.httpx2, "AsyncClient", _mock_client_factory(handler)
    )

    result = _run(_run_sync_all_servers)

    assert result["status"] == "success"
    assert result["created"] == 1
    assert calls == 2
    assert 7.0 in sleeps


def test_sync_follows_pagination_cursor_across_pages(monkeypatch):
    """The registry paginates at a fixed page size and returns
    metadata.nextCursor; a full sync must follow it instead of stopping
    after page one."""
    pages = [
        {
            "servers": [{"server": {"name": "audit.fixture/page1"}}],
            "metadata": {"nextCursor": "cursor-2", "count": 1},
        },
        {
            "servers": [{"server": {"name": "audit.fixture/page2"}}],
            "metadata": {"count": 1},  # no nextCursor -> last page
        },
    ]
    calls = []

    def handler(request):
        calls.append(dict(request.url.params))
        return httpx2.Response(200, json=pages[len(calls) - 1])

    monkeypatch.setattr(
        scraper_module.httpx2, "AsyncClient", _mock_client_factory(handler)
    )

    result = _run(_run_sync_all_servers)

    assert result["status"] == "success"
    assert result["created"] == 2
    assert len(calls) == 2
    assert calls[1].get("cursor") == "cursor-2"


def test_sync_keeps_only_the_latest_version_per_namespace(monkeypatch):
    """The registry lists every historical version of a server under the
    same namespace; only the entry flagged isLatest should win, regardless
    of array order."""
    payload = {
        "servers": [
            {
                "server": {
                    "name": "audit.fixture/versioned",
                    "version": "1.0.1",
                    "description": "new",
                },
                "_meta": {
                    "io.modelcontextprotocol.registry/official": {"isLatest": True}
                },
            },
            {
                "server": {
                    "name": "audit.fixture/versioned",
                    "version": "1.0.0",
                    "description": "old",
                },
                "_meta": {
                    "io.modelcontextprotocol.registry/official": {"isLatest": False}
                },
            },
        ],
        "metadata": {"count": 2},
    }

    def handler(request):
        return httpx2.Response(200, json=payload)

    monkeypatch.setattr(
        scraper_module.httpx2, "AsyncClient", _mock_client_factory(handler)
    )

    result = _run(_run_sync_all_servers)
    assert result["status"] == "success"
    assert result["created"] == 1  # the two entries collapse into one row

    with TestClient(app) as client:
        resp = client.get("/api/v1/servers/audit.fixture/versioned")
    server = resp.json()["data"]["server"]
    assert server["version"] == "1.0.1"
    assert server["description"] == "new"


def test_sync_processes_multiple_batches_correctly(monkeypatch):
    """Upserts are chunked (registry_scraper._BATCH_SIZE); a sync spanning
    several batches must still create every server and report an accurate
    total, not just whatever fits in the first chunk."""
    monkeypatch.setattr(scraper_module, "_BATCH_SIZE", 2)
    payload = {
        "servers": [
            {"server": {"name": f"audit.fixture/batch-{i}"}} for i in range(5)
        ],
        "metadata": {"count": 5},
    }

    def handler(request):
        return httpx2.Response(200, json=payload)

    monkeypatch.setattr(
        scraper_module.httpx2, "AsyncClient", _mock_client_factory(handler)
    )

    result = _run(_run_sync_all_servers)

    assert result["status"] == "success"
    assert result["created"] == 5
    assert result["updated"] == 0
    assert result["total"] == 5

    with TestClient(app) as client:
        for i in range(5):
            resp = client.get(f"/api/v1/servers/audit.fixture/batch-{i}")
            assert resp.status_code == 200


def test_sync_upserts_existing_servers_across_batches(monkeypatch):
    """A second sync over servers that already exist must update them in
    place (batched upsert), not create duplicates or skip later batches."""
    monkeypatch.setattr(scraper_module, "_BATCH_SIZE", 2)
    namespaces = [f"audit.fixture/upsert-{i}" for i in range(5)]
    current_description = "first pass"

    def make_payload():
        return {
            "servers": [
                {"server": {"name": ns, "description": current_description}}
                for ns in namespaces
            ],
            "metadata": {"count": 5},
        }

    def handler(request):
        return httpx2.Response(200, json=make_payload())

    # _mock_client_factory captures httpx2.AsyncClient at call time, so it
    # can only be applied once per test - a second call would wrap the
    # first mock instead of the real client. Swapping current_description
    # (read by `handler` on every call) lets one patch serve both syncs.
    monkeypatch.setattr(
        scraper_module.httpx2, "AsyncClient", _mock_client_factory(handler)
    )
    first_result = _run(_run_sync_all_servers)
    assert first_result["created"] == 5
    assert first_result["updated"] == 0

    current_description = "second pass"
    second_result = _run(_run_sync_all_servers)

    assert second_result["status"] == "success"
    assert second_result["created"] == 0
    assert second_result["updated"] == 5
    assert second_result["total"] == 5

    with TestClient(app) as client:
        resp = client.get(f"/api/v1/servers/{namespaces[0]}")
    assert resp.json()["data"]["server"]["description"] == "second pass"


def test_get_server_response_matches_dto_shape_with_populated_relations():
    """The dedicated response DTOs (not response_model=dict) must correctly
    serialize a server with real test results, compatibilities and
    ratings attached - not just the empty-relations happy path."""
    ns = "audit.fixture/full-detail"
    _run(_seed_full_detail, ns)

    with TestClient(app) as client:
        resp = client.get(f"/api/v1/servers/{ns}")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["server"]["namespace"] == ns
    assert data["average_rating"] == 4.0
    assert len(data["test_results"]) == 1
    assert data["test_results"][0]["version"] == "1.0.0"
    assert len(data["compatibilities"]) == 1
    assert data["compatibilities"][0]["client"] == "claude"
    # relationship collections must never leak onto the flat server object
    assert "ratings" not in data["server"]
    assert "test_results" not in data["server"]


def test_cors_allows_configured_origin_but_not_arbitrary_ones():
    """allow_origins must be an explicit allow-list, not "*", since
    allow_credentials=True makes a wildcard equivalent to no CORS
    protection at all for credentialed requests."""
    with TestClient(app) as client:
        allowed = client.get(
            "/api/v1/health", headers={"Origin": "http://localhost:3000"}
        )
        untrusted = client.get(
            "/api/v1/health", headers={"Origin": "https://evil.example.com"}
        )

    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert untrusted.headers.get("access-control-allow-origin") is None


def test_sync_registry_endpoint_requires_admin_token(monkeypatch):
    """The docstring always claimed "(admin only)" - now it's enforced."""
    monkeypatch.setattr(settings, "admin_api_key", "s3cret")

    with TestClient(app) as client:
        no_token = client.post("/api/v1/admin/sync-registry")
        wrong_token = client.post(
            "/api/v1/admin/sync-registry", headers={"X-Admin-Token": "wrong"}
        )

    assert no_token.status_code == 401
    assert wrong_token.status_code == 401


def test_sync_registry_endpoint_fails_closed_when_unconfigured(monkeypatch):
    """With no ADMIN_API_KEY set at all, the endpoint must refuse everyone
    rather than silently allowing open access."""
    monkeypatch.setattr(settings, "admin_api_key", None)

    with TestClient(app) as client:
        resp = client.post("/api/v1/admin/sync-registry")

    assert resp.status_code == 503
