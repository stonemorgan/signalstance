import os
import re

import anthropic

from business_config import BUSINESS, OWNER, PLATFORM, CONTENT, TENANT_DIR
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MAX_TOKENS
from database import get_recent_articles, mark_article_used
from feeds import FEED_CATEGORIES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _flatten_config(d, prefix=""):
    """Flatten nested dict to dot-notation keys: {'owner.name': 'Dana Wang', ...}"""
    flat = {}
    for k, v in d.items():
        key = f"{prefix}{k}" if prefix else k
        if isinstance(v, dict):
            flat.update(_flatten_config(v, f"{key}."))
        elif isinstance(v, list):
            flat[key] = ", ".join(str(i) for i in v)
        else:
            flat[key] = str(v)
    return flat


_FLAT_CONFIG = _flatten_config(BUSINESS)


CATEGORY_FILE_MAP = {
    "pattern": "prompts/category_pattern.md",
    "faq": "prompts/category_faq.md",
    "noticed": "prompts/category_noticed.md",
    "hottake": "prompts/category_hottake.md",
}


def load_prompt(filepath):
    """Load a prompt .md file from the tenant directory (with framework fallback).

    Checks the tenant directory first, then falls back to the framework directory.
    Substitutes {{key}} placeholders from business config.
    """
    # Try tenant directory first
    tenant_path = os.path.join(TENANT_DIR, filepath)
    if os.path.exists(tenant_path):
        prompt_path = tenant_path
    else:
        # Fall back to framework directory
        prompt_path = os.path.join(os.path.dirname(__file__), filepath)

    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    def _replacer(match):
        key = match.group(1).strip()
        return _FLAT_CONFIG.get(key, match.group(0))

    return re.sub(r"\{\{(.+?)\}\}", _replacer, template)


def generate_posts(category, raw_input, source_url=None):
    base_prompt = load_prompt("prompts/base_system.md")
    category_prompt = load_prompt(CATEGORY_FILE_MAP[category])

    system_prompt = f"{base_prompt}\n\n---\n\n## Category-Specific Instructions\n\n{category_prompt}"

    user_message = f'Here is the insight/observation to turn into LinkedIn posts:\n\n"{raw_input}"'
    if source_url:
        user_message += f"\n\nSource URL for reference: {source_url}"

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        timeout=120,
    )

    full_response = response.content[0].text
    drafts = parse_drafts(full_response)
    return drafts


def generate_autopilot():
    """Generate posts using web search to find current news topics."""
    base_prompt = load_prompt("prompts/base_system.md")
    autopilot_prompt = load_prompt("prompts/autopilot.md")

    system_prompt = f"{base_prompt}\n\n---\n\n## Autopilot Instructions\n\n{autopilot_prompt}"

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Find a current, relevant topic related to {OWNER['niche_summary']} and generate {PLATFORM['name']} posts about it. Search for recent news first, then write the posts.",
            }
        ],
        timeout=120,
    )

    # Extract text content from multi-block response
    full_text = ""
    for block in response.content:
        if block.type == "text":
            full_text += block.text

    # Check if nothing compelling was found
    if "NOTHING_FOUND: true" in full_text:
        return None, {
            "source_summary": "Nothing compelling found in today's news cycle.",
            "source_url": None,
            "category": None,
            "insight": None,
            "nothing_found": True,
        }

    source_info = extract_source_info(full_text)
    drafts = parse_drafts(full_text)
    return drafts, source_info


def generate_from_url(url):
    """Generate reaction posts based on a URL's content using web search."""
    base_prompt = load_prompt("prompts/base_system.md")
    url_react_prompt = load_prompt("prompts/url_react.md")

    system_prompt = f"{base_prompt}\n\n---\n\n## URL Reaction Instructions\n\n{url_react_prompt}"

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Read this article/post and generate {PLATFORM['name']} reaction posts from {OWNER['name']}'s perspective:\n\n{url}",
            }
        ],
        timeout=120,
    )

    # Extract text content from multi-block response
    full_text = ""
    for block in response.content:
        if block.type == "text":
            full_text += block.text

    # Check if URL was inaccessible
    if "URL_ERROR: true" in full_text:
        return None, {
            "source_summary": "Could not access this URL. It may be behind a paywall or unavailable.",
            "url_error": True,
        }

    source_info = extract_source_info(full_text)
    source_info["source_url"] = url
    drafts = parse_drafts(full_text)
    return drafts, source_info


