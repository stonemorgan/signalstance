# Phase 4: Tenant Directory Structure & Multi-Business Support (Optional)

**Goal:** Separate the reusable framework (Flask routes, database, engine, renderer) from tenant-specific content (prompts, feeds, brand config) into distinct directories. Enable running the same app for different businesses by swapping the tenant directory.

**Prerequisite:** Phases 1-3 complete
**Estimated effort:** 8-12 hours
**Impact:** Enables true multi-tenant deployment. Each new business is a new tenant directory, not a codebase fork. Only pursue this phase if you plan to deploy for 2+ businesses.

---

## Context

After Phases 1-3, the codebase has:
- A centralized `business_config.json` with all identity/brand/schedule/scoring values
- Templatized prompt files with `{{variable}}` placeholders and clearly marked authored sections
- A config-driven frontend

But everything still lives in one flat directory. To support multiple businesses, you'd need to:
1. Copy the whole directory
2. Edit `business_config.json` and all 11 prompt files
3. Maintain two parallel codebases

This phase restructures the project so that framework code is shared and tenant-specific content is isolated.

---

## Target Directory Structure

```
signalstance/
├── framework/                          # Shared, reusable code
│   ├── app.py                          # Flask routes
│   ├── engine.py                       # Content generation pipeline
│   ├── database.py                     # SQLite CRUD
│   ├── carousel_renderer.py            # PDF generation
│   ├── feed_scanner.py                 # RSS fetching + scoring
│   ├── business_config.py              # Config loader (reads from active tenant)
│   ├── schema.sql                      # Database DDL
│   ├── requirements.txt                # Python dependencies
│   ├── templates/
│   │   └── index.html                  # Frontend SPA
│   └── static/
│       └── style.css                   # Styling
│
├── tenants/
│   ├── dana-wang/                      # Dana Wang / Raleigh Resume tenant
│   │   ├── business_config.json        # All identity, brand, schedule, scoring
│   │   ├── feeds.json                  # Default RSS feeds for this tenant
│   │   ├── prompts/
│   │   │   ├── base_system.md
│   │   │   ├── category_pattern.md
│   │   │   ├── category_faq.md
│   │   │   ├── category_noticed.md
│   │   │   ├── category_hottake.md
│   │   │   ├── autopilot.md
│   │   │   ├── url_react.md
│   │   │   ├── feed_react.md
│   │   │   ├── carousel_tips.md
│   │   │   ├── carousel_beforeafter.md
│   │   │   └── carousel_mythreality.md
│   │   ├── generated_carousels/        # PDF output (per-tenant)
│   │   └── signal_stance.db            # SQLite database (per-tenant)
│   │
│   └── _template/                      # Template tenant for new businesses
│       ├── business_config.json        # Skeleton with placeholders
│       ├── feeds.json                  # Empty feed list
│       └── prompts/
│           ├── base_system.md          # Template with {{}} vars + blank authored sections
│           └── ...                     # All 11 prompt templates
│
├── run.py                              # Entry point: selects tenant, starts app
├── MODULARITY-ASSESSMENT.md
├── MODULARIZATION-PHASE-*.md
└── .env                                # Shared: API key, model settings
```

---

## Step 1: Create `run.py` entry point

**Create file:** `signalstance/run.py`

This is the new entry point that selects a tenant and starts the app.

