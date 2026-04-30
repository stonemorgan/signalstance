# Changelog

All notable changes to Signal & Stance are documented here.

## [Unreleased]

### Added
- **Token-based auth + CSRF + 127.0.0.1 bind** — Closes audit Findings 1 (Critical, no auth) and 2 (High, no CSRF).
  - **Auth:** shared-secret token (`SIGNALSTANCE_AUTH_TOKEN`, auto-generated and printed at startup if unset) validated via `hmac.compare_digest`. Flask signed-cookie session (`SIGNALSTANCE_SECRET_KEY`, also auto-generated). Routes: `GET /login` (token-input page), `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/status`. Global `_auth_and_csrf_gate` `before_request` hook returns 401 JSON for unauthed `/api/*` and redirects unauthed `/` to `/login`. `_AUTH_EXEMPT_PATHS` whitelists the login UI/endpoints/static assets.
  - **CSRF:** double-submit cookie. `/api/auth/login` issues a `csrf_token` cookie at login; `apiFetch` reads it and sets `X-CSRF-Token` on state-changing requests; the gate compares header to cookie via `hmac.compare_digest`. `_CSRF_EXEMPT_PATHS` only contains the login endpoint (no cookie exists yet at that point — the secret token IS the auth).
  - **Network exposure:** default `SIGNALSTANCE_BIND_HOST=127.0.0.1` so the server isn't reachable on the LAN unless explicitly opted in.
  - **Frontend:** `apiFetch` reads cookie + injects header automatically; 401 triggers `/login` redirect; logout button in header (visible only when `auth_required` from `/api/auth/status`). New `templates/login.html` with dark-mode parity.
  - **Test suite:** 24 new tests (`test_auth.py`, `test_csrf.py`); autouse conftest fixture disables auth + rate limiting for the existing suite.
- **Rate limiting / generation caps via flask-limiter** — Closes audit Findings 2.1, 2.2, 2.3, 6.1, 6.2 (Critical+High).
  - 6 generation routes get `RATE_LIMIT_GENERATIONS` (default `10 per minute;100 per day`); `/api/feeds/refresh` gets `RATE_LIMIT_FEED_REFRESH` (default `1 per 5 minutes`); read endpoints fall under `RATE_LIMIT_DEFAULT` (default `200 per minute`). All env-tunable.
  - Custom 429 handler returns the standard `{success: false, error: …}` JSON shape with `Retry-After` computed from `limiter.current_limit.reset_at`.
  - In-memory storage (resets on restart, fine for single-user local tool).
- **Accessibility (WAI-ARIA) and form-state persistence** — `role=tablist` / `role=tab` / `aria-selected` / roving `tabindex` on tab bar (arrow-key nav between tabs); `aria-expanded` on collapsibles; `aria-label` on form controls; `role=radiogroup` on output-format and template selectors; muted/faint/placeholder color tokens bumped for WCAG AA 4.5:1. `sessionStorage` `ss-form-state-v1` persists category, raw input, URL, output format, template, and collapsible-open state across reload; restored at the end of `applyConfig()` after categories render.
- **Schema migration system** — `PRAGMA user_version`-based runner in `database.py` applies numbered migrations from `framework/migrations/*.sql`. Fresh DBs are stamped at the latest version (no migration scripts run on empty new files); legacy DBs at `user_version=0` get pending migrations applied in order with progress tracked atomically. `_is_fresh_db()` distinguishes the two by checking for any user tables before `schema.sql` runs.
- **Migration `0001_add_cascade_delete.sql`** — first real migration. Recreates four tables to add proper FK behavior: `generations.insight_id` and `feed_articles.feed_id` and `carousel_data.generation_id` get `ON DELETE CASCADE`; `calendar_slots.generation_id` gets `ON DELETE SET NULL` so slot history survives draft deletion. Closes the audit's deferred CASCADE-rules item which was blocked on having a migration system.
- **Tenant config validation at startup** — new `ConfigError` exception in `business_config.py` plus a `_validate()` checker that runs on import. Catches malformed JSON (with line/column), missing required top-level keys, missing nested keys, wrong types, unknown weekday names in `schedule.days`, and missing entries in `schedule.suggested_times`. `feeds.json` parsing also wrapped. `run.py` catches `ConfigError` and exits 1 with a one-line message instead of a stack trace.
- **`apiFetch()` helper in the SPA** — wraps `fetch()` so HTTP errors and non-JSON responses surface as thrown `Error` objects with the backend's `{success, error}` envelope message. Replaces 33 inline `fetch().then(r => r.json()).then(...)` chains. Empty `.catch(() => {})` blocks now `console.error()`; user-initiated calendar mutations `alert()` with the error message; feed-add surfaces it inline.
- **Hash-based SPA routing for back-button support** — top-level tab and calendar week now persist in `location.hash` (`#/create | #/calendar | #/calendar/YYYY-MM-DD | #/feed`). Tab clicks and calendar prev/next push history entries via `pushState`; `popstate` calls `applyRoute()` to re-render. Direct deep links (e.g. `/#/calendar/2026-04-27`) land on the right view. The previous `switchToTab(name)` is now a thin wrapper around `pushRoute()` + `renderTab()`; existing programmatic callers continue to work without changes.
- **Batch DB helpers to eliminate N+1 queries** — `get_carousel_data_for_generations(ids)` returns a `{generation_id: data}` dict in a single `WHERE generation_id IN (?,…)` query, and `get_feeds_with_article_counts(enabled_only)` returns feeds with `article_count` via a single `LEFT JOIN feed_articles … GROUP BY f.id`. The single-row functions (`get_carousel_data`, `get_feeds`) are unchanged for their other callers.
- **Prompt-injection resistance in `engine.py`** — new `_xml_wrap(tag, content)` helper wraps untrusted user/RSS content in XML delimiters and defangs literal closing tags so values can't escape the wrapper. New `_SECURITY_GUARDRAIL` constant is appended to every system prompt, instructing Claude to treat tagged content as data, not instructions. Applied at all 5 generation entry points (`generate_posts`, `generate_autopilot`, `generate_from_url`, `generate_from_feed_article`, `generate_carousel_content`) plus `feed_scanner.score_articles`. Tenant `prompts/*.md` files unchanged — defense lives in code so every tenant inherits the protection.
- **`_server_error(e, message=...)` helper in `app.py`** — logs the full exception (with traceback) via `app.logger.exception()` and returns a sanitized 500 JSON response. Replaces the prior pattern where 17 routes returned `str(e)` directly to the client, which could leak file paths, schema details, and Python internals. `_handle_api_error()`'s default branch also goes through this helper. ValueError 400s with hand-crafted domain messages (e.g., "Slot not found") still surface their text as before.
- **`@require_api_key` decorator and `_save_drafts(insight_id, drafts)` helper in `app.py`** — replaces 6 duplicated `if API_KEY_MISSING: return ...` blocks (with slightly inconsistent messages) and 5 duplicated draft-saving loops (with inconsistent `draft["angle"]` vs `draft.get("angle", "")` access). Net deletion in `app.py`; centralizes the 503 message and fixes a latent KeyError when draft dicts lacked an `angle` field.
- **`SIGNALSTANCE_OVERVIEW.md`** — codebase guide and user manual at the project root covering architecture, feature tour, data flow diagrams, tenant resolution, schema, and effectiveness tips.
- **`framework/tests/test_config_validation.py`** — 11 tests covering missing file, malformed JSON, missing/wrong-typed keys, unknown weekdays, missing day subkeys, missing suggested-time entries, empty `schedule.days`, non-object root.
- **`framework/tests/test_migrations.py`** — 8 tests covering fresh-DB stamping, legacy-DB upgrade with data preservation, idempotent re-run, CASCADE delete on generations / feed_articles / carousel_data, SET NULL on calendar_slots, and discovery sort order.

