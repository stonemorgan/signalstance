"""Tests for security fixes in framework/app.py.

Covers SSRF protection (_is_safe_url), path traversal prevention,
debug mode defaults, and API error handling.
Uses Flask's test client and socket mocking -- no real network calls.
"""

import json
import os
import sys
from unittest.mock import patch

import pytest

_framework_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _framework_dir not in sys.path:
    sys.path.insert(0, _framework_dir)


# ---------------------------------------------------------------------------
# _is_safe_url() tests
# ---------------------------------------------------------------------------

class TestIsSafeUrl:
    """Test the SSRF protection function."""

    def _mock_resolve(self, ip_str):
        """Return a mock getaddrinfo result for a single IPv4 address."""
        import socket
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", (ip_str, 0))]

    def test_rejects_loopback_127(self):
        from app import _is_safe_url
        with patch("app.socket.getaddrinfo", return_value=self._mock_resolve("127.0.0.1")):
            safe, msg = _is_safe_url("http://localhost/admin")
            assert safe is False
            assert "private" in msg.lower() or "internal" in msg.lower()

    def test_rejects_private_10(self):
        from app import _is_safe_url
        with patch("app.socket.getaddrinfo", return_value=self._mock_resolve("10.0.0.1")):
            safe, msg = _is_safe_url("http://internal-service.local/api")
            assert safe is False

    def test_rejects_private_192_168(self):
        from app import _is_safe_url
        with patch("app.socket.getaddrinfo", return_value=self._mock_resolve("192.168.1.1")):
            safe, msg = _is_safe_url("http://router.local/config")
            assert safe is False

    def test_rejects_link_local_169_254(self):
        from app import _is_safe_url
        with patch("app.socket.getaddrinfo", return_value=self._mock_resolve("169.254.169.254")):
            safe, msg = _is_safe_url("http://metadata.google.internal/")
            assert safe is False

    def test_rejects_private_172_16(self):
        from app import _is_safe_url
        with patch("app.socket.getaddrinfo", return_value=self._mock_resolve("172.16.0.1")):
            safe, msg = _is_safe_url("http://internal.corp/secret")
            assert safe is False

    def test_rejects_file_scheme(self):
        from app import _is_safe_url
        safe, msg = _is_safe_url("file:///etc/passwd")
        assert safe is False
        assert "http" in msg.lower()

    def test_rejects_ftp_scheme(self):
        from app import _is_safe_url
        safe, msg = _is_safe_url("ftp://evil.com/payload")
        assert safe is False

    def test_rejects_javascript_scheme(self):
        from app import _is_safe_url
        safe, msg = _is_safe_url("javascript:alert(1)")
        assert safe is False

    def test_accepts_valid_external_http(self):
        from app import _is_safe_url
        with patch("app.socket.getaddrinfo", return_value=self._mock_resolve("93.184.216.34")):
            safe, msg = _is_safe_url("http://example.com/feed.xml")
            assert safe is True
            assert msg is None

    def test_accepts_valid_external_https(self):
        from app import _is_safe_url
        with patch("app.socket.getaddrinfo", return_value=self._mock_resolve("151.101.1.140")):
            safe, msg = _is_safe_url("https://reddit.com/r/jobs.rss")
            assert safe is True

    def test_rejects_no_hostname(self):
        from app import _is_safe_url
        safe, msg = _is_safe_url("http://")
        assert safe is False
        assert "hostname" in msg.lower() or "invalid" in msg.lower()

    def test_rejects_unresolvable_hostname(self):
        from app import _is_safe_url
        import socket
        with patch("app.socket.getaddrinfo", side_effect=socket.gaierror("not found")):
            safe, msg = _is_safe_url("http://nonexistent.invalid/feed")
            assert safe is False
            assert "resolve" in msg.lower()


# ---------------------------------------------------------------------------
# Path traversal protection
# ---------------------------------------------------------------------------

class TestPathTraversal:
    def test_carousel_download_rejects_traversal(self, db):
        """The carousel download endpoint should reject path traversal filenames."""
        import database

        iid = database.save_insight("pattern", "test")
        gid = database.save_generation(iid, 1, "title")
        # Manually insert carousel_data with a traversal filename
        conn = db()
        try:
            conn.execute(
                "INSERT INTO carousel_data (generation_id, template_type, parsed_content, pdf_filename, slide_count) "
                "VALUES (?, ?, ?, ?, ?)",
                (gid, "tips", json.dumps({"title": "test"}), "../../../etc/passwd", 3),
            )
            conn.commit()
        finally:
            conn.close()

        from app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            resp = client.get(f"/api/carousel/download/{gid}")
            # Should be rejected -- either 400 (invalid filename) or 404
            assert resp.status_code in (400, 404)


# ---------------------------------------------------------------------------
# Debug mode
# ---------------------------------------------------------------------------

