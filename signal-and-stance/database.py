import os
import sqlite3
from datetime import date, datetime, timedelta

from config import CONTENT_SCHEDULE, DATABASE_PATH, SUGGESTED_TIMES


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    conn = get_connection()
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    conn.close()


def save_insight(category, raw_input, source_url=None):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO insights (category, raw_input, source_url) VALUES (?, ?, ?)",
        (category, raw_input, source_url),
    )
    insight_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return insight_id


def get_insights(unused_only=False, limit=50, offset=0):
    conn = get_connection()
    if unused_only:
        rows = conn.execute(
            "SELECT * FROM insights WHERE used = 0 ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM insights ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    # Get total count
    if unused_only:
        total = conn.execute("SELECT COUNT(*) FROM insights WHERE used = 0").fetchone()[0]
    else:
        total = conn.execute("SELECT COUNT(*) FROM insights").fetchone()[0]
    conn.close()
    return [dict(row) for row in rows], total


def mark_insight_used(insight_id):
    conn = get_connection()
    conn.execute("UPDATE insights SET used = 1 WHERE id = ?", (insight_id,))
    conn.commit()
    conn.close()


def save_generation(insight_id, draft_number, content):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO generations (insight_id, draft_number, content) VALUES (?, ?, ?)",
        (insight_id, draft_number, content),
    )
    generation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return generation_id


