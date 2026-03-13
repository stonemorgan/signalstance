import sqlite3
from config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    with open("schema.sql", "r") as f:
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


def get_insights(limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM insights ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


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


def get_generation_history(limit=50):
    conn = get_connection()
    rows = conn.execute(
        """SELECT g.id, g.insight_id, g.draft_number, g.content, g.copied, g.created_at,
                  i.category, i.raw_input
           FROM generations g
           JOIN insights i ON g.insight_id = i.id
           ORDER BY g.created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