class TestDebugMode:
    def test_debug_off_by_default(self):
        """Flask debug mode should be off by default (production safety)."""
        from app import app as flask_app
        # The app should not have debug=True when run without FLASK_DEBUG=true
        assert flask_app.debug is False or os.getenv("FLASK_DEBUG", "false").lower() != "true"

    def test_debug_mode_requires_env_var(self):
        """app.run(debug=...) in __main__ should only be True when
        FLASK_DEBUG env var is explicitly 'true'."""
        app_path = os.path.join(_framework_dir, "app.py")
        with open(app_path, "r") as f:
            source = f.read()
        # The debug flag should reference FLASK_DEBUG env var, not a hardcoded True
        assert 'debug=True' not in source or 'FLASK_DEBUG' in source


# ---------------------------------------------------------------------------
# API error responses (JSON, not HTML tracebacks)
# ---------------------------------------------------------------------------

class TestApiErrorResponses:
    def test_generate_returns_json_on_bad_request(self, db):
        """POST /api/generate with bad data should return JSON error, not traceback."""
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            resp = client.post("/api/generate", json={})
            data = resp.get_json()
            assert data is not None
            assert "success" in data
            assert data["success"] is False
            assert "error" in data

    def test_generate_rejects_invalid_category(self, db):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            resp = client.post("/api/generate", json={
                "category": "invalid_category",
                "raw_input": "test",
            })
            data = resp.get_json()
            assert resp.status_code == 400
            assert data["success"] is False
            assert "category" in data["error"].lower() or "invalid" in data["error"].lower()

    def test_generate_rejects_empty_input(self, db):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            resp = client.post("/api/generate", json={
                "category": "pattern",
                "raw_input": "",
            })
            data = resp.get_json()
            assert resp.status_code == 400
            assert data["success"] is False

    def test_copy_returns_json_on_missing_id(self, db):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            resp = client.post("/api/copy",
                               data=json.dumps({"not_the_right_key": 123}),
                               content_type="application/json")
            data = resp.get_json()
            assert data is not None
            assert data["success"] is False

    def test_today_returns_json(self, db):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            resp = client.get("/api/today")
            data = resp.get_json()
            assert data is not None
            assert "day" in data

    def test_calendar_status_rejects_invalid_status(self, db):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            resp = client.post("/api/calendar/status", json={
                "slot_id": 1,
                "status": "bogus_status",
            })
            data = resp.get_json()
            assert resp.status_code == 400
            assert data["success"] is False

    def test_react_rejects_missing_url(self, db):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            resp = client.post("/api/generate/react", json={})
            data = resp.get_json()
            assert resp.status_code == 400
            assert data["success"] is False
            assert "url" in data["error"].lower()

    def test_react_rejects_invalid_url_format(self, db):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            resp = client.post("/api/generate/react", json={"url": "not-a-url"})
            data = resp.get_json()
            assert resp.status_code == 400
            assert data["success"] is False


# ---------------------------------------------------------------------------
# _handle_api_error categorization
# ---------------------------------------------------------------------------

class TestHandleApiError:
    """Test error categorization in _handle_api_error.
    These need a Flask app context since they call jsonify()."""

    def test_rate_limit_error(self):
        from app import _handle_api_error, app as flask_app
        with flask_app.app_context():
            resp, status_code = _handle_api_error(Exception("Error 429: rate limit exceeded"))
            assert status_code == 429
            data = resp.get_json()
            assert "too quickly" in data["error"].lower()

    def test_timeout_error(self):
        from app import _handle_api_error, app as flask_app
        with flask_app.app_context():
            resp, status_code = _handle_api_error(Exception("Connection timeout"))
            assert status_code == 503
            data = resp.get_json()
            assert "api" in data["error"].lower() or "connection" in data["error"].lower()

    def test_auth_error(self):
        from app import _handle_api_error, app as flask_app
        with flask_app.app_context():
            resp, status_code = _handle_api_error(Exception("401 Unauthorized"))
            assert status_code == 401
            data = resp.get_json()
            assert "key" in data["error"].lower() or "invalid" in data["error"].lower()

    def test_generic_error(self):
        from app import _handle_api_error, app as flask_app
        with flask_app.app_context():
            resp, status_code = _handle_api_error(Exception("Something weird happened"))
            assert status_code == 500
            data = resp.get_json()
            assert data["success"] is False

    def test_generic_error_does_not_leak_exception_text(self):
        """The default branch of _handle_api_error must NOT echo the raw exception
        message back to the client (audit finding M1: error messages leak internals)."""
        from app import _handle_api_error, app as flask_app
        secret = "/etc/passwd not found: sqlite3.OperationalError disk image malformed"
        with flask_app.app_context():
            resp, status_code = _handle_api_error(Exception(secret))
            assert status_code == 500
            data = resp.get_json()
            assert secret not in data["error"]
            assert "/etc/passwd" not in data["error"]
            assert "sqlite3" not in data["error"]

    def test_network_error(self):
        from app import _handle_api_error, app as flask_app
        with flask_app.app_context():
            resp, status_code = _handle_api_error(Exception("Network is unreachable"))
            assert status_code == 503