### Changed
- **`framework/schema.sql`** now reflects the latest schema. New DBs get `ON DELETE CASCADE` / `SET NULL` on FK references directly without going through migrations.
- **`framework/tests/conftest.py`** — `db` fixture now calls `database.init_db()` (which runs schema.sql + migrations) instead of executing `schema.sql` directly, so tests use the production code path.
- **`/api/history` route** — was up to 1+30+90 = 121 queries (1 for insights, N for drafts, M for per-draft carousel lookup). Now 3 queries: insights, all drafts via `WHERE insight_id IN (…)`, all carousels via `get_carousel_data_for_generations()`.
- **`/api/feeds` route** — was 1+N queries (1 for feeds, N for per-feed `SELECT COUNT(*)`). Now 1 query via `get_feeds_with_article_counts()`. The inline `from database import get_connection` in `app.py` is gone.
- **`get_generation_history()`** — refactored to fetch all drafts for the limited insight set in a single `IN`-clause query, then group in Python.
- **Test count** — full suite is now 166 tests (was 97), ~7-8 seconds, no external dependencies. New tests cover multi-insight history grouping, empty history, batch carousel lookup (and empty short-circuit), feeds-with-counts (including zero-article feeds and the enabled filter), `_xml_wrap` defang behavior, sanitized 500 responses (synthetic `AttributeError` injection check), preservation of ValueError messages, `_save_drafts` persistence + missing-`angle` fallback, `require_api_key` short-circuit + pass-through, rate-limit 429 shape + Retry-After, feed-refresh cooldown, login flow, session persistence, logout, constant-time token compare, CSRF rejection on missing/mismatched headers, and login-endpoint CSRF exemption.

## [1.15.0] - 2026-03-16

### Added
- **`CLAUDE.md`** — project-level instruction file for all Claude Code sessions. 255 lines covering model requirements, architecture overview, tech stack, key commands, environment variables, code conventions, multi-tenant rules, security rules, testing requirements, database schema, agent inventory, and key files reference. Loaded automatically at the start of every Claude Code conversation.
- **`.claude/settings.json`** — project-level Claude Code settings enforcing the Opus model and defining permission guardrails.
  - `"model": "opus"` ensures all interactive sessions use Opus regardless of user's global settings or `--model` CLI flag.
  - Allow list: `python run.py`, `python -m pytest`, `python setup_tenant.py`, `pip install`, `ls`, `git`, `mkdir -p audit-reports`, `cd framework && pytest`.
  - Deny list: `rm -rf` (recursive delete), `git push --force`, `git reset --hard` (destructive git), any command containing `ANTHROPIC_API_KEY` (key exposure prevention).