def generate_from_feed_article(article):
    """Generate 3 post drafts reacting to a feed article.

    Args:
        article: dict with title, summary, url, feed_name, feed_category,
                 relevance_reason, and optionally weight.

    Returns:
        list of draft dicts with 'content' and 'angle' keys.
    """
    base_prompt = load_prompt("prompts/base_system.md")
    feed_react_prompt = load_prompt("prompts/feed_react.md")

    system_prompt = (
        f"{base_prompt}\n\n---\n\n"
        f"## Feed Reaction Instructions\n\n{feed_react_prompt}"
    )

    category_desc = FEED_CATEGORIES.get(
        article.get("feed_category", ""), ""
    )

    _default_relevance = f"Matches {OWNER['name']}'s niche."
    user_message = (
        f"Generate {PLATFORM['name']} posts reacting to this article from {OWNER['name']}'s curated feed.\n\n"
        f"**Article title:** {article.get('title', '')}\n\n"
        f"**Summary:** {article.get('summary', 'No summary available.')}\n\n"
        f"**Source publication:** {article.get('feed_name', 'Unknown')}\n\n"
        f"**Feed category:** {article.get('feed_category', 'general')} — {category_desc}\n\n"
        f"**Why this is relevant:** {article.get('relevance_reason', _default_relevance)}"
    )

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        timeout=120,
    )

    full_response = response.content[0].text
    drafts = parse_drafts(full_response)
    return drafts


def generate_autopilot_from_feeds():
    """Generate content from the curated feed pool, falling back to web search.

    Returns:
        dict with 'method' ('feed' or 'web_search'), 'source_article' (or None),
        'drafts' (list), and 'source_info' (for web_search compatibility).
    """
    # Try high-relevance articles first (score >= 0.7)
    candidates = get_recent_articles(limit=10, min_relevance=0.7, unused_only=True)

    if not candidates:
        # Fall back to medium-relevance (score >= 0.5)
        candidates = get_recent_articles(limit=10, min_relevance=0.5, unused_only=True)

    if candidates:
        # Pick the best candidate: highest (relevance_score * weight), most recent as tiebreaker
        best = max(
            candidates,
            key=lambda a: (
                (a.get("relevance_score") or 0) * (a.get("weight") or 1.0),
                a.get("published_at") or "",
            ),
        )

        drafts = generate_from_feed_article(best)
        mark_article_used(best["id"])

        return {
            "method": "feed",
            "source_article": {
                "id": best["id"],
                "title": best["title"],
                "url": best["url"],
                "feed_name": best.get("feed_name", ""),
                "relevance_score": best.get("relevance_score"),
                "relevance_reason": best.get("relevance_reason", ""),
            },
            "drafts": drafts,
            "source_info": None,
        }

    # No feed candidates — fall back to web search autopilot
    drafts, source_info = generate_autopilot()
    return {
        "method": "web_search",
        "source_article": None,
        "drafts": drafts,
        "source_info": source_info,
    }


CAROUSEL_PROMPT_MAP = {
    "tips": "prompts/carousel_tips.md",
    "beforeafter": "prompts/carousel_beforeafter.md",
    "mythreality": "prompts/carousel_mythreality.md",
}


def generate_carousel_content(template_type, raw_input):
    """Generate structured carousel slide content from an insight.

    Args:
        template_type: "tips", "beforeafter", or "mythreality"
        raw_input: The owner's insight/observation text

    Returns:
        dict with title, subtitle, slides list, and cta — or error dict
    """
    if template_type not in CAROUSEL_PROMPT_MAP:
        return {"error": f"Unknown template type: {template_type}"}

    base_prompt = load_prompt("prompts/base_system.md")
    carousel_prompt = load_prompt(CAROUSEL_PROMPT_MAP[template_type])

    system_prompt = (
        f"{base_prompt}\n\n---\n\n"
        f"## Carousel Content Instructions\n\n{carousel_prompt}"
    )

    user_message = (
        f'Generate carousel slide content based on this insight:\n\n"{raw_input}"'
    )

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        timeout=120,
    )

    raw_content = response.content[0].text
    parsed = parse_carousel_content(template_type, raw_content)
    parsed["_raw"] = raw_content
    return parsed


def parse_carousel_content(template_type, raw_content):
    """Parse Claude's structured carousel response into a dict.

    Uses line-by-line keyword matching. Returns a clear error dict if parsing fails.
    """
    if template_type == "tips":
        return _parse_tips(raw_content)
    elif template_type == "beforeafter":
        return _parse_beforeafter(raw_content)
    elif template_type == "mythreality":
        return _parse_mythreality(raw_content)
    else:
        return {"error": f"Unknown template type: {template_type}"}


def _extract_field(text, label):
    """Extract the value after a label like 'TITLE:' from text.

    Handles the value being on the same line or spanning until the next label.
    """
    pattern = re.compile(
        rf"^{re.escape(label)}\s*(.+?)$", re.MULTILINE
    )
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return None


