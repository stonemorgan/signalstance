# Modularity Assessment Report

**Signal & Stance Codebase**
**Date:** 2026-03-15
**Question:** How easily could this entire app ecosystem be swapped from Dana Wang's resume writing business to an entirely different business with a different owner?

---

## 1. Architecture Overview

Signal & Stance is a locally-hosted Flask (Python 3.11+) web application that generates LinkedIn content in a specific business owner's voice. It uses Claude (Anthropic API) for content generation and SQLite for persistence.

**Stack:** Flask 3.0 + vanilla HTML/CSS/JS + SQLite + Anthropic Claude API + ReportLab (PDF)

**File inventory (runtime-critical):**

| File | Lines | Role |
|------|-------|------|
| `signal-and-stance/app.py` | 918 | Flask routes (24+ endpoints) |
| `signal-and-stance/engine.py` | 480 | Content generation, prompt loading, parsing |
| `signal-and-stance/database.py` | 531 | SQLite schema, CRUD |
| `signal-and-stance/carousel_renderer.py` | 492 | PDF carousel generation |
| `signal-and-stance/feed_scanner.py` | 185 | RSS fetching, relevance scoring |
| `signal-and-stance/config.py` | 46 | App settings, schedule, times |
| `signal-and-stance/brand.py` | 36 | Visual identity for carousels |
| `signal-and-stance/feeds.py` | 107 | 12 default RSS feeds + categories |
| `signal-and-stance/schema.sql` | 77 | Database DDL |
| `signal-and-stance/templates/index.html` | ~3200 | Entire frontend (SPA) |
| `signal-and-stance/static/style.css` | ~900 | All styling |
| `signal-and-stance/prompts/` (11 files) | ~600 | Voice profile + generation templates |

---

## 2. Coupling Inventory

Every hardcoded business-specific reference is catalogued below, organized by coupling category.

---

### Category A: Owner Identity

Direct references to the business owner's name, credentials, education, and personal branding.

| # | File | Line(s) | Content | Swap Effort |
|---|------|---------|---------|-------------|
| A1 | `brand.py` | 1 | Comment: `Dana Wang / Raleigh Resume` | Trivial |
| A2 | `brand.py` | 26 | `"author_name": "Dana Wang"` | Trivial |
| A3 | `brand.py` | 27 | `"author_title": "Certified Professional Resume Writer (CPRW)"` | Trivial |
| A4 | `brand.py` | 28 | `"author_business": "Raleigh Resume"` | Trivial |
| A5 | `brand.py` | 29 | `"author_url": "linkedin.com/in/danaxwang"` | Trivial |
| A6 | `prompts/base_system.md` | 1 | Full identity paragraph: name, CPRW, Raleigh Resume, PARWCC, UNC Chapel Hill, Fortune 30 clients, board seats | **Full rewrite** |
| A7 | `prompts/base_system.md` | 34-38 | Credentials block: CPRW, PARWCC, MA UNC Chapel Hill, Fortune 30, executive/board resumes, LinkedIn optimization, ATS, federal resumes | **Full rewrite** |
| A8 | `prompts/base_system.md` | 62 | Self-eval: "Would a VP of Marketing or Director of Engineering find this relevant?" | Moderate |
| A9 | `prompts/base_system.md` | 63 | "Does it sound like Dana wrote it at her desk after a client call" | Moderate |
| A10 | `prompts/base_system.md` | 67 | "Does it use at least one of Dana's signature framings" | Moderate |
| A11 | `config.py` | 38 | Comment: "Dana uses these as guidance when scheduling on LinkedIn" | Trivial |
| A12 | `feed_scanner.py` | 103 | "Score a batch of articles for relevance to Dana's niche" | Moderate |
| A13 | `feed_scanner.py` | 113-128 | Entire scoring system prompt names "Dana Wang, a Certified Professional Resume Writer (CPRW)" with full niche description | **Full rewrite** |
| A14 | `engine.py` | 114 | "generate LinkedIn reaction posts from Dana's perspective" | Moderate |
| A15 | `engine.py` | 161 | "Generate LinkedIn posts reacting to this article from Dana's curated feed" | Moderate |
| A16 | `engine.py` | 166 | "Matches Dana niche" | Moderate |
| A17 | `engine.py` | 245 | Comment: "Dana's insight/observation text" | Trivial |