```python
"""Signal & Stance launcher.

Usage:
    python run.py                     # Uses default tenant (first in tenants/)
    python run.py --tenant dana-wang  # Uses specific tenant
    python run.py --list              # Lists available tenants
"""

import argparse
import os
import sys


def get_tenants_dir():
    return os.path.join(os.path.dirname(__file__), "tenants")


def list_tenants():
    tenants_dir = get_tenants_dir()
    tenants = []
    for name in sorted(os.listdir(tenants_dir)):
        tenant_path = os.path.join(tenants_dir, name)
        config_path = os.path.join(tenant_path, "business_config.json")
        if os.path.isdir(tenant_path) and os.path.exists(config_path) and name != "_template":
            tenants.append(name)
    return tenants


def main():
    parser = argparse.ArgumentParser(description="Signal & Stance launcher")
    parser.add_argument("--tenant", "-t", help="Tenant directory name")
    parser.add_argument("--list", "-l", action="store_true", help="List available tenants")
    args = parser.parse_args()

    if args.list:
        tenants = list_tenants()
        if tenants:
            print("Available tenants:")
            for t in tenants:
                print(f"  - {t}")
        else:
            print("No tenants found. Create one in tenants/ using _template as a guide.")
        sys.exit(0)

    # Select tenant
    tenants = list_tenants()
    if args.tenant:
        if args.tenant not in tenants:
            print(f"Tenant '{args.tenant}' not found. Available: {', '.join(tenants)}")
            sys.exit(1)
        tenant_name = args.tenant
    elif tenants:
        tenant_name = tenants[0]
        print(f"No tenant specified, using: {tenant_name}")
    else:
        print("No tenants found. Create one in tenants/ using _template as a guide.")
        sys.exit(1)

    tenant_path = os.path.join(get_tenants_dir(), tenant_name)

    # Set environment variable so framework code knows which tenant to load
    os.environ["SIGNALSTANCE_TENANT_DIR"] = tenant_path

    # Add framework to Python path
    framework_dir = os.path.join(os.path.dirname(__file__), "framework")
    sys.path.insert(0, framework_dir)

    # Import and run the app
    from app import app
    from config import FLASK_PORT
    app.run(debug=True, port=FLASK_PORT)


if __name__ == "__main__":
    main()
```

---

## Step 2: Update `business_config.py` to read from tenant directory

**Edit file:** `framework/business_config.py`

The config loader needs to find `business_config.json` in the active tenant directory (set by `SIGNALSTANCE_TENANT_DIR` env var) rather than in the framework directory.

```python
"""Centralized business configuration loader.

Reads business_config.json from the active tenant directory.
The tenant directory is specified by the SIGNALSTANCE_TENANT_DIR environment variable.
Falls back to looking in the same directory as this file (for backwards compatibility).
"""

import json
import os
import re

# Determine tenant directory
TENANT_DIR = os.environ.get("SIGNALSTANCE_TENANT_DIR")
if not TENANT_DIR:
    # Backwards compatibility: look in same directory as this file
    TENANT_DIR = os.path.dirname(__file__)

_CONFIG_PATH = os.path.join(TENANT_DIR, "business_config.json")

if not os.path.exists(_CONFIG_PATH):
    raise FileNotFoundError(
        f"business_config.json not found at {_CONFIG_PATH}. "
        f"Set SIGNALSTANCE_TENANT_DIR to the tenant directory."
    )

with open(_CONFIG_PATH, "r", encoding="utf-8") as _f:
    BUSINESS = json.load(_f)


def _resolve(template_str):
    """Replace {section.key} placeholders with values from BUSINESS config."""
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

## Step 3: Update `engine.py` to load prompts from tenant directory

**Edit file:** `framework/engine.py`

The `load_prompt()` function currently loads from the framework directory. It needs to check the tenant directory first.

```python
from business_config import TENANT_DIR

def load_prompt(filepath):
    """Load a prompt .md file from the tenant directory (with framework fallback)."""
    # Try tenant directory first
    tenant_path = os.path.join(TENANT_DIR, filepath)
    if os.path.exists(tenant_path):
        prompt_path = tenant_path
    else:
        # Fall back to framework directory
        prompt_path = os.path.join(os.path.dirname(__file__), filepath)

    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Template substitution (from Phase 2)
    def _replacer(match):
        key = match.group(1).strip()
        return _FLAT_CONFIG.get(key, match.group(0))
    return _re.sub(r"\{\{(.+?)\}\}", _replacer, template)
