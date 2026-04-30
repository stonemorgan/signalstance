#!/usr/bin/env python
"""Generate a SignalStance tenant from intake markdown documents.

Reads four markdown files from an intake directory, uses Claude to
extract structured config and synthesize the voice profile, and writes
a tenant directory ready for `python run.py --tenant <name>`.

Usage:
    python scripts/intake_tenant.py taylor-morgan --from intake/taylor-morgan
    python scripts/intake_tenant.py taylor-morgan --from intake/taylor-morgan --dry-run
    python scripts/intake_tenant.py taylor-morgan --from intake/taylor-morgan --force
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "framework"))

from validate import validate_business_config, ConfigError

DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
TEMPERATURE_EXTRACTION = 0.1
TEMPERATURE_SYNTHESIS = 0.3

SCORING_DESCRIPTION_TEMPLATE = (
    "Score articles for relevance to {owner.name}'s niche: {owner.niche_summary}. "
    "Target audience: {owner.audience}."
)

REQUIRED_INTAKE_FILES = (
    "01-identity.md",
    "02-voice-samples.md",
    "03-content-rhythm.md",
    "04-brand-and-feeds.md",
)

CAROUSEL_TEMPLATES = ["tips", "beforeafter", "mythreality"]

IDENTITY_SYSTEM_PROMPT = """You extract structured identity data from a tenant intake markdown document for a content-generation platform.

Return only valid JSON matching this exact schema:

{
  "owner": {
    "name": string,
    "title": string,
    "business": string,
    "url": string,
    "credentials": [string],
    "niche_summary": string,
    "audience": string,
    "audience_examples": string,
    "specializations": [string],
    "client_outcomes": string
  },
  "scoring_seed": {
    "high": string,
    "low": string
  }
}

Field rules:
- owner.name, title, business: from the "## Name & Business" section.
- owner.url: the first URL listed under "## Links".
- owner.credentials: bullet items from "## Credentials" section, as an array of plain strings (no leading dash).
- owner.niche_summary: the single paragraph from the "## Niche" section, joined into one line with no embedded newlines.
- owner.audience: the line beginning "Description:" under "## Audience", without the "Description:" prefix.
- owner.audience_examples: the line beginning "Examples:" under "## Audience", without the "Examples:" prefix, as a single comma-separated string.
- owner.specializations: bullet items from "## Specializations", as an array of plain strings.
- owner.client_outcomes: the paragraph from the "## Client outcomes" section. Empty string "" if absent or only contains a placeholder.
- scoring_seed.high: one sentence suitable for an article-relevance scorer, describing what's directly relevant to this person's niche. Use the literal placeholder strings {owner.name} and {owner.niche_summary} where natural — these are template placeholders that will be substituted later.
- scoring_seed.low: one sentence suitable for an article-relevance scorer, describing what is unrelated, off-topic, or off-niche.

Hard rules:
- Output JSON only. No preamble, no markdown code fences, no trailing commentary.
- Use only values that appear in the source text. Do not invent.
- Strip markdown formatting from extracted strings (no leading hyphens, no surrounding asterisks, no quote marks).
- Lines beginning with > or > * are reviewer notes — ignore them as source data.
- For absent optional fields, return empty string "" or empty array [].
"""

CONTENT_RHYTHM_SYSTEM_PROMPT = """You extract structured content-rhythm data from a tenant intake markdown document.

Return only valid JSON matching this exact schema:

{
  "platform": {
    "name": string,
    "post_word_range": [int, int],
    "carousel_dimensions": [int, int],
    "scheduling_url": string
  },
  "content": {
    "categories": {
      "pattern":  {"label": string, "prompt_label": string, "placeholder": string},
      "faq":      {"label": string, "prompt_label": string, "placeholder": string},
      "noticed":  {"label": string, "prompt_label": string, "placeholder": string},
      "hottake":  {"label": string, "prompt_label": string, "placeholder": string}
    },
    "default_ctas": {
      "tips": string,
      "beforeafter": string,
      "mythreality": string,
      "general": string
    }
  },
  "schedule": {
    "days": {
      "<Weekday>": {"content_type": string, "suggestion": string},
      ...
    },
    "suggested_times": {
      "<Weekday>": string,
      ...
    },
    "timezone": string
  }
}

Field rules:

