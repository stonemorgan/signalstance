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
                "insight_category": d.pop("insight_category"),
                "insight_text": d.pop("insight_text"),
            }
        else:
            d.pop("draft_content", None)
            d.pop("insight_category", None)
            d.pop("insight_text", None)
            d["draft"] = None
        d.pop("draft_insight_id", None)
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
