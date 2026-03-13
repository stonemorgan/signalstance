import re
from datetime import date, datetime, timedelta

from flask import Flask, jsonify, render_template, request

from config import ANTHROPIC_API_KEY, CONTENT_SCHEDULE, FLASK_PORT, SUGGESTED_TIMES
from database import (
    assign_draft_to_slot,
    clear_slot,
    generate_week_slots,
    get_generation_history,
    get_insights,
    get_week_slots,
    get_week_stats,
    init_db,
    mark_generation_copied,
    save_generation,
    save_insight,
    update_slot_status,
)
from engine import generate_autopilot, generate_from_url, generate_posts

app = Flask(__name__)

VALID_CATEGORIES = {"pattern", "faq", "noticed", "hottake", "autopilot", "url_react"}
API_KEY_MISSING = not ANTHROPIC_API_KEY


@app.route("/")
def index():
    try:
        return render_template("index.html", api_key_missing=API_KEY_MISSING)
    except Exception:
        return "Signal & Stance is running."


@app.route("/api/generate", methods=["POST"])
def generate():
    if API_KEY_MISSING:
        return jsonify({"success": False, "error": "API key not configured. See setup instructions."}), 503

    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Request body must be JSON"}), 400

        category = data.get("category", "").strip()
        raw_input_text = data.get("raw_input", "").strip()

        if category not in {"pattern", "faq", "noticed", "hottake"}:
            return jsonify({
                "success": False,
                "error": "Invalid category. Must be one of: pattern, faq, noticed, hottake",
            }), 400

        if not raw_input_text:
            return jsonify({"success": False, "error": "raw_input is required"}), 400

        source_url = data.get("source_url")

        # Generate drafts via the Anthropic API
        drafts = generate_posts(category, raw_input_text, source_url)

        # Save insight
        insight_id = save_insight(category, raw_input_text, source_url)

        # Save drafts and build response
        drafts_response = []
        for i, draft in enumerate(drafts, start=1):
            gen_id = save_generation(insight_id, i, draft["content"])
            drafts_response.append({
                "id": gen_id,
                "draft_number": i,
                "content": draft["content"],
                "angle": draft["angle"],
            })

        response = {"success": True, "insight_id": insight_id, "drafts": drafts_response}

        for_slot_id = data.get("for_slot_id")
        if for_slot_id:
            from database import get_connection
            conn = get_connection()
            slot = conn.execute(
                "SELECT id, slot_date, day_of_week FROM calendar_slots WHERE id = ?",
                (for_slot_id,),
            ).fetchone()
            conn.close()
            if slot:
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                response["for_slot"] = {
                    "slot_id": slot["id"],
                    "day_name": day_names[slot["day_of_week"]],
                    "date": slot["slot_date"],
                }

        return jsonify(response)

    except Exception as e:
        return _handle_api_error(e)


@app.route("/api/generate/autopilot", methods=["POST"])
def generate_autopilot_route():
    if API_KEY_MISSING:
        return jsonify({"success": False, "error": "API key not configured. See setup instructions."}), 503

    try:
        drafts, source_info = generate_autopilot()

        # Handle "nothing found" case
        if drafts is None:
            if source_info.get("nothing_found"):
                return jsonify({
                    "success": True,
                    "nothing_found": True,
                    "source_summary": source_info["source_summary"],
                })
            # URL error or other issue
            return jsonify({
                "success": False,
                "error": source_info.get("source_summary", "Could not generate autopilot content."),
            }), 400

        # Determine category from source info (default to 'noticed')
        category = source_info.get("category", "noticed")
        if category not in VALID_CATEGORIES:
            category = "autopilot"

        # Save insight
        raw_input_text = source_info.get("insight") or source_info.get("source_summary", "auto-generated")
        source_url = source_info.get("source_url")
        insight_id = save_insight("autopilot", raw_input_text, source_url)

        # Save drafts and build response
        drafts_response = []
        for i, draft in enumerate(drafts, start=1):
            gen_id = save_generation(insight_id, i, draft["content"])
            drafts_response.append({
                "id": gen_id,
                "draft_number": i,
                "content": draft["content"],
                "angle": draft["angle"],
            })

        return jsonify({
            "success": True,
            "insight_id": insight_id,
            "source_summary": source_info.get("source_summary", ""),
            "source_url": source_url,
            "drafts": drafts_response,
        })

    except Exception as e:
        return _handle_api_error(e)


