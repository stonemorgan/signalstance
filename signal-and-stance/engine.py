import os
import re

import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MAX_TOKENS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

CATEGORY_FILE_MAP = {
    "pattern": "prompts/category_pattern.md",
    "faq": "prompts/category_faq.md",
    "noticed": "prompts/category_noticed.md",
    "hottake": "prompts/category_hottake.md",
}


def load_prompt(filepath):
    prompt_path = os.path.join(os.path.dirname(__file__), filepath)
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


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
                "content": "Find a current, relevant career/hiring/resume topic and generate LinkedIn posts about it. Search for recent news first, then write the posts.",
            }
        ],
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
                "content": f"Read this article/post and generate LinkedIn reaction posts from Dana's perspective:\n\n{url}",
            }
        ],
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