### Changed
- Opus model is now enforced at three levels: `.claude/settings.json` for interactive sessions, agent frontmatter (`model: opus`) for all 9 agents, and documented as a project requirement in `CLAUDE.md`.

## [1.14.0] - 2026-03-15

### Added
- **Pytest test suite** — 97 automated tests across 3 modules, runnable in ~3 seconds with zero external dependencies or API keys.
  - `framework/tests/test_database.py` (39 tests) — CRUD operations, calendar state machine transitions, foreign key enforcement, connection cleanup, carousel data round-trips.
  - `framework/tests/test_engine_parsing.py` (29 tests) — draft parsing, carousel content parsing (tips, before/after, myth/reality), field extraction, edge cases.
  - `framework/tests/test_app_security.py` (29 tests) — SSRF URL validation, path traversal rejection, debug mode defaults, API error response format, error categorization.
  - `framework/tests/conftest.py` — shared fixtures with in-memory SQLite and patched config for isolated testing.
- **SSRF protection on feed URLs** — new `_is_safe_url()` helper in `app.py` validates that feed URLs use http/https and do not resolve to private IP ranges (127.x, 10.x, 172.16-31.x, 192.168.x, 169.254.x, IPv6 loopback/ULA/link-local). Applied to the `POST /api/feeds` endpoint.
- **Path traversal guard on carousel downloads** — `GET /api/carousel/download/<id>` now verifies the resolved file path stays within the carousel output directory using `os.path.realpath()`.
- **Database performance indexes** — added indexes on `calendar_slots(slot_date)`, `generations(insight_id)`, and `feed_articles(feed_id)` to eliminate full table scans on frequent queries.
- **Calendar slot uniqueness constraint** — `UNIQUE INDEX` on `calendar_slots(slot_date)` prevents duplicate slots from concurrent requests.

### Changed
- **Flask debug mode off by default** — `app.run()` in both `app.py` and `run.py` now reads `FLASK_DEBUG` environment variable instead of hardcoding `debug=True`. Debug mode requires explicit opt-in via `FLASK_DEBUG=true`.
- **SQLite WAL mode enabled** — `get_connection()` now executes `PRAGMA journal_mode=WAL` for concurrent read/write support, eliminating "database is locked" errors during background feed refresh.
- **Foreign key enforcement enabled** — `get_connection()` now executes `PRAGMA foreign_keys=ON`, activating all referential integrity constraints declared in `schema.sql`.
- **SQLite busy timeout increased** — `sqlite3.connect()` now uses `timeout=30` (was default 5 seconds), reducing lock contention failures under concurrent access.
- **Database connection leak prevention** — all 24+ functions in `database.py` and 5 inline connection uses in `app.py` now use `try/finally` blocks to guarantee `conn.close()` even when exceptions occur.
- **Claude API call timeouts** — all `client.messages.create()` calls in `engine.py` now use `timeout=120` (2 minutes) and `feed_scanner.py` scoring uses `timeout=60`. Previously used the SDK default of 10 minutes.
- **Regenerate button double-click protection** — the regenerate button is now disabled during API calls and re-enabled on completion or error, preventing duplicate generation requests.
- **Calendar state machine enforcement** — `clear_slot()` now rejects clearing published slots with a `ValueError`. `assign_draft_to_slot()` now validates the slot is empty or draft_ready before assignment, rejecting scheduled/published slots.
- **Atomic calendar status transitions** — `update_slot_status()` now uses a single `UPDATE ... WHERE status IN (...)` query instead of separate read-then-write, eliminating the TOCTOU race condition.

### Fixed
- Database connections no longer leak when exceptions occur mid-operation (was a resource exhaustion risk under sustained error conditions).
- Calendar slots can no longer enter invalid states via concurrent requests or state machine bypasses.
- Feed URL addition no longer allows SSRF attacks targeting internal network services or cloud metadata endpoints.
- Carousel PDF downloads no longer vulnerable to path traversal via crafted filenames in the database.

## [1.13.0] - 2026-03-15

### Added
- **Audit agent suite** — 8 specialized Claude Code subagents for comprehensive codebase review, each targeting a specific domain: security, error resilience, data integrity, API robustness, frontend quality, code optimization, test coverage, and implementation execution.
- **`audit-suite` orchestrator agent** — master agent that coordinates the full 4-phase audit workflow: parallel audit (6 agents), triage & synthesis, implementation of critical fixes, and test coverage generation.
- **`/audit` slash command** — skill that triggers the full audit workflow from within any Claude Code conversation. Supports optional arguments to customize behavior (e.g., stop after triage).
- **`scripts/run-audit.sh`** — shell script for one-command audit execution with three modes: full audit (default), `--audit-only` (no code changes), and `--resume` (continue interrupted audit).
- **`scripts/run-audit.bat`** — Windows batch script equivalent for the audit runner.
- **Audit reports output** — all findings, triage summaries, implementation reports, and test coverage reports saved to `audit-reports/` for traceability across runs.

