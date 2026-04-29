"""Tests for framework/database.py.

Uses an in-memory SQLite database via the `db` fixture from conftest.
Covers CRUD operations, state machine transitions, foreign key enforcement,
and connection cleanup.
"""

import sqlite3
from datetime import date, timedelta

import pytest


# ---------------------------------------------------------------------------
# Schema / init_db
# ---------------------------------------------------------------------------

class TestInitDb:
    """Verify that init_db() creates all expected tables."""

    def test_tables_created(self, db):
        """init_db (via the db fixture) should create all required tables."""
        conn = db()
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            table_names = {row["name"] for row in tables}
            expected = {
                "insights",
                "generations",
                "config",
                "calendar_slots",
                "feeds",
                "feed_articles",
                "carousel_data",
            }
            assert expected.issubset(table_names), (
                f"Missing tables: {expected - table_names}"
            )
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

class TestInsights:
    def test_save_and_get_insight_roundtrip(self, db):
        """save_insight() should persist an insight that get_insights() returns."""
        import database

        insight_id = database.save_insight("pattern", "Test insight text", "https://example.com")
        assert isinstance(insight_id, int)
        assert insight_id > 0

        rows, total = database.get_insights()
        assert total == 1
        assert len(rows) == 1
        assert rows[0]["category"] == "pattern"
        assert rows[0]["raw_input"] == "Test insight text"
        assert rows[0]["source_url"] == "https://example.com"
        assert rows[0]["used"] == 0

    def test_get_insights_unused_only(self, db):
        """get_insights(unused_only=True) should filter used insights."""
        import database

        id1 = database.save_insight("faq", "used insight")
        database.mark_insight_used(id1)
        database.save_insight("faq", "unused insight")

        rows, total = database.get_insights(unused_only=True)
        assert total == 1
        assert rows[0]["raw_input"] == "unused insight"

    def test_get_insights_pagination(self, db):
        """get_insights() should respect limit and offset."""
        import database

        for i in range(5):
            database.save_insight("pattern", f"insight {i}")

        rows, total = database.get_insights(limit=2, offset=0)
        assert total == 5
        assert len(rows) == 2

        rows2, _ = database.get_insights(limit=2, offset=2)
        assert len(rows2) == 2

    def test_mark_insight_used(self, db):
        """mark_insight_used() should set used=1."""
        import database

        iid = database.save_insight("noticed", "some observation")
        database.mark_insight_used(iid)

        rows, _ = database.get_insights()
        assert rows[0]["used"] == 1


# ---------------------------------------------------------------------------
# Generations
# ---------------------------------------------------------------------------

class TestGenerations:
    def test_save_and_get_generation_roundtrip(self, db):
        """save_generation/get_generations_for_insight round-trip."""
        import database

        insight_id = database.save_insight("pattern", "test")
        gen_id = database.save_generation(insight_id, 1, "Draft content here")
        assert isinstance(gen_id, int)

        gens = database.get_generations_for_insight(insight_id)
        assert len(gens) == 1
        assert gens[0]["content"] == "Draft content here"
        assert gens[0]["draft_number"] == 1
        assert gens[0]["copied"] == 0

    def test_multiple_generations_ordered(self, db):
        """Multiple generations should be ordered by draft_number."""
        import database

        iid = database.save_insight("faq", "question")
        database.save_generation(iid, 2, "Second draft")
        database.save_generation(iid, 1, "First draft")
        database.save_generation(iid, 3, "Third draft")

        gens = database.get_generations_for_insight(iid)
        assert [g["draft_number"] for g in gens] == [1, 2, 3]

    def test_mark_generation_copied(self, db):
        """mark_generation_copied() marks both generation and parent insight."""
        import database

        iid = database.save_insight("pattern", "test")
        gid = database.save_generation(iid, 1, "content")

        database.mark_generation_copied(gid)

        gens = database.get_generations_for_insight(iid)
        assert gens[0]["copied"] == 1

        rows, _ = database.get_insights()
        assert rows[0]["used"] == 1

    def test_generation_history(self, db):
        """get_generation_history() returns insights that have generations."""
        import database

        iid = database.save_insight("noticed", "history test")
        database.save_generation(iid, 1, "draft 1")
        database.save_generation(iid, 2, "draft 2")

        history = database.get_generation_history(limit=10)
        assert len(history) == 1
        assert history[0]["insight_id"] == iid
        assert len(history[0]["drafts"]) == 2

    def test_generation_history_groups_drafts_per_insight(self, db):
        """Drafts must stay grouped under their own insight when many insights exist."""
        import database

        iid_a = database.save_insight("noticed", "insight A")
        database.save_generation(iid_a, 1, "A1")
        database.save_generation(iid_a, 2, "A2")

        iid_b = database.save_insight("pattern", "insight B")
        database.save_generation(iid_b, 1, "B1")

        iid_c = database.save_insight("hottake", "insight C with no drafts")

        history = database.get_generation_history(limit=10)
        by_id = {h["insight_id"]: h for h in history}
        assert iid_c not in by_id  # insights with no drafts are excluded
        assert [d["content"] for d in by_id[iid_a]["drafts"]] == ["A1", "A2"]
        assert [d["content"] for d in by_id[iid_b]["drafts"]] == ["B1"]

    def test_generation_history_empty(self, db):
        """No insights with drafts → empty list, no errors."""
        import database
        assert database.get_generation_history(limit=10) == []


