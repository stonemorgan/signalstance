# Phase 1: Centralized Business Configuration

**Goal:** Extract all scattered business identity, domain, and brand values into a single `business_config.json` file and wire the codebase to read from it.

**Prerequisite:** None (this is the foundation phase)
**Estimated effort:** 3-4 hours
**Impact:** Eliminates ~30 of 66 coupling points. After this phase, changing the business owner, brand colors, platform, schedule, and feed categories is a single-file edit.

---

## Context

The Signal & Stance codebase currently scatters business-specific values across 6+ files:
- `brand.py` — author name, title, business, URL, colors, fonts
- `config.py` — weekly schedule, posting times, database name
- `feeds.py` — 12 RSS feeds, 10 category definitions
- `feed_scanner.py` lines 113-128 — hardcoded scoring prompt with owner identity
- `engine.py` lines 68, 114, 161, 166, 245, 342, 376, 409 — scattered Dana-specific strings and CTA defaults
- `carousel_renderer.py` line 426 — default CTA fallback
- `app.py` line 58 — app name fallback
- `templates/index.html` lines 6, 20, 37 — app name in titles/headers

This phase creates a single source of truth that all these files read from.

---

## Step 1: Create `business_config.json`

**Create file:** `signal-and-stance/business_config.json`

```json
{
  "app_name": "Signal & Stance",
  "database_name": "signal_stance.db",

  "owner": {
    "name": "Dana Wang",
    "title": "Certified Professional Resume Writer (CPRW)",
    "business": "Raleigh Resume",
    "url": "linkedin.com/in/danaxwang",
    "credentials": [
      "CPRW certification via PARWCC",
      "MA from UNC Chapel Hill"
    ],
    "niche_summary": "Executive resume writing, LinkedIn optimization, ATS compliance, career coaching for senior professionals",
    "audience": "VPs, Directors, C-suite leaders, Board members",
    "audience_examples": "VP of Marketing, Director of Engineering, CFO, Board Director",
    "specializations": [
      "executive and board-level resumes",
      "LinkedIn profile optimization",
      "ATS compliance",
      "federal resumes",
      "salary negotiation positioning"
    ],
    "client_outcomes": "Fortune 30 companies, high-growth startups, Board seats"
  },

  "platform": {
    "name": "LinkedIn",
    "post_word_range": [150, 300],
    "carousel_dimensions": [1080, 1080],
    "scheduling_url": "https://linkedin.com/feed"
  },

  "brand": {
    "primary": "#1B3A4B",
    "secondary": "#4A90A4",
    "accent": "#D4A574",
    "background": "#FAFAF8",
    "background_alt": "#F0EDE8",
    "text_dark": "#2C2C2C",
    "text_light": "#FFFFFF",
    "text_muted": "#6B7280",
    "divider": "#D1D5DB",
    "negative": "#C0392B",
    "positive": "#27AE60",
    "font_heading": "Helvetica-Bold",
    "font_body": "Helvetica",
    "font_accent": "Helvetica-Oblique"
  },

  "content": {
    "categories": {
      "pattern": {
        "label": "Pattern",
        "prompt_label": "I keep seeing...",
        "placeholder": "Describe a pattern you keep seeing in your work or industry..."
      },
      "faq": {
        "label": "FAQ",
        "prompt_label": "Client asked...",
        "placeholder": "What question do you keep getting asked? What's your take?"
      },
      "noticed": {
        "label": "Noticed",
        "prompt_label": "Just noticed...",
        "placeholder": "What did you notice recently that others might have missed?"
      },
      "hottake": {
        "label": "Hot Take",
        "prompt_label": "Hot take...",
        "placeholder": "What's your spicy opinion? Why do you believe it?"
      }
    },
    "carousel_templates": ["tips", "beforeafter", "mythreality"],
    "default_ctas": {
      "tips": "Follow for more expert strategy",
      "beforeafter": "Save this for your next update",
      "mythreality": "Follow for more myth-busting strategy",
      "general": "Follow for more career strategy"
    }
  },

  "schedule": {
    "days": {
      "Monday": {
        "content_type": "Educational / Pattern",
        "suggestion": "Share a specific, actionable insight from your expertise"
      },
      "Tuesday": {
        "content_type": "Tactical Tip",
        "suggestion": "Share a specific, actionable tip from your domain"
      },
      "Wednesday": {
        "content_type": "Deep Dive / Story",
        "suggestion": "Tell a story or go deeper on a topic with a client example"
      },
      "Thursday": {
        "content_type": "Thought Leadership / Hot Take",
        "suggestion": "Challenge a common misconception in your industry"
      },
      "Friday": {
        "content_type": "Quick Win / Encouragement",
        "suggestion": "Share a quick, implementable insight your audience can use today"
      }
    },
    "suggested_times": {
      "Monday": "8:00 AM",
      "Tuesday": "7:30 AM",
      "Wednesday": "12:00 PM",
      "Thursday": "8:00 AM",
      "Friday": "9:00 AM"
    },
    "timezone": "EST"
  },

  "feeds": {
    "categories": {
      "leadership": "Executive leadership, management strategy, C-suite perspectives",
      "careers": "General career advice, professional development, job search strategies",
      "executive_careers": "Senior-level and executive career content specifically",
      "hr_recruiting": "Recruiting practices, hiring processes, what recruiters look for",
      "labor_data": "Employment statistics, job market reports, economic indicators",
      "linkedin": "LinkedIn platform updates, algorithm changes, feature releases",
      "hr_tech": "HR technology, ATS platforms, recruiting tools",
      "compensation": "Salary data, compensation trends, negotiation research",
      "workplace": "Workplace culture, remote work, employee experience",
      "business_news": "General business news with career relevance"
    }
  },

  "scoring": {
    "high_relevance_threshold": 0.7,
    "medium_relevance_threshold": 0.5,
    "scoring_description": "Score articles for relevance to {owner.name}'s niche: {owner.niche_summary}. Target audience: {owner.audience}.",
    "scoring_high": "Directly relevant to {owner.niche_summary} or topics {owner.audience} would care about",
    "scoring_low": "Unrelated industry news, entry-level advice, or topics {owner.name} has no credible expertise to comment on"
  }
}
```

