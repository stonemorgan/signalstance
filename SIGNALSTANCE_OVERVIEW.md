# SignalStance — Codebase Overview & User Guide

> A locally hosted, multi-tenant Flask app that turns half-baked professional insights into ready-to-post LinkedIn content (text posts + branded PDF carousels), grounded in a custom voice profile and a curated RSS feed pool scored by Claude.

---

## 1. What this project is

**SignalStance** (UI name: *Signal & Stance*) is a personal content studio you run on your own machine. You give it a thought — a pattern you've noticed, a client question, a hot take, a URL, or nothing at all — and it returns three distinct LinkedIn post drafts written in your voice, or a branded 1080×1080 PDF carousel. It also runs a weekly calendar so you can plan, assign drafts, and track what's scheduled vs. published.

It is **multi-tenant by design**: one install can support multiple businesses/personas, each with isolated config, prompts, database, and generated output. The live example in this repo is `dana-wang` (Dana Wang / Raleigh Resume, a Certified Professional Resume Writer).

### Core purpose

Solo experts and small-business owners lose hours staring at a blank LinkedIn composer. SignalStance compresses the loop:

1. Capture raw insight → 2. Claude writes 3 drafts in your voice → 3. Pick one → 4. Slot it into the week's calendar → 5. Copy/paste to LinkedIn.

Target time from insight to posted content: **under 5 minutes**.

---

## 2. Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask 3.0+ |
| AI | Anthropic Claude via official SDK (`anthropic>=0.40.0`) — default model `claude-sonnet-4-20250514` |
| Database | SQLite (WAL mode, FK enforcement, per-tenant file) |
| RSS | `feedparser` + `requests` |
| PDF | ReportLab (1080×1080 slides) |
| Frontend | Vanilla JavaScript SPA, CSS custom properties, no build step |
| Testing | pytest with in-memory SQLite + Flask test client |
| Env | `python-dotenv` |

No frameworks on the frontend, no build pipeline, no Docker required. It is intentionally a small, local tool.

---

## 3. Repository map

```
signalstance/
├── run.py                    # CLI entry — selects a tenant and starts Flask
├── setup_tenant.py           # Scaffolds a new tenant from _template/
├── CLAUDE.md                 # Project-level instructions for Claude Code
├── .env                      # ANTHROPIC_API_KEY (never commit)
│
├── framework/                # Shared, tenant-agnostic code
│   ├── app.py                # Flask routes, 30+ JSON endpoints
│   ├── engine.py             # Claude prompt orchestration + response parsing
│   ├── database.py           # SQLite CRUD + calendar state machine
│   ├── carousel_renderer.py  # ReportLab PDF generation (3 templates)
│   ├── feed_scanner.py       # RSS fetch + Claude-based relevance scoring
│   ├── business_config.py    # Loads the active tenant's JSON config
│   ├── config.py             # Env vars + derived schedule
│   ├── brand.py              # Typography/colors/dimensions for carousels
│   ├── feeds.py              # Feed list loader
│   ├── schema.sql            # Latest schema: 7 tables, FK CASCADE/SET NULL, indexes
│   ├── migrations/           # Numbered SQL migrations (PRAGMA user_version)
│   ├── templates/index.html  # Single-page app (apiFetch wraps all fetch calls)
│   ├── static/style.css      # Stylesheet with dark mode
│   └── tests/                # pytest suite (116 tests, conftest + 5 test files)
│
├── tenants/
│   ├── _template/            # Blueprint for new tenants
│   └── dana-wang/            # Live example tenant
│       ├── business_config.json
│       ├── feeds.json
│       ├── signal_stance.db
│       ├── generated_carousels/
│       └── prompts/          # 11 .md prompt templates
│
├── .claude/
│   ├── settings.json         # Forces Opus model + permissions
│   ├── agents/               # 9 specialized audit agents
│   └── skills/audit/         # /audit slash-command skill
│
├── scripts/
│   ├── run-audit.sh          # Full 4-phase audit runner (bash)
│   └── run-audit.bat         # Same for Windows
│
└── audit-reports/            # Generated audit findings (already populated)
```

---

## 4. Feature tour

### 4.1 Four input modes

All produce three LinkedIn drafts plus an "angle description" per draft.

| Mode | How it works | Endpoint |
|---|---|---|
| **Category input** | You pick a category (Pattern / FAQ / Noticed / Hot Take) and paste an observation | `POST /api/generate` |
| **URL reaction** | You paste a URL; Claude (with `web_search` tool) reads it and reacts | `POST /api/generate/react` |
| **Autopilot** | Zero input: picks the highest-relevance unused article from your feed pool; falls back to web-search if nothing strong | `POST /api/generate/autopilot` |
| **Feed-article reaction** | Click any fetched article; Claude generates a reaction post | `POST /api/articles/<id>/generate` |

