import re
import sys
from datetime import datetime

from flask import Flask, jsonify, render_template, request

from config import ANTHROPIC_API_KEY, CONTENT_SCHEDULE, FLASK_PORT
from database import (
    get_generation_history,
    get_insights,
    init_db,
    mark_generation_copied,
    save_generation,
    save_insight,
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
        data = request.get_json()
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

        return jsonify({"success": True, "insight_id": insight_id, "drafts": drafts_response})

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
        data = request.get_json() or {}

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
        data = request.get_json()
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
    if "401" in error_str or "auth" in error_str.lower() or "invalid" in error_str.lower() and "key" in error_str.lower():
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