# ---------------------------------------------------------------------------
# Calendar slots
# ---------------------------------------------------------------------------

class TestCalendarSlots:
    def _monday(self):
        """Return the Monday of a fixed test week."""
        return date(2025, 6, 2)  # A Monday

    def test_generate_week_slots_creates_5(self, db):
        """generate_week_slots() should create 5 slots for Mon-Fri."""
        import database

        monday = self._monday()
        database.generate_week_slots(monday)

        conn = db()
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM calendar_slots WHERE slot_date BETWEEN ? AND ?",
                (monday.isoformat(), (monday + timedelta(days=4)).isoformat()),
            ).fetchone()[0]
        finally:
            conn.close()
        assert count == 5

    def test_generate_week_slots_idempotent(self, db):
        """Calling generate_week_slots twice should not create duplicates."""
        import database

        monday = self._monday()
        database.generate_week_slots(monday)
        database.generate_week_slots(monday)

        conn = db()
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM calendar_slots WHERE slot_date BETWEEN ? AND ?",
                (monday.isoformat(), (monday + timedelta(days=4)).isoformat()),
            ).fetchone()[0]
        finally:
            conn.close()
        assert count == 5

    def test_get_week_slots_structure(self, db):
        """get_week_slots() returns slots with correct structure."""
        import database

        monday = self._monday()
        database.generate_week_slots(monday)

        slots = database.get_week_slots(monday)
        assert len(slots) == 5
        for slot in slots:
            assert "id" in slot
            assert "slot_date" in slot
            assert "day_of_week" in slot
            assert "status" in slot
            assert "draft" in slot
            assert slot["status"] == "empty"
            assert slot["draft"] is None

    def test_assign_draft_to_empty_slot(self, db):
        """assign_draft_to_slot() should work for empty slots."""
        import database

        monday = self._monday()
        database.generate_week_slots(monday)
        slots = database.get_week_slots(monday)
        slot_id = slots[0]["id"]

        iid = database.save_insight("pattern", "test")
        gid = database.save_generation(iid, 1, "draft content")

        database.assign_draft_to_slot(slot_id, gid)

        updated = database.get_week_slots(monday)
        assert updated[0]["status"] == "draft_ready"
        assert updated[0]["draft"] is not None
        assert updated[0]["draft"]["generation_id"] == gid

    def test_assign_draft_to_draft_ready_slot(self, db):
        """assign_draft_to_slot() should work for draft_ready slots (replace draft)."""
        import database

        monday = self._monday()
        database.generate_week_slots(monday)
        slots = database.get_week_slots(monday)
        slot_id = slots[0]["id"]

        iid = database.save_insight("pattern", "test")
        gid1 = database.save_generation(iid, 1, "first draft")
        gid2 = database.save_generation(iid, 2, "second draft")

        database.assign_draft_to_slot(slot_id, gid1)
        database.assign_draft_to_slot(slot_id, gid2)

        updated = database.get_week_slots(monday)
        assert updated[0]["draft"]["generation_id"] == gid2

    def test_assign_draft_to_published_slot_raises(self, db):
        """assign_draft_to_slot() should raise ValueError for published slots."""
        import database

        monday = self._monday()
        database.generate_week_slots(monday)
        slots = database.get_week_slots(monday)
        slot_id = slots[0]["id"]

        iid = database.save_insight("pattern", "test")
        gid = database.save_generation(iid, 1, "draft")

        database.assign_draft_to_slot(slot_id, gid)
        database.update_slot_status(slot_id, "scheduled")
        database.update_slot_status(slot_id, "published")

        gid2 = database.save_generation(iid, 2, "another draft")
        with pytest.raises(ValueError, match="Cannot assign draft"):
            database.assign_draft_to_slot(slot_id, gid2)

    def test_assign_draft_to_scheduled_slot_raises(self, db):
        """assign_draft_to_slot() should raise ValueError for scheduled slots."""
        import database

        monday = self._monday()
        database.generate_week_slots(monday)
        slots = database.get_week_slots(monday)
        slot_id = slots[0]["id"]

        iid = database.save_insight("pattern", "test")
        gid = database.save_generation(iid, 1, "draft")

        database.assign_draft_to_slot(slot_id, gid)
        database.update_slot_status(slot_id, "scheduled")

        gid2 = database.save_generation(iid, 2, "another")
        with pytest.raises(ValueError, match="Cannot assign draft"):
            database.assign_draft_to_slot(slot_id, gid2)

    def test_clear_slot_works_for_draft_ready(self, db):
        """clear_slot() should reset a draft_ready slot to empty."""
        import database

        monday = self._monday()
        database.generate_week_slots(monday)
        slots = database.get_week_slots(monday)
        slot_id = slots[0]["id"]

        iid = database.save_insight("pattern", "test")
        gid = database.save_generation(iid, 1, "draft")
        database.assign_draft_to_slot(slot_id, gid)

        database.clear_slot(slot_id)

        updated = database.get_week_slots(monday)
        assert updated[0]["status"] == "empty"
        assert updated[0]["draft"] is None

    def test_clear_published_slot_raises(self, db):
        """clear_slot() should raise ValueError for published slots."""
        import database

        monday = self._monday()
        database.generate_week_slots(monday)
        slots = database.get_week_slots(monday)
        slot_id = slots[0]["id"]

        iid = database.save_insight("pattern", "test")
        gid = database.save_generation(iid, 1, "draft")
        database.assign_draft_to_slot(slot_id, gid)
        database.update_slot_status(slot_id, "scheduled")
        database.update_slot_status(slot_id, "published")

        with pytest.raises(ValueError, match="Cannot clear a published slot"):
            database.clear_slot(slot_id)


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------

