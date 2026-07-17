"""Coverage for the ratings/reviews endpoints in src/api/reviews.py."""

import asyncio
from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.db.models import MCPServer, User
from src.db.session import AsyncSessionLocal, engine, init_db
from src.main import app
from src.services.github_auth import GitHubAuthService


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


async def _seed_server_and_user(namespace: str, github_id="gh-1", username="reviewer"):
    await init_db()
    async with AsyncSessionLocal() as db:
        server = MCPServer(namespace=namespace, name="Test Server")
        user = User(github_id=github_id, username=username)
        db.add(server)
        db.add(user)
        await db.commit()
        await db.refresh(server)
        await db.refresh(user)
        return server.id, user.id


def _token_for(user_id: int) -> str:
    return GitHubAuthService().mint_jwt(SimpleNamespace(id=user_id))


def _authed_client(client: TestClient, user_id: int) -> None:
    client.cookies.set("access_token", _token_for(user_id))


def test_ratings_get_route_is_not_swallowed_by_server_detail_route():
    """reviews.router must be registered before servers.router in main.py -
    otherwise GET /servers/{ns}/ratings matches servers.py's own
    {namespace:path} route first (namespace ends up "<ns>/ratings"),
    returning a misleading 404 instead of ever reaching the ratings
    handler."""
    ns = "routing-order.test/pkg"
    _run(_seed_server, ns)

    with TestClient(app) as client:
        response = client.get(f"/api/v1/servers/{ns}/ratings")

    assert response.status_code == 200
    assert response.json()["total_ratings"] == 0


def test_rate_server_requires_auth():
    ns = "auth-required.test/pkg"
    _run(_seed_server, ns)

    with TestClient(app) as client:
        response = client.post(f"/api/v1/servers/{ns}/ratings", json={"score": 5})

    assert response.status_code == 401


def test_rate_server_rejects_out_of_range_score():
    ns = "bad-score.test/pkg"
    server_id, user_id = _run(_seed_server_and_user, ns)

    with TestClient(app) as client:
        _authed_client(client, user_id)
        response = client.post(f"/api/v1/servers/{ns}/ratings", json={"score": 6})

    assert response.status_code == 422


def test_rate_server_upserts_not_duplicates():
    ns = "upsert-rating.test/pkg"
    server_id, user_id = _run(_seed_server_and_user, ns)

    with TestClient(app) as client:
        _authed_client(client, user_id)
        first = client.post(f"/api/v1/servers/{ns}/ratings", json={"score": 3})
        second = client.post(f"/api/v1/servers/{ns}/ratings", json={"score": 5})

    assert first.json()["total_ratings"] == 1
    assert second.json()["total_ratings"] == 1
    assert second.json()["average_score"] == 5.0
    assert second.json()["my_score"] == 5


def test_ratings_distribution_buckets_all_five_scores():
    ns = "distribution.test/pkg"
    server_id, user_id = _run(_seed_server_and_user, ns)

    with TestClient(app) as client:
        _authed_client(client, user_id)
        client.post(f"/api/v1/servers/{ns}/ratings", json={"score": 4})
        response = client.get(f"/api/v1/servers/{ns}/ratings")

    buckets = {b["score"]: b["count"] for b in response.json()["distribution"]}
    assert buckets == {5: 0, 4: 1, 3: 0, 2: 0, 1: 0}


def test_submit_review_creates_then_edits_in_place():
    ns = "review-upsert.test/pkg"
    server_id, user_id = _run(_seed_server_and_user, ns)

    with TestClient(app) as client:
        _authed_client(client, user_id)
        created = client.post(
            f"/api/v1/servers/{ns}/reviews",
            json={"title": "First pass", "content": "Works fine."},
        )
        edited = client.post(
            f"/api/v1/servers/{ns}/reviews",
            json={"title": "After more use", "content": "Even better than I thought."},
        )
        listed = client.get(f"/api/v1/servers/{ns}/reviews")

    assert created.status_code == 200
    assert created.json()["created_at"] == created.json()["updated_at"]
    assert edited.json()["title"] == "After more use"
    assert edited.json()["updated_at"] > edited.json()["created_at"]
    assert listed.json()["pagination"]["total"] == 1
    assert listed.json()["data"][0]["title"] == "After more use"


def test_list_reviews_includes_author_fields_and_paginates():
    ns = "review-list.test/pkg"
    server_id, user_id = _run(_seed_server_and_user, ns, github_id="gh-2", username="alice")

    with TestClient(app) as client:
        _authed_client(client, user_id)
        client.post(
            f"/api/v1/servers/{ns}/reviews", json={"title": "Nice", "content": "Solid server."}
        )
        response = client.get(f"/api/v1/servers/{ns}/reviews", params={"skip": 0, "limit": 10})

    review = response.json()["data"][0]
    assert review["author_username"] == "alice"
    assert response.json()["pagination"] == {"skip": 0, "limit": 10, "total": 1}


def test_get_my_review_404_when_none_submitted():
    ns = "my-review.test/pkg"
    server_id, user_id = _run(_seed_server_and_user, ns)

    with TestClient(app) as client:
        _authed_client(client, user_id)
        response = client.get(f"/api/v1/servers/{ns}/reviews/me")

    assert response.status_code == 404
