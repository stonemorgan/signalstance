# SignalStance — Claude Code Project Instructions

## Model Requirement

All Claude Code sessions and agents MUST use the **Opus** model. This applies to:
- Interactive Claude Code sessions (enforced via `.claude/settings.json`)
- All 9 agents in `.claude/agents/` (enforced via frontmatter `model: opus`)
- Any new agents or skills created for this project

## Project Overview

SignalStance is a multi-tenant Flask application that uses Claude AI to generate LinkedIn content for professionals. It ingests RSS feeds, scores article relevance, generates post drafts and PDF carousels, and manages a weekly content calendar. Each tenant has isolated configuration, prompts, database, and generated output.

## Architecture

```
signalstance/
├── framework/                  # Shared application code
│   ├── app.py                 (998 lines — Flask routes, API endpoints)
│   ├── engine.py              (522 lines — Claude AI content generation)
│   ├── database.py            (605 lines — SQLite operations, state machine)
│   ├── carousel_renderer.py   (492 lines — ReportLab PDF generation)
│   ├── feed_scanner.py        (182 lines — RSS fetch + relevance scoring)
│   ├── business_config.py     (62 lines — tenant config loader)
│   ├── config.py              (31 lines — env vars + derived settings)
│   ├── brand.py               (33 lines — colors, fonts, dimensions)
│   ├── feeds.py               (14 lines — feed config loader)
│   ├── schema.sql             (85 lines — 7 tables + indexes)
│   ├── requirements.txt
│   ├── templates/
│   │   └── index.html         (2537 lines — full SPA, vanilla JS)
│   ├── static/
│   │   └── style.css          (1891 lines — dark mode, responsive)
│   └── tests/
│       ├── conftest.py        (shared fixtures, in-memory SQLite)
│       ├── test_app_security.py
│       ├── test_database.py
│       └── test_engine_parsing.py
├── tenants/                    # Per-business directories
│   ├── _template/             (blueprint for new tenants)
│   └── dana-wang/             (example: Dana Wang CPRW)
├── .claude/
│   ├── agents/                (9 audit agents, all model: opus)
│   ├── skills/
│   └── settings.json          (project-level model + permissions)
├── scripts/
│   ├── run-audit.sh
│   └── run-audit.bat
├── audit-reports/              (generated audit findings)
├── run.py                     (76 lines — CLI entry point)
├── setup_tenant.py            (41 lines — tenant scaffolding)
├── .env                       (ANTHROPIC_API_KEY — never commit)
└── CLAUDE.md                  (this file)
```

## Tech Stack

- **Python 3.11+**, Flask 3.0+, SQLite with WAL mode
- **Anthropic SDK** (anthropic>=0.40.0) — Claude API for content generation and feed scoring
- **ReportLab** — PDF carousel rendering (1080x1080 slides)
- **feedparser** + **requests** — RSS feed ingestion
- **python-dotenv** — Environment variable loading
- **Frontend** — Vanilla JavaScript SPA, CSS custom properties, no frameworks
- **Testing** — pytest with Flask test client and in-memory SQLite

## Key Commands

```bash
# Run the app (defaults to first tenant)
python run.py
python run.py --tenant dana-wang
python run.py --list

# Run tests
cd framework && python -m pytest tests/ -v

# Install dependencies
pip install -r framework/requirements.txt

# Create a new tenant
python setup_tenant.py <tenant-name>

# Run full audit suite
bash scripts/run-audit.sh
# or on Windows:
scripts\run-audit.bat
```

## Environment Variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Set in `.env`, never commit |
| `ANTHROPIC_MODEL` | No | `claude-sonnet-4-20250514` | Claude model for content generation |
| `MAX_TOKENS` | No | `4096` | Max tokens per Claude response |
| `FLASK_PORT` | No | `5000` | Flask server port |
| `FLASK_DEBUG` | No | `false` | Set `true` only for local dev |
| `SIGNALSTANCE_TENANT_DIR` | Auto | — | Set by `run.py` based on `--tenant` flag |

## Code Conventions

### Python Style
- Functional style preferred over classes (except where Flask patterns require it)
- `snake_case` for functions and variables
- `_` prefix for module-private helpers (e.g., `_handle_api_error`, `_is_safe_url`)
- `UPPERCASE` for module-level constants
- No type annotations on existing code — don't add them unless writing new modules

### Database Function Naming
Prefix indicates the operation:
- `save_` — insert new row
- `get_` — read/query
- `update_` — modify existing row
- `delete_` — remove row
- `mark_` — flip a boolean/status field
- `clear_` — reset to default state
- `assign_` — link one entity to another
- `seed_` — insert default data if not present

### Database Patterns
- Always use `try/finally` with `conn.close()` for connection cleanup
- All SQL must use parameterized queries (`?` placeholders) — never string formatting
- Every connection opens with `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON`
- Use `sqlite3.Row` factory for dict-like access
- Connection timeout: 30 seconds

### Flask Routes
- RESTful endpoints under `/api/*`
- All API responses return JSON with a `success` boolean field
- Error handling via `_handle_api_error(e)` which categorizes exceptions:
  - 429 → rate limit, 503 → timeout/network, 401 → auth, 500 → generic
- Input validation: check required fields, validate categories against known list
- Background operations use daemon threads (feed refresh, carousel cleanup)

### Prompt Templates
- Template files are `.md` in tenant `prompts/` directory
- Variable substitution: `{{key.subkey}}` replaced from flattened `business_config.json`
- Resolution order: tenant directory first, then `framework/` fallback
- `engine.py:load_prompt()` handles loading and substitution

### Calendar State Machine
```
empty → draft_ready → scheduled → published
  ↓         ↓            ↓           ↓
skipped   skipped      skipped     skipped
  ↓
empty
```
Legal transitions enforced in `database.py:_LEGAL_TRANSITIONS` dict.