### 4.2 Carousel generation

Three templates, all rendered to 1080×1080 multi-page PDFs with your brand colors, fonts, and a cover + CTA slide.

- **Numbered Tips** — "5 mistakes" / "7 strategies" style, one tip per slide
- **Before / After** — weak vs strong example pairs with tinted boxes
- **Myth vs Reality** — quoted myth + green "REALITY" pill with the correction

Endpoints: `POST /api/generate/carousel`, `POST /api/generate/carousel/regenerate`, `GET /api/carousel/download/<generation_id>` (path-traversal-hardened with `realpath` check).

### 4.3 Weekly calendar (state machine)

Mon–Fri slots auto-generated per week. Each slot moves through a guarded state machine enforced atomically in SQL:

```
empty → draft_ready → scheduled → published
  ↓          ↓             ↓            ↓
skipped   skipped       skipped     skipped
  ↓
empty
```

- `published` slots **cannot** be cleared or overwritten.
- `assign_draft_to_slot` requires the slot to be `empty` or `draft_ready`.
- Status updates use a single `UPDATE … WHERE status IN (…)` — no TOCTOU race.

Endpoints: `/api/calendar`, `/api/calendar/assign`, `/api/calendar/status`, `/api/calendar/clear`, `/api/calendar/skip`.

### 4.4 RSS feed pool

Twelve default feeds ship with the `dana-wang` tenant (McKinsey, Fast Company, HR Dive, BLS, Indeed Hiring Lab, Fortune, etc.). On startup a daemon thread refreshes any feed older than 6 hours. Each new article is scored 0.0–1.0 for niche relevance by Claude (batch of 20 at a time, JSON-validated response). Articles are `used`/`dismissed`-tracked so autopilot never reuses them.

Endpoints: `/api/feeds` (CRUD), `/api/feeds/refresh`, `/api/articles`, `/api/articles/<id>/dismiss`.

### 4.5 History + insight bank

Every generation is persisted. The UI exposes an **Insight Bank** (raw observations captured but not yet turned into drafts) and **History** (last 30 days of generations with attached carousel previews).

### 4.6 Security posture (from Phase 5 hardening)

- SSRF protection on user-supplied feed URLs — blocks `127/8`, `10/8`, `172.16/12`, `192.168/16`, `169.254/16`, and IPv6 loopback/ULA/link-local.
- Path-traversal guard on PDF downloads (`realpath` must be inside `generated_carousels/`).
- Parameterized SQL everywhere — zero string-formatted queries.
- `FLASK_DEBUG` defaults off (prevents Werkzeug RCE).
- `/api/config` explicitly excludes the API key.
- Connection `try/finally` on all ~24 DB functions; 30-second busy timeout; WAL mode; FK enforcement.
- Tenant config validated on startup — `ConfigError` with file path + missing key instead of cryptic `KeyError` tracebacks.
- Frontend HTTP errors flow through `apiFetch()` → `.catch(err => ...)` consistently; no silent failures on 4xx/5xx.

### 4.7 Audit suite (Claude Code only)

Nine specialized agents in `.claude/agents/` — run the full 4-phase audit via `bash scripts/run-audit.sh` or the `/audit` skill. Outputs land in `audit-reports/`. The most recent run surfaced 74 findings and auto-fixed 14 Critical/High items (see `audit-reports/09-final-summary.md`).

---

## 5. Architecture & data flow

```
         ┌──────────────────┐
         │  index.html SPA  │  (Create | Calendar | Feed tabs)
         └────────┬─────────┘
                  │  apiFetch() JSON
                  ▼
    ┌──────────────────────────────┐
    │        Flask (app.py)        │
    │  - input validation          │
    │  - SSRF / path-traversal     │
    │  - _handle_api_error()       │
    └──┬────────────┬──────────────┘
       │            │
       ▼            ▼
 ┌──────────┐  ┌──────────────┐      ┌───────────────────┐
 │ engine.py│→ │ anthropic API│      │ feed_scanner.py   │
 │ (prompts │  │  + web_search│      │ (feedparser +     │
 │  + parse)│  └──────────────┘      │  Claude scoring)  │
 └────┬─────┘                        └─────────┬─────────┘
      │                                        │
      ▼                                        ▼
 ┌─────────────────────────────────────────────────────┐
 │             database.py  →  SQLite (WAL)            │
 │  insights | generations | calendar_slots | feeds    │
 │  feed_articles | carousel_data | config             │
 └──────────────────────────────────────────────────────┘
      │
      ▼
 ┌─────────────────────┐
 │ carousel_renderer   │→  tenants/<tenant>/generated_carousels/*.pdf
 │ (ReportLab)         │
 └─────────────────────┘
```