def get_generations_for_insight(insight_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM generations WHERE insight_id = ? ORDER BY draft_number",
        (insight_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_generation_copied(generation_id):
    conn = get_connection()
    conn.execute("UPDATE generations SET copied = 1 WHERE id = ?", (generation_id,))
    # Also mark the parent insight as used
    conn.execute(
        "UPDATE insights SET used = 1 WHERE id = (SELECT insight_id FROM generations WHERE id = ?)",
        (generation_id,),
    )
    conn.commit()
    conn.close()


def get_generation_history(limit=30):
    """Get recent generation sessions grouped by insight."""
    conn = get_connection()
    # Get recent insights that have generations
    insights = conn.execute(
        """SELECT i.id, i.category, i.raw_input, i.source_url, i.created_at, i.used
           FROM insights i
           WHERE EXISTS (SELECT 1 FROM generations g WHERE g.insight_id = i.id)
           ORDER BY i.created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()

    history = []
    for insight in insights:
        drafts = conn.execute(
            """SELECT id, draft_number, content, copied, created_at
               FROM generations
               WHERE insight_id = ?
               ORDER BY draft_number""",
            (insight["id"],),
        ).fetchall()

        history.append({
            "insight_id": insight["id"],
            "category": insight["category"],
            "raw_input": insight["raw_input"],
            "source_url": insight["source_url"],
            "generated_at": insight["created_at"],
            "used": insight["used"],
            "drafts": [dict(d) for d in drafts],
        })

    conn.close()
    return history


def _get_monday(start_date=None):
    """Calculate the Monday of the week containing start_date."""
    if start_date is None:
        start_date = date.today()
    elif isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)
    return start_date - timedelta(days=start_date.weekday())


def generate_week_slots(start_date=None):
    """Create calendar slots for Mon-Fri if they don't exist."""
    monday = _get_monday(start_date)
    conn = get_connection()

    existing = conn.execute(
        "SELECT COUNT(*) FROM calendar_slots WHERE slot_date BETWEEN ? AND ?",
        (monday.isoformat(), (monday + timedelta(days=4)).isoformat()),
    ).fetchone()[0]

    if existing >= 5:
        conn.close()
        return

    for day_offset in range(5):
        slot_date = monday + timedelta(days=day_offset)
        already = conn.execute(
            "SELECT id FROM calendar_slots WHERE slot_date = ?",
            (slot_date.isoformat(),),
        ).fetchone()
        if already:
            continue
        schedule = CONTENT_SCHEDULE.get(day_offset, {})
        content_type = schedule.get("type", "General")
        conn.execute(
            "INSERT INTO calendar_slots (slot_date, day_of_week, content_type) VALUES (?, ?, ?)",
            (slot_date.isoformat(), day_offset, content_type),
        )

    conn.commit()
    conn.close()


def get_week_slots(start_date=None):
    """Return 5 slot dicts for Mon-Fri with joined generation/insight data."""
    monday = _get_monday(start_date)
    friday = monday + timedelta(days=4)
    conn = get_connection()

    rows = conn.execute(
        """SELECT cs.*,
                  g.content AS draft_content,
                  g.insight_id AS draft_insight_id,
                  i.category AS insight_category,
                  i.raw_input AS insight_text
           FROM calendar_slots cs
           LEFT JOIN generations g ON cs.generation_id = g.id
           LEFT JOIN insights i ON g.insight_id = i.id
           WHERE cs.slot_date BETWEEN ? AND ?
           ORDER BY cs.slot_date""",
        (monday.isoformat(), friday.isoformat()),
    ).fetchall()

    slots = []
    for row in rows:
        d = dict(row)
        if d.get("generation_id"):
            d["draft"] = {
                "generation_id": d["generation_id"],
                "content": d.pop("draft_content"),
                "insight_id": d.pop("draft_insight_id"),
                "insight_category": d.pop("insight_category"),
                "insight_text": d.pop("insight_text"),
            }
        else:
            d.pop("draft_content", None)
            d.pop("draft_insight_id", None)
            d.pop("insight_category", None)
            d.pop("insight_text", None)
            d["draft"] = None
        slots.append(d)

    conn.close()
    return slots


def assign_draft_to_slot(slot_id, generation_id):
    """Link a generation to a slot and set status to draft_ready."""
    conn = get_connection()
    conn.execute(
        "UPDATE calendar_slots SET generation_id = ?, status = 'draft_ready', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (generation_id, slot_id),
    )
    conn.commit()
    conn.close()


# Legal status transitions
_LEGAL_TRANSITIONS = {
    "empty": {"draft_ready", "skipped"},
    "draft_ready": {"scheduled", "empty", "skipped"},
    "scheduled": {"published", "draft_ready", "skipped"},
    "published": {"skipped"},
    "skipped": {"empty"},
}


def update_slot_status(slot_id, status, scheduled_time=None, notes=None):
    """Update a slot's status after validating the transition is legal."""
    conn = get_connection()
    current = conn.execute(
        "SELECT status FROM calendar_slots WHERE id = ?", (slot_id,)
    ).fetchone()
    if not current:
        conn.close()
        raise ValueError("Slot not found")

    current_status = current["status"]
    if status not in _LEGAL_TRANSITIONS.get(current_status, set()):
        conn.close()
        raise ValueError(f"Cannot transition from '{current_status}' to '{status}'")

    conn.execute(
        """UPDATE calendar_slots
           SET status = ?, scheduled_time = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (status, scheduled_time, notes, slot_id),
    )
    conn.commit()
    conn.close()


def clear_slot(slot_id):
    """Reset a slot to empty."""
    conn = get_connection()
    conn.execute(
        """UPDATE calendar_slots
           SET status = 'empty', generation_id = NULL,
               scheduled_time = NULL, notes = NULL,
               updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (slot_id,),
    )
    conn.commit()
    conn.close()


def get_week_stats(start_date=None):
    """Return status counts for the week."""
    monday = _get_monday(start_date)
    friday = monday + timedelta(days=4)
    conn = get_connection()

    rows = conn.execute(
        """SELECT status, COUNT(*) as cnt
           FROM calendar_slots
           WHERE slot_date BETWEEN ? AND ?
           GROUP BY status""",
        (monday.isoformat(), friday.isoformat()),
    ).fetchall()

    stats = {"total": 0, "empty": 0, "draft_ready": 0, "scheduled": 0, "published": 0, "skipped": 0}
    for row in rows:
        stats[row["status"]] = row["cnt"]
        stats["total"] += row["cnt"]
    stats["filled"] = stats["draft_ready"] + stats["scheduled"] + stats["published"]
    conn.close()
    return stats


# ── Feed management ──────────────────────────────────────────────────────────

def seed_default_feeds():
    """Insert default feeds if they don't already exist (matched by URL)."""
    from feeds import DEFAULT_FEEDS

    conn = get_connection()
    for feed in DEFAULT_FEEDS:
        existing = conn.execute("SELECT id FROM feeds WHERE url = ?", (feed["url"],)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO feeds (url, name, category, weight, enabled) VALUES (?, ?, ?, ?, ?)",
                (feed["url"], feed["name"], feed["category"], feed["weight"], 1 if feed["enabled"] else 0),
            )
    conn.commit()
    conn.close()


def get_feeds(enabled_only=True):
    conn = get_connection()
    if enabled_only:
        rows = conn.execute("SELECT * FROM feeds WHERE enabled = 1 ORDER BY category, name").fetchall()
    else:
        rows = conn.execute("SELECT * FROM feeds ORDER BY category, name").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_feed(url, name, category, weight=1.0):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM feeds WHERE url = ?", (url,)).fetchone()
    if existing:
        conn.close()
        return None, "A feed with this URL already exists"
    cursor = conn.execute(
        "INSERT INTO feeds (url, name, category, weight, enabled) VALUES (?, ?, ?, ?, 1)",
        (url, name, category, weight),
    )
    feed_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return feed_id, None


def update_feed(feed_id, enabled=None, name=None, category=None, weight=None):
    conn = get_connection()
    updates = []
    params = []
    if enabled is not None:
        updates.append("enabled = ?")
        params.append(1 if enabled else 0)
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if category is not None:
        updates.append("category = ?")
        params.append(category)
    if weight is not None:
        updates.append("weight = ?")
        params.append(weight)
    if not updates:
        conn.close()
        return
    params.append(feed_id)
    conn.execute(f"UPDATE feeds SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()


def delete_feed(feed_id):
    conn = get_connection()
    conn.execute("DELETE FROM feed_articles WHERE feed_id = ?", (feed_id,))
    conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
    conn.commit()
    conn.close()


def update_feed_fetch_status(feed_id, last_fetched_at=None, last_error=None):
    conn = get_connection()
    if last_fetched_at:
        conn.execute(
            "UPDATE feeds SET last_fetched_at = ?, last_error = NULL WHERE id = ?",
            (last_fetched_at, feed_id),
        )
    if last_error:
        conn.execute(
            "UPDATE feeds SET last_error = ? WHERE id = ?",
            (last_error, feed_id),
        )
    conn.commit()
    conn.close()


# ── Article management ───────────────────────────────────────────────────────

def save_articles(feed_id, articles):
    """Bulk insert articles, skipping duplicates by URL. Returns count of new articles."""
    conn = get_connection()
    new_count = 0
    for article in articles:
        url = article.get("url", "")
        if not url:
            continue
        existing = conn.execute("SELECT id FROM feed_articles WHERE url = ?", (url,)).fetchone()
        if existing:
            continue
        conn.execute(
            """INSERT INTO feed_articles (feed_id, title, url, summary, author, published_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (feed_id, article["title"], url, article.get("summary", ""),
             article.get("author"), article.get("published_at")),
        )
        new_count += 1
    conn.commit()
    conn.close()
    return new_count


def get_recent_articles(limit=50, min_relevance=None, unused_only=True, category=None):
    conn = get_connection()
    query = """SELECT fa.*, f.name AS feed_name, f.category AS feed_category, f.weight
               FROM feed_articles fa
               JOIN feeds f ON fa.feed_id = f.id
               WHERE fa.dismissed = 0"""
    params = []

    if unused_only:
        query += " AND fa.used = 0"
    if min_relevance is not None:
        query += " AND fa.relevance_score >= ?"
        params.append(min_relevance)
    if category:
        query += " AND f.category = ?"
        params.append(category)

    query += " ORDER BY fa.published_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_article_used(article_id):
    conn = get_connection()
    conn.execute("UPDATE feed_articles SET used = 1 WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()


def mark_article_dismissed(article_id):
    conn = get_connection()
    conn.execute("UPDATE feed_articles SET dismissed = 1 WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()


def update_article_relevance(article_id, score, reason):
    conn = get_connection()
    conn.execute(
        "UPDATE feed_articles SET relevance_score = ?, relevance_reason = ? WHERE id = ?",
        (score, reason, article_id),
    )
    conn.commit()
    conn.close()


def get_article_by_id(article_id):
    conn = get_connection()
    row = conn.execute(
        """SELECT fa.*, f.name AS feed_name, f.category AS feed_category, f.weight
           FROM feed_articles fa
           JOIN feeds f ON fa.feed_id = f.id
           WHERE fa.id = ?""",
        (article_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_feed_stats():
    conn = get_connection()
    total_feeds = conn.execute("SELECT COUNT(*) FROM feeds").fetchone()[0]
    enabled_feeds = conn.execute("SELECT COUNT(*) FROM feeds WHERE enabled = 1").fetchone()[0]
    total_articles = conn.execute("SELECT COUNT(*) FROM feed_articles").fetchone()[0]
    articles_7d = conn.execute(
        "SELECT COUNT(*) FROM feed_articles WHERE fetched_at >= datetime('now', '-7 days')"
    ).fetchone()[0]
    high_relevance = conn.execute(
        "SELECT COUNT(*) FROM feed_articles WHERE relevance_score >= 0.7"
    ).fetchone()[0]
    used_count = conn.execute(
        "SELECT COUNT(*) FROM feed_articles WHERE used = 1"
    ).fetchone()[0]
    conn.close()
    return {
        "total_feeds": total_feeds,
        "enabled_feeds": enabled_feeds,
        "total_articles": total_articles,
        "articles_last_7_days": articles_7d,
        "high_relevance": high_relevance,
        "used_for_content": used_count,
    }
