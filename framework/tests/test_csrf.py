"""Tests for the double-submit-cookie CSRF protection.

CSRF is enforced on state-changing methods (POST/PUT/PATCH/DELETE) only when
auth is enabled. The login endpoint itself is exempt — the secret token is
the auth, and there is no cookie to compare against until login succeeds.
"""

import os
import sys

import pytest

_framework_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _framework_dir not in sys.path:
    sys.path.insert(0, _framework_dir)


_TEST_TOKEN = "csrf-test-token"


@pytest.fixture()
def authed_client(app_client, monkeypatch):
    """Re-enable auth, log in, and return a client with a valid session +
    csrf_token cookie."""
    import app as app_module
    from app import app as flask_app

    monkeypatch.setattr(app_module, "AUTH_TOKEN", _TEST_TOKEN)
    flask_app.config["AUTH_ENABLED"] = True

    login = app_client.post("/api/auth/login", json={"token": _TEST_TOKEN})
    assert login.status_code == 200, "fixture precondition: login must succeed"

    yield app_client

    flask_app.config["AUTH_ENABLED"] = False


def _csrf_token(client):
    cookie = client.get_cookie("csrf_token")
    return cookie.value if cookie else None


class TestCsrfRejection:

    def test_post_without_csrf_header_is_forbidden(self, authed_client):
        # /api/copy is a simple authed POST; we send no CSRF header.
        r = authed_client.post("/api/copy", json={"generation_id": 1})
        assert r.status_code == 403
        body = r.get_json()
        assert body["success"] is False
        assert "csrf" in body["error"].lower()

    def test_post_with_wrong_csrf_header_is_forbidden(self, authed_client):
        r = authed_client.post(
            "/api/copy",
            json={"generation_id": 1},
            headers={"X-CSRF-Token": "not-the-real-token"},
        )
        assert r.status_code == 403

    def test_post_with_matching_csrf_header_is_allowed(self, authed_client):
        token = _csrf_token(authed_client)
        assert token, "fixture should have set csrf_token cookie"

        # /api/copy with a non-existent generation_id still passes CSRF and
        # reaches the handler (which is the only gate we're testing here).
        # We only assert that we did NOT get 403.
        r = authed_client.post(
            "/api/copy",
            json={"generation_id": 1},
            headers={"X-CSRF-Token": token},
        )
        assert r.status_code != 403

    def test_delete_requires_csrf(self, authed_client):
        r = authed_client.delete("/api/feeds/1")
        assert r.status_code == 403

    def test_put_requires_csrf(self, authed_client):
        r = authed_client.put("/api/feeds/1", json={"name": "x"})
        assert r.status_code == 403


class TestCsrfExemptions:

    def test_get_requests_unaffected(self, authed_client):
        r = authed_client.get("/api/today")
        assert r.status_code == 200

    def test_login_endpoint_does_not_require_csrf(self, app_client, monkeypatch):
        """An unauthed user POSTing to /api/auth/login has no CSRF cookie yet,
        so the login endpoint must be exempt or login is impossible."""
        import app as app_module
        from app import app as flask_app

        monkeypatch.setattr(app_module, "AUTH_TOKEN", _TEST_TOKEN)
        flask_app.config["AUTH_ENABLED"] = True
        try:
            r = app_client.post("/api/auth/login", json={"token": _TEST_TOKEN})
            assert r.status_code == 200
        finally:
            flask_app.config["AUTH_ENABLED"] = False


class TestCsrfDisabledWithAuth:
    """When AUTH_ENABLED=False (default test state), CSRF is also bypassed."""

    def test_no_csrf_required_when_auth_disabled(self, app_client):
        # /api/copy POST works even without an X-CSRF-Token header
        r = app_client.post("/api/copy", json={"generation_id": 1})
        # Won't be 403 (CSRF rejection); may be 200 or 4xx depending on data
        assert r.status_code != 403