### Frontend
- Vanilla JavaScript — no frameworks, no build step
- All API calls via `fetch()` with JSON request/response
- Dark mode via CSS custom properties
- UI config loaded dynamically from `/api/config` endpoint
- Categories, templates, and schedule driven by tenant `business_config.json`

## Multi-Tenant Rules

1. **Never hardcode tenant-specific values in `framework/`** — all business-specific data comes from `business_config.json`, `feeds.json`, and `prompts/`
2. **Always load config through `business_config.py`** — never read `business_config.json` directly
3. **Each tenant has its own SQLite database** — path derived from `SIGNALSTANCE_TENANT_DIR` + config `database_name`
4. **Prompt resolution is tenant-first** — check `{tenant_dir}/prompts/` before `framework/` fallback
5. **Generated carousels go to `{tenant_dir}/generated_carousels/`** — never to a shared location
6. **New tenants are created from `_template/`** — use `setup_tenant.py`, never copy another tenant
7. **Framework code must work with any valid `business_config.json`** — don't assume specific categories, colors, or schedule
8. **The `_template/` directory is the canonical schema** — if you add new config fields, update the template first

## Security Rules

### NEVER Do
- **No string-formatted SQL** — always use parameterized queries with `?` placeholders
- **No `FLASK_DEBUG=true` in production** — debug mode is off by default, keep it that way
- **No committed `.env` files** — `.env` is in `.gitignore`, keep API keys out of version control
- **No `innerHTML` with unsanitized data** — the frontend uses `textContent` for user-supplied strings
- **No file downloads outside `generated_carousels/`** — carousel download validates `realpath()` is within `CAROUSEL_DIR`
- **No HTTP requests without SSRF validation** — `_is_safe_url()` blocks private IP ranges (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16)
- **No API key exposure in frontend** — `/api/config` explicitly excludes `ANTHROPIC_API_KEY`

### Existing Security Measures
- SSRF protection on feed URLs (`_is_safe_url()` in app.py)
- Path traversal protection on carousel downloads (realpath check)
- Error responses return JSON, not HTML tracebacks
- Input validation on categories, required fields, URL formats
- Rate limit error handling (429 from Claude API)

## Testing Requirements

### Principles
- **No real API keys** — tests patch `ANTHROPIC_API_KEY` to `"test-key-not-real"`
- **No network calls** — mock external services, never hit real APIs or feeds
- **Real SQLite** — use in-memory database with full schema (shared URI for connection reuse)
- **Flask test client** — use `app.test_client()` for endpoint tests

### Running Tests
```bash
cd framework && python -m pytest tests/ -v
```

### Writing New Tests
- Add fixtures to `tests/conftest.py` — the `db` fixture provides a clean in-memory database, `app_client` provides a Flask test client
- Security tests go in `test_app_security.py`
- Database tests go in `test_database.py`
- Parsing/engine tests go in `test_engine_parsing.py`
- New test files: `test_<module>.py` in `framework/tests/`

## Database Schema

| Table | Purpose | Key Columns |
|---|---|---|
| `insights` | User observations / raw input | category, raw_input, source_url, used |
| `generations` | AI-generated drafts | insight_id (FK), draft_number, content, copied |
| `config` | Key-value app settings | key, value |
| `calendar_slots` | Weekly content calendar | slot_date (unique), day_of_week, content_type, generation_id (FK), status |
| `feeds` | RSS feed sources | url, name, category, weight, enabled, last_fetched_at |
| `feed_articles` | Fetched articles | feed_id (FK), title, url, relevance_score, relevance_reason, used, dismissed |
| `carousel_data` | PDF carousel metadata | generation_id (FK), template_type, parsed_content (JSON), pdf_filename, slide_count |

## Agents and Skills

### Audit Suite
The project includes a 4-phase audit system run via `scripts/run-audit.sh`:
1. **Discovery** — 6 specialist agents scan in parallel (security, errors, data, API, frontend, code quality)
2. **Triage** — Orchestrator deduplicates and prioritizes findings
3. **Fix** — Implementation executor applies fixes
4. **Verify** — Test architect writes regression tests

### Agent Inventory

| Agent | Role | Model |
|---|---|---|
| `audit-suite` | Master orchestrator | Opus |
| `security-auditor` | XSS, injection, SSRF, tenant isolation | Opus |
| `error-resilience` | Exception handling, crashes, race conditions | Opus |
| `data-integrity` | SQLite concurrency, schema, state machine | Opus |
| `api-robustness` | Claude API errors, rate limits, costs | Opus |
| `frontend-reviewer` | SPA bugs, state management, accessibility | Opus |
| `codebase-optimizer` | Dead code, duplication, architecture debt | Opus |
| `test-architect` | Test coverage design | Opus |
| `implementation-executor` | Applies fixes from audit findings | Opus |

## Key Files Reference

| Area | Primary File | Supporting Files |
|---|---|---|
| Flask routes & API | `framework/app.py` | `framework/config.py` |
| Content generation | `framework/engine.py` | tenant `prompts/*.md` |
| Database operations | `framework/database.py` | `framework/schema.sql` |
| PDF carousels | `framework/carousel_renderer.py` | `framework/brand.py` |
| RSS feeds | `framework/feed_scanner.py` | `framework/feeds.py` |
| Tenant config | `framework/business_config.py` | tenant `business_config.json` |
| Frontend SPA | `framework/templates/index.html` | `framework/static/style.css` |
| App entry point | `run.py` | `framework/config.py` |
| Tenant setup | `setup_tenant.py` | `tenants/_template/` |
| Tests | `framework/tests/conftest.py` | `framework/tests/test_*.py` |