---

## Step 2: Create `business_config.py` loader module

**Create file:** `signal-and-stance/business_config.py`

This module loads `business_config.json` and provides convenient accessors. It also performs simple `{owner.name}` style interpolation in string values from the scoring section.

```python
"""Centralized business configuration loader.

Reads business_config.json once at import time and exposes the config
as a module-level dict. All business-specific identity, brand, domain,
and scheduling values live in that JSON file.
"""

import json
import os
import re

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "business_config.json")

with open(_CONFIG_PATH, "r", encoding="utf-8") as _f:
    BUSINESS = json.load(_f)


def _resolve(template_str):
    """Replace {section.key} placeholders with values from BUSINESS config.

    Supports one level of nesting: {owner.name}, {platform.name}, etc.
    """
    def _replacer(match):
        path = match.group(1)
        parts = path.split(".")
        val = BUSINESS
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part, match.group(0))
            else:
                return match.group(0)
        return str(val) if not isinstance(val, dict) else match.group(0)

    return re.sub(r"\{(\w+\.\w+)\}", _replacer, template_str)


# Convenience accessors
OWNER = BUSINESS["owner"]
PLATFORM = BUSINESS["platform"]
BRAND_COLORS = BUSINESS["brand"]
CONTENT = BUSINESS["content"]
SCHEDULE = BUSINESS["schedule"]
FEEDS_CONFIG = BUSINESS["feeds"]
SCORING = BUSINESS["scoring"]
APP_NAME = BUSINESS["app_name"]

# Pre-resolved scoring strings
SCORING_DESCRIPTION = _resolve(SCORING["scoring_description"])
SCORING_HIGH = _resolve(SCORING["scoring_high"])
SCORING_LOW = _resolve(SCORING["scoring_low"])
```

---

## Step 3: Update `brand.py` to read from business config

**Edit file:** `signal-and-stance/brand.py`

Replace the entire file contents. The BRAND dict should be assembled from `business_config.json` so that `carousel_renderer.py` (which imports `BRAND`) continues to work without changes.

```python
"""Brand configuration for carousel rendering.

Reads visual identity and author metadata from business_config.json.
"""

from business_config import BRAND_COLORS, OWNER, PLATFORM

BRAND = {
    # Colors
    "primary": BRAND_COLORS["primary"],
    "secondary": BRAND_COLORS["secondary"],
    "accent": BRAND_COLORS["accent"],
    "background": BRAND_COLORS["background"],
    "background_alt": BRAND_COLORS["background_alt"],
    "text_dark": BRAND_COLORS["text_dark"],
    "text_light": BRAND_COLORS["text_light"],
    "text_muted": BRAND_COLORS["text_muted"],
    "divider": BRAND_COLORS["divider"],
    "negative": BRAND_COLORS["negative"],
    "positive": BRAND_COLORS["positive"],
    # Typography
    "font_heading": BRAND_COLORS["font_heading"],
    "font_body": BRAND_COLORS["font_body"],
    "font_accent": BRAND_COLORS["font_accent"],
    # Slide dimensions
    "slide_width": PLATFORM["carousel_dimensions"][0],
    "slide_height": PLATFORM["carousel_dimensions"][1],
    # Author
    "author_name": OWNER["name"],
    "author_title": OWNER["title"],
    "author_business": OWNER["business"],
    "author_url": OWNER["url"],
}
```

