"""Tests for the auth gate (login, logout, session, status endpoint).

Auth is disabled by default for the rest of the suite via an autouse fixture
in conftest. These tests opt back in via `auth_client`, which sets a known
AUTH_TOKEN, enables AUTH_ENABLED, and clears any prior session cookie state.
"""

import os
import sys

import pytest

_framework_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _framework_dir not in sys.path:
    sys.path.insert(0, _framework_dir)


_TEST_TOKEN = "test-token-do-not-use-in-prod"


@pytest.fixture()
def auth_client(app_client, monkeypatch):
    """Re-enable auth with a known token. Patches app.AUTH_TOKEN so the
    /api/auth/login route validates against `_TEST_TOKEN`."""
    import app as app_module
    from app import app as flask_app

    monkeypatch.setattr(app_module, "AUTH_TOKEN", _TEST_TOKEN)
    flask_app.config["AUTH_ENABLED"] = True

    yield app_client

    flask_app.config["AUTH_ENABLED"] = False


class TestAuthGate:
    """Routes are inaccessible without a valid session."""

    def test_api_returns_401_when_unauthed(self, auth_client):
        r = auth_client.get("/api/today")
        assert r.status_code == 401
        body = r.get_json()
        assert body["success"] is False
        assert "auth" in body["error"].lower()

    def test_index_redirects_to_login_when_unauthed(self, auth_client):
        r = auth_client.get("/", follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/login")

    def test_login_page_accessible_unauthed(self, auth_client):
        r = auth_client.get("/login")
        assert r.status_code == 200
        # Login form is rendered
        assert b"token" in r.data.lower()

    def test_status_endpoint_accessible_unauthed(self, auth_client):
        r = auth_client.get("/api/auth/status")
        assert r.status_code == 200
        body = r.get_json()
        assert body["authed"] is False
        assert body["auth_required"] is True


class TestLoginFlow:

    def test_login_with_valid_token_succeeds(self, auth_client):
        r = auth_client.post("/api/auth/login", json={"token": _TEST_TOKEN})
        assert r.status_code == 200
        assert r.get_json()["success"] is True
        # CSRF cookie was set
        cookies = r.headers.getlist("Set-Cookie")
        assert any("csrf_token=" in c for c in cookies)

    def test_login_with_wrong_token_returns_401(self, auth_client):
        r = auth_client.post("/api/auth/login", json={"token": "wrong-token"})
        assert r.status_code == 401
        assert r.get_json()["success"] is False

    def test_login_with_missing_token_returns_400(self, auth_client):
        r = auth_client.post("/api/auth/login", json={})
        assert r.status_code == 400

    def test_login_uses_constant_time_compare(self, auth_client, monkeypatch):
        """Verify hmac.compare_digest is used (not == comparison)."""
        import hmac as hmac_module
        calls = []
        original = hmac_module.compare_digest

        def spy(a, b):
            calls.append((a, b))
            return original(a, b)

        monkeypatch.setattr("app.hmac.compare_digest", spy)
        auth_client.post("/api/auth/login", json={"token": _TEST_TOKEN})
        assert len(calls) == 1, "compare_digest should be called exactly once on login"

    def test_authed_session_can_access_api(self, auth_client):
        """After login, GET endpoints work with the session cookie."""
        login = auth_client.post("/api/auth/login", json={"token": _TEST_TOKEN})
        assert login.status_code == 200

        r = auth_client.get("/api/today")
        assert r.status_code == 200

    def test_login_page_redirects_when_already_authed(self, auth_client):
        auth_client.post("/api/auth/login", json={"token": _TEST_TOKEN})
        r = auth_client.get("/login", follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/")


def _csrf_headers(client):
    """Read the csrf_token cookie set by login and return matching header dict."""
    for cookie in client.cookie_jar if hasattr(client, "cookie_jar") else []:
        if cookie.name == "csrf_token":
            return {"X-CSRF-Token": cookie.value}
    # Fallback for newer werkzeug test clients (no cookie_jar attr)
    token = client.get_cookie("csrf_token")
    return {"X-CSRF-Token": token.value} if token else {}


class TestLogout:

    def test_logout_clears_session(self, auth_client):
        auth_client.post("/api/auth/login", json={"token": _TEST_TOKEN})
        r = auth_client.post("/api/auth/logout", headers=_csrf_headers(auth_client))
        assert r.status_code == 200

        # After logout, API requires auth again
        r2 = auth_client.get("/api/today")
        assert r2.status_code == 401

    def test_logout_when_not_logged_in_returns_401(self, auth_client):
        """Logout is auth-protected; unauthed callers get 401."""
        r = auth_client.post("/api/auth/logout")
        assert r.status_code == 401


class TestStatusEndpoint:

    def test_status_reflects_authed_state(self, auth_client):
        before = auth_client.get("/api/auth/status").get_json()
        assert before["authed"] is False

        auth_client.post("/api/auth/login", json={"token": _TEST_TOKEN})
        after = auth_client.get("/api/auth/status").get_json()
        assert after["authed"] is True

    def test_status_when_auth_disabled(self, app_client):
        """When AUTH_ENABLED is false (the default app_client state), status
        reports auth_required: false."""
        r = app_client.get("/api/auth/status")
        body = r.get_json()
        assert body["authed"] is True
        assert body["auth_required"] is False


class TestAuthDisabled:
    """When AUTH_ENABLED=False (the default app_client state), all gates are
    bypassed and the existing app behaves as before."""

    def test_api_accessible_without_login(self, app_client):
        r = app_client.get("/api/today")
        assert r.status_code == 200

    def test_index_accessible_without_login(self, app_client):
        r = app_client.get("/")
        # Index renders OK (or returns the fallback string)
        assert r.status_code == 200