class TestStatusTransitions:
    def _create_slot(self, db):
        import database
        monday = date(2025, 7, 7)
        database.generate_week_slots(monday)
        slots = database.get_week_slots(monday)
        slot_id = slots[0]["id"]
        # Put a draft on it so transitions are meaningful
        iid = database.save_insight("faq", "question")
        gid = database.save_generation(iid, 1, "content")
        database.assign_draft_to_slot(slot_id, gid)
        return slot_id

    def test_legal_transition_draft_ready_to_scheduled(self, db):
        import database
        sid = self._create_slot(db)
        database.update_slot_status(sid, "scheduled", scheduled_time="9:00 AM")
        conn = db()
        try:
            row = conn.execute("SELECT status FROM calendar_slots WHERE id = ?", (sid,)).fetchone()
        finally:
            conn.close()
        assert row["status"] == "scheduled"

    def test_legal_transition_scheduled_to_published(self, db):
        import database
        sid = self._create_slot(db)
        database.update_slot_status(sid, "scheduled")
        database.update_slot_status(sid, "published")
        conn = db()
        try:
            row = conn.execute("SELECT status FROM calendar_slots WHERE id = ?", (sid,)).fetchone()
        finally:
            conn.close()
        assert row["status"] == "published"

    def test_illegal_transition_empty_to_published(self, db):
        """Cannot go directly from empty to published."""
        import database
        monday = date(2025, 7, 14)
        database.generate_week_slots(monday)
        slots = database.get_week_slots(monday)
        sid = slots[0]["id"]

        with pytest.raises(ValueError, match="Cannot transition"):
            database.update_slot_status(sid, "published")

    def test_illegal_transition_empty_to_scheduled(self, db):
        """Cannot go directly from empty to scheduled."""
        import database
        monday = date(2025, 7, 21)
        database.generate_week_slots(monday)
        slots = database.get_week_slots(monday)
        sid = slots[0]["id"]

        with pytest.raises(ValueError, match="Cannot transition"):
            database.update_slot_status(sid, "scheduled")

    def test_legal_transition_skipped_to_empty(self, db):
        import database
        monday = date(2025, 7, 28)
        database.generate_week_slots(monday)
        slots = database.get_week_slots(monday)
        sid = slots[0]["id"]

        database.update_slot_status(sid, "skipped")
        database.update_slot_status(sid, "empty")
        conn = db()
        try:
            row = conn.execute("SELECT status FROM calendar_slots WHERE id = ?", (sid,)).fetchone()
        finally:
            conn.close()
        assert row["status"] == "empty"

    def test_published_to_empty_illegal(self, db):
        """published -> empty is not legal."""
        import database
        sid = self._create_slot(db)
        database.update_slot_status(sid, "scheduled")
        database.update_slot_status(sid, "published")

        with pytest.raises(ValueError, match="Cannot transition"):
            database.update_slot_status(sid, "empty")

    def test_slot_not_found_raises(self, db):
        """Updating a non-existent slot raises ValueError."""
        import database
        with pytest.raises(ValueError, match="Slot not found"):
            database.update_slot_status(99999, "empty")