**Verification:** `carousel_renderer.py` imports `from brand import BRAND` and accesses keys like `BRAND["author_name"]`, `BRAND["primary"]`, `BRAND["slide_width"]`, etc. All these keys are preserved, so **no changes needed in `carousel_renderer.py`**.

---

## Step 4: Update `config.py` to read from business config

**Edit file:** `signal-and-stance/config.py`

Replace the hardcoded `CONTENT_SCHEDULE`, `SUGGESTED_TIMES`, and `DATABASE_PATH` with values from business config.

The current file (46 lines) should become:

```python
import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from business_config import BUSINESS, SCHEDULE

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
DATABASE_PATH = os.path.join(
    os.path.dirname(__file__), BUSINESS["database_name"]
)

# Weekly content schedule — read from business config
CONTENT_SCHEDULE = {}
for day, info in SCHEDULE["days"].items():
    CONTENT_SCHEDULE[day] = {
        "type": info["content_type"],
        "suggestion": info["suggestion"],
    }

# Suggested posting times
SUGGESTED_TIMES = SCHEDULE["suggested_times"]
```

**Verification:** `database.py` imports `CONTENT_SCHEDULE` and `SUGGESTED_TIMES` from `config.py`. The dict structure is preserved (`CONTENT_SCHEDULE["Monday"]["type"]` and `CONTENT_SCHEDULE["Monday"]["suggestion"]`), so `database.py` needs no changes.

---

## Step 5: Update `feeds.py` to read categories from business config

**Edit file:** `signal-and-stance/feeds.py`

The `FEED_CATEGORIES` dict at lines 95-106 should read from business config. The `DEFAULT_FEEDS` list (12 feeds) stays in this file for now — feeds are content-specific data, not identity config.

Replace lines 95-106 (the `FEED_CATEGORIES` definition) with:

```python
from business_config import FEEDS_CONFIG

FEED_CATEGORIES = FEEDS_CONFIG["categories"]
```

Keep the `DEFAULT_FEEDS` list unchanged (lines 1-93). The feeds are still hardcoded but they're already isolated in this one file and are intentionally content-specific.

---

## Step 6: Update `feed_scanner.py` scoring prompt

**Edit file:** `signal-and-stance/feed_scanner.py`

The hardcoded scoring prompt at lines 113-128 references "Dana Wang, a Certified Professional Resume Writer (CPRW)..." This should read from business config.

Replace the hardcoded system prompt (around lines 113-128 inside `score_articles()`) with a dynamically built prompt:

```python
from business_config import OWNER, SCORING_DESCRIPTION, SCORING_HIGH, SCORING_LOW

# Inside score_articles(), replace the hardcoded system_prompt string with:
system_prompt = (
    f"You are an editorial relevance scorer for {OWNER['name']}, "
    f"a {OWNER['title']} who specializes in {OWNER['niche_summary']}. "
    f"Target audience: {OWNER['audience']}.\n\n"
    f"Score each article from 0.0 to 1.0 for relevance.\n\n"
    f"High (0.8-1.0): {SCORING_HIGH}\n"
    f"Medium (0.5-0.7): Tangentially relevant — could be spun into content with effort\n"
    f"Low (0.2-0.4): Weak connection to the niche\n"
    f"None (0.0-0.1): {SCORING_LOW}\n\n"
    f"Return JSON array: [{{\"id\": <id>, \"score\": <float>, \"reason\": \"<1 sentence>\"}}]"
)
```

Find the exact location by searching for `"You are an editorial relevance scorer"` or `"Dana Wang, a Certified Professional"` in `feed_scanner.py`.

---

## Step 7: Update `engine.py` scattered strings

**Edit file:** `signal-and-stance/engine.py`

There are 8 hardcoded strings to replace. Add this import at the top:

```python
from business_config import OWNER, PLATFORM, CONTENT
```

Then make these replacements:

1. **Line 68** (autopilot user message) — replace:
   ```python
   "Find a current, relevant career/hiring/resume topic"
   ```
   with:
   ```python
   f"Find a current, relevant topic related to {OWNER['niche_summary']}"
   ```

2. **Line 114** (URL reaction user message) — replace:
   ```python
   f"Read this article/post and generate LinkedIn reaction posts from Dana's perspective:\n\n{url}"
   ```
   with:
   ```python
   f"Read this article/post and generate {PLATFORM['name']} reaction posts from {OWNER['name']}'s perspective:\n\n{url}"
   ```

3. **Line 161** (feed article user message) — replace:
   ```python
   f"Generate LinkedIn posts reacting to this article from Dana's curated feed.\n\n"
   ```
   with:
   ```python
   f"Generate {PLATFORM['name']} posts reacting to this article from {OWNER['name']}'s curated feed.\n\n"
   ```