def _parse_tips(raw_content):
    """Parse Numbered Tips carousel content."""
    title = _extract_field(raw_content, "TITLE:")
    subtitle = _extract_field(raw_content, "SUBTITLE:")
    cta = _extract_field(raw_content, "CTA:")

    if not title:
        return {"error": "Could not parse TITLE from response", "_raw": raw_content}

    slides = []
    for n in range(1, 12):  # Support up to 11 tips, expect 5-7
        headline = _extract_field(raw_content, f"TIP {n} HEADLINE:")
        body = _extract_field(raw_content, f"TIP {n} BODY:")
        if headline and body:
            slides.append({
                "number": n,
                "headline": headline,
                "body": body,
            })
        elif headline:
            # Body might be missing but headline exists
            slides.append({
                "number": n,
                "headline": headline,
                "body": "",
            })
        else:
            break  # No more tips found

    if not slides:
        return {"error": "Could not parse any tips from response", "_raw": raw_content}

    return {
        "title": title,
        "subtitle": subtitle,
        "slides": slides,
        "cta": cta or CONTENT["default_ctas"]["tips"],
    }


def _parse_beforeafter(raw_content):
    """Parse Before/After carousel content."""
    title = _extract_field(raw_content, "TITLE:")
    subtitle = _extract_field(raw_content, "SUBTITLE:")
    cta = _extract_field(raw_content, "CTA:")

    if not title:
        return {"error": "Could not parse TITLE from response", "_raw": raw_content}

    slides = []
    for n in range(1, 10):  # Support up to 9 pairs, expect 4-6
        before = _extract_field(raw_content, f"PAIR {n} BEFORE:")
        after = _extract_field(raw_content, f"PAIR {n} AFTER:")
        note = _extract_field(raw_content, f"PAIR {n} NOTE:")
        if before and after:
            slides.append({
                "before": before,
                "after": after,
                "note": note,
            })
        else:
            break

    if not slides:
        return {"error": "Could not parse any pairs from response", "_raw": raw_content}

    return {
        "title": title,
        "subtitle": subtitle,
        "slides": slides,
        "cta": cta or CONTENT["default_ctas"]["beforeafter"],
    }


def _parse_mythreality(raw_content):
    """Parse Myth vs Reality carousel content."""
    title = _extract_field(raw_content, "TITLE:")
    subtitle = _extract_field(raw_content, "SUBTITLE:")
    cta = _extract_field(raw_content, "CTA:")

    if not title:
        return {"error": "Could not parse TITLE from response", "_raw": raw_content}

    slides = []
    for n in range(1, 10):  # Support up to 9 myths, expect 4-6
        myth = _extract_field(raw_content, f"MYTH {n}:")
        reality = _extract_field(raw_content, f"REALITY {n}:")
        if myth and reality:
            slides.append({
                "number": n,
                "myth": myth,
                "reality": reality,
            })
        else:
            break

    if not slides:
        return {"error": "Could not parse any myths from response", "_raw": raw_content}

    return {
        "title": title,
        "subtitle": subtitle,
        "slides": slides,
        "cta": cta or CONTENT["default_ctas"]["mythreality"],
    }


def extract_source_info(text):
    """Extract source metadata from the response text."""
    info = {
        "source_summary": "",
        "source_url": None,
        "category": None,
        "insight": None,
    }

    # Extract SOURCE_SUMMARY
    match = re.search(r"SOURCE_SUMMARY:\s*(.+?)(?:\n|$)", text)
    if match:
        info["source_summary"] = match.group(1).strip()

    # Extract SOURCE_URL
    match = re.search(r"SOURCE_URL:\s*(.+?)(?:\n|$)", text)
    if match:
        info["source_url"] = match.group(1).strip()

    # Extract CATEGORY
    match = re.search(r"CATEGORY:\s*(.+?)(?:\n|$)", text)
    if match:
        info["category"] = match.group(1).strip()

    # Extract INSIGHT
    match = re.search(r"INSIGHT:\s*(.+?)(?:\n|$)", text)
    if match:
        info["insight"] = match.group(1).strip()

    # Extract REACTION_TYPE
    match = re.search(r"REACTION_TYPE:\s*(.+?)(?:\n|$)", text)
    if match:
        info["reaction_type"] = match.group(1).strip()

    return info


def parse_drafts(response_text):
    """Parse the API response into 3 separate drafts with angle descriptions."""
    # Split on Draft N: markers (handles "Draft 1:", "Draft 2:", "Draft 3:")
    parts = re.split(r"Draft\s+\d+\s*:", response_text)

    # First element is anything before "Draft 1:" (should be empty/whitespace)
    # Remaining elements are the draft bodies
    draft_parts = [p.strip() for p in parts[1:] if p.strip()]

    drafts = []
    for part in draft_parts:
        # Extract the angle description from brackets at the end
        angle_match = re.search(r"\[([^\]]+)\]\s*$", part)
        if angle_match:
            angle = angle_match.group(1)
            content = part[: angle_match.start()].strip()
        else:
            angle = ""
            content = part.strip()

        drafts.append({"content": content, "angle": angle})

    # Graceful degradation: if parsing didn't find 3 drafts, handle it
    if len(drafts) == 0:
        drafts = [{"content": response_text.strip(), "angle": ""}]
    elif len(drafts) < 3:
        # Return whatever we got
        pass

    return drafts
