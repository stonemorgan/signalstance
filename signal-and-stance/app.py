import os
import re
import threading
import time
from datetime import date, datetime, timedelta

from flask import Flask, jsonify, render_template, request, send_file

from config import ANTHROPIC_API_KEY, CONTENT_SCHEDULE, FLASK_PORT, SUGGESTED_TIMES
from database import (
    add_feed,
    assign_draft_to_slot,
    clear_slot,
    delete_feed,
    generate_week_slots,
    get_article_by_id,
    get_carousel_data,
    get_feed_stats,
    get_feeds,
    get_generation_history,
    get_insights,
    get_recent_articles,
    get_week_slots,
    get_week_stats,
    init_db,
    mark_article_dismissed,
    mark_article_used,
    mark_generation_copied,
    save_carousel_data,
    save_generation,
    save_insight,
    seed_default_feeds,
    update_feed,
    update_slot_status,
)
from engine import (
    generate_autopilot,
    generate_autopilot_from_feeds,
    generate_carousel_content,
    generate_from_feed_article,
    generate_from_url,
    generate_posts,
)
from carousel_renderer import render_carousel
from feed_scanner import fetch_feed, refresh_and_score

app = Flask(__name__)

VALID_CATEGORIES = {"pattern", "faq", "noticed", "hottake", "autopilot", "url_react", "feed_react"}
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
        result = generate_autopilot_from_feeds()
        method = result["method"]
        drafts = result["drafts"]
        source_article = result["source_article"]

        # ── Feed-sourced autopilot ──
        if method == "feed":
            if not drafts:
                return jsonify({
                    "success": False,
                    "error": "Feed article was found but draft generation failed.",
                }), 500

            raw_input_text = source_article.get("title", "auto-generated from feed")
            source_url = source_article.get("url")
            insight_id = save_insight("autopilot", raw_input_text, source_url)

            drafts_response = []
            for i, draft in enumerate(drafts, start=1):
                gen_id = save_generation(insight_id, i, draft["content"])
                drafts_response.append({
                    "id": gen_id,
                    "draft_number": i,
                    "content": draft["content"],
                    "angle": draft.get("angle", ""),
                })

            return jsonify({
                "success": True,
                "insight_id": insight_id,
                "method": "feed",
                "source_article": source_article,
                "source_summary": source_article.get("title", ""),
                "source_url": source_url,
                "drafts": drafts_response,
            })

        # ── Web search fallback ──
        source_info = result["source_info"]

        # Handle "nothing found" case
        if drafts is None:
            if source_info and source_info.get("nothing_found"):
                return jsonify({
                    "success": True,
                    "nothing_found": True,
                    "method": "web_search",
                    "source_article": None,
                    "source_summary": source_info["source_summary"],
                })
            return jsonify({
                "success": False,
                "error": (source_info or {}).get("source_summary", "Could not generate autopilot content."),
            }), 400

        # Determine category from source info (default to 'noticed')
        category = (source_info or {}).get("category", "noticed")
        if category not in VALID_CATEGORIES:
            category = "autopilot"

        raw_input_text = (source_info or {}).get("insight") or (source_info or {}).get("source_summary", "auto-generated")
        source_url = (source_info or {}).get("source_url")
        insight_id = save_insight("autopilot", raw_input_text, source_url)

        drafts_response = []
        for i, draft in enumerate(drafts, start=1):
            gen_id = save_generation(insight_id, i, draft["content"])
            drafts_response.append({
                "id": gen_id,
                "draft_number": i,
                "content": draft["content"],
                "angle": draft.get("angle", ""),
            })

        return jsonify({
            "success": True,
            "insight_id": insight_id,
            "method": "web_search",
            "source_article": None,
            "source_summary": (source_info or {}).get("source_summary", ""),
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
        # Enrich with carousel data
        for item in rows:
            for draft in item.get("drafts", []):
                cd = get_carousel_data(draft["id"])
                if cd:
                    draft["carousel"] = {
                        "template_type": cd["template_type"],
                        "slide_count": cd["slide_count"],
                        "pdf_filename": cd["pdf_filename"],
                        "title": cd["parsed_content"].get("title", ""),
                        "pdf_url": f"/api/carousel/download/{draft['id']}",
                        "file_exists": os.path.isfile(os.path.join(CAROUSEL_DIR, cd["pdf_filename"])) if cd["pdf_filename"] else False,
                    }
        return jsonify({"success": True, "history": rows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/insight/<int:insight_id>/generations")
def insight_generations(insight_id):
    try:
        from database import get_generations_for_insight
        gens = get_generations_for_insight(insight_id)
        return jsonify({"success": True, "generations": gens})
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


# ── Feed & Article Routes ────────────────────────────────────────────────────


@app.route("/api/feeds")
def feeds_list():
    try:
        feeds = get_feeds(enabled_only=False)
        from database import get_connection
        conn = get_connection()
        for feed in feeds:
            count = conn.execute(
                "SELECT COUNT(*) FROM feed_articles WHERE feed_id = ?", (feed["id"],)
            ).fetchone()[0]
            feed["article_count"] = count
            feed["enabled"] = bool(feed["enabled"])
        conn.close()
        stats = get_feed_stats()
        return jsonify({"success": True, "feeds": feeds, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/feeds", methods=["POST"])
def feeds_add():
    try:
        data = request.get_json(silent=True) or {}
        url = data.get("url", "").strip()
        name = data.get("name", "").strip()
        category = data.get("category", "careers").strip()
        weight = float(data.get("weight", 1.0))

        if not url or not name:
            return jsonify({"success": False, "error": "url and name are required"}), 400

        feed_id, error = add_feed(url, name, category, weight)
        if error:
            return jsonify({"success": False, "error": error}), 400

        # Immediately fetch the new feed to verify it works
        feed = {"id": feed_id, "url": url, "name": name, "category": category, "weight": weight}
        fetch_result = fetch_feed(feed)

        return jsonify({
            "success": True,
            "feed_id": feed_id,
            "fetch_result": fetch_result,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/feeds/<int:feed_id>", methods=["PUT"])
def feeds_update(feed_id):
    try:
        data = request.get_json(silent=True) or {}
        update_feed(
            feed_id,
            enabled=data.get("enabled"),
            name=data.get("name"),
            category=data.get("category"),
            weight=data.get("weight"),
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/feeds/<int:feed_id>", methods=["DELETE"])
def feeds_delete(feed_id):
    try:
        delete_feed(feed_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/articles")
def articles_list():
    try:
        limit = min(int(request.args.get("limit", 30)), 200)
        min_relevance = request.args.get("min_relevance")
        if min_relevance is not None:
            min_relevance = float(min_relevance)
        category = request.args.get("category")
        unused_only = request.args.get("unused_only", "true").lower() != "false"

        articles = get_recent_articles(
            limit=limit,
            min_relevance=min_relevance,
            unused_only=unused_only,
            category=category,
        )
        return jsonify({"success": True, "articles": articles})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/articles/<int:article_id>/generate", methods=["POST"])
def articles_generate(article_id):
    if API_KEY_MISSING:
        return jsonify({"success": False, "error": "API key not configured. See setup instructions."}), 503

    try:
        article = get_article_by_id(article_id)
        if not article:
            return jsonify({"success": False, "error": "Article not found"}), 404

        drafts = generate_from_feed_article(article)
        if not drafts:
            return jsonify({"success": False, "error": "Draft generation failed."}), 500

        # Save insight and generations
        insight_id = save_insight("feed_react", article["title"], article["url"])

        drafts_response = []
        for i, draft in enumerate(drafts, start=1):
            gen_id = save_generation(insight_id, i, draft["content"])
            drafts_response.append({
                "id": gen_id,
                "draft_number": i,
                "content": draft["content"],
                "angle": draft.get("angle", ""),
            })

        # Mark the article as used
        mark_article_used(article_id)

        return jsonify({
            "success": True,
            "insight_id": insight_id,
            "method": "feed",
            "source_article": {
                "id": article["id"],
                "title": article["title"],
                "url": article["url"],
                "feed_name": article.get("feed_name", ""),
                "relevance_score": article.get("relevance_score"),
                "relevance_reason": article.get("relevance_reason", ""),
            },
            "drafts": drafts_response,
        })

    except Exception as e:
        return _handle_api_error(e)


@app.route("/api/articles/<int:article_id>/dismiss", methods=["POST"])
def articles_dismiss(article_id):
    try:
        mark_article_dismissed(article_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── Carousel Routes ──────────────────────────────────────────────────────


CAROUSEL_DIR = os.path.join(os.path.dirname(__file__), "generated_carousels")
VALID_TEMPLATES = {"tips", "beforeafter", "mythreality"}


@app.route("/api/generate/carousel", methods=["POST"])
def generate_carousel_route():
    if API_KEY_MISSING:
        return jsonify({"success": False, "error": "API key not configured."}), 503

    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Request body must be JSON"}), 400

        category = data.get("category", "").strip()
        raw_input_text = data.get("raw_input", "").strip()
        template_type = data.get("template_type", "").strip()

        if category not in {"pattern", "faq", "noticed", "hottake"}:
            return jsonify({"success": False, "error": "Invalid category."}), 400
        if not raw_input_text:
            return jsonify({"success": False, "error": "raw_input is required"}), 400
        if template_type not in VALID_TEMPLATES:
            return jsonify({"success": False, "error": "Invalid template_type. Must be one of: tips, beforeafter, mythreality"}), 400

        # Save insight
        insight_id = save_insight(category, raw_input_text)

        # Generate carousel content
        parsed = generate_carousel_content(template_type, raw_input_text)
        if "error" in parsed:
            return jsonify({"success": False, "error": parsed["error"]}), 500

        # Render PDF
        os.makedirs(CAROUSEL_DIR, exist_ok=True)
        timestamp = int(time.time())
        pdf_filename = f"carousel_{insight_id}_{template_type}_{timestamp}.pdf"
        pdf_path = os.path.join(CAROUSEL_DIR, pdf_filename)

        render_result = render_carousel(parsed, template_type, pdf_path)
        if not render_result.get("success"):
            return jsonify({"success": False, "error": render_result.get("error", "PDF rendering failed")}), 500

        # Save generation record (use carousel title as content for history)
        gen_id = save_generation(insight_id, 1, parsed["title"])

        # Save carousel metadata
        slide_count = render_result["page_count"]
        save_carousel_data(gen_id, template_type, parsed, pdf_filename, slide_count)

        return jsonify({
            "success": True,
            "insight_id": insight_id,
            "generation_id": gen_id,
            "carousel": {
                "title": parsed["title"],
                "subtitle": parsed.get("subtitle"),
                "template_type": template_type,
                "slide_count": slide_count,
                "pdf_url": f"/api/carousel/download/{gen_id}",
                "slides_preview": parsed["slides"],
                "cta": parsed.get("cta", ""),
            },
        })

    except Exception as e:
        return _handle_api_error(e)


@app.route("/api/carousel/download/<int:generation_id>")
def download_carousel(generation_id):
    carousel = get_carousel_data(generation_id)
    if not carousel or not carousel.get("pdf_filename"):
        return jsonify({"success": False, "error": "Carousel not found"}), 404

    filepath = os.path.join(CAROUSEL_DIR, carousel["pdf_filename"])
    if not os.path.isfile(filepath):
        return jsonify({"success": False, "error": "PDF file not found"}), 404

    return send_file(filepath, as_attachment=True, download_name=carousel["pdf_filename"])


@app.route("/api/generate/carousel/regenerate", methods=["POST"])
def regenerate_carousel_route():
    if API_KEY_MISSING:
        return jsonify({"success": False, "error": "API key not configured."}), 503

    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Request body must be JSON"}), 400

        insight_id = data.get("insight_id")
        template_type = data.get("template_type", "").strip()

        if not insight_id:
            return jsonify({"success": False, "error": "insight_id is required"}), 400
        if template_type not in VALID_TEMPLATES:
            return jsonify({"success": False, "error": "Invalid template_type."}), 400

        # Fetch the original insight
        from database import get_connection
        conn = get_connection()
        insight = conn.execute("SELECT * FROM insights WHERE id = ?", (insight_id,)).fetchone()
        conn.close()

        if not insight:
            return jsonify({"success": False, "error": "Insight not found"}), 404

        raw_input_text = insight["raw_input"]

        # Generate new carousel content
        parsed = generate_carousel_content(template_type, raw_input_text)
        if "error" in parsed:
            return jsonify({"success": False, "error": parsed["error"]}), 500

        # Render new PDF
        os.makedirs(CAROUSEL_DIR, exist_ok=True)
        timestamp = int(time.time())
        pdf_filename = f"carousel_{insight_id}_{template_type}_{timestamp}.pdf"
        pdf_path = os.path.join(CAROUSEL_DIR, pdf_filename)

        render_result = render_carousel(parsed, template_type, pdf_path)
        if not render_result.get("success"):
            return jsonify({"success": False, "error": render_result.get("error", "PDF rendering failed")}), 500

        # Save new generation
        gen_id = save_generation(insight_id, 1, parsed["title"])

        slide_count = render_result["page_count"]
        save_carousel_data(gen_id, template_type, parsed, pdf_filename, slide_count)

        return jsonify({
            "success": True,
            "insight_id": insight_id,
            "generation_id": gen_id,
            "carousel": {
                "title": parsed["title"],
                "subtitle": parsed.get("subtitle"),
                "template_type": template_type,
                "slide_count": slide_count,
                "pdf_url": f"/api/carousel/download/{gen_id}",
                "slides_preview": parsed["slides"],
                "cta": parsed.get("cta", ""),
            },
        })

    except Exception as e:
        return _handle_api_error(e)


@app.route("/api/feeds/refresh", methods=["POST"])
def feeds_refresh():
    try:
        results = refresh_and_score()
        return jsonify({
            "success": True,
            "fetch_results": results["fetch"],
            "scoring_results": {
                "scored": results["scored"],
                "high_relevance": results["high_relevance"],
            },
        })
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


def cleanup_old_carousels(days=30):
    """Delete PDF files older than N days from generated_carousels/."""
    if not os.path.isdir(CAROUSEL_DIR):
        return
    cutoff = time.time() - (days * 86400)
    for filename in os.listdir(CAROUSEL_DIR):
        if not filename.endswith(".pdf"):
            continue
        filepath = os.path.join(CAROUSEL_DIR, filename)
        try:
            if os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)
        except OSError:
            pass


# Initialize database and seed feeds on startup
init_db()
seed_default_feeds()
os.makedirs(CAROUSEL_DIR, exist_ok=True)
cleanup_old_carousels()


def maybe_refresh_feeds():
    """Refresh feeds if stale (>6 hours since last fetch). Run in background thread."""
    try:
        feeds = get_feeds(enabled_only=True)
        if not feeds:
            return

        fetched_times = [f["last_fetched_at"] for f in feeds if f["last_fetched_at"]]
        if not fetched_times:
            print("  [Feed Scanner] No feeds have been fetched yet — running initial refresh...")
            results = refresh_and_score()
            print(f"  [Feed Scanner] Done: {results['fetch']['successful']} feeds fetched, "
                  f"{results['fetch']['new_articles']} new articles, {results['scored']} scored")
            return

        last_fetched = max(fetched_times)
        last_dt = datetime.fromisoformat(last_fetched)
        if datetime.now() - last_dt > timedelta(hours=6):
            print("  [Feed Scanner] Feeds are stale — refreshing in background...")
            results = refresh_and_score()
            print(f"  [Feed Scanner] Done: {results['fetch']['successful']} feeds fetched, "
                  f"{results['fetch']['new_articles']} new articles, {results['scored']} scored")
        else:
            print(f"  [Feed Scanner] Feeds are fresh (last fetched: {last_fetched}). Skipping refresh.")
    except Exception as e:
        print(f"  [Feed Scanner] Background refresh failed: {e}")


if __name__ == "__main__":
    if API_KEY_MISSING:
        print("\n" + "=" * 60)
        print("  WARNING: ANTHROPIC_API_KEY is not set!")
        print("  Create a .env file in the project root with:")
        print("  ANTHROPIC_API_KEY=your-key-here")
        print("=" * 60 + "\n")
        print("  Starting anyway — the app will show setup instructions.\n")

    # Auto-refresh feeds in background if stale
    threading.Thread(target=maybe_refresh_feeds, daemon=True).start()

    app.run(debug=True, port=FLASK_PORT)