4. **Line 166** (default relevance reason) — replace:
   ```python
   "Matches Dana niche."
   ```
   with:
   ```python
   f"Matches {OWNER['name']}'s niche."
   ```

5. **Line 245** (docstring comment) — replace:
   ```python
   "Dana's insight/observation text"
   ```
   with:
   ```python
   "The owner's insight/observation text"
   ```

6. **Line 342** (tips CTA default) — replace:
   ```python
   "Follow for more executive career strategy"
   ```
   with:
   ```python
   CONTENT["default_ctas"]["tips"]
   ```

7. **Line 376** (beforeafter CTA default) — replace:
   ```python
   "Save this for your next resume update"
   ```
   with:
   ```python
   CONTENT["default_ctas"]["beforeafter"]
   ```

8. **Line 409** (mythreality CTA default) — replace:
   ```python
   "Follow for more myth-busting resume strategy"
   ```
   with:
   ```python
   CONTENT["default_ctas"]["mythreality"]
   ```

---

## Step 8: Update `app.py` fallback string

**Edit file:** `signal-and-stance/app.py`

1. Add import at top:
   ```python
   from business_config import APP_NAME
   ```

2. **Line 58** — replace:
   ```python
   "Signal & Stance is running."
   ```
   with:
   ```python
   f"{APP_NAME} is running."
   ```

---

## Step 9: Update `templates/index.html` title/headers

**Edit file:** `signal-and-stance/templates/index.html`

Since this is a Jinja2 template served by Flask, the simplest approach is to pass `app_name` from the route.

1. **In `app.py`**, update the index route (around line 56):
   ```python
   return render_template("index.html", api_key_missing=API_KEY_MISSING, app_name=APP_NAME)
   ```

2. **In `index.html`**, replace the 3 hardcoded "Signal & Stance" references:
   - **Line 6**: `<title>Signal &amp; Stance</title>` -> `<title>{{ app_name }}</title>`
   - **Line 20**: `<h1>Signal &amp; Stance</h1>` -> `<h1>{{ app_name }}</h1>`
   - **Line 37**: `<h1>Signal &amp; Stance</h1>` -> `<h1>{{ app_name }}</h1>`

---

## Step 10: Update `carousel_renderer.py` default CTA

**Edit file:** `signal-and-stance/carousel_renderer.py`

1. Add import at top:
   ```python
   from business_config import CONTENT
   ```

2. **Line 426** (inside `render_carousel()`) — find the default CTA fallback string `"Follow for more career strategy"` and replace with:
   ```python
   CONTENT["default_ctas"]["general"]
   ```

---

## Verification Checklist

After completing all steps, verify:

- [ ] `python -c "from business_config import BUSINESS; print(BUSINESS['owner']['name'])"` prints "Dana Wang"
- [ ] `python -c "from brand import BRAND; print(BRAND['author_name'])"` prints "Dana Wang"
- [ ] `python -c "from config import CONTENT_SCHEDULE; print(CONTENT_SCHEDULE['Monday']['type'])"` prints "Educational / Pattern"
- [ ] `python -c "from feeds import FEED_CATEGORIES; print(list(FEED_CATEGORIES.keys()))"` prints the 10 category keys
- [ ] `python app.py` starts without errors
- [ ] The UI loads and shows the app name from config
- [ ] Generate a test post (any category) — should work identically
- [ ] Generate a carousel — PDF should show correct author info
- [ ] Run existing tests: `python test_engine.py` and `python test_carousel.py`

---

## What This Phase Achieves

**Before:** Business identity spread across 15+ files, 66 coupling points.
**After:** All identity/brand/schedule/scoring config in one JSON file. Changing the business owner, brand, schedule, or scoring criteria is a single-file edit.

**Coupling points eliminated:** ~30 (all trivial + most moderate points from categories A, C, and parts of B, D, E, F)

**What remains for Phase 2:** The 11 prompt `.md` files still contain deeply authored, domain-specific content (voice rules, tone, examples, content arcs). Phase 2 addresses this with prompt templating.

---

## Files Created
- `signal-and-stance/business_config.json` (NEW)
- `signal-and-stance/business_config.py` (NEW)

## Files Modified
- `signal-and-stance/brand.py` (rewrite to read from business config)
- `signal-and-stance/config.py` (rewrite schedule/times to read from business config)
- `signal-and-stance/feeds.py` (replace FEED_CATEGORIES with business config import)
- `signal-and-stance/feed_scanner.py` (replace hardcoded scoring prompt)
- `signal-and-stance/engine.py` (replace 8 hardcoded strings)
- `signal-and-stance/app.py` (replace fallback string, pass app_name to template)
- `signal-and-stance/templates/index.html` (3 title/header replacements)
- `signal-and-stance/carousel_renderer.py` (1 default CTA replacement)