### Agent Definitions
- `.claude/agents/security-auditor.md` — XSS, injection, path traversal, tenant isolation, prompt injection, API key exposure
- `.claude/agents/error-resilience.md` — crash paths, unhandled exceptions, race conditions, resource leaks
- `.claude/agents/data-integrity.md` — SQLite concurrency, schema gaps, state machine bugs, orphaned data
- `.claude/agents/api-robustness.md` — Claude API error handling, rate limits, feed fetching, cost management
- `.claude/agents/frontend-reviewer.md` — SPA bugs, state management, DOM issues, accessibility
- `.claude/agents/codebase-optimizer.md` — dead code, duplication, architecture debt, performance
- `.claude/agents/test-architect.md` — test gap analysis and implementation (has write access)
- `.claude/agents/implementation-executor.md` — executes fixes from audit findings (has write access)
- `.claude/agents/audit-suite.md` — orchestrator coordinating all of the above

### Changed
- `.gitignore` — added `audit-reports/` to excluded paths

## [1.12.0] - 2026-03-15

### Added
- **Multi-tenant architecture** — the framework code (`framework/`) is now fully separated from tenant-specific content (`tenants/`). Each business gets its own directory with config, prompts, feeds, database, and generated files.
- **`run.py`** — new entry point that selects a tenant and starts the app. Supports `--tenant <name>` to specify a tenant, `--list` to show available tenants, and defaults to the first tenant found.
- **`setup_tenant.py`** — helper script to create new tenants from the `_template` skeleton. Usage: `python setup_tenant.py <tenant-name>`.
- **`tenants/_template/`** — skeleton tenant directory with placeholder `business_config.json`, empty `feeds.json`, and 11 template prompt files. Each prompt has `{{variable}}` placeholders and clearly marked `<!-- AUTHORED SECTION -->` areas telling new users exactly what to fill in.
- **`tenants/dana-wang/`** — Dana Wang's business content moved here from the old `signal-and-stance/` directory. Contains `business_config.json`, `feeds.json`, 11 prompt files, database, and generated carousels.
- **`tenants/dana-wang/feeds.json`** — Dana's 12 default RSS feeds extracted from the old hardcoded `feeds.py` into a JSON file.
- **`SIGNALSTANCE_TENANT_DIR`** environment variable — tells the framework which tenant directory to use. Set automatically by `run.py`.

### Changed
- **Directory renamed** — `signal-and-stance/` renamed to `framework/` to clarify its role as shared, reusable code.
- **`business_config.py`** — now reads `business_config.json` from the active tenant directory (set by `SIGNALSTANCE_TENANT_DIR`). Falls back to looking in its own directory for backwards compatibility. Exports `TENANT_DIR` for use by other modules.
- **`engine.py`** — `load_prompt()` now checks the tenant directory first for prompt files, falling back to the framework directory. This means tenants can selectively override prompts.
- **`config.py`** — database path (`DATABASE_PATH`) now points to the tenant directory instead of the framework directory. `.env` loading searches both the framework directory and the parent (root) directory.
- **`feeds.py`** — rewritten to load `DEFAULT_FEEDS` from the tenant's `feeds.json` file instead of a hardcoded Python list. Returns an empty list if `feeds.json` doesn't exist.
- **`carousel_renderer.py`** — `OUTPUT_DIR` now points to `generated_carousels/` within the tenant directory instead of the framework directory.
- **`app.py`** — `CAROUSEL_DIR` now uses `TENANT_DIR` for carousel PDF storage. Imports `TENANT_DIR` from `business_config`.
- **`.gitignore`** — moved to project root with patterns for tenant databases (`tenants/*/*.db`), tenant carousel PDFs (`tenants/*/generated_carousels/*.pdf`), and framework-level backwards compatibility.

### Removed
- **`signal-and-stance/` directory** — renamed to `framework/`.
- **Hardcoded `DEFAULT_FEEDS` in `feeds.py`** — replaced by tenant `feeds.json` loading.
- **`signal-and-stance/.gitignore`** — replaced by root-level `.gitignore`.

## [1.11.0] - 2026-03-15

### Added
- **`/api/config` endpoint** — serves a safe subset of `business_config.json` to the frontend (app name, owner, platform, content categories, schedule timezone, feed categories). No API keys or scoring internals are exposed.
- **`loadConfig()` / `applyConfig()`** — async config loader in the frontend with try/catch fallback to hardcoded defaults so the app still works if the endpoint fails.
- **`selectCategory(key)`** — centralized category selection function replacing 5 duplicated `categoryBtns.forEach(...)` patterns across the codebase.
- **`renderCategoryButtons()`** — generates category buttons dynamically from `content.categories` config, preserving existing CSS classes and click behavior.
- **`renderFeedCategoryDropdowns()`** — populates all `.feed-category-select` dropdowns (article filter and add-feed form) from `feeds.categories` config, preserving the "All categories" first option on the filter.
- **`getCategoryDisplayName(key)`** — converts category keys to display names (e.g., `executive_careers` → "Executive Careers"), replacing the hardcoded `feedCatLabels` map.