```

This means:
- Tenant prompts override framework defaults
- If a tenant doesn't provide a specific prompt, the framework version is used
- Prompt files can be added incrementally

---

## Step 4: Update `config.py` for tenant-aware database path

**Edit file:** `framework/config.py`

The database should live in the tenant directory, not the framework directory.

```python
from business_config import BUSINESS, SCHEDULE, TENANT_DIR

DATABASE_PATH = os.path.join(TENANT_DIR, BUSINESS["database_name"])
```

---

## Step 5: Extract `DEFAULT_FEEDS` to tenant `feeds.json`

**Create file:** `tenants/dana-wang/feeds.json`

Move the `DEFAULT_FEEDS` list from `feeds.py` into a JSON file in the tenant directory:

```json
[
  {
    "url": "https://www.mckinsey.com/insights/rss",
    "name": "McKinsey Insights",
    "category": "leadership",
    "weight": 1.2
  },
  {
    "url": "https://www.fastcompany.com/section/work-life/rss",
    "name": "Fast Company Work Life",
    "category": "careers",
    "weight": 1.0
  }
  // ... all 12 feeds
]
```

**Edit file:** `framework/feeds.py`

Update to load feeds from the tenant directory:

```python
import json
import os
from business_config import FEEDS_CONFIG, TENANT_DIR

FEED_CATEGORIES = FEEDS_CONFIG["categories"]

# Load default feeds from tenant directory
_FEEDS_PATH = os.path.join(TENANT_DIR, "feeds.json")
if os.path.exists(_FEEDS_PATH):
    with open(_FEEDS_PATH, "r", encoding="utf-8") as f:
        DEFAULT_FEEDS = json.load(f)
else:
    DEFAULT_FEEDS = []
```

---

## Step 6: Update `carousel_renderer.py` for tenant output directory

**Edit file:** `framework/carousel_renderer.py`

Carousel PDFs should be stored in the tenant directory:

```python
from business_config import TENANT_DIR

OUTPUT_DIR = os.path.join(TENANT_DIR, "generated_carousels")
```

---

## Step 7: Create the `_template` tenant

**Create directory:** `tenants/_template/`

This is a skeleton tenant that new businesses copy and customize.

**Create file:** `tenants/_template/business_config.json`

```json
{
  "app_name": "My Content Studio",
  "database_name": "content.db",

  "owner": {
    "name": "YOUR NAME",
    "title": "YOUR PROFESSIONAL TITLE",
    "business": "YOUR BUSINESS NAME",
    "url": "YOUR WEBSITE OR PROFILE URL",
    "credentials": ["CREDENTIAL 1", "CREDENTIAL 2"],
    "niche_summary": "Brief description of your expertise area",
    "audience": "Description of your target audience",
    "audience_examples": "Example job titles in your audience",
    "specializations": ["Specialization 1", "Specialization 2"],
    "client_outcomes": "Notable outcomes your clients achieve"
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
      "tips": "Follow for more expert insights",
      "beforeafter": "Save this for later",
      "mythreality": "Follow for more myth-busting content",
      "general": "Follow for more expert content"
    }
  },

  "schedule": {
    "days": {
      "Monday": { "content_type": "Educational / Pattern", "suggestion": "Share an insight from your expertise" },
      "Tuesday": { "content_type": "Tactical Tip", "suggestion": "Share an actionable tip from your domain" },
      "Wednesday": { "content_type": "Deep Dive / Story", "suggestion": "Tell a story or go deep on a topic" },
      "Thursday": { "content_type": "Thought Leadership / Hot Take", "suggestion": "Challenge a common misconception" },
      "Friday": { "content_type": "Quick Win / Encouragement", "suggestion": "Share a quick, implementable insight" }
    },
    "suggested_times": {
      "Monday": "8:00 AM", "Tuesday": "7:30 AM", "Wednesday": "12:00 PM",
      "Thursday": "8:00 AM", "Friday": "9:00 AM"
    },
    "timezone": "EST"
  },

  "feeds": {
    "categories": {
      "industry": "Your primary industry news",
      "trends": "Trends and developments in your field",
      "general": "General business and professional content"
    }
  },

  "scoring": {
    "high_relevance_threshold": 0.7,
    "medium_relevance_threshold": 0.5,
    "scoring_description": "Score articles for relevance to {owner.name}'s niche: {owner.niche_summary}.",
    "scoring_high": "Directly relevant to {owner.niche_summary}",
    "scoring_low": "Unrelated to {owner.name}'s expertise"
  }
}
```

**Create file:** `tenants/_template/feeds.json`

```json
[]
```

**Create template prompt files** in `tenants/_template/prompts/`:

Each should have the templatized structure from Phase 2 with blank authored sections clearly marked:

```markdown
<!-- tenants/_template/prompts/base_system.md -->