### Tenant resolution

1. `run.py --tenant <name>` sets `SIGNALSTANCE_TENANT_DIR` env var.
2. `business_config.py` reads `<tenant>/business_config.json` at import.
3. `config.py` derives `DATABASE_PATH`, `CONTENT_SCHEDULE`, `SUGGESTED_TIMES`.
4. `engine.load_prompt()` checks `<tenant>/prompts/` first, then `framework/` fallback.
5. Carousels write to `<tenant>/generated_carousels/`.

Every business-specific value (voice, feeds, brand colors, schedule, scoring rubric) lives in the tenant directory. **`framework/` must work with any valid `business_config.json`.**

### Prompt templating

Prompt `.md` files use `{{key.subkey}}` placeholders. `engine._flatten_config()` produces a dot-notation map from `BUSINESS`, and `load_prompt()` substitutes on read. That means one voice profile (`base_system.md`) drives all eleven downstream prompts: `category_pattern.md`, `category_faq.md`, `category_noticed.md`, `category_hottake.md`, `autopilot.md`, `url_react.md`, `feed_react.md`, `carousel_tips.md`, `carousel_beforeafter.md`, `carousel_mythreality.md`.

### Database schema (7 tables)

| Table | Purpose |
|---|---|
| `insights` | Raw observations (category, text, optional source URL, used flag) |
| `generations` | AI-generated draft posts (FK → insights, **CASCADE** on delete) |
| `calendar_slots` | Mon–Fri weekly slots with status state machine (FK → generations, **SET NULL** on delete; UNIQUE `slot_date`) |
| `feeds` | RSS feed sources (URL, category, weight, enabled, last error) |
| `feed_articles` | Fetched articles (FK → feeds, **CASCADE** on delete; relevance_score, used, dismissed) |
| `carousel_data` | PDF metadata (FK → generations, **CASCADE** on delete; JSON parsed_content, filename, slide_count) |
| `config` | Key-value app settings |

Schema state is tracked via `PRAGMA user_version`; `framework/migrations/NNNN_*.sql` files apply incremental upgrades for legacy DBs while fresh DBs get the latest `schema.sql` directly. `init_db()` runs the migration runner on startup.

---

## 6. How to use it (quick start)

### Prerequisites

