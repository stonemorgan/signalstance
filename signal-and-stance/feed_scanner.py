import json
import re
from datetime import datetime

import anthropic
import feedparser
import requests

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from database import (
    get_feeds,
    get_recent_articles,
    save_articles,
    update_article_relevance,
    update_feed_fetch_status,
)
from feeds import FEED_CATEGORIES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_FEED_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch_feed(feed):
    """Fetch a single RSS feed and store new articles."""
    try:
        # Use requests with proper User-Agent to avoid 403s, then parse with feedparser
        resp = requests.get(feed["url"], headers=_FEED_HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)

        if parsed.bozo and not parsed.entries:
            error_msg = str(parsed.bozo_exception)
            update_feed_fetch_status(feed["id"], last_error=error_msg)
            return {"success": False, "error": error_msg}

        articles = []
        for entry in parsed.entries:
            # Extract published date
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6]).isoformat()

            # Extract summary
            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary
            elif hasattr(entry, "content") and entry.content:
                summary = entry.content[0].get("value", "")

            # Strip HTML tags
            summary = re.sub(r"<[^>]+>", "", summary).strip()
            if len(summary) > 500:
                summary = summary[:497] + "..."

            articles.append({
                "title": entry.get("title", "Untitled"),
                "url": entry.get("link", ""),
                "summary": summary,
                "author": entry.get("author", None),
                "published_at": published,
            })

        new_count = save_articles(feed["id"], articles)
        update_feed_fetch_status(feed["id"], last_fetched_at=datetime.now().isoformat())

        return {"success": True, "new_articles": new_count, "total_entries": len(articles)}

    except Exception as e:
        error_msg = str(e)
        update_feed_fetch_status(feed["id"], last_error=error_msg)
        return {"success": False, "error": error_msg}


def fetch_all_feeds():
    """Fetch all enabled feeds. Returns a summary dict."""
    feeds = get_feeds(enabled_only=True)
    results = {
        "total_feeds": len(feeds),
        "successful": 0,
        "failed": 0,
        "new_articles": 0,
        "errors": [],
    }

    for feed in feeds:
        result = fetch_feed(feed)
        if result["success"]:
            results["successful"] += 1
            results["new_articles"] += result["new_articles"]
        else:
            results["failed"] += 1
            results["errors"].append({"feed": feed["name"], "error": result["error"]})

    return results


def score_articles(articles):
    """Score a batch of articles for relevance to Dana's niche."""
    if not articles:
        return []

    article_list = ""
    for i, article in enumerate(articles):
        article_list += f"\n[{i+1}] Title: {article['title']}\n"
        article_list += f"    Source: {article.get('feed_name', 'Unknown')} ({article.get('feed_category', 'Unknown')})\n"
        article_list += f"    Summary: {(article.get('summary') or '')[:300]}\n"

    system_prompt = """You are an editorial relevance scorer for Dana Wang, a Certified Professional Resume Writer (CPRW) who specializes in executive and board-level resume writing, LinkedIn profile optimization, ATS compliance, and career coaching for senior professionals (VPs, Directors, C-suite, Board members).

Score each article on a scale of 0.0 to 1.0 based on how likely Dana would have a strong, specific professional reaction to it that she could turn into a LinkedIn post for her audience.

Scoring criteria:
- 0.8–1.0: Directly relevant to executive careers, resume strategy, ATS systems, LinkedIn optimization, salary negotiation, or hiring trends at the senior level. Dana would read this and immediately think "I need to post about this."
- 0.5–0.7: Relevant to careers or hiring broadly, but not specifically focused on Dana's executive niche. She could adapt it with her perspective but would need to add significant angle.
- 0.2–0.4: Tangentially relevant — general business news, workplace trends, or HR topics that might have a career angle if stretched.
- 0.0–0.1: Not relevant — entry-level advice, unrelated industry news, product announcements, or topics Dana has no credible expertise to comment on.

Respond ONLY with valid JSON — no preamble, no markdown backticks, no commentary. Format:
[
  {"index": 1, "score": 0.85, "reason": "Directly about executive hiring trends — strong match for Dana's niche"},
  {"index": 2, "score": 0.3, "reason": "General workplace culture piece — would need heavy adaptation"},
  ...
]"""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Score these articles for relevance:\n{article_list}"}
            ],
        )

        response_text = response.content[0].text.strip()
        # Handle possible markdown backtick wrapping
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        scores = json.loads(response_text)
    except (json.JSONDecodeError, IndexError, Exception):
        # If parsing fails, assign neutral scores
        scores = [
            {"index": i + 1, "score": 0.5, "reason": "Scoring failed — manual review needed"}
            for i in range(len(articles))
        ]

    # Save scores to database
    for score_item in scores:
        idx = score_item["index"] - 1
        if 0 <= idx < len(articles):
            update_article_relevance(
                articles[idx]["id"],
                score_item["score"],
                score_item["reason"],
            )

    return scores


def refresh_and_score():
    """Fetch all feeds and score new articles. Returns a complete summary."""
    # Step 1: Fetch
    fetch_results = fetch_all_feeds()

    # Step 2: Score unscored articles
    unscored = get_recent_articles(limit=200, unused_only=False)
    unscored = [a for a in unscored if a["relevance_score"] is None]

    score_results = []
    for i in range(0, len(unscored), 20):
        batch = unscored[i : i + 20]
        batch_scores = score_articles(batch)
        score_results.extend(batch_scores)

    return {
        "fetch": fetch_results,
        "scored": len(score_results),
        "high_relevance": len([s for s in score_results if s.get("score", 0) >= 0.7]),
    }