### Changed
- **6 hardcoded "LinkedIn" references** in scheduling UI, copy-and-schedule flow, unschedule reminder, paste hint, and `window.open` URL now read from `APP_CONFIG.platform.name` and `APP_CONFIG.platform.scheduling_url` with `|| 'LinkedIn'` fallbacks.
- **3 hardcoded "EST" references** in calendar time displays (published, scheduled, suggested) now read from `APP_CONFIG.schedule.timezone`.
- **Category buttons** in the Create tab are no longer hardcoded HTML — generated dynamically from config on page load.
- **Feed category dropdowns** (article filter and add-feed form) are no longer hardcoded `<option>` elements — populated from config on page load.
- **`formatCategory()`** now checks `APP_CONFIG.content.categories` first for display labels, falling back to a static map only for internal categories (autopilot, url_react, feed_react).
- **`contentTypeToCat` mapping** documented as config-dependent with a comment explaining its relationship to `business_config.json` content types and categories.
- **`app.py`** imports `BUSINESS` from `business_config` alongside `APP_NAME`.

### Removed
- **`feedCatLabels` hardcoded map** — replaced by dynamic `getCategoryDisplayName()`.
- **`categoryBtns` static NodeList** — removed; all category selection now uses `selectCategory()` with live DOM queries.

## [1.10.0] - 2026-03-15

### Added
- **Prompt template engine** — `load_prompt()` in `engine.py` now performs `{{key.subkey}}` placeholder substitution using a flattened version of `business_config.json`. Template variables like `{{owner.name}}`, `{{platform.name}}`, `{{owner.audience}}` are resolved automatically at load time.
- **`_flatten_config()`** helper that converts the nested config dict into dot-notation keys (e.g., `owner.name`, `content.default_ctas.tips`). List values are auto-joined as comma-separated strings.
- **`<!-- AUTHORED SECTION -->`** and **`<!-- TEMPLATED -->`** documentation markers in all 11 prompt files. Authored sections contain domain-specific voice rules, examples, and content arcs that must be manually rewritten per business. Templated sections are auto-filled from config.
- **Template verification tests** in `test_engine.py` and `test_carousel.py` — load all 11 prompt files via `load_prompt()` and assert zero unresolved `{{}}` placeholders remain.

### Changed
- **`prompts/base_system.md`** — identity paragraph, credentials block, platform references, and audience references in the self-evaluation checklist are now template variables. Voice rules, signature language, hard rules, and example hooks remain as authored content.
- **`prompts/category_pattern.md`**, **`category_faq.md`**, **`category_noticed.md`**, **`category_hottake.md`** — all owner name references replaced with `{{owner.name}}`; platform references with `{{platform.name}}`. Content arcs, example hooks, and tone descriptions remain as authored content.
- **`prompts/autopilot.md`** — owner name, audience, niche summary, and expertise references templatized. Search topics and category mapping remain as authored content.
- **`prompts/url_react.md`** and **`feed_react.md`** — owner name, platform, audience, and niche references templatized. Reaction approaches and feed category calibration remain as authored content.
- **`prompts/carousel_tips.md`**, **`carousel_beforeafter.md`**, **`carousel_mythreality.md`** — owner name and platform references templatized. Content rules and example outputs remain as authored content.

## [1.9.0] - 2026-03-15

### Added
- **`business_config.json`** — single source of truth for all business identity, brand colors, typography, content schedule, posting times, feed categories, scoring criteria, default CTAs, and platform settings. Changing the business owner, brand, schedule, or domain is now a single-file edit.
- **`business_config.py`** — loader module that reads `business_config.json` at import time and exposes convenience accessors (`OWNER`, `PLATFORM`, `BRAND_COLORS`, `CONTENT`, `SCHEDULE`, `FEEDS_CONFIG`, `SCORING`, `APP_NAME`). Includes `{section.key}` template interpolation for scoring strings.

### Changed
- **`brand.py`** now reads all colors, fonts, author identity, and slide dimensions from `business_config.json` instead of hardcoding them. The `BRAND` dict structure is preserved — no downstream changes needed.
- **`config.py`** now reads `CONTENT_SCHEDULE`, `SUGGESTED_TIMES`, and `DATABASE_PATH` from `business_config.json`. Integer keys (0=Monday through 4=Friday) are preserved for backward compatibility. `ANTHROPIC_MODEL`, `MAX_TOKENS`, and `FLASK_PORT` are now overridable via environment variables.
- **`feeds.py`** — `FEED_CATEGORIES` dict now reads from `business_config.json`. `DEFAULT_FEEDS` list remains in this file.
- **`feed_scanner.py`** — scoring system prompt is now built dynamically from `business_config.json` owner identity and scoring criteria instead of a hardcoded paragraph.
- **`engine.py`** — replaced 8 hardcoded business-specific strings with config reads: autopilot topic description, URL/feed reaction messages, default relevance reason, and 3 CTA defaults.
- **`app.py`** — app name read from config and passed to the template via `app_name` variable; fallback string uses config.
- **`templates/index.html`** — 3 hardcoded "Signal & Stance" references replaced with `{{ app_name }}` Jinja2 variable.
- **`carousel_renderer.py`** — default CTA fallback now reads from `business_config.json` instead of a hardcoded string.

## [1.8.0] - 2026-03-13

