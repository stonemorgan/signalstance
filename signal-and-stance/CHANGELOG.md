# Changelog

All notable changes to Signal & Stance are documented here.

## [Unreleased]

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