@app.route("/api/generate/react", methods=["POST"])
def generate_react_route():
    if API_KEY_MISSING:
        return jsonify({"success": False, "error": "API key not configured. See setup instructions."}), 503

    try:
        data = request.get_json(silent=True) or {}

        url = data.get("url", "").strip()
        if not url:
            return jsonify({"success": False, "error": "URL is required"}), 400

        # Basic URL validation
        if not re.match(r"^https?://\S+", url):
            return jsonify({"success": False, "error": "Please enter a valid URL starting with http:// or https://"}), 400

        drafts, source_info = generate_from_url(url)

        # Handle URL error case
        if drafts is None:
            error_msg = source_info.get("source_summary", "Could not read that URL.")
            if source_info.get("url_error"):
                error_msg = "Couldn't read that URL. It may be behind a paywall or unavailable. Try pasting the article text into the observation field instead."
            return jsonify({"success": False, "error": error_msg}), 400

        # Save insight
        raw_input_text = source_info.get("source_summary", url)
        insight_id = save_insight("url_react", raw_input_text, url)

        # Save drafts and build response
        drafts_response = []
        for i, draft in enumerate(drafts, start=1):
            gen_id = save_generation(insight_id, i, draft["content"])
            drafts_response.append({
                "id": gen_id,
                "draft_number": i,
                "content": draft["content"],
                "angle": draft["angle"],
            })

        return jsonify({
            "success": True,
            "insight_id": insight_id,
            "source_summary": source_info.get("source_summary", ""),
            "source_url": url,
            "drafts": drafts_response,
        })

    except Exception as e:
        return _handle_api_error(e)


@app.route("/api/copy", methods=["POST"])
def copy():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Request body must be JSON"}), 400

        generation_id = data.get("generation_id")
        if generation_id is None:
            return jsonify({"success": False, "error": "generation_id is required"}), 400

        mark_generation_copied(generation_id)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/today")