- Python 3.11+
- An Anthropic API key from [console.anthropic.com](https://console.anthropic.com)

### Setup (first time)

```bash
# 1. Install dependencies
pip install -r framework/requirements.txt

# 2. Add your API key to .env at the project root
echo "ANTHROPIC_API_KEY=sk-ant-…" > .env

# 3. (Optional) create a new tenant for yourself
python setup_tenant.py my-brand

# 4. Run the app — auto-picks first tenant, or use --tenant
python run.py --tenant dana-wang
# or:
python run.py --list

# 5. Open http://localhost:5000
```

### Daily workflow

1. **Create tab** — pick a category (Pattern, FAQ, Noticed, Hot Take), paste an observation, click *Generate Drafts*. Or paste a URL. Or click *Generate an idea for me* (autopilot).
2. Pick a draft, click *Copy*, paste to LinkedIn. (Copying marks the parent insight as `used`.)
3. **Feed tab** — click *Refresh Feeds* to pull the latest articles; filter by category or "High relevance only"; click any article to generate a reaction post.
4. **Calendar tab** — assign drafts to Mon–Fri slots, mark scheduled/published, navigate weeks with `«` / `»`.
5. For visuals, select *Carousel* in the output-format toggle, pick a template (Tips / Before-After / Myth-Reality), and download the generated PDF.

### Running tests

```bash
cd framework && python -m pytest tests/ -v
# 116 tests, ~3-4s, no network or API key required
```

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — (required) | Claude API credentials |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Claude model for all generation |
| `MAX_TOKENS` | `4096` | Max tokens per response |
| `FLASK_PORT` | `5000` | HTTP port |
| `FLASK_DEBUG` | `false` | Leave off in production (RCE risk) |
| `SIGNALSTANCE_TENANT_DIR` | auto | Set by `run.py --tenant`; don't set manually |

---

## 7. Creating a new tenant (making it yours)

```bash
python setup_tenant.py <tenant-name>
```

This copies `tenants/_template/` to `tenants/<tenant-name>/`. Then:

1. **`business_config.json`** — fill in `owner` (name, title, business, credentials, niche, audience), `platform` (LinkedIn by default), `brand` hex colors, weekly `schedule`, `feeds.categories` (your topic taxonomy), and `scoring` rubric.
2. **`feeds.json`** — list your starter RSS sources as `[{ url, name, category, weight, enabled }]`. Categories must match keys in `feeds.categories`.
3. **`prompts/base_system.md`** — the most important file. It defines voice: tone, stance, signature language, hard rules, post structure, self-evaluation checklist, and the required `Draft 1 / Draft 2 / Draft 3` output format. Every other prompt inherits from this.
4. Optionally customize the other 10 prompts (category-specific angles, carousel formats, autopilot/feed-react templates). They ship pre-wired to `{{owner.name}}`, `{{platform.name}}`, etc.
5. `python run.py --tenant <tenant-name>` — database and `generated_carousels/` are created on first run.

**Rule of thumb:** never hardcode tenant data in `framework/`. If you need a new knob, add it to `_template/business_config.json` first.

---

## 8. Effectiveness tips

- **Voice is everything.** Spend real time on `base_system.md`. The framework is mechanically sound; the output quality is bottlenecked by the voice profile. Include hard "never do" rules — they matter more than the "do" rules.
- **Curate your feeds.** Autopilot is only as good as the pool. Aim for 10–15 feeds across 5+ categories, with `weight` reflecting how frequently you'd want posts sourced from each.
- **Use the insight bank.** Dump half-formed thoughts into the Create tab without generating — they persist and can be revisited when inspiration is dry.
- **Regenerate surgically.** If only one of three drafts is close, click *Regenerate* — all three will re-roll; the saved insight is reused so you don't pay for re-prompting context.
- **Don't trust autopilot blind.** Always read what Claude pulled from your feed — it's genuinely good but occasionally picks a weak hook. Dismissing an article teaches the system to skip it.
- **Carousels ≠ posts.** Carousels cost more tokens and more time to produce well. Use them for "save this" content (Before/After examples, myth-busting), not for reactions.
- **Back up the tenant DB.** Each tenant's `*.db` file holds everything — insights, drafts, calendar, feeds. Copy it before experimenting with schema changes.
- **Keep `FLASK_DEBUG=false`.** The startup banner will remind you, but it bears repeating: debug mode exposes the Werkzeug console.
- **Read the audit reports.** `audit-reports/09-final-summary.md` is a good map of what's been hardened and what known gaps remain (no auth, no rate limiting on endpoints — acceptable for a local-only tool, risky if you expose it publicly).

---

## 9. Known limitations & production caveats

This is a **local-only personal tool** as shipped. If you ever expose it to a network:

- No authentication layer — anyone on the network can hit the API.
- No rate limiting — unbounded Claude API spend if abused.
- No CSRF tokens on state-changing endpoints.
- `send_file` is served by Flask's dev server (fine for localhost; use a real WSGI server + reverse proxy if exposing).

For solo daily-driver use on `localhost`, the current posture is appropriate.

---

## 10. Where to look next in the code

| You want to… | Open |
|---|---|
| Add a new API endpoint | `framework/app.py` |
| Change how drafts are generated | `framework/engine.py` + tenant `prompts/*.md` |
| Add a DB column or table | `framework/schema.sql` + the relevant CRUD in `database.py` |
| Change carousel design | `framework/carousel_renderer.py` + `framework/brand.py` |
| Tweak RSS fetching / scoring | `framework/feed_scanner.py` |
| Edit the UI | `framework/templates/index.html` + `framework/static/style.css` |
| Create a second persona | `python setup_tenant.py <name>` then edit `tenants/<name>/` |
| Audit the codebase with Claude | `bash scripts/run-audit.sh` or `/audit` |

---

*Report generated by reading `run.py`, `framework/app.py`, `framework/engine.py`, `framework/database.py`, `framework/config.py`, `framework/business_config.py`, `framework/feed_scanner.py`, `framework/carousel_renderer.py`, `framework/schema.sql`, `framework/brand.py`, `framework/feeds.py`, `framework/requirements.txt`, `framework/templates/index.html`, `framework/README.md`, `tenants/dana-wang/business_config.json`, `tenants/dana-wang/feeds.json`, `tenants/dana-wang/prompts/base_system.md`, `tenants/_template/business_config.json`, `scripts/run-audit.sh`, `audit-reports/09-final-summary.md`, `CLAUDE.md`, and `.claude/settings.json`.*
