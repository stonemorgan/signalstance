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