Platform:
- platform.name: from the "## Platform settings" section. Default "LinkedIn" if absent.
- platform.post_word_range: from the "## Platform settings" section, as a [min, max] integer array. Default [150, 300] if absent.
- platform.carousel_dimensions: from "## Platform settings". Default [1080, 1080].
- platform.scheduling_url: derive from platform.name. For LinkedIn: "https://linkedin.com/feed".

Content categories — for EACH of the four keys (pattern, faq, noticed, hottake):
- label: short title, drawn from the "### <Title>" subheading inside "## Content categories" (e.g. "Pattern", "FAQ", "Noticed", "Hot Take"). Capitalize naturally.
- prompt_label: a short trigger phrase (3-5 words) that fits this category for THIS tenant, ending with an ellipsis. Examples: "I keep seeing...", "Client asked...", "Just noticed...", "Hot take...". Make it specific to the description if possible.
- placeholder: a single sentence of helper text suitable for a textarea placeholder. Should reflect the category's description for THIS tenant.

Content default_ctas:
- For each carousel template (tips, beforeafter, mythreality, general): if the intake provides an explicit CTA string, use it verbatim. If the intake says "auto" or leaves the field blank, generate a brand-appropriate, NON-engagement-bait CTA suitable for this tenant — prefer pointing to the tenant's website (e.g. "More writing at signalstance.com") over "follow for more" framings. Read the intake's notes about CTA preferences and honor them.

Schedule:
- schedule.days: for each weekday listed under "## Posting cadence", an entry with "content_type" (the bolded type, e.g. "Educational / Pattern") and "suggestion" (the trailing quoted instructional sentence). Only include weekdays that are actually scheduled — skip weekdays the tenant marks as flex/skip/optional/blank.
- schedule.suggested_times: for each weekday in schedule.days, a corresponding time string like "8:00 AM". From the "## Posting times" section.
- schedule.timezone: from "## Posting times" section. Default "EST" if absent.

Hard rules:
- Output JSON only. No preamble, no markdown code fences, no commentary.
- The four content category keys must be exactly: pattern, faq, noticed, hottake.
- Schedule days must use full weekday names ("Monday", not "Mon"). Valid: Monday, Tuesday, Wednesday, Thursday, Friday.
- Every weekday key in schedule.days MUST also appear in schedule.suggested_times.
- Lines beginning with > or > * are reviewer notes — ignore them as source data.
"""

BRAND_SYSTEM_PROMPT = """You extract brand colors and fonts from a tenant intake markdown document.

Return only valid JSON matching this exact schema:

{
  "brand": {
    "primary": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "background": "#hex",
    "background_alt": "#hex",
    "text_dark": "#hex",
    "text_light": "#hex",
    "text_muted": "#hex",
    "divider": "#hex",
    "negative": "#hex",
    "positive": "#hex",
    "font_heading": string,
    "font_body": string,
    "font_accent": string
  }
}

Field rules:
- For each color role: extract the explicit hex code from "## Brand colors" if provided. The line format is "<role>: #HEXCODE — comment" or similar. Strip leading text/comments and return only the hex code (uppercase).
- All 11 color roles are required. If a role is missing, return a sensible harmonized default.
- For fonts: extract from "## Brand fonts" section. The user has specified Helvetica family — use exactly:
    "font_heading": "Helvetica-Bold"
    "font_body": "Helvetica"
    "font_accent": "Helvetica-Oblique"
  Even if the intake mentions other fonts (e.g. Fraunces, Inter), default to Helvetica for now per project policy.

Hard rules:
- Output JSON only. No preamble, no markdown code fences, no commentary.
- All hex codes must start with "#" followed by exactly 6 hex characters.
- Lines beginning with > or > * are reviewer notes — ignore them as source data.
"""

FEEDS_SYSTEM_PROMPT = """You extract RSS feed configuration from a tenant intake markdown document.

Return only valid JSON matching this exact schema:

{
  "categories": {
    "<category_key>": "<one-sentence description>",
    ...
  },
  "urls": [
    {
      "url": string,
      "name": string,
      "category": string,
      "weight": float,
      "enabled": true
    },
    ...
  ]
}

Field rules:

categories:
- Extract from "## Feed categories" section. Each line has the format "name: description".
- Use snake_case keys (e.g. "executive_careers", "ai_professional"). Convert spaces and special chars in the source key to underscores; lowercase.
- If the intake says "auto" instead of providing categories, generate sensible category keys derived from topic hints in "## RSS feeds — topic hints". Limit to 6-10 categories.

