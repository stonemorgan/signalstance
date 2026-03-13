import os
import sqlite3

from config import DATABASE_PATH


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