### Added
- **Carousel output format in UI** — "Output: Text Post / Carousel" radio toggle in the Create tab between the textarea and Generate button. Selecting "Carousel" reveals a template picker with three options (Numbered Tips, Before/After, Myth vs Reality) and changes the button text to "Generate Carousel"
- **Carousel results display** — carousel-specific result card showing title, template type, slide count, horizontal slide preview strip (Cover, Tip 1, Tip 2..., CTA boxes), full slide content details, "Download PDF" button, "Regenerate Content" button, and "Add to Calendar" button
- **Carousel history integration** — carousel entries in the History section display a "Carousel" tag alongside the category tag, show the carousel title and slide count instead of draft text, and include a "Download PDF" link when the file still exists
- **`POST /api/generate/carousel`** — main carousel generation endpoint. Validates category, raw_input, and template_type; saves insight; calls `generate_carousel_content()` + `render_carousel()`; saves generation and carousel metadata; returns carousel info with download URL and slide previews
- **`GET /api/carousel/download/<generation_id>`** — serves the generated PDF file for download, returns 404 if carousel data or file doesn't exist
- **`POST /api/generate/carousel/regenerate`** — regenerates carousel content from the same insight with new API call, renders new PDF, returns updated carousel data
- **`carousel_data` database table** — stores carousel metadata (generation_id FK, template_type, parsed_content as JSON, pdf_filename, slide_count)
- **`save_carousel_data()`** and **`get_carousel_data()`** database functions
- **`cleanup_old_carousels(days=30)`** — runs on app startup, deletes PDF files older than 30 days from `generated_carousels/`
- **`generated_carousels/` directory** created automatically on app startup
- History API (`GET /api/history`) now enriches responses with carousel metadata including template type, slide count, download URL, and file existence check

### Changed
- `GET /api/history` response now includes a `carousel` object on drafts that are carousels, with `template_type`, `slide_count`, `title`, `pdf_url`, and `file_exists` fields
- Generate button text dynamically updates: "Generate Drafts" (text), "Generate Carousel" (carousel), or "Generate Reaction" (URL)
- Results section heading switches between "Your Drafts" and "Your Carousel" based on output type
- Regenerate button hidden for carousel results (carousel card has its own "Regenerate Content" button)

## [1.7.0] - 2026-03-13

### Added
- **PDF carousel renderer** — generates branded 1080×1080 multi-page PDF carousels from structured content produced by the carousel content engine
- `carousel_renderer.py` with full rendering pipeline: cover slide, template-specific content slides, and call-to-action closing slide
- Three visual templates matching the content templates:
  - **Numbered Tips** — large teal watermark number, alternating white/off-white backgrounds, headline + body layout
  - **Before/After** — red/green comparison boxes with checkmark/cross markers, optional annotation notes
  - **Myth vs Reality** — curly-quoted myths, green "REALITY" pill divider label, alternating backgrounds
- `render_carousel(parsed_content, template_type, output_path)` orchestrator — validates input, renders all slides, saves PDF, returns `{success, path, file_size, page_count}`
- Cover slide renderer — navy background, gold accent bar, 64pt title, subtitle, author footer
- CTA slide renderer — author credentials block, teal rounded CTA box, LinkedIn URL
- `draw_wrapped_text()` helper using ReportLab Paragraph + Frame for proper text wrapping with XML escaping
- `draw_footer()` and `draw_accent_line()` shared decorators across content slides
- All colors and fonts sourced from `brand.py` for consistency
- `reportlab>=4.0` added to requirements.txt
- `generated_carousels/` added to .gitignore
- Auto-creates `generated_carousels/` output directory on first render

## [1.6.0] - 2026-03-13

### Added
- **Carousel content generation** — generate structured multi-slide LinkedIn carousel content from the same insights used for text posts. Three templates available: Numbered Tips, Before/After, and Myth vs Reality.
- `brand.py` — centralized brand configuration with colors (primary navy, teal accent, warm gold), typography (Helvetica family), Dana's identity info, and slide dimensions (1080×1080)
- `prompts/carousel_tips.md` — Numbered Tips carousel prompt with strict `TIP N HEADLINE:` / `TIP N BODY:` output format, 5–7 tips, headlines ≤6 words, body ≤30 words, number required in title
- `prompts/carousel_beforeafter.md` — Before/After carousel prompt with `PAIR N BEFORE:` / `PAIR N AFTER:` / `PAIR N NOTE:` format, 4–6 pairs, realistic weak-to-strong resume transformations
- `prompts/carousel_mythreality.md` — Myth vs Reality carousel prompt with `MYTH N:` / `REALITY N:` format, 4–6 pairs, real misconceptions grounded in ATS/recruiter expertise
- `generate_carousel_content(template_type, raw_input)` in engine.py — loads base system prompt + carousel-specific prompt, calls the API, returns parsed content dict
- `parse_carousel_content(template_type, raw_content)` in engine.py — parses Claude's structured text response into template-specific dicts using line-by-line keyword matching
- `_extract_field(text, label)` helper for reliable single-line field extraction from structured text
- `_parse_tips()`, `_parse_beforeafter()`, `_parse_mythreality()` — template-specific parsers returning structured dicts with title, subtitle, slides list, and CTA
- `CAROUSEL_PROMPT_MAP` dict mapping template types to prompt file paths
- `test_carousel.py` — test script validating all 3 templates with realistic inputs, content rules, and parsing reliability