You are writing {{platform.name}} posts as {{owner.name}}. {{owner.name}} is a {{owner.title}} who runs {{owner.business}}. They work with {{owner.audience}}.

## Tone & Voice

<!-- AUTHORED SECTION: Define the persona's voice. How does this person communicate? -->
<!-- DELETE THIS COMMENT AND WRITE YOUR VOICE RULES HERE -->

## Signature Language

<!-- AUTHORED SECTION: What metaphors, stats, and framings does this person use? -->
<!-- DELETE THIS COMMENT AND LIST SIGNATURE PHRASES HERE -->

## Hard Rules

<!-- AUTHORED SECTION: What should this persona NEVER do? -->
<!-- DELETE THIS COMMENT AND LIST ANTI-PATTERNS HERE -->

## Credentials

- {{owner.credentials}}
- Works with: {{owner.audience}}
- Specializes in: {{owner.specializations}}

## {{platform.name}} Post Structure

Posts must be {{platform.post_word_range}} words.

<!-- AUTHORED SECTION: Platform-specific formatting rules -->
<!-- DELETE THIS COMMENT AND ADD PLATFORM RULES HERE -->

## Self-Evaluation Checklist

- [ ] Would {{owner.audience_examples}} find this relevant?
- [ ] Does it sound like {{owner.name}} — not like generic AI?
- [ ] Is there a specific, non-obvious insight?
- [ ] Would someone save or share this?
```

Create similar templates for all 11 prompt files.

---

## Step 8: Move Dana's content to `tenants/dana-wang/`

Move (not copy) Dana's business-specific files:
- `business_config.json` -> `tenants/dana-wang/business_config.json`
- All `prompts/*.md` files -> `tenants/dana-wang/prompts/`
- `feeds.py` DEFAULT_FEEDS data -> `tenants/dana-wang/feeds.json`
- `signal_stance.db` -> `tenants/dana-wang/signal_stance.db`
- `generated_carousels/` -> `tenants/dana-wang/generated_carousels/`

---

## Step 9: Update `.gitignore`

Add tenant-specific files that shouldn't be tracked:

```
tenants/*/signal_stance.db
tenants/*/content.db
tenants/*/*.db
tenants/*/generated_carousels/*.pdf
```

---

## Step 10: Create new-tenant setup script

**Create file:** `setup_tenant.py`

```python
"""Create a new tenant from the template."""

import os
import shutil
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python setup_tenant.py <tenant-name>")
        print("Example: python setup_tenant.py alex-chen")
        sys.exit(1)

    tenant_name = sys.argv[1]
    tenants_dir = os.path.join(os.path.dirname(__file__), "tenants")
    template_dir = os.path.join(tenants_dir, "_template")
    target_dir = os.path.join(tenants_dir, tenant_name)

    if os.path.exists(target_dir):
        print(f"Tenant '{tenant_name}' already exists at {target_dir}")
        sys.exit(1)

    if not os.path.exists(template_dir):
        print(f"Template directory not found at {template_dir}")
        sys.exit(1)

    shutil.copytree(template_dir, target_dir)
    os.makedirs(os.path.join(target_dir, "generated_carousels"), exist_ok=True)

    print(f"Created tenant: {target_dir}")
    print(f"\nNext steps:")
    print(f"  1. Edit {os.path.join(target_dir, 'business_config.json')} with your business details")
    print(f"  2. Add RSS feeds to {os.path.join(target_dir, 'feeds.json')}")
    print(f"  3. Write your voice profile in {os.path.join(target_dir, 'prompts', 'base_system.md')}")
    print(f"  4. Customize remaining prompt files in {os.path.join(target_dir, 'prompts/')}")
    print(f"  5. Run: python run.py --tenant {tenant_name}")


if __name__ == "__main__":
    main()
```

---

## Verification Checklist

- [ ] `python run.py --list` shows "dana-wang"
- [ ] `python run.py --tenant dana-wang` starts the app successfully
- [ ] `python run.py` (no args) defaults to dana-wang
- [ ] All existing functionality works (generate, calendar, feeds, carousels)
- [ ] `python setup_tenant.py test-tenant` creates a new tenant from template
- [ ] `python run.py --tenant test-tenant` starts (may fail on generation without prompts filled in, but app loads)
- [ ] Database files are created in the tenant directory, not the framework directory
- [ ] Carousel PDFs are saved in the tenant's `generated_carousels/` directory
- [ ] Prompts load from the tenant directory

---

## What This Phase Achieves

**Before (after Phases 1-3):** Single-tenant app with centralized config. Swapping businesses means editing config + prompts in-place.

**After:** Multi-tenant-ready architecture. Each business is a self-contained directory with its own config, prompts, feeds, database, and generated files. The framework code is shared. Adding a new business is:

1. `python setup_tenant.py new-business` (30 seconds)
2. Fill in `business_config.json` (15 minutes)
3. Add RSS feeds to `feeds.json` (30 minutes)
4. Write prompt files (10-20 hours of creative work)
5. `python run.py --tenant new-business`

**Total setup time for a new business:** ~12-22 hours (dominated by prompt authoring), down from ~35 hours before any modularization.

---

## Files Created
- `run.py` (entry point)
- `setup_tenant.py` (new tenant helper)
- `tenants/_template/` (entire template directory)
- `tenants/dana-wang/` (Dana's content moved here)

## Files Modified
- `framework/business_config.py` (tenant-aware config loading)
- `framework/engine.py` (tenant-aware prompt loading)
- `framework/config.py` (tenant-aware database path)
- `framework/feeds.py` (load feeds from tenant JSON)
- `framework/carousel_renderer.py` (tenant-aware output directory)
- `.gitignore` (exclude tenant databases and PDFs)

## Directory Moves
- `signal-and-stance/` -> `framework/` (rename)
- `business_config.json` -> `tenants/dana-wang/business_config.json`
- `prompts/` -> `tenants/dana-wang/prompts/`
- `signal_stance.db` -> `tenants/dana-wang/signal_stance.db`
- `generated_carousels/` -> `tenants/dana-wang/generated_carousels/`
- `feeds.py` DEFAULT_FEEDS -> `tenants/dana-wang/feeds.json`

---

## Decision: Should You Do This Phase?

**Do Phase 4 if:**
- You plan to deploy this app for 2+ different businesses
- You want to offer this as a white-label product
- You want to keep business content completely isolated from framework code

**Skip Phase 4 if:**
- This is only for Dana Wang's business
- You might swap once in the future but aren't sure
- The effort isn't justified by the use case

Phases 1-3 alone bring the modularity score from 4/10 to approximately 7/10 and reduce swap effort from ~35 hours to ~15-20 hours. Phase 4 brings it to ~9/10 but requires significant restructuring.
