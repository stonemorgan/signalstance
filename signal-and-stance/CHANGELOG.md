# Changelog

All notable changes to Signal & Stance are documented here.

## [Unreleased]

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
- Placeholder handlers for Generate Content, Pick from Bank, Copy & Schedule, Change, Clear, Mark as Published, Unschedule (console.log stubs for Part 2 wiring)

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