## [1.5.0] - 2026-03-13

### Added
- **Feed tab** — third tab in the UI (`[ Create ] [ Calendar ] [ Feed ]`) for browsing and acting on curated RSS articles directly in the browser
- **Article feed view** — scrollable list of article cards showing title (clickable, opens source URL), feed name, category tag, relative time, truncated summary, relevance score badge (green/amber/gray), and relevance reason
- **"Generate Post From This" button** on each article card — generates 3 drafts from the article, switches to the Create tab, and displays source info (article title, feed name, relevance score) above the drafts
- **"Dismiss" button** on each article card — removes the article with a smooth fade-out animation, no confirmation needed
- **Feed controls** — "Last refreshed" timestamp with "Refresh Feeds" button, category filter dropdown (10 categories), "High relevance only" checkbox, and live article count
- **Refresh loading state** — shows "Scanning feeds..." during refresh (30-60 seconds), then displays results summary ("Found 47 new articles, 8 highly relevant") before auto-hiding
- **Feed management view** — accessible via "Manage Feeds" link; shows all feeds with enable/disable toggle, name, category tag, URL, last fetched time, article count, error status, and remove button with confirmation
- **Add feed form** — inline form with URL, Name, and Category dropdown; immediately fetches the feed on add and shows success/failure feedback
- **Autopilot status line** in Create tab — shows "Drawing from N curated articles · Last refreshed [time]" or "No curated articles available · Will search the web" below the autopilot button
- **Feed source info in results** — when autopilot or "Generate Post From This" uses a feed article, shows "Based on: [linked title] / via [feed name] · Relevance: [score]" above the drafts
- Empty states for no articles ("Click Refresh Feeds to scan your curated sources") and no matching filters ("Try broadening your search")
- `feed_react` category tag styling in CSS
- Feed category tag colors for all 10 categories (leadership, careers, executive_careers, hr_recruiting, labor_data, linkedin, hr_tech, compensation, workplace, business_news)

### Changed
- Tab switching now handles three tabs (create, calendar, feed) with mutual exclusion
- `showSource()` function accepts optional `sourceArticle` parameter for feed-sourced results
- `doAutopilot()` detects `method: "feed"` in response and displays feed-specific source info
- `formatCategory()` now includes `feed_react` mapping
- Autopilot status line refreshes after generation and feed refresh

## [1.4.0] - 2026-03-13

### Added
- **Feed-powered autopilot** — "Generate an idea for me" now draws from the curated RSS feed pool instead of relying on web search. Picks the highest-scoring unused article and generates 3 drafts reacting to it with Dana's expertise.
- `prompts/feed_react.md` — new prompt for generating LinkedIn posts from RSS article titles and summaries. Posts stand alone, cite data naturally, and narrow general trends to Dana's executive niche.
- `generate_from_feed_article(article)` in engine.py — generates 3 post drafts from a feed article dict using the base voice profile + feed reaction prompt
- `generate_autopilot_from_feeds()` in engine.py — upgraded autopilot flow: tries high-relevance articles (score >= 0.7) first, falls back to medium-relevance (>= 0.5), then falls back to web search
- `POST /api/articles/<id>/generate` — one-click content generation from a specific feed article. Saves insight, marks article as used, returns standard draft response.
- `feed_react` added as a valid insight category
- Autopilot API response now includes `method` field ("feed" or "web_search") and `source_article` object with article title, URL, feed name, relevance score, and relevance reason

### Changed
- `POST /api/generate/autopilot` now calls `generate_autopilot_from_feeds()` instead of `generate_autopilot()` directly. Response is a backward-compatible superset — existing fields (`success`, `insight_id`, `drafts`, `source_summary`, `source_url`) are preserved, with new `method` and `source_article` fields added.

## [1.3.0] - 2026-03-13

### Added
- **RSS Feed Scanner** — curated feed system that pulls articles from 12 high-quality career, leadership, HR, and labor market sources
- `feeds.py` with default feed list and category definitions covering leadership, careers, executive careers, HR/recruiting, labor data, HR tech, workplace, and business news
- `feed_scanner.py` module with feed fetching (via `requests` + `feedparser`), Claude-powered relevance scoring, and batch refresh
- `feeds` and `feed_articles` database tables with full CRUD and deduplication on article URL
- 9 new database functions: `seed_default_feeds`, `get_feeds`, `add_feed`, `update_feed`, `delete_feed`, `update_feed_fetch_status`, `save_articles`, `get_recent_articles`, `mark_article_used`, `mark_article_dismissed`, `update_article_relevance`, `get_article_by_id`, `get_feed_stats`
- 7 new API routes:
  - `GET /api/feeds` — list all feeds with status, article counts, and summary stats
  - `POST /api/feeds` — add a new feed (immediately fetches to verify)
  - `PUT /api/feeds/<id>` — update feed properties (enabled, name, category, weight)
  - `DELETE /api/feeds/<id>` — remove a feed and its articles
  - `GET /api/articles` — browse articles with filters (limit, min_relevance, category, unused_only)
  - `POST /api/articles/<id>/dismiss` — soft-dismiss an article from the feed pool
  - `POST /api/feeds/refresh` — fetch all feeds and score new articles, returns full results summary