def today():
    try:
        weekday = datetime.today().weekday()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if weekday in CONTENT_SCHEDULE:
            schedule = CONTENT_SCHEDULE[weekday]
            return jsonify({
                "day": day_names[weekday],
                "type": schedule["type"],
                "suggestion": schedule["suggestion"],
            })
        else:
            return jsonify({
                "day": day_names[weekday],
                "type": "Weekend",
                "suggestion": "No content scheduled for weekends. Rest up or bank insights for next week.",
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/insights")
def insights():
    try:
        unused_only = request.args.get("unused", "").lower() == "true"
        limit = min(int(request.args.get("limit", 50)), 100)
        offset = int(request.args.get("offset", 0))
        rows, total = get_insights(unused_only=unused_only, limit=limit, offset=offset)
        return jsonify({"success": True, "insights": rows, "total": total})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history")
def history():
    try:
        limit = min(int(request.args.get("limit", 30)), 100)
        rows = get_generation_history(limit=limit)
        return jsonify({"success": True, "history": rows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/calendar")
def calendar():
    try:
        week_param = request.args.get("week", "current")
        today = date.today()

        if week_param == "current":
            monday = today - timedelta(days=today.weekday())
        elif week_param == "next":
            monday = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
        else:
            try:
                target = date.fromisoformat(week_param)
                monday = target - timedelta(days=target.weekday())
            except ValueError:
                return jsonify({"success": False, "error": "Invalid week parameter"}), 400

        friday = monday + timedelta(days=4)
        generate_week_slots(monday)
        slots = get_week_slots(monday)
        stats = get_week_stats(monday)

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for slot in slots:
            dow = slot.get("day_of_week", 0)
            slot["day_name"] = day_names[dow]
            schedule = CONTENT_SCHEDULE.get(dow, {})
            slot["suggestion"] = schedule.get("suggestion", "")
            slot["suggested_time"] = SUGGESTED_TIMES.get(dow, "9:00 AM")

        return jsonify({
            "success": True,
            "week_start": monday.isoformat(),
            "week_end": friday.isoformat(),
            "stats": stats,
            "slots": slots,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/calendar/assign", methods=["POST"])
def calendar_assign():
    try:
        data = request.get_json(silent=True) or {}
        slot_id = data.get("slot_id")
        generation_id = data.get("generation_id")

        if not slot_id or not generation_id:
            return jsonify({"success": False, "error": "slot_id and generation_id are required"}), 400

        from database import get_connection
        conn = get_connection()
        slot = conn.execute("SELECT id FROM calendar_slots WHERE id = ?", (slot_id,)).fetchone()
        gen = conn.execute("SELECT id FROM generations WHERE id = ?", (generation_id,)).fetchone()
        conn.close()

        if not slot:
            return jsonify({"success": False, "error": "Slot not found"}), 404
        if not gen:
            return jsonify({"success": False, "error": "Generation not found"}), 404

        assign_draft_to_slot(slot_id, generation_id)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/calendar/status", methods=["POST"])
def calendar_status():
    try:
        data = request.get_json(silent=True) or {}
        slot_id = data.get("slot_id")
        status = data.get("status")
        scheduled_time = data.get("scheduled_time")
        notes = data.get("notes")

        if not slot_id or not status:
            return jsonify({"success": False, "error": "slot_id and status are required"}), 400

        valid_statuses = {"empty", "draft_ready", "scheduled", "published", "skipped"}
        if status not in valid_statuses:
            return jsonify({"success": False, "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

        update_slot_status(slot_id, status, scheduled_time, notes)
        return jsonify({"success": True})

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/calendar/clear", methods=["POST"])
def calendar_clear():
    try:
        data = request.get_json(silent=True) or {}
        slot_id = data.get("slot_id")

        if not slot_id:
            return jsonify({"success": False, "error": "slot_id is required"}), 400

        clear_slot(slot_id)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/calendar/skip", methods=["POST"])
def calendar_skip():
    try:
        data = request.get_json(silent=True) or {}
        slot_id = data.get("slot_id")

        if not slot_id:
            return jsonify({"success": False, "error": "slot_id is required"}), 400

        from database import get_connection
        conn = get_connection()
        slot = conn.execute("SELECT status FROM calendar_slots WHERE id = ?", (slot_id,)).fetchone()
        conn.close()

        if not slot:
            return jsonify({"success": False, "error": "Slot not found"}), 404

        if slot["status"] == "skipped":
            clear_slot(slot_id)
        else:
            update_slot_status(slot_id, "skipped")

        return jsonify({"success": True})

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _handle_api_error(e):
    """Handle API errors with user-friendly messages."""
    error_str = str(e)

    # Rate limit
    if "429" in error_str or "rate" in error_str.lower():
        return jsonify({
            "success": False,
            "error": "You're generating too quickly. Wait a moment and try again.",
        }), 429

    # Network/connection errors
    if "connect" in error_str.lower() or "timeout" in error_str.lower() or "network" in error_str.lower():
        return jsonify({
            "success": False,
            "error": "Can't reach the Anthropic API. Check your internet connection.",
        }), 503

    # Authentication
    if "401" in error_str or "auth" in error_str.lower() or ("invalid" in error_str.lower() and "key" in error_str.lower()):
        return jsonify({
            "success": False,
            "error": "API key is invalid. Check your .env file.",
        }), 401

    # Default
    return jsonify({"success": False, "error": f"Generation failed: {error_str}"}), 500


# Initialize database on startup
init_db()

if __name__ == "__main__":
    if API_KEY_MISSING:
        print("\n" + "=" * 60)
        print("  WARNING: ANTHROPIC_API_KEY is not set!")
        print("  Create a .env file in the project root with:")
        print("  ANTHROPIC_API_KEY=your-key-here")
        print("=" * 60 + "\n")
        print("  Starting anyway — the app will show setup instructions.\n")

    app.run(debug=True, port=FLASK_PORT)
