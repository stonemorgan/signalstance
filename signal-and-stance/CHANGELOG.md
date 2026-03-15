# Changelog

All notable changes to Signal & Stance are documented here.

## [Unreleased]

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