urls:
- Extract from "## RSS feeds — known URLs" section. Each line is a URL, optionally followed by "(category=<name>, weight=<float>)" parens.
- name: a human-readable name for the feed source (extract from the URL domain or use a sensible label).
- category: the snake_case category from the parens, must match one of the keys in the categories object. If not specified, pick the closest matching category.
- weight: from the parens; default 1.0 if not specified.
- enabled: always true.
- If "## RSS feeds — known URLs" is empty (no actual URLs provided, only topic hints), return an empty array [].

Hard rules:
- Output JSON only. No preamble, no markdown code fences, no commentary.
- Every url's "category" field must be a key that exists in the "categories" object.
- Lines beginning with > or > * are reviewer notes — ignore them as source data.
"""

VOICE_SYNTHESIS_SYSTEM_PROMPT = """You synthesize a voice profile (system prompt) for a content-generation system. The output becomes the system prompt that Claude follows when drafting LinkedIn posts in this person's voice.

Output a single Markdown document with these sections in order:

```
<!-- TEMPLATED: Auto-filled from business_config.json -->

You are writing {{platform.name}} posts as {{owner.name}}. {{owner.name}} is a {{owner.title}} who runs {{owner.business}}. They work with {{owner.audience}}.

## Voice Rules

<!-- AUTHORED SECTION: These rules define the persona's voice. -->

Write in first person as {{owner.name}}. Follow these rules exactly:

**Tone:** [3-5 sentences distilled from the intake's voice notes — directness, register, posture toward the reader.]

**Stance:** [3-5 sentences on the writer's relationship to the audience and topic — confidence level, expertise framing, attitude.]

**Signature language and framing:**

[6-10 bullet points covering metaphors, recurring framings, signature phrases, structural habits, and what voice notes call out as distinctive. Pull directly from the intake's "Voice notes" section and what's evident in the sample posts.]

**Hard rules — never do these:**

[8-15 bullet points distilled from the intake's "Anti-patterns" and "Topics to avoid" sections. State each as a negative rule (no ___, never ___).]

## Credentials

<!-- TEMPLATED: Auto-filled from business_config.json. Use naturally, don't force into every post. -->

- {{owner.credentials}}
- Works with: {{owner.audience}}
- Specializes in: {{owner.specializations}}
- Client outcomes: {{owner.client_outcomes}}

## {{platform.name}} Post Structure Rules

<!-- AUTHORED SECTION: Platform-specific structure rules. -->

**Hook (first line):** [3-5 sentences on what makes a strong opening line for this tenant. Include 2-3 examples of "good hooks" and 1-2 "bad hooks" if the intake gives material to derive them from.]

**Body:** [2-4 sentences on paragraph rhythm, length, structural defaults. Pull from the intake's structural notes.]

**Length:** [1-2 sentences with the post word range from the intake's content rhythm — use the post_word_range value from platform settings if you can derive it, otherwise default to 200-500 words for editorial-register content.]

**CTA (closing):** [2-3 sentences on how the post should end. CRITICAL: honor the tenant's stated CTA preferences. If the intake's anti-patterns explicitly forbid engagement-bait endings ("Agree?", "Thoughts?", "What do you think?"), the CTA rule must say to end on the insight or implication, NOT on a question.]

**Overall feel:** [2-3 sentences capturing the overall register — who this should sound like talking to whom.]

## Self-Evaluation Checklist

Before finalizing each draft, verify:
- [6-9 yes/no checks specific to this tenant's voice — pulled from the intake's distinctive perspectives, hard rules, and audience profile.]

## Output Format

Generate exactly 3 distinct draft variations. Each draft must take a genuinely different angle or framing on the same core insight — not just rewording the same post three times.

Format your output exactly like this:

Draft 1:

[Full post text here]

[Angle description in brackets — e.g., "Direct advice angle — leads with the mistake"]

Draft 2:

[Full post text here]

[Angle description in brackets]

Draft 3:

[Full post text here]

[Angle description in brackets]

Do not include any preamble, commentary, or explanation before Draft 1 or after Draft 3. Start immediately with "Draft 1:" and end after the last angle description.
```