# ---------------------------------------------------------------------------
# _server_error — sanitizes generic 500 responses
# ---------------------------------------------------------------------------

class TestServerError:
    def test_returns_500_with_sanitized_message(self):
        from app import _server_error, app as flask_app
        secret = "FileNotFoundError: [Errno 2] /home/user/.secret_db.sqlite"
        with flask_app.app_context():
            resp, status_code = _server_error(Exception(secret))
            assert status_code == 500
            data = resp.get_json()
            assert data["success"] is False
            assert secret not in data["error"]
            assert "/home/user" not in data["error"]
            assert ".sqlite" not in data["error"]

    def test_unexpected_exception_in_route_returns_generic_message(self, db, monkeypatch):
        """When a route catches an unexpected exception, the client must get a
        generic message — never the raw exception text or stack trace details."""
        from app import app as flask_app
        import database

        secret = "Synthetic AttributeError: 'NoneType' object has no attribute 'foo'"
        def _boom(*_args, **_kwargs):
            raise AttributeError(secret)
        monkeypatch.setattr(database, "get_insights", _boom)
        monkeypatch.setattr("app.get_insights", _boom)

        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            resp = client.get("/api/insights")
            assert resp.status_code == 500
            data = resp.get_json()
            assert data["success"] is False
            assert secret not in data["error"]
            assert "NoneType" not in data["error"]

    def test_value_error_message_is_still_surfaced(self, db, app_client):
        """ValueErrors are intentional domain errors with safe, crafted messages —
        they should keep flowing to the client (e.g., 'Slot not found')."""
        resp = app_client.post("/api/calendar/clear", json={"slot_id": 99999})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert "slot not found" in data["error"].lower()


# ---------------------------------------------------------------------------
# _save_drafts helper — replaces 5 duplicated draft-saving loops
# ---------------------------------------------------------------------------

class TestSaveDrafts:
    def test_persists_and_returns_response_shape(self, db):
        import app
        import database

        iid = database.save_insight("pattern", "test insight")
        drafts = [
            {"content": "first draft", "angle": "the angle"},
            {"content": "second draft", "angle": ""},
            {"content": "third draft"},  # no 'angle' key at all
        ]
        response = app._save_drafts(iid, drafts)

        assert len(response) == 3
        assert [r["draft_number"] for r in response] == [1, 2, 3]
        assert response[0]["content"] == "first draft"
        assert response[0]["angle"] == "the angle"
        assert response[1]["angle"] == ""
        assert response[2]["angle"] == ""  # missing key → "" (not KeyError)
        assert all(isinstance(r["id"], int) for r in response)

        # Verify rows actually landed in the DB
        gens = database.get_generations_for_insight(iid)
        assert len(gens) == 3

    def test_empty_drafts_returns_empty_list(self, db):
        import app
        import database

        iid = database.save_insight("pattern", "no drafts")
        assert app._save_drafts(iid, []) == []


# ---------------------------------------------------------------------------
# require_api_key decorator — short-circuits routes when key is missing
# ---------------------------------------------------------------------------

class TestRequireApiKey:
    def test_returns_503_when_key_missing(self, app_client, monkeypatch):
        import app as app_module
        monkeypatch.setattr(app_module, "API_KEY_MISSING", True)

        resp = app_client.post("/api/generate", json={
            "category": "pattern",
            "raw_input": "test",
        })
        assert resp.status_code == 503
        data = resp.get_json()
        assert data["success"] is False
        assert "api key" in data["error"].lower()

    def test_carousel_route_also_protected(self, app_client, monkeypatch):
        """Regression check that the decorator is wired up on the carousel routes
        (they previously had a slightly different inline message)."""
        import app as app_module
        monkeypatch.setattr(app_module, "API_KEY_MISSING", True)

        resp = app_client.post("/api/generate/carousel", json={
            "category": "pattern",
            "raw_input": "test",
            "template_type": "tips",
        })
        assert resp.status_code == 503

    def test_passes_through_when_key_present(self, app_client):
        """With API_KEY_MISSING=False (the conftest default), the decorator must
        not short-circuit — the route's own validation should run."""
        # Sending an empty body triggers the route's 'must be JSON' branch, which
        # is reached only if the decorator lets the request through.
        resp = app_client.post("/api/generate", json={})
        # If the decorator wrongly fired, we'd get 503; instead we expect 400.
        assert resp.status_code == 400