- Relevance scoring via Claude API — each article scored 0.0-1.0 based on relevance to executive resume writing, LinkedIn optimization, and senior career strategy
- Auto-refresh on startup — background thread checks feed freshness and refreshes if stale (>6 hours)
- Default feeds seeded automatically on first startup
- `feedparser>=6.0.0` and `requests>=2.31.0` added to requirements.txt

### Changed
- Feed fetcher uses `requests` with proper User-Agent header instead of feedparser's default HTTP client (fixes 403 blocks from BLS and other government/corporate sources)

### Fixed
- 11 of 16 original feed URLs were broken (404, 403, DNS failures, dead domains). Replaced with verified working alternatives:
  - HBR (404) replaced by McKinsey Insights
  - SHRM (dead RSS) replaced by HR Dive
  - ERE (404) replaced by RecruitingDaily
  - The Muse (503) replaced by Ask a Manager
  - The Ladders (403) replaced by Inc.
  - Reuters Business (domain dead since 2020), WSJ Careers (paywall 401), LinkedIn Blog (no RSS), HR Technologist (defunct 404), PayScale (no RSS) — removed and replaced where possible

## [1.2.1] - 2026-03-13

### Added
- **"Add to Calendar" button** on every draft card — assign any generated draft to an empty calendar slot without starting from the Calendar tab first. Shows a dropdown listing empty slots from the current and next week.

## [1.2.0] - 2026-03-13

### Added
- **Create ↔ Calendar interaction** — "Generate Content" on a calendar slot switches to Create tab with category pre-selected and a context banner showing which day you're generating for
- **"Use for [Day]" buttons** on draft cards when generating for a calendar slot — assigns the chosen draft and returns to the Calendar tab
- **Pick from Bank** — inline panel on empty calendar slots lists past insights filtered by matching category, with "Show all categories" toggle
- **Copy & Schedule flow** — copies draft to clipboard, opens LinkedIn in a new tab, shows confirmation panel with time input; persists across tab switches until confirmed or cancelled
- **Change draft panel** — shows all 3 drafts from the generation session inline, highlights the current selection, click to reassign; includes "Regenerate" button to re-enter the generation flow
- **Mark as Published** — one-click status update on scheduled slots
- **Unschedule** — returns scheduled slots to draft ready with a reminder to cancel on LinkedIn
- **Clear** — resets draft ready slots back to empty
- `GET /api/insight/<id>/generations` API route for fetching sibling drafts
- `insight_id` now included in calendar slot draft data for cross-referencing

### Changed
- Calendar tab now always refreshes data when activated (ensures up-to-date state)
- Tab switching extracted into reusable `switchToTab()` helper

### Removed
- All `console.log` placeholder stubs replaced with working implementations

## [1.1.0] - 2026-03-13

### Added
- **Content Calendar** — weekly view (Mon-Fri) with 5 day cards showing slot status
- Tab system to switch between Create and Calendar views
- Calendar slots with 5 status states: empty, draft_ready, scheduled, published, skipped
- Week navigation arrows to browse past and future weeks
- Skip/Unskip toggle for days Dana decides not to post
- Past week detection — past weeks render as read-only with no action buttons
- "Show full post" toggle on day cards (truncates at ~200 characters)
- Week stats summary in calendar header ("3 of 5 slots filled")
- Suggested posting times per day in `config.py` (`SUGGESTED_TIMES`)
- `calendar_slots` database table with generation foreign key
- 6 new database functions: `generate_week_slots`, `get_week_slots`, `assign_draft_to_slot`, `update_slot_status`, `clear_slot`, `get_week_stats`
- Status transition validation (prevents illegal state changes like empty → published)
- 5 new API routes: `GET /api/calendar`, `POST /api/calendar/assign`, `/status`, `/clear`, `/skip`
- `for_slot_id` optional parameter on `POST /api/generate` for calendar-aware generation
- CSS variables for calendar status colors with dark theme support
- Left border accent colors per slot status (draft=blue-gray, scheduled=blue, published=green, skipped=gray)

## [1.0.0] - 2026-03-13

### Added
- Dark mode with persistent toggle (saved to localStorage)
- Manual content generation across 4 categories: Pattern, FAQ, Noticed, Hot Take
- Autopilot mode — searches current career/hiring news and generates posts automatically
- URL reaction mode — reads an article and generates Dana's professional take
- 3 draft variations per generation with different angles
- Copy-to-clipboard with visual confirmation and backend tracking
- Insight Bank — browse and reuse past observations
- Generation History — expand past sessions to review or copy older drafts
- Daily content schedule banner with rotating suggestions (Mon-Fri)
- Ctrl+Enter / Cmd+Enter keyboard shortcut for fast generation
- SQLite database for persisting insights and generations
- Full voice profile and prompt system in `prompts/` directory
- Setup page with clear instructions when API key is missing
- User-friendly error messages for rate limits, network issues, and auth failures

### Fixed
- `request.get_json()` now uses `silent=True` to return clean error messages instead of Flask 415 internals
- Added explicit parentheses to auth error check for operator precedence clarity
- Removed unused `sys` import
