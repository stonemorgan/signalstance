"""Tests for the schema migration system in database.py.

Covers:
- Fresh DBs are stamped at the latest user_version (no migrations run on
  empty new files).
- Legacy DBs at user_version=0 get all migrations applied in order.
- Re-running migrations on an up-to-date DB is a no-op.
- After migration 0001, the schema actually exhibits ON DELETE CASCADE
  / SET NULL behavior on FK references.
"""

import os
import sqlite3
import tempfile

import pytest


_LEGACY_SCHEMA = """
CREATE TABLE insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    raw_input TEXT NOT NULL,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used INTEGER DEFAULT 0
);
CREATE TABLE generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id INTEGER NOT NULL,
    draft_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    copied INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insight_id) REFERENCES insights(id)
);
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE calendar_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_date DATE NOT NULL,
    day_of_week INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    generation_id INTEGER,
    status TEXT NOT NULL DEFAULT 'empty',
    scheduled_time TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generation_id) REFERENCES generations(id)
);
CREATE TABLE feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_fetched_at TIMESTAMP,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE feed_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    summary TEXT,
    author TEXT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    relevance_score REAL,
    relevance_reason TEXT,
    used INTEGER DEFAULT 0,
    dismissed INTEGER DEFAULT 0,
    FOREIGN KEY (feed_id) REFERENCES feeds(id)
);
CREATE TABLE carousel_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation_id INTEGER NOT NULL UNIQUE,
    template_type TEXT NOT NULL,
    parsed_content TEXT NOT NULL,
    pdf_filename TEXT,
    slide_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generation_id) REFERENCES generations(id)
);
"""


@pytest.fixture()
def tmp_db_path():
    """A temp file path for a SQLite DB. Cleans up on teardown."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)  # let SQLite create it fresh
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture()
def isolated_database(monkeypatch, tmp_db_path):
    """Patch DATABASE_PATH on both modules so init_db() targets a temp file."""
    import config
    import database

    monkeypatch.setattr(config, "DATABASE_PATH", tmp_db_path)
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_db_path)
    return database


def _latest_migration_version():
    import database
    migs = database._discover_migrations()
    return migs[-1][0] if migs else 0


def test_fresh_db_stamps_latest_user_version(isolated_database):
    """A brand-new DB should end up at the latest migration version
    without running any migrations (schema.sql already represents v1+)."""
    isolated_database.init_db()
    conn = isolated_database.get_connection()
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == _latest_migration_version()
    finally:
        conn.close()


def test_fresh_db_has_cascade_in_ddl(isolated_database):
    isolated_database.init_db()
    conn = isolated_database.get_connection()
    try:
        ddl = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name='generations'"
        ).fetchone()[0]
        assert "CASCADE" in ddl
    finally:
        conn.close()


def test_legacy_db_gets_migrated(isolated_database, tmp_db_path):
    """A pre-existing DB at user_version=0 with the old schema should be
    upgraded to the latest version with data preserved."""
    legacy = sqlite3.connect(tmp_db_path)
    legacy.executescript(_LEGACY_SCHEMA)
    legacy.execute(
        "INSERT INTO insights (id, category, raw_input) VALUES (1, 'pattern', 'kept')"
    )
    legacy.execute(
        "INSERT INTO generations (id, insight_id, draft_number, content) "
        "VALUES (10, 1, 1, 'draft kept')"
    )
    legacy.commit()
    assert legacy.execute("PRAGMA user_version").fetchone()[0] == 0
    legacy.close()

    isolated_database.init_db()

    conn = isolated_database.get_connection()
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == _latest_migration_version()
        # Data must survive the table-recreate
        assert conn.execute("SELECT raw_input FROM insights WHERE id=1").fetchone()[0] == "kept"
        assert conn.execute("SELECT content FROM generations WHERE id=10").fetchone()[0] == "draft kept"
        # New schema must have CASCADE
        ddl = conn.execute("SELECT sql FROM sqlite_master WHERE name='generations'").fetchone()[0]
        assert "CASCADE" in ddl
    finally:
        conn.close()


def test_rerunning_init_db_is_idempotent(isolated_database):
    """Calling init_db() twice should not change user_version or break anything."""
    isolated_database.init_db()
    conn = isolated_database.get_connection()
    try:
        v1 = conn.execute("PRAGMA user_version").fetchone()[0]
    finally:
        conn.close()

    isolated_database.init_db()
    conn = isolated_database.get_connection()
    try:
        v2 = conn.execute("PRAGMA user_version").fetchone()[0]
    finally:
        conn.close()

    assert v1 == v2 == _latest_migration_version()


def test_cascade_delete_removes_generations(isolated_database):
    """After migration 0001, deleting an insight should cascade to generations."""
    isolated_database.init_db()
    conn = isolated_database.get_connection()
    try:
        conn.execute("INSERT INTO insights (id, category, raw_input) VALUES (1, 'pattern', 'x')")
        conn.execute(
            "INSERT INTO generations (id, insight_id, draft_number, content) "
            "VALUES (10, 1, 1, 'draft')"
        )
        conn.commit()
        conn.execute("DELETE FROM insights WHERE id=1")
        conn.commit()
        remaining = conn.execute("SELECT COUNT(*) FROM generations WHERE id=10").fetchone()[0]
        assert remaining == 0
    finally:
        conn.close()


def test_cascade_delete_removes_feed_articles(isolated_database):
    """Deleting a feed should cascade to its articles."""
    isolated_database.init_db()
    conn = isolated_database.get_connection()
    try:
        conn.execute(
            "INSERT INTO feeds (id, url, name, category) "
            "VALUES (1, 'https://example.com/feed', 'Example', 'industry')"
        )
        conn.execute(
            "INSERT INTO feed_articles (id, feed_id, title, url) "
            "VALUES (100, 1, 'Article', 'https://example.com/a')"
        )
        conn.commit()
        conn.execute("DELETE FROM feeds WHERE id=1")
        conn.commit()
        remaining = conn.execute("SELECT COUNT(*) FROM feed_articles WHERE id=100").fetchone()[0]
        assert remaining == 0
    finally:
        conn.close()


def test_set_null_unlinks_calendar_slot(isolated_database):
    """Deleting a generation should null out the slot's generation_id, not
    delete the slot."""
    isolated_database.init_db()
    conn = isolated_database.get_connection()
    try:
        conn.execute("INSERT INTO insights (id, category, raw_input) VALUES (1, 'pattern', 'x')")
        conn.execute(
            "INSERT INTO generations (id, insight_id, draft_number, content) "
            "VALUES (10, 1, 1, 'draft')"
        )
        conn.execute(
            "INSERT INTO calendar_slots "
            "(id, slot_date, day_of_week, content_type, generation_id, status) "
            "VALUES (50, '2026-05-01', 4, 'tip', 10, 'draft_ready')"
        )
        conn.commit()
        conn.execute("DELETE FROM generations WHERE id=10")
        conn.commit()
        slot = conn.execute(
            "SELECT id, generation_id FROM calendar_slots WHERE id=50"
        ).fetchone()
        assert slot is not None, "slot should still exist after generation delete"
        assert slot["generation_id"] is None
    finally:
        conn.close()


def test_discover_migrations_sorted_and_filtered():
    """_discover_migrations should return migrations in version order and
    skip non-migration files."""
    import database
    migs = database._discover_migrations()
    versions = [v for v, _ in migs]
    assert versions == sorted(versions)
    # Every entry must be (int, existing-file)
    for v, path in migs:
        assert isinstance(v, int)
        assert os.path.exists(path)
