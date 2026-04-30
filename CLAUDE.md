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
│   ├── app.py                 (Flask routes, API endpoints)
│   ├── engine.py              (Claude AI content generation)
│   ├── database.py            (SQLite operations, migrations, state machine)
│   ├── carousel_renderer.py   (ReportLab PDF generation)
│   ├── feed_scanner.py        (RSS fetch + relevance scoring)
│   ├── business_config.py     (tenant config loader; uses validate.py)
│   ├── validate.py            (pure schema validator — no import side effects)
│   ├── config.py              (env vars + derived settings)
│   ├── brand.py               (colors, fonts, dimensions)
│   ├── feeds.py               (feed config loader)
│   ├── schema.sql             (latest schema — 7 tables, indexes, FK rules)
│   ├── migrations/            (numbered SQL migrations, PRAGMA user_version)
│   │   └── 0001_add_cascade_delete.sql
│   ├── requirements.txt
│   ├── templates/
│   │   ├── index.html         (full SPA, vanilla JS, apiFetch helper)
│   │   └── login.html         (token-input login page)
│   ├── static/
│   │   └── style.css          (dark mode, responsive)
│   └── tests/                 (166 tests, ~7-8s, no external deps)
│       ├── conftest.py        (shared fixtures, in-memory SQLite)
│       ├── test_app_security.py
│       ├── test_database.py
│       ├── test_engine_parsing.py
│       ├── test_config_validation.py
│       ├── test_migrations.py
│       ├── test_rate_limiting.py
│       ├── test_auth.py
│       └── test_csrf.py
├── tenants/                    # Per-business directories
│   ├── _template/             (blueprint copied by setup_tenant.py)
│   ├── _intake_template/      (intake-doc schema; 4 .md files + README)
│   ├── dana-wang/             (example: Dana Wang CPRW)
│   └── taylor-morgan/         (Taylor Morgan / Signal Stance — built via intake)
├── intake/                     # Working dirs for tenant intake (per-tenant subdirs)
│   └── taylor-morgan/         (filled-in source-of-truth that produced the tenant)
├── .claude/
│   ├── agents/                (9 audit agents, all model: opus)
│   ├── skills/
│   └── settings.json          (project-level model + permissions)
├── scripts/
│   ├── intake_tenant.py       (CLI: intake markdown → ready-to-run tenant)
│   ├── run-audit.sh
│   └── run-audit.bat
├── audit-reports/              (generated audit findings)
├── run.py                     (76 lines — CLI entry point)
├── setup_tenant.py            (41 lines — bare-template scaffolding)
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

# Create a new tenant from the bare template (manual fill-in)
python setup_tenant.py <tenant-name>

# Create a new tenant from filled-in intake markdown (preferred)
# 1. cp -r tenants/_intake_template intake/<tenant-name>
# 2. Fill in the four .md files (identity, voice samples, content rhythm, brand+feeds)
# 3. Run the extraction:
python scripts/intake_tenant.py <tenant-name> --from intake/<tenant-name>
python scripts/intake_tenant.py <tenant-name> --from intake/<tenant-name> --dry-run
python scripts/intake_tenant.py <tenant-name> --from intake/<tenant-name> --force

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
| `SIGNALSTANCE_BIND_HOST` | No | `127.0.0.1` | Host the Flask server binds to. Override only when intentionally exposing on the LAN |
| `SIGNALSTANCE_AUTH_TOKEN` | No | auto-generated | Shared-secret token for the login page. If unset, a fresh token is generated and printed at startup |
| `SIGNALSTANCE_SECRET_KEY` | No | auto-generated | Flask session signing key. If unset, sessions invalidate on every restart |
| `AUTH_ENABLED` | No | `true` | Set `false` to disable auth + CSRF (used by tests) |
| `RATE_LIMIT_ENABLED` | No | `true` | Set `false` to disable flask-limiter (used by tests) |
| `RATE_LIMIT_GENERATIONS` | No | `10 per minute;100 per day` | flask-limiter window string for the 6 generation routes |
| `RATE_LIMIT_FEED_REFRESH` | No | `1 per 5 minutes` | Cooldown for `/api/feeds/refresh` |
| `RATE_LIMIT_DEFAULT` | No | `200 per minute` | Per-endpoint default for any route without an explicit limit |

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
- Schema changes go through the migration system: update `schema.sql` (latest) AND add `migrations/NNNN_*.sql` (incremental upgrade for legacy DBs). `init_db()` runs `run_migrations()` on startup; `PRAGMA user_version` tracks state.
- FK behavior: `generations.insight_id`, `feed_articles.feed_id`, `carousel_data.generation_id` use `ON DELETE CASCADE`; `calendar_slots.generation_id` uses `ON DELETE SET NULL` so slots survive draft deletion.