Hard rules for output:
- Keep ALL {{template}} variables literal — do NOT substitute them with the owner's actual values. They will be substituted at runtime.
- Output Markdown only. No code fences around the entire response, no preamble, no commentary.
- Distill the source — don't copy phrasing verbatim from the intake. The voice profile should READ LIKE Claude wrote it, not like the intake was copy-pasted.
- Hard rules section must be specific anti-patterns, not platitudes. Pull from the intake's anti-patterns directly.
- Sample posts are a calibration target for tone and structure — read them carefully but don't quote from them.
- The Self-Evaluation Checklist must be specific to this tenant — generic items like "is it well-written?" don't belong.
"""


def parse_intake_dir(intake_dir):
    """Read all four required intake files. Returns dict of {filename: text}."""
    files = {}
    for name in REQUIRED_INTAKE_FILES:
        path = intake_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Missing intake file: {path}")
        files[name] = path.read_text(encoding="utf-8")
    return files


def _strip_code_fences(text):
    """Strip ```json fences if Claude wraps its response despite instructions."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json|markdown|md)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _claude_extract_json(client, model, system_prompt, intake_text, source_label):
    """Call Claude with a system prompt and intake markdown; parse JSON response."""
    msg = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE_EXTRACTION,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Source file: {source_label}\n\n"
                    f"<intake_section>\n{intake_text}\n</intake_section>\n\n"
                    "Return only valid JSON matching the schema. No prose, no fences."
                ),
            }
        ],
    )
    raw = msg.content[0].text
    cleaned = _strip_code_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Claude returned invalid JSON for {source_label}: {e}\n\n"
            f"Raw response:\n{raw[:1000]}"
        ) from e


def _claude_synthesize_markdown(client, model, system_prompt, voice_text, owner):
    """Call Claude to synthesize a markdown voice profile from voice samples."""
    user_content = (
        f"Owner identity (for context — do NOT substitute these into the output):\n"
        f"{json.dumps(owner, indent=2)}\n\n"
        f"<voice_intake>\n{voice_text}\n</voice_intake>\n\n"
        "Generate the voice profile Markdown document."
    )
    msg = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE_SYNTHESIS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    return _strip_code_fences(msg.content[0].text)


def _slug_to_db_name(business_name):
    """Convert a business name to a snake_case .db filename."""
    cleaned = re.sub(r"\W+", "_", business_name.strip().lower()).strip("_")
    return f"{cleaned}.db"


def assemble_business_config(identity_data, content_data, brand_data, feeds_categories):
    """Combine the four extraction outputs into a single business_config dict."""
    business_name = identity_data["owner"]["business"]
    return {
        "app_name": business_name,
        "database_name": _slug_to_db_name(business_name),
        "owner": identity_data["owner"],
        "platform": content_data["platform"],
        "brand": brand_data["brand"],
        "content": {
            "categories": content_data["content"]["categories"],
            "carousel_templates": CAROUSEL_TEMPLATES,
            "default_ctas": content_data["content"]["default_ctas"],
        },
        "schedule": content_data["schedule"],
        "feeds": {"categories": feeds_categories},
        "scoring": {
            "high_relevance_threshold": 0.7,
            "medium_relevance_threshold": 0.5,
            "scoring_description": SCORING_DESCRIPTION_TEMPLATE,
            "scoring_high": identity_data["scoring_seed"]["high"],
            "scoring_low": identity_data["scoring_seed"]["low"],
        },
    }


def write_tenant(target_dir, template_dir, config, voice_profile, feed_urls):
    """Materialize a tenant directory from the template + extracted content."""
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(template_dir, target_dir)

    (target_dir / "business_config.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    (target_dir / "feeds.json").write_text(
        json.dumps(feed_urls, indent=2) + "\n", encoding="utf-8"
    )
    (target_dir / "prompts" / "base_system.md").write_text(
        voice_profile + "\n", encoding="utf-8"
    )
    (target_dir / "generated_carousels").mkdir(exist_ok=True)


def count_voice_samples(voice_text):
    """Approximate count of sample posts in the voice intake (separated by --- on its own line)."""
    in_block = False
    blocks = 0
    for line in voice_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_block = not in_block
            if in_block:
                blocks += 1
    if blocks > 0:
        return blocks
    return 1 + sum(1 for line in voice_text.splitlines() if line.strip() == "---")


def print_readiness_report(tenant_name, target_dir, config, voice_text, feed_urls):
    print()
    print(f"[OK] Tenant created at {target_dir}")
    print()
    print("Readiness:")
    print(f"  - business_config.json: validated against framework schema")
    print(f"  - prompts/base_system.md: synthesized from {count_voice_samples(voice_text)} voice samples")
    print(f"  - prompts/category_*.md, prompts/carousel_*.md: copied from _template (review and tune as needed)")
    if not feed_urls:
        print(f"  - feeds.json: EMPTY — no RSS URLs provided in intake (topic hints only). Add URLs and refresh feeds in-app.")
    else:
        print(f"  - feeds.json: {len(feed_urls)} feed(s) configured")
    print()
    print(f"Next step:")
    print(f"  python run.py --tenant {tenant_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a SignalStance tenant from intake markdown documents.",
    )
    parser.add_argument("tenant_name", help="snake-case name for the new tenant directory")
    parser.add_argument(
        "--from", dest="intake_dir", required=True,
        help="path to the intake/<tenant>/ directory containing the four .md files",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="overwrite an existing tenant directory",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="generate config in-memory and print it, don't write any files",
    )
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(PROJECT_ROOT / "framework" / ".env")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set. Add it to .env at the project root.")

    intake_dir = Path(args.intake_dir).resolve()
    if not intake_dir.exists():
        sys.exit(f"ERROR: intake directory not found: {intake_dir}")

    target_dir = PROJECT_ROOT / "tenants" / args.tenant_name
    if target_dir.exists() and not args.force and not args.dry_run:
        sys.exit(
            f"ERROR: tenant directory already exists at {target_dir}.\n"
            f"Use --force to overwrite, or --dry-run to preview without writing."
        )

    template_dir = PROJECT_ROOT / "tenants" / "_template"
    if not template_dir.exists():
        sys.exit(f"ERROR: template directory not found: {template_dir}")

    try:
        intake_files = parse_intake_dir(intake_dir)
    except FileNotFoundError as e:
        sys.exit(f"ERROR: {e}")

    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic(api_key=api_key)

    print(f"[1/5] Extracting identity from 01-identity.md ...")
    identity_data = _claude_extract_json(
        client, model, IDENTITY_SYSTEM_PROMPT,
        intake_files["01-identity.md"], "01-identity.md",
    )

    print(f"[2/5] Extracting content rhythm from 03-content-rhythm.md ...")
    content_data = _claude_extract_json(
        client, model, CONTENT_RHYTHM_SYSTEM_PROMPT,
        intake_files["03-content-rhythm.md"], "03-content-rhythm.md",
    )

    print(f"[3/5] Extracting brand from 04-brand-and-feeds.md ...")
    brand_data = _claude_extract_json(
        client, model, BRAND_SYSTEM_PROMPT,
        intake_files["04-brand-and-feeds.md"], "04-brand-and-feeds.md",
    )

    print(f"[4/5] Extracting feeds from 04-brand-and-feeds.md ...")
    feeds_data = _claude_extract_json(
        client, model, FEEDS_SYSTEM_PROMPT,
        intake_files["04-brand-and-feeds.md"], "04-brand-and-feeds.md",
    )

    print(f"[5/5] Synthesizing voice profile from 02-voice-samples.md ...")
    voice_profile = _claude_synthesize_markdown(
        client, model, VOICE_SYNTHESIS_SYSTEM_PROMPT,
        intake_files["02-voice-samples.md"], identity_data["owner"],
    )

    config = assemble_business_config(
        identity_data, content_data, brand_data, feeds_data["categories"],
    )

    try:
        validate_business_config(config, "<generated>")
    except ConfigError as e:
        print(f"\nVALIDATION ERROR: {e}", file=sys.stderr)
        print("\n--- Generated config (for debugging) ---", file=sys.stderr)
        print(json.dumps(config, indent=2), file=sys.stderr)
        sys.exit(2)

    if args.dry_run:
        print()
        print("=" * 60)
        print("DRY RUN — no files written. Generated artifacts:")
        print("=" * 60)
        print()
        print("--- business_config.json ---")
        print(json.dumps(config, indent=2))
        print()
        print(f"--- feeds.json ({len(feeds_data['urls'])} entries) ---")
        print(json.dumps(feeds_data["urls"], indent=2))
        print()
        print("--- prompts/base_system.md ---")
        print(voice_profile)
        return

    write_tenant(target_dir, template_dir, config, voice_profile, feeds_data["urls"])
    print_readiness_report(
        args.tenant_name, target_dir, config,
        intake_files["02-voice-samples.md"], feeds_data["urls"],
    )


if __name__ == "__main__":
    main()
