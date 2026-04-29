"""Shared fixtures for SignalStance test suite.

Provides in-memory SQLite database fixtures and Flask test client fixtures
that require no external API keys or network access.
"""

import os
import sys
import sqlite3
import uuid

import pytest

# Ensure framework directory is on sys.path so imports work
_framework_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _framework_dir not in sys.path:
    sys.path.insert(0, _framework_dir)

# Auto-detect tenant directory so tests work without manually setting env var
if not os.environ.get("SIGNALSTANCE_TENANT_DIR"):
    _project_root = os.path.dirname(_framework_dir)
    _default_tenant = os.path.join(_project_root, "tenants", "dana-wang")
    if os.path.isdir(_default_tenant):
        os.environ["SIGNALSTANCE_TENANT_DIR"] = _default_tenant


@pytest.fixture()
def db(monkeypatch):
    """Create an in-memory SQLite database with the full schema applied.

    Patches get_connection in the database module so that all database
    functions operate on a shared in-memory database.

    A 'keeper' connection is held open for the lifetime of the fixture to
    prevent SQLite from destroying the in-memory database when individual
    connections close.
    """
    import config
    import database

    # Use a unique name per test to avoid cross-test contamination
    db_name = f"testdb_{uuid.uuid4().hex[:8]}"
    shared_uri = f"file:{db_name}?mode=memory&cache=shared"

    monkeypatch.setattr(config, "DATABASE_PATH", shared_uri)
    monkeypatch.setattr(database, "DATABASE_PATH", shared_uri)

    def _get_shared_connection():
        conn = sqlite3.connect(shared_uri, uri=True, timeout=30)
        conn.row_factory = sqlite3.Row
        # WAL mode is silently ignored for in-memory databases, which is fine.
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    monkeypatch.setattr(database, "get_connection", _get_shared_connection)

    # Open a keeper connection that stays alive for the test duration,
    # preventing SQLite from destroying the in-memory DB when other
    # connections close.
    keeper = sqlite3.connect(shared_uri, uri=True, timeout=30)

    # Initialize schema and run migrations through the production code path.
    database.init_db()

    yield _get_shared_connection

    keeper.close()


@pytest.fixture()
def app_client(monkeypatch, db):
    """Create a Flask test client with an in-memory database.

    Patches the API key so the app can run without external dependencies.
    Rate limiting is disabled by default — tests that exercise it should
    re-enable via `flask_app.config["RATELIMIT_ENABLED"] = True` and reset
    the limiter storage between cases.
    """
    import config

    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "test-key-not-real")

    from app import app as flask_app, limiter

    flask_app.config["TESTING"] = True
    flask_app.config["DEBUG"] = False
    flask_app.config["RATELIMIT_ENABLED"] = False
    limiter.enabled = False
    limiter.reset()

    with flask_app.test_client() as client:
        yield client