### Flask Routes
- RESTful endpoints under `/api/*`
- All API responses return JSON with a `success` boolean field
- Routes that call the Anthropic API use `@require_api_key` to short-circuit with 503 when `ANTHROPIC_API_KEY` is unset — don't reinvent the inline check
- Generation routes persist drafts via `_save_drafts(insight_id, drafts)` — don't open a new enumerate/save_generation loop in route bodies
- Error handling via `_handle_api_error(e)` for Anthropic-API-adjacent exceptions (429/503/401/500); catch-all `except Exception` should `return _server_error(e)` so the full exception is logged and only a generic message reaches the client. ValueError 400s with hand-crafted messages (e.g., "Slot not found") still surface their `str(e)`.
- Input validation: check required fields, validate categories against known list
- Background operations use daemon threads (feed refresh, carousel cleanup)
- Auth + CSRF are enforced globally via the `_auth_and_csrf_gate` `before_request` hook in `app.py`. Any new route is protected by default. Add the path to `_AUTH_EXEMPT_PATHS` only for unauthenticated UX surfaces (login page, login endpoint, status probe). Add to `_CSRF_EXEMPT_PATHS` only when there's no cookie to compare (currently just `/api/auth/login`). State-changing methods (POST/PUT/PATCH/DELETE) require an `X-CSRF-Token` header matching the `csrf_token` cookie set at login.
- Rate limiting: generation routes use `@limiter.limit(RATE_LIMIT_GENERATIONS)`, `/api/feeds/refresh` uses `@limiter.limit(RATE_LIMIT_FEED_REFRESH)`. Keep the limiter decorator between `@app.route(...)` and `@require_api_key`. The 429 handler in `app.py` returns the standard JSON shape with a computed `Retry-After`.

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
- All API calls go through `apiFetch(url, opts)` — wraps `fetch()` so HTTP errors and non-JSON responses throw with `body.error` as the message. Don't call `fetch()` directly for app endpoints; use `apiFetch()` so `data.success` branches collapse to `.then(data => ...)` plus a `.catch(err => ...)`.
- Hash-based SPA routing (`#/create | #/calendar | #/calendar/YYYY-MM-DD | #/feed`). Tab clicks and calendar prev/next push history entries via `pushState`; `popstate` calls `applyRoute()` to re-render. New programmatic tab switches must call `switchToTab(name)`, not `renderTab()` directly, so URL stays in sync.
- Dark mode via CSS custom properties
- UI config loaded dynamically from `/api/config` endpoint
- Categories, templates, and schedule driven by tenant `business_config.json`

## Multi-Tenant Rules

1. **Never hardcode tenant-specific values in `framework/`** — all business-specific data comes from `business_config.json`, `feeds.json`, and `prompts/`
2. **Always load config through `business_config.py`** — never read `business_config.json` directly
3. **Each tenant has its own SQLite database** — path derived from `SIGNALSTANCE_TENANT_DIR` + config `database_name`
4. **Prompt resolution is tenant-first** — check `{tenant_dir}/prompts/` before `framework/` fallback
5. **Generated carousels go to `{tenant_dir}/generated_carousels/`** — never to a shared location
6. **New tenants are created from `_template/`** — use `setup_tenant.py` for a bare scaffold, or `scripts/intake_tenant.py` for the LLM-assisted flow that reads filled-in markdown from `intake/<name>/` and synthesizes the voice profile. Never copy another tenant directly
7. **Framework code must work with any valid `business_config.json`** — don't assume specific categories, colors, or schedule
8. **The `_template/` directory is the canonical schema** — if you add new config fields, update the template first AND `tenants/_intake_template/` so the intake flow can capture them
9. **Voice profile synthesis is non-deterministic** — re-running the intake script produces a slightly different `prompts/base_system.md` each time. Lock in a version you're happy with and avoid casual re-runs that overwrite hand-tuned voice rules

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
- Error responses return JSON, not HTML tracebacks; `_server_error()` keeps raw exception text out of 500 responses (logged via `app.logger.exception`)
- Input validation on categories, required fields, URL formats
- Rate limit error handling (429 from Claude API)
- Prompt injection resistance: untrusted content (insights, URLs, feed-article fields) is wrapped in XML tags via `engine._xml_wrap()` before reaching Claude; system prompts append `engine._SECURITY_GUARDRAIL` instructing the model to treat tagged content as data. Closing-tag defang prevents wrapped values from escaping the delimiter.
- Auth: shared-secret token + Flask signed-cookie session. `/login` page → `/api/auth/login` validates with `hmac.compare_digest`. Global `_auth_and_csrf_gate` `before_request` hook returns 401 JSON for unauthed `/api/*` and redirects unauthed `/` to `/login`.
- CSRF: double-submit cookie. `/api/auth/login` issues a `csrf_token` cookie at login; `apiFetch` reads it and sets `X-CSRF-Token` on state-changing requests; the gate compares header to cookie via `hmac.compare_digest`.
- Network exposure: default `BIND_HOST=127.0.0.1` so the server isn't reachable on the LAN unless explicitly opted in.
- Rate limiting: flask-limiter on the 6 generation routes (`10/min;100/day` default) and `/api/feeds/refresh` (`1 per 5 minutes`). Standard JSON 429 with `Retry-After`.

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
- Add fixtures to `tests/conftest.py` — the `db` fixture provides a clean in-memory database via `database.init_db()` (which runs schema.sql + migrations); `app_client` provides a Flask test client
- Security tests go in `test_app_security.py`
- Database tests go in `test_database.py`
- Parsing/engine tests go in `test_engine_parsing.py`
- Config validation tests go in `test_config_validation.py`
- Migration tests go in `test_migrations.py`
- Auth/CSRF tests go in `test_auth.py` / `test_csrf.py`
- Rate-limit tests go in `test_rate_limiting.py`
- New test files: `test_<module>.py` in `framework/tests/`
- Current count: 166 tests, ~7-8 seconds

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
| Config schema validator | `framework/validate.py` | `validate_business_config()` (pure, no side effects) |
| Frontend SPA | `framework/templates/index.html` | `framework/static/style.css` |
| App entry point | `run.py` | `framework/config.py` |
| Tenant scaffolding (bare) | `setup_tenant.py` | `tenants/_template/` |
| Tenant intake (LLM-assisted) | `scripts/intake_tenant.py` | `tenants/_intake_template/`, `intake/<name>/` |
| Tests | `framework/tests/conftest.py` | `framework/tests/test_*.py` |
