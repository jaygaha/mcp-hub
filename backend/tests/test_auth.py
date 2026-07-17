"""Coverage for the GitHub OAuth flow: login redirect, callback (success, mismatched state, user denial), /me, and logout. GitHub itself is mocked via 
httpx2.MockTransport, mirroring test_regressions.py's pattern."""

import httpx2
from fastapi.testclient import TestClient

from src.config import settings
from src.main import app
from src.services import github_auth as github_auth_module


def _mock_client_factory(handler):
    real_async_client = httpx2.AsyncClient

    def make_client(*args, **kwargs):
        kwargs["transport"] = httpx2.MockTransport(handler)
        return real_async_client(*args, **kwargs)

    return make_client


def _github_handler(request):
    if request.url.path == "/login/oauth/access_token":
        return httpx2.Response(200, json={"access_token": "gh-token-123"})
    if request.url.path == "/user":
        return httpx2.Response(
            200, json={"id": 42, "login": "octocat", "avatar_url": "https://example.com/a.png"}
        )
    return httpx2.Response(404, json={"error": "unexpected request"})


def test_login_fails_closed_without_client_id_configured(monkeypatch):
    monkeypatch.setattr(settings, "github_client_id", None)

    with TestClient(app) as client:
        response = client.get("/api/v1/auth/login", follow_redirects=False)

    assert response.status_code == 503


def test_login_redirects_to_github_with_state_cookie(monkeypatch):
    monkeypatch.setattr(settings, "github_client_id", "test-client-id")

    with TestClient(app) as client:
        response = client.get("/api/v1/auth/login", follow_redirects=False)

    assert response.status_code == 307
    location = response.headers["location"]
    assert "github.com/login/oauth/authorize" in location
    assert "client_id=test-client-id" in location
    assert "state=" in location
    assert response.cookies.get("oauth_state") is not None


def test_callback_rejects_mismatched_state(monkeypatch):
    monkeypatch.setattr(settings, "github_client_id", "test-client-id")
    monkeypatch.setattr(settings, "github_client_secret", "test-secret")

    with TestClient(app) as client:
        client.get("/api/v1/auth/login", follow_redirects=False)
        response = client.get(
            "/api/v1/auth/github/callback",
            params={"code": "abc", "state": "wrong-state"},
        )

    assert response.status_code == 400


def test_callback_handles_user_denial(monkeypatch):
    monkeypatch.setattr(settings, "github_client_id", "test-client-id")

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/auth/github/callback",
            params={"error": "access_denied", "state": "irrelevant"},
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["location"] == f"{settings.frontend_url}?auth_error=denied"


def test_callback_success_sets_access_token_and_upserts_user(monkeypatch):
    monkeypatch.setattr(settings, "github_client_id", "test-client-id")
    monkeypatch.setattr(settings, "github_client_secret", "test-secret")
    monkeypatch.setattr(
        github_auth_module.httpx2, "AsyncClient", _mock_client_factory(_github_handler)
    )

    with TestClient(app) as client:
        login_response = client.get("/api/v1/auth/login", follow_redirects=False)
        state = login_response.headers["location"].split("state=")[1].split("&")[0]

        callback_response = client.get(
            "/api/v1/auth/github/callback",
            params={"code": "auth-code", "state": state},
            follow_redirects=False,
        )
        assert callback_response.status_code == 307
        assert callback_response.headers["location"] == settings.frontend_url
        assert callback_response.cookies.get("access_token") is not None

        me_response = client.get("/api/v1/auth/me")

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "octocat"


def test_me_requires_authentication():
    with TestClient(app) as client:
        no_cookie = client.get("/api/v1/auth/me")

        client.cookies.set("access_token", "not-a-jwt")
        garbage_cookie = client.get("/api/v1/auth/me")

    assert no_cookie.status_code == 401
    assert garbage_cookie.status_code == 401


def test_logout_clears_cookie():
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/logout", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == settings.frontend_url
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