**Total: 17 coupling points**

---

### Category B: Business Domain (Resume Writing)

Content and logic that assumes the business is about resume writing, career strategy, and executive positioning.

| # | File | Line(s) | Content | Swap Effort |
|---|------|---------|---------|-------------|
| B1 | `prompts/base_system.md` | 7-9 | Tone rules: "ROI, metrics, business cases," empathetic-but-authoritative stance framing | **Full rewrite** |
| B2 | `prompts/base_system.md` | 11-17 | Signature language: "marketing assets," "business cases for hiring you," "6-second scan," "20% interview rate," "$55k salary increase," pitch deck analogy | **Full rewrite** |
| B3 | `prompts/base_system.md` | 19-32 | Hard rules: 14 specific "never do" rules (no "You've got this!", no numbered lists, etc.) | **Full rewrite** |
| B4 | `prompts/base_system.md` | 40-54 | LinkedIn post structure: hook rules, body rules, length 150-300 words, CTA rules | Moderate |
| B5 | `prompts/base_system.md` | 56-68 | Self-evaluation checklist (8 items referencing Dana's voice, VPs, etc.) | **Full rewrite** |
| B6 | `prompts/category_pattern.md` | 1-19 | Entire file: resume pattern/mistake post template with ATS, recruiters, salary references | **Full rewrite** |
| B7 | `prompts/category_faq.md` | 1-19 | Entire file: client FAQ template with resume-specific examples and arcs | **Full rewrite** |
| B8 | `prompts/category_hottake.md` | 1-19 | Entire file: hot take template with resume/cover letter examples | **Full rewrite** |
| B9 | `prompts/category_noticed.md` | 1-17 | Entire file: market observation template about hiring and career shifts | **Full rewrite** |
| B10 | `prompts/autopilot.md` | 1-86 | Entire file: web search topics (executive hiring, ATS, LinkedIn, salary data, etc.), evaluation criteria, Dana-specific quality gate | **Full rewrite** |
| B11 | `prompts/url_react.md` | 1-71 | Entire file: URL reaction with resume/career/executive positioning framing | **Full rewrite** |
| B12 | `prompts/feed_react.md` | 1-89 | Entire file: feed reaction with category-specific approaches (labor_data, leadership, hr_recruiting, etc.) | **Full rewrite** |
| B13 | `prompts/carousel_tips.md` | 1-91 | Entire file: resume-specific tip examples ("7 Resume Mistakes"), Dana's voice rules | **Full rewrite** |
| B14 | `prompts/carousel_beforeafter.md` | 1-90 | Entire file: resume before/after examples with resume bullets | **Full rewrite** |
| B15 | `prompts/carousel_mythreality.md` | 1-83 | Entire file: ATS myth examples, resume misconceptions | **Full rewrite** |
| B16 | `config.py` | 13-34 | Weekly content schedule: types ("Educational / Pattern," "Tactical Tip," "Hot Take") and suggestions referencing "resumes, LinkedIn, or job search" | Moderate |
| B17 | `feed_scanner.py` | 113-128 | Scoring criteria: "executive careers, resume strategy, ATS systems, LinkedIn optimization, salary negotiation, hiring trends at the senior level" | **Full rewrite** |
| B18 | `engine.py` | 68 | Autopilot user message: "Find a current, relevant career/hiring/resume topic" | Moderate |
| B19 | `engine.py` | 342 | Default CTA fallback: "Follow for more executive career strategy" | Trivial |
| B20 | `engine.py` | 376 | Default CTA fallback: "Save this for your next resume update" | Trivial |
| B21 | `engine.py` | 409 | Default CTA fallback: "Follow for more myth-busting resume strategy" | Trivial |
| B22 | `carousel_renderer.py` | 426 | Default CTA fallback: "Follow for more career strategy" | Trivial |

**Total: 22 coupling points**

---

### Category C: Brand Identity & Visual Design

App name, color palette, typography, and visual branding baked into the codebase.

| # | File | Line(s) | Content | Swap Effort |
|---|------|---------|---------|-------------|
| C1 | `brand.py` | 6-18 | Full color palette: navy (#1B3A4B), teal (#4A90A4), gold (#D4A574), semantic colors | Trivial |
| C2 | `brand.py` | 20-23 | Typography: Helvetica variants | Trivial |
| C3 | `brand.py` | 33-34 | Slide dimensions: 1080x1080 | Trivial |
| C4 | `templates/index.html` | 6 | `<title>Signal &amp; Stance</title>` | Trivial |
| C5 | `templates/index.html` | 20 | `<h1>Signal &amp; Stance</h1>` | Trivial |
| C6 | `templates/index.html` | 37 | `<h1>Signal &amp; Stance</h1>` (mobile) | Trivial |
| C7 | `app.py` | 58 | Fallback: `"Signal & Stance is running."` | Trivial |
| C8 | `carousel_renderer.py` | 1 | Docstring: "PDF carousel renderer for Signal & Stance" | Trivial |
| C9 | `config.py` | 10 | Database name: `"signal_stance.db"` | Trivial |

**Total: 9 coupling points**

---

### Category D: Platform Coupling (LinkedIn)

Assumes the distribution platform is LinkedIn specifically.

| # | File | Line(s) | Content | Swap Effort |
|---|------|---------|---------|-------------|
| D1 | `prompts/base_system.md` | 1 | "writing LinkedIn posts" | Trivial |
| D2 | `prompts/base_system.md` | 40-54 | LinkedIn-specific post structure (150-300 words, "see more" hook, paragraph spacing for LinkedIn's collapse behavior) | Moderate |
| D3 | `templates/index.html` | 1461 | "Scheduled for [time] EST on LinkedIn" | Trivial |
| D4 | `templates/index.html` | 1500 | "Copy & Schedule on LinkedIn" button | Trivial |
| D5 | `templates/index.html` | 1549 | "cancel the scheduled post on LinkedIn" | Trivial |
| D6 | `templates/index.html` | 1762 | Opens LinkedIn in new tab | Trivial |
| D7 | `templates/index.html` | 1781 | "Paste your post on LinkedIn, then use the clock icon to schedule it" | Trivial |
| D8 | `config.py` | 37-38 | Comments referencing "LinkedIn engagement sweet spots" | Trivial |
| D9 | `templates/index.html` | 208, 235 | Feed category dropdown: "LinkedIn" option | Trivial |
| D10 | `templates/index.html` | 2070 | Category display map: `'linkedin': 'LinkedIn'` | Trivial |

**Total: 10 coupling points**

---

### Category E: Feed Sources & Niche Targeting

Hardcoded RSS feeds and category taxonomy targeting the resume/career/executive niche.

| # | File | Line(s) | Content | Swap Effort |
|---|------|---------|---------|-------------|
| E1 | `feeds.py` | 1-93 | 12 hardcoded RSS feeds: McKinsey, Fast Company, HR Dive, RecruitingDaily, Undercover Recruiter, BLS, Indeed Hiring Lab, Ask a Manager, Inc., Fortune, Workology, Glassdoor | **Full replacement** |
| E2 | `feeds.py` | 95-106 | 10 category definitions: leadership, careers, executive_careers, hr_recruiting, labor_data, linkedin, hr_tech, compensation, workplace, business_news | **Full replacement** |

**Total: 2 coupling points (but high impact)**

---

### Category F: Content Categories & Generation Logic

The 4 content category types (pattern, faq, noticed, hottake) and 3 carousel templates (tips, beforeafter, mythreality).

| # | File | Line(s) | Content | Swap Effort |
|---|------|---------|---------|-------------|
| F1 | `engine.py` | 12-17 | `CATEGORY_FILE_MAP`: pattern, faq, noticed, hottake | Low-Moderate |
| F2 | `engine.py` | 232-236 | `CAROUSEL_PROMPT_MAP`: tips, beforeafter, mythreality | Low-Moderate |
| F3 | `app.py` | 49 | `VALID_CATEGORIES` set | Trivial |
| F4 | `app.py` | 74 | Category validation in `/api/generate` | Trivial |
| F5 | `app.py` | 659 | `VALID_TEMPLATES` set | Trivial |
| F6 | `templates/index.html` | ~200-240 | Category selector buttons (Pattern, FAQ, Noticed, Hot Take) | Moderate |

**Total: 6 coupling points**

---

### Coupling Summary

| Category | Points | Full Rewrite Needed | Moderate | Trivial |
|----------|--------|-------------------|----------|---------|
| A: Owner Identity | 17 | 3 | 4 | 10 |
| B: Business Domain | 22 | 15 | 3 | 4 |
| C: Brand/Visual | 9 | 0 | 0 | 9 |
| D: Platform (LinkedIn) | 10 | 0 | 1 | 9 |
| E: Feed Sources | 2 | 2 | 0 | 0 |
| F: Content Categories | 6 | 0 | 2 | 4 |
| **TOTAL** | **66** | **20** | **10** | **36** |

---

## 3. Modularity Score

### Score: 4 / 10

**Translation:** The app is a *moderately coupled monolith* with a clean architecture undermined by deep domain embedding. The infrastructure (Flask routes, database, PDF renderer, feed scanner) is solid and generic. But the *content layer* — prompts, voice rules, scoring criteria, feed sources — is hardwired to a single business identity at every level.

### What's good (why it's not a 1/10)

1. **`brand.py` exists.** Visual identity (colors, fonts, author info) is centralized in one 36-line file. Changing the carousel branding is a single-file edit.

2. **`config.py` exists.** App settings, schedule, and times are centralized. Easy to swap.

3. **`feeds.py` is separate.** Default feeds and categories are isolated, not scattered across multiple files.

4. **Prompt files are separate.** Voice rules and generation templates live in `prompts/` as `.md` files loaded at runtime, not embedded in Python code. They're replaceable without touching any `.py` file.

5. **The database schema is domain-agnostic.** Tables like `insights`, `generations`, `calendar_slots`, `feeds`, `feed_articles`, and `carousel_data` have generic column names. Nothing in `schema.sql` says "resume" or "Dana."

6. **`database.py` is domain-agnostic.** Zero business-specific references. Pure CRUD.

7. **`static/style.css` is domain-agnostic.** Zero business references. Colors are in CSS custom properties, not hardcoded.

8. **The generation architecture is cleanly layered.** `engine.py` loads prompts from files, calls Claude, parses responses. The prompt content is what's coupled, not the machinery.

### What's bad (why it's not a 7/10)

1. **All 11 prompt files (600+ lines) must be rewritten from scratch.** These aren't templates with fill-in-the-blank variables. They are deeply authored voice profiles, tone rules, content arcs, scoring rubrics, and example outputs. Writing a new `base_system.md` for a different business is equivalent to building a new product's creative brief. This is the single biggest barrier.

2. **`feed_scanner.py` contains a hardcoded scoring prompt** (lines 113-128) that names the owner, their certification, and their exact niche. The scoring logic is inseparable from the business identity.

3. **`engine.py` has scattered Dana-specific strings** in user messages sent to Claude (lines 68, 114, 161, 166). These reference "Dana's perspective," "Dana's curated feed," and "Dana niche."

4. **The content category system (pattern/faq/noticed/hottake) is resume-business-specific.** While the categories are structurally generic, their names and descriptions assume a consulting/service business where the owner observes client patterns, answers client FAQs, and takes industry stances. A product business, a retail business, or a SaaS business would need different category archetypes.

5. **LinkedIn is assumed as the only distribution channel.** The frontend has LinkedIn-specific scheduling UI, the prompts target LinkedIn post structure, and the carousel dimensions are LinkedIn-optimized (1080x1080). Swapping to Twitter/X, Instagram, or a blog would require UI changes plus prompt rewrites.

6. **No configuration abstraction layer.** There's no `business_config.json` or "tenant" concept. Business identity is spread across `brand.py`, `config.py`, `feeds.py`, all 11 prompt files, scattered `engine.py` strings, and `feed_scanner.py`. A swap requires touching 15+ files.

---

## 4. What Would Need to Change for a Full Business Swap

Assume the target: swap from "Dana Wang / Resume Writing / LinkedIn" to "Alex Chen / Independent Bookshop / Instagram."

### Tier 1: Must Change (app won't work correctly otherwise)

| # | File | What to Change | Effort |
|---|------|---------------|--------|
| 1 | `prompts/base_system.md` | Complete rewrite: new owner identity, voice rules, tone, signature language, hard rules, post structure, self-eval checklist | **4-8 hours** |
| 2 | `prompts/category_pattern.md` | Complete rewrite: new content arc for this business's "patterns" | **1-2 hours** |
| 3 | `prompts/category_faq.md` | Complete rewrite: new FAQ arc | **1-2 hours** |
| 4 | `prompts/category_hottake.md` | Complete rewrite: new hot take arc | **1-2 hours** |
| 5 | `prompts/category_noticed.md` | Complete rewrite: new observation arc | **1-2 hours** |
| 6 | `prompts/autopilot.md` | Complete rewrite: new search topics, evaluation criteria, quality gate | **2-3 hours** |
| 7 | `prompts/url_react.md` | Complete rewrite: new reaction approaches | **1-2 hours** |
| 8 | `prompts/feed_react.md` | Complete rewrite: new feed-specific approaches | **2-3 hours** |
| 9 | `prompts/carousel_tips.md` | Complete rewrite: new examples and rules | **1-2 hours** |
| 10 | `prompts/carousel_beforeafter.md` | Complete rewrite: new before/after domain examples | **1-2 hours** |
| 11 | `prompts/carousel_mythreality.md` | Complete rewrite: new myth/reality domain examples | **1-2 hours** |
| 12 | `brand.py` | Replace all 5 identity fields + potentially colors/fonts | **15 min** |
| 13 | `feeds.py` | Replace all 12 feeds and 10 category definitions | **1-2 hours** |
| 14 | `feed_scanner.py` lines 113-128 | Rewrite scoring system prompt for new niche | **30 min** |
| 15 | `config.py` lines 13-34 | Rewrite weekly schedule types and suggestions | **15 min** |

**Tier 1 total: ~20-35 hours** (dominated by prompt writing)

### Tier 2: Should Change (functional but wrong/confusing otherwise)

| # | File | What to Change | Effort |
|---|------|---------------|--------|
| 16 | `templates/index.html` | Replace 3x "Signal & Stance" title/headers | 5 min |
| 17 | `templates/index.html` | Replace ~6 LinkedIn references in scheduling UI | 15 min |
| 18 | `templates/index.html` | Update feed category dropdown options | 10 min |
| 19 | `app.py` line 58 | Replace "Signal & Stance is running" fallback | 1 min |
| 20 | `config.py` line 10 | Rename database file from `signal_stance.db` | 1 min |
| 21 | `config.py` line 38 | Remove Dana-specific comment | 1 min |
| 22 | `engine.py` lines 68, 114, 161, 166, 245 | Replace 5 Dana/resume-specific strings in user messages and comments | 10 min |
| 23 | `engine.py` lines 342, 376, 409 | Replace 3 default CTA fallback strings | 5 min |
| 24 | `carousel_renderer.py` line 1 | Update docstring | 1 min |
| 25 | `carousel_renderer.py` line 426 | Update default CTA fallback | 1 min |

**Tier 2 total: ~50 minutes**

### Tier 3: Optional / Cosmetic

| # | File | What to Change | Effort |
|---|------|---------------|--------|
| 26 | Project root directory name | Rename `signal-and-stance/` | 5 min |
| 27 | `static/style.css` | Adjust CSS custom properties if new brand colors differ significantly from the existing palette | 15-30 min |
| 28 | 6 documentation `.md` files | Rewrite project overview and build stage docs | 2-4 hours |
| 29 | `app.py` line 49 | Potentially rename content categories if the 4-type system doesn't fit | 30 min |
| 30 | `templates/index.html` category buttons | Update button labels if categories change | 15 min |

**Tier 3 total: ~3-5 hours**

### Grand Total Estimate: ~24-41 hours

---

## 5. Modularity Heat Map

Files ranked by coupling density (most coupled first):

```
COUPLING DENSITY (business references per file)

prompts/base_system.md        ██████████████████████████████  CRITICAL
prompts/feed_react.md         ████████████████████████        HIGH
prompts/autopilot.md          ████████████████████████        HIGH
prompts/carousel_tips.md      ██████████████████              HIGH
prompts/carousel_beforeafter  ██████████████████              HIGH
prompts/carousel_mythreality  ██████████████████              HIGH
prompts/category_pattern.md   ████████████████                HIGH
prompts/category_faq.md       ████████████████                HIGH
prompts/category_hottake.md   ████████████████                HIGH
prompts/category_noticed.md   ████████████████                HIGH
prompts/url_react.md          ████████████████                HIGH
feed_scanner.py               ██████████████                  HIGH
feeds.py                      ████████████                    MODERATE
engine.py                     ████████                        MODERATE
brand.py                      ██████                          LOW (centralized)
config.py                     ████                            LOW
app.py                        ██                              MINIMAL
templates/index.html          ██                              MINIMAL
carousel_renderer.py          █                               MINIMAL
database.py                   ·                               ZERO
schema.sql                    ·                               ZERO
static/style.css              ·                               ZERO
```

---

## 6. Recommendations for Making It Swappable

### R1: Create a `business.json` config file (HIGH IMPACT)

Pull all business identity into one file that prompts and code read from:

```json
{
  "owner": {
    "name": "Dana Wang",
    "title": "Certified Professional Resume Writer (CPRW)",
    "business": "Raleigh Resume",
    "url": "linkedin.com/in/danaxwang",
    "credentials": ["CPRW via PARWCC", "MA from UNC Chapel Hill"],
    "niche_summary": "Executive resume writing, LinkedIn optimization, ATS compliance",
    "audience": "VPs, Directors, C-suite, Board members"
  },
  "platform": {
    "name": "LinkedIn",
    "post_format": "text",
    "word_range": [150, 300],
    "carousel_dimensions": [1080, 1080]
  },
  "brand": {
    "app_name": "Signal & Stance",
    "colors": { ... },
    "fonts": { ... }
  },
  "content": {
    "categories": {
      "pattern": { "label": "I keep seeing...", "suggestion": "..." },
      ...
    },
    "schedule": { ... }
  }
}
```

Merge current `brand.py`, `config.py` identity fields, and the scattered string references into this single source of truth. **Estimated effort: 3-4 hours.** Would eliminate ~30 of the 66 coupling points.

### R2: Templatize the prompt files (HIGH IMPACT)

Convert prompt `.md` files to use `{{variable}}` placeholders that get filled from `business.json` at load time:

```markdown
You are writing {{platform.name}} posts as {{owner.name}}. {{owner.name}} is a
{{owner.title}} who runs {{owner.business}}. They partner with {{owner.audience}}...
```

This would let the same prompt structure serve different businesses. A Jinja2-style substitution in `engine.py`'s `load_prompt()` would handle it. **Estimated effort: 6-8 hours.** Would convert the 11 prompt files from "must rewrite" to "review and adjust."

**Caveat:** Only ~40% of prompt content is templatizable. The voice rules ("Resumes are marketing assets"), content arcs, scoring criteria, and examples are deeply domain-specific authored content. These sections would still need manual rewriting for a meaningfully different business domain (e.g., resume writing -> bookshop). But for adjacent domains (resume writing -> career coaching -> executive branding), templating would save significant time.

### R3: Move `engine.py` user messages to prompt files (LOW EFFORT)

The 5 Dana-specific strings in `engine.py` (lines 68, 114, 161, 166, 245) should be moved into the corresponding prompt `.md` files or read from `business.json`. This keeps `engine.py` as pure infrastructure.

**Estimated effort: 30 minutes.**

### R4: Abstract the `feed_scanner.py` scoring prompt (MODERATE EFFORT)

The scoring system prompt (lines 113-128) should load its niche description from `business.json` rather than having a hardcoded paragraph about Dana Wang, CPRW, executive resumes, etc.

**Estimated effort: 30 minutes.**

### R5: Add a platform abstraction to the frontend (LOW PRIORITY)

Replace the 6 hardcoded "LinkedIn" references in `index.html` with a JS variable read from a config endpoint (e.g., `GET /api/config` returning `{ platform: "LinkedIn" }`). This would make platform swaps (LinkedIn -> Instagram -> blog) a config change instead of an HTML edit.

**Estimated effort: 1 hour.**

### R6: Separate "framework" from "tenant" at the directory level (OPTIONAL)

If multi-tenant support is ever desired, restructure as:

```
signalstance/
  framework/          # engine, renderer, scanner, routes, schema
  tenants/
    dana-wang/        # prompts/, brand.json, feeds.json, business.json
    alex-chen/        # prompts/, brand.json, feeds.json, business.json
```

This is significant refactoring and only worth it if you plan to deploy this for multiple businesses. **Estimated effort: 8-12 hours.**

---

## 7. File-by-File Swap Checklist

A complete checklist for someone swapping to a new business:

```
MUST CHANGE
[ ] prompts/base_system.md          - Full rewrite (identity + voice + rules)
[ ] prompts/category_pattern.md     - Full rewrite (content arc)
[ ] prompts/category_faq.md         - Full rewrite (content arc)
[ ] prompts/category_hottake.md     - Full rewrite (content arc)
[ ] prompts/category_noticed.md     - Full rewrite (content arc)
[ ] prompts/autopilot.md            - Full rewrite (search topics + eval criteria)
[ ] prompts/url_react.md            - Full rewrite (reaction approaches)
[ ] prompts/feed_react.md           - Full rewrite (category approaches)
[ ] prompts/carousel_tips.md        - Full rewrite (examples + rules)
[ ] prompts/carousel_beforeafter.md - Full rewrite (examples + rules)
[ ] prompts/carousel_mythreality.md - Full rewrite (examples + rules)
[ ] brand.py                        - Replace identity fields + colors
[ ] feeds.py                        - Replace all feeds + categories
[ ] feed_scanner.py:113-128         - Rewrite scoring prompt
[ ] config.py:13-34                 - Rewrite schedule types + suggestions

SHOULD CHANGE
[ ] templates/index.html            - Replace app name (3 spots) + LinkedIn refs (6 spots) + category dropdown
[ ] engine.py                       - Replace 5 Dana-specific strings + 3 CTA defaults
[ ] app.py:58                       - Replace fallback string
[ ] config.py:10                    - Rename database file
[ ] carousel_renderer.py:426        - Replace default CTA

OPTIONAL
[ ] Directory/repo names
[ ] Documentation .md files
[ ] CSS custom properties (if brand colors change significantly)
[ ] Content category names (if 4-type system doesn't fit new domain)
```

---

## 8. Bottom Line

**The architecture is cleanly layered. The content is deeply coupled.**

The good news: the coupling is concentrated, not scattered. 80% of the swap work lives in the 11 prompt files and 2 config files (`feeds.py`, `feed_scanner.py` scoring prompt). The Python infrastructure (`app.py`, `database.py`, `engine.py`, `carousel_renderer.py`) is largely business-agnostic and would survive a swap with minor string replacements.

The hard truth: the prompt files aren't configuration — they're *creative work*. Rewriting `base_system.md` for a new business isn't filling in a template. It's building a new voice profile from scratch: tone rules, signature language, content arcs, quality criteria, scoring rubrics, and worked examples. That's 20-35 hours of work regardless of how the code is structured, because the value of this app *is* the prompts.

**If you plan to swap businesses once:** just do the checklist above. The current structure is fine.

**If you plan to swap businesses repeatedly or serve multiple tenants:** implement R1 (business.json) and R2 (prompt templating) first. That reduces each subsequent swap from ~35 hours to ~10-15 hours for a same-domain swap, or ~20-25 hours for a cross-domain swap.