# ---------------------------------------------------------------------------
# Feeds CRUD
# ---------------------------------------------------------------------------

class TestFeeds:
    def test_add_and_get_feed(self, db):
        import database

        feed_id, error = database.add_feed(
            "https://example.com/feed.xml", "Example Feed", "careers", 1.0
        )
        assert feed_id is not None
        assert error is None

        feeds = database.get_feeds(enabled_only=True)
        assert len(feeds) == 1
        assert feeds[0]["name"] == "Example Feed"
        assert feeds[0]["url"] == "https://example.com/feed.xml"

    def test_add_duplicate_feed_url(self, db):
        import database

        database.add_feed("https://example.com/rss", "Feed A", "careers")
        feed_id, error = database.add_feed("https://example.com/rss", "Feed B", "tech")
        assert feed_id is None
        assert "already exists" in error

    def test_update_feed(self, db):
        import database

        fid, _ = database.add_feed("https://test.com/feed", "Original", "careers")
        database.update_feed(fid, name="Updated Name", category="leadership", weight=2.0)

        feeds = database.get_feeds(enabled_only=True)
        assert feeds[0]["name"] == "Updated Name"
        assert feeds[0]["category"] == "leadership"
        assert feeds[0]["weight"] == 2.0

    def test_update_feed_enable_disable(self, db):
        import database

        fid, _ = database.add_feed("https://test.com/feed2", "Test", "careers")
        database.update_feed(fid, enabled=False)

        feeds_enabled = database.get_feeds(enabled_only=True)
        assert len(feeds_enabled) == 0

        feeds_all = database.get_feeds(enabled_only=False)
        assert len(feeds_all) == 1

    def test_delete_feed(self, db):
        import database

        fid, _ = database.add_feed("https://del.com/feed", "Delete Me", "careers")
        database.delete_feed(fid)

        feeds = database.get_feeds(enabled_only=False)
        assert len(feeds) == 0

    def test_get_feeds_with_article_counts(self, db):
        """Each feed gets an article_count via JOIN — feeds with no articles return 0."""
        import database

        fid_a, _ = database.add_feed("https://a.com/feed", "Feed A", "careers")
        fid_b, _ = database.add_feed("https://b.com/feed", "Feed B", "leadership")
        # Feed A has 2 articles; Feed B has none.
        database.save_articles(fid_a, [
            {"title": "T1", "url": "https://a.com/1", "summary": "s"},
            {"title": "T2", "url": "https://a.com/2", "summary": "s"},
        ])

        feeds = database.get_feeds_with_article_counts(enabled_only=False)
        by_id = {f["id"]: f for f in feeds}
        assert by_id[fid_a]["article_count"] == 2
        assert by_id[fid_b]["article_count"] == 0

    def test_get_feeds_with_article_counts_respects_enabled_filter(self, db):
        import database

        fid_on, _ = database.add_feed("https://on.com/feed", "On", "careers")
        fid_off, _ = database.add_feed("https://off.com/feed", "Off", "careers")
        database.update_feed(fid_off, enabled=False)

        enabled = database.get_feeds_with_article_counts(enabled_only=True)
        all_feeds = database.get_feeds_with_article_counts(enabled_only=False)
        assert {f["id"] for f in enabled} == {fid_on}
        assert {f["id"] for f in all_feeds} == {fid_on, fid_off}


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------

class TestArticles:
    def test_save_articles_and_dedup(self, db):
        """save_articles() should insert new articles and skip duplicates by URL."""
        import database

        fid, _ = database.add_feed("https://feed.com/rss", "Test Feed", "careers")

        articles = [
            {"title": "Article 1", "url": "https://example.com/1", "summary": "summary 1"},
            {"title": "Article 2", "url": "https://example.com/2", "summary": "summary 2"},
        ]
        new_count = database.save_articles(fid, articles)
        assert new_count == 2

        # Insert again -- duplicates should be skipped
        new_count2 = database.save_articles(fid, articles)
        assert new_count2 == 0

    def test_save_articles_skips_empty_url(self, db):
        import database

        fid, _ = database.add_feed("https://feed2.com/rss", "Feed2", "careers")
        articles = [
            {"title": "No URL", "url": "", "summary": "x"},
            {"title": "Has URL", "url": "https://example.com/3", "summary": "y"},
        ]
        new_count = database.save_articles(fid, articles)
        assert new_count == 1

    def test_save_articles_with_mixed_new_and_dupe(self, db):
        """save_articles with some new and some duplicate URLs."""
        import database

        fid, _ = database.add_feed("https://feed3.com/rss", "Feed3", "careers")
        batch1 = [
            {"title": "A", "url": "https://example.com/a"},
        ]
        database.save_articles(fid, batch1)

        batch2 = [
            {"title": "A dupe", "url": "https://example.com/a"},
            {"title": "B new", "url": "https://example.com/b"},
        ]
        count = database.save_articles(fid, batch2)
        assert count == 1


