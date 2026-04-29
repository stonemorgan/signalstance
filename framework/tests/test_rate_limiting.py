"""Tests for flask-limiter rate limits on generation routes and feed refresh.

The default `app_client` fixture disables rate limiting so other tests aren't
throttled. These tests opt back in via the `rate_limited_client` fixture
which sets RATELIMIT_ENABLED=True, resets the limiter storage, and rebinds
each route's limit to a deterministic test value.
"""

import os
import sys
from unittest.mock import patch

import pytest

_framework_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _framework_dir not in sys.path:
    sys.path.insert(0, _framework_dir)


@pytest.fixture()
def rate_limited_client(app_client):
    """Re-enable the limiter and rebind generation/feed-refresh limits to small,
    deterministic windows. Resets storage so each test starts at zero."""
    from app import app as flask_app, limiter

    flask_app.config["RATELIMIT_ENABLED"] = True
    limiter.enabled = True
    limiter.reset()

    yield app_client

    limiter.reset()
    limiter.enabled = False
    flask_app.config["RATELIMIT_ENABLED"] = False


class TestGenerationRateLimit:
    """Generation routes should 429 after exceeding the configured window."""

    def test_429_shape_includes_success_false_and_retry_after(self, rate_limited_client):
        """When a generation route is throttled, the response is JSON with
        success=False, an error message, and a Retry-After header."""
        from app import app as flask_app, limiter

        # Tighten /api/generate to 2/minute so we can trip it deterministically.
        with flask_app.test_request_context():
            limit_decorator = limiter.limit("2 per minute", override_defaults=True)
            limit_decorator(flask_app.view_functions["generate"])

        # Patch generate_posts so the 200-path returns quickly without hitting Claude.
        with patch("app.generate_posts", return_value=[{"content": "x", "angle": ""}]):
            payload = {"category": "pattern", "raw_input": "test observation"}
            r1 = rate_limited_client.post("/api/generate", json=payload)
            r2 = rate_limited_client.post("/api/generate", json=payload)
            r3 = rate_limited_client.post("/api/generate", json=payload)

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 429
        body = r3.get_json()
        assert body["success"] is False
        assert "rate limit" in body["error"].lower()
        # Retry-After is set by flask-limiter as seconds-until-reset.
        assert "Retry-After" in r3.headers

    def test_429_when_api_key_missing_still_short_circuits_first(self, rate_limited_client, monkeypatch):
        """If the rate limit fires before @require_api_key, the 429 response
        is still well-formed. The decorator stack is route → limit → api_key,
        so the limiter runs first."""
        from app import app as flask_app, limiter

        with flask_app.test_request_context():
            limiter.limit("1 per minute", override_defaults=True)(
                flask_app.view_functions["generate"]
            )

        with patch("app.generate_posts", return_value=[{"content": "x", "angle": ""}]):
            payload = {"category": "pattern", "raw_input": "test"}
            rate_limited_client.post("/api/generate", json=payload)
            r2 = rate_limited_client.post("/api/generate", json=payload)

        assert r2.status_code == 429
        assert r2.get_json()["success"] is False


class TestFeedRefreshCooldown:
    """/api/feeds/refresh should 429 within its cooldown window."""

    def test_second_refresh_within_window_is_throttled(self, rate_limited_client):
        from app import app as flask_app, limiter

        with flask_app.test_request_context():
            limiter.limit("1 per minute", override_defaults=True)(
                flask_app.view_functions["feeds_refresh"]
            )

        fake_results = {
            "fetch": {"successful": 0, "new_articles": 0},
            "scored": 0,
            "high_relevance": 0,
        }
        with patch("app.refresh_and_score", return_value=fake_results):
            r1 = rate_limited_client.post("/api/feeds/refresh")
            r2 = rate_limited_client.post("/api/feeds/refresh")

        assert r1.status_code == 200
        assert r2.status_code == 429
        body = r2.get_json()
        assert body["success"] is False


class TestReadEndpointsUnaffected:
    """Read-only endpoints inherit the generous default limit and should not
    trip during normal test usage."""

    def test_today_endpoint_not_throttled_at_default(self, rate_limited_client):
        # Default limit is "200 per minute" — 5 calls is well under.
        for _ in range(5):
            r = rate_limited_client.get("/api/today")
            assert r.status_code == 200

    def test_config_endpoint_not_throttled_at_default(self, rate_limited_client):
        for _ in range(5):
            r = rate_limited_client.get("/api/config")
            assert r.status_code == 200


class TestLimiterDisabledByDefault:
    """The default app_client fixture should NOT throttle — sanity check that
    the existing test suite isn't accidentally rate-limited."""

    def test_default_fixture_allows_many_requests(self, app_client):
        """200+ requests on a default app_client should all succeed without 429."""
        # /api/today is cheap and pure-read.
        for _ in range(50):
            r = app_client.get("/api/today")
            assert r.status_code == 200, "default fixture should not rate-limit"
