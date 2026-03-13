# Changelog

All notable changes to Signal & Stance are documented here.

## [Unreleased]

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