# ---------------------------------------------------------------------------
# Foreign key enforcement
# ---------------------------------------------------------------------------

class TestForeignKeys:
    def test_fk_generation_requires_valid_insight(self, db):
        """Inserting a generation with a non-existent insight_id should fail
        because foreign keys are enforced."""
        conn = db()
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO generations (insight_id, draft_number, content) VALUES (?, ?, ?)",
                    (99999, 1, "orphan"),
                )
                conn.commit()
        finally:
            conn.close()

    def test_fk_feed_article_requires_valid_feed(self, db):
        """Inserting a feed_article with a non-existent feed_id should fail."""
        conn = db()
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO feed_articles (feed_id, title, url) VALUES (?, ?, ?)",
                    (99999, "orphan", "https://orphan.com"),
                )
                conn.commit()
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Connection cleanup
# ---------------------------------------------------------------------------

class TestConnectionCleanup:
    def test_connections_close_after_operations(self, db):
        """Verify that database functions don't leak connections.
        We test this indirectly by running many operations and confirming
        no errors occur (connection pool exhaustion would fail)."""
        import database

        for i in range(20):
            iid = database.save_insight("pattern", f"insight {i}")
            database.save_generation(iid, 1, f"draft {i}")

        rows, total = database.get_insights(limit=100)
        assert total == 20

    def test_get_connection_returns_row_factory(self, db):
        """get_connection() should return connections with Row factory."""
        import database
        conn = database.get_connection()
        try:
            assert conn.row_factory == sqlite3.Row
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Carousel data
# ---------------------------------------------------------------------------

class TestCarouselData:
    def test_save_and_get_carousel_data(self, db):
        import database

        iid = database.save_insight("pattern", "carousel test")
        gid = database.save_generation(iid, 1, "Carousel Title")

        parsed = {"title": "Test Title", "slides": [{"number": 1, "headline": "H", "body": "B"}]}
        database.save_carousel_data(gid, "tips", parsed, "carousel_1.pdf", 3)

        result = database.get_carousel_data(gid)
        assert result is not None
        assert result["template_type"] == "tips"
        assert result["slide_count"] == 3
        assert result["parsed_content"]["title"] == "Test Title"

    def test_get_carousel_data_not_found(self, db):
        import database
        result = database.get_carousel_data(99999)
        assert result is None

    def test_get_carousel_data_for_generations_batch(self, db):
        """Batch helper returns a dict keyed by generation_id, parsed_content decoded."""
        import database

        iid = database.save_insight("pattern", "batch test")
        gid_a = database.save_generation(iid, 1, "draft a")
        gid_b = database.save_generation(iid, 2, "draft b")
        gid_c = database.save_generation(iid, 3, "draft c (no carousel)")

        database.save_carousel_data(gid_a, "tips", {"title": "A"}, "a.pdf", 5)
        database.save_carousel_data(gid_b, "beforeafter", {"title": "B"}, "b.pdf", 4)

        result = database.get_carousel_data_for_generations([gid_a, gid_b, gid_c])
        assert set(result.keys()) == {gid_a, gid_b}
        assert result[gid_a]["parsed_content"]["title"] == "A"
        assert result[gid_b]["template_type"] == "beforeafter"

    def test_get_carousel_data_for_generations_empty(self, db):
        """Empty input must short-circuit to {} without opening a connection."""
        import database
        assert database.get_carousel_data_for_generations([]) == {}


# ---------------------------------------------------------------------------
# Week stats
# ---------------------------------------------------------------------------

class TestWeekStats:
    def test_week_stats_counts(self, db):
        import database

        monday = date(2025, 8, 4)
        database.generate_week_slots(monday)

        stats = database.get_week_stats(monday)
        assert stats["total"] == 5
        assert stats["empty"] == 5
        assert stats["filled"] == 0
