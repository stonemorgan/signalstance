from datetime import datetime

from flask import Flask, jsonify, render_template, request

from config import CONTENT_SCHEDULE, FLASK_PORT
from database import (
    get_generation_history,
    get_insights,
    init_db,
    mark_generation_copied,
    save_generation,
    save_insight,
)

app = Flask(__name__)

VALID_CATEGORIES = {"pattern", "faq", "noticed", "hottake"}

# Mock drafts used until engine.py is wired up
MOCK_DRAFTS = [
    {
        "content": (
            "I reviewed 14 executive resumes this month.\n\n"
            "11 of them made the same mistake: listing responsibilities instead of results.\n\n"
            "Your resume is not a job description rewrite. It's a business case for hiring you.\n\n"
            "The fix takes 20 minutes. The impact lasts your entire career.\n\n"
            "Have you audited your resume for this?"
        ),
        "angle": "Direct advice angle — leads with the pattern",
    },
    {
        "content": (
            "A client came to me last week — VP of Operations, 18 years of experience, managing a $40M P&L.\n\n"
            "Her resume read like a Wikipedia article about her company.\n\n"
            "We rewrote it around three metrics: revenue influenced, team scale, and process efficiency gains.\n\n"
            "She had interviews within two weeks.\n\n"
            "Your experience isn't the problem. How you frame it might be."
        ),
        "angle": "Story-driven — opens with a client scenario",
    },
    {
        "content": (
            "6 seconds.\n\n"
            "That's the average time a recruiter spends on your resume before deciding yes or no.\n\n"
            "In those 6 seconds, they're not reading your career summary. "
            "They're scanning for numbers, titles, and company names.\n\n"
            "If your resume doesn't pass the 6-second scan, the rest doesn't matter.\n\n"
            "What does the top third of your resume actually say?"
        ),
        "angle": "Data-driven — leads with the metric",
    },
]


@app.route("/")
def index():
    try:
        return render_template("index.html")
    except Exception:
        return "Signal & Stance is running."


@app.route("/api/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body must be JSON"}), 400

        category = data.get("category", "").strip()
        raw_input = data.get("raw_input", "").strip()

        if category not in VALID_CATEGORIES:
            return jsonify({
                "success": False,
                "error": f"Invalid category. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}",
            }), 400

        if not raw_input:
            return jsonify({"success": False, "error": "raw_input is required"}), 400

        # Save insight
        insight_id = save_insight(category, raw_input, data.get("source_url"))

        # Use mock drafts (engine.py not wired up yet)
        drafts_response = []
        for i, mock in enumerate(MOCK_DRAFTS, start=1):
            gen_id = save_generation(insight_id, i, mock["content"])
            drafts_response.append({
                "id": gen_id,
                "draft_number": i,
                "content": mock["content"],
                "angle": mock["angle"],
            })

        return jsonify({"success": True, "insight_id": insight_id, "drafts": drafts_response})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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
        if weekday in CONTENT_SCHEDULE:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            schedule = CONTENT_SCHEDULE[weekday]
            return jsonify({
                "day": day_names[weekday],
                "type": schedule["type"],
                "suggestion": schedule["suggestion"],
            })
        else:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
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
        rows = get_insights()
        return jsonify({"success": True, "insights": rows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history")
def history():
    try:
        rows = get_generation_history()
        return jsonify({"success": True, "history": rows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Initialize database on startup
init_db()

if __name__ == "__main__":
    app.run(debug=True, port=FLASK_PORT)
