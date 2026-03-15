# Signal & Stance

A locally hosted web app that helps generate social media content in a consistent, authentic voice. Built for daily use — go from insight to published post in under 5 minutes. The target platform (LinkedIn, Instagram, etc.) is configurable via `business_config.json`.

## Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

### Installation

1. Clone or download the project, then navigate to the project directory:

```bash
cd signal-and-stance
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your API key:

```
ANTHROPIC_API_KEY=your-api-key-here
```

4. Run the app:

```bash
python app.py
```

5. Open [http://localhost:5000](http://localhost:5000) in your browser.

## Usage

### Daily Workflow (Create Tab)

1. Open the app and check today's content suggestion in the banner
2. Choose one of three input methods:

**Manual (recommended):** Select a category, type a 1-2 sentence observation from your work, and click Generate. This produces the most authentic content.

**URL Reaction:** Paste a link to an article or post that sparked a thought. The tool reads the content and generates your professional reaction — not a summary.

**Autopilot:** Click "Generate an idea for me" when you have no specific observation. The tool draws from your curated RSS feed pool — picking the highest-relevance unused article and generating a professional reaction. If no feed articles are available, it falls back to web search automatically. A status line below the button shows how many curated articles are available.

3. Review the 3 draft variations
4. Click "Copy" on the best one, or click **"Add to Calendar"** to assign the draft to an empty calendar slot
5. Paste into LinkedIn, make any final tweaks, and post

### Weekly Workflow (Calendar Tab)

The Calendar tab shows your week laid out with content slots for Monday through Friday. Each day has a content type (Pattern, Tactical Tip, Deep Dive, Hot Take, Quick Win) and a suggested posting time.

1. Switch to the **Calendar** tab and navigate to the week you want to plan
2. Click **Generate Content** on an empty day — this switches to the Create tab with the matching category pre-selected and a banner showing which day you're generating for
3. Type your insight and generate as usual. Each draft card now shows a **"Use for [Day]"** button
4. Click **"Use for [Day]"** on the draft you want — the app assigns it and returns to the Calendar
5. Click **Copy & Schedule on LinkedIn** — the draft is copied to your clipboard and LinkedIn opens in a new tab
6. Paste into LinkedIn, use the clock icon to schedule, then return to Signal & Stance
7. Enter the time you scheduled and click **"I've Scheduled It"** to confirm
8. After the post goes live, click **Mark as Published** to complete the slot

**Other calendar actions:**

- **Pick from Bank** — browse past insights directly from a calendar slot, pick one to pre-fill the Create form
- **Change** — swap the assigned draft for a different variation from the same generation session, or click Regenerate to create new drafts
- **Clear** — reset a draft ready slot back to empty
- **Skip / Unskip** — mark days you don't plan to post
- **Unschedule** — return a scheduled slot to draft ready (remember to also cancel on LinkedIn)
- Past weeks display as read-only history

Slot statuses flow in this order: **empty** → **draft ready** → **scheduled** → **published**. Any slot can also be marked as **skipped**.

### Feed Tab

The Feed tab lets you browse curated articles and generate content from them directly in the browser.

1. Switch to the **Feed** tab to see recent articles from your curated RSS sources
2. Use the **category filter** and **"High relevance only"** checkbox to narrow the list
3. Click **"Refresh Feeds"** to scan all sources for new articles (takes 30-60 seconds)
4. Click an **article title** to open the original source in a new tab
5. Click **"Generate Post From This"** on any article — switches to the Create tab with 3 drafts and source info displayed
6. Click **"Dismiss"** to remove articles you're not interested in

**Feed Management:** Click "Manage Feeds" at the bottom of the article list to:

- Enable/disable feeds with the toggle checkbox
- See feed status (last fetched, article count, errors)
- Remove feeds (with confirmation)
- Add new feeds with the URL/Name/Category form at the bottom

### RSS Feed Scanner

The Feed Scanner pulls articles from curated RSS sources and scores them for relevance to the business owner's niche using Claude. Feed categories and scoring criteria are configured in `business_config.json`.

**API endpoints:**

- `GET /api/feeds` — list all feeds with status and article counts
- `POST /api/feeds` — add a new feed (JSON body: `url`, `name`, `category`)
- `PUT /api/feeds/<id>` — update feed properties (`enabled`, `name`, `category`, `weight`)
- `DELETE /api/feeds/<id>` — remove a feed and its articles
- `GET /api/articles` — browse articles (query params: `limit`, `min_relevance`, `category`, `unused_only`)
- `POST /api/articles/<id>/generate` — generate 3 post drafts from a specific article
- `POST /api/articles/<id>/dismiss` — dismiss an article from the pool
- `POST /api/feeds/refresh` — fetch all feeds and score new articles

**Frontend config:** `GET /api/config` — returns a safe subset of `business_config.json` for the frontend (app name, owner, platform, content categories, schedule timezone, feed categories). No API keys or scoring internals are exposed.

**Autopilot integration:** The autopilot (`POST /api/generate/autopilot`) now checks the feed pool first. The response includes a `method` field ("feed" or "web_search") and a `source_article` object when a feed article was used.

**Auto-refresh:** On startup, feeds are refreshed in the background if they haven't been fetched in over 6 hours.

**Managing feeds:** Edit `feeds.py` to change the default feed list. New feeds added via the API or the Feed tab's management view are stored in the database and persist across restarts. Feed URLs are tested on add — if a feed returns an error, it's saved but flagged.

**Relevance scoring:** Articles are scored 0.0-1.0 based on how relevant they are to the business owner's niche (configured in `business_config.json` under `scoring` and `owner`). Articles scoring 0.7+ are considered high relevance and shown with a green badge in the Feed tab.

### Carousel Generation

Generate branded LinkedIn carousel PDFs directly from the app. Carousels are multi-slide PDF documents that display as swipeable card decks when uploaded to LinkedIn as document posts.

1. Select a category and type your insight as usual
2. Switch the **Output** toggle from "Text Post" to **"Carousel"**
3. Choose a template:
   - **Numbered Tips** — "7 mistakes", "5 strategies" — one tip per slide with headline + body
   - **Before / After** — weak vs strong resume examples side by side
   - **Myth vs Reality** — debunk common misconceptions with expert corrections
4. Click **"Generate Carousel"**
5. Review the result card showing the carousel title, slide preview strip, and full slide content
6. Click **"Download PDF"** to get the file, then upload it to LinkedIn as a document post
7. Click **"Regenerate Content"** if you want different slide content with the same template

Carousels also appear in the History section with a "Carousel" tag and a download link. Old PDFs are automatically cleaned up after 30 days.

**Carousel API endpoints:**

- `POST /api/generate/carousel` — generate a carousel (JSON body: `category`, `raw_input`, `template_type`). Returns carousel info with `pdf_url`, `slides_preview`, and metadata.
- `GET /api/carousel/download/<generation_id>` — download the generated PDF file
- `POST /api/generate/carousel/regenerate` — regenerate with the same insight (JSON body: `insight_id`, `template_type`)

### PDF Carousel Rendering

Render structured carousel content into branded 1080×1080 multi-page PDFs using `carousel_renderer.py`.

```python
from carousel_renderer import render_carousel

result = render_carousel(parsed_content, "tips")
# result = {"success": True, "path": "generated_carousels/carousel_tips_1234.pdf", "file_size": 7611, "page_count": 7}
```

Each PDF contains:
- **Cover slide** — navy background with gold accent bar, title (64pt), subtitle, and author footer
- **Content slides** — template-specific layouts matching the three content templates (tips with watermark numbers, before/after with red/green comparison boxes, myth/reality with pill dividers)
- **CTA slide** — author credentials, LinkedIn URL, and call-to-action in a teal rounded box

All visual styling (colors, fonts, identity) is sourced from `business_config.json` via `brand.py`. PDFs are saved to `generated_carousels/` and automatically cleaned up after 30 days.

### Tips for Good Insights

- **Short and specific beats long and vague.** "Executives are burying board experience as a single bullet point" is better than "I've been noticing resume trends lately."
- **Include a number or detail when you can.** "3 of my last 5 clients had the same ATS issue" gives the tool more to work with.
- **Use the category that matches your observation.** Each category triggers different framing and angle strategies.

### Insight Bank

Past insights are saved automatically. Open the Insight Bank section to browse previous observations. Click "Use this" to pre-fill the form and generate fresh drafts from an older idea.

### History

The History section shows your recent generation activity. Expand any entry to see the drafts and copy ones you may have skipped initially.

### Dark Mode

Click the moon/sun icon in the top-right corner to toggle dark mode. Your preference is saved automatically and persists across sessions.

## Customization

### Business Configuration

All business identity, brand, schedule, and domain settings live in a single file: **`business_config.json`**. Edit this file to change:

- **Owner identity** — name, title, business name, URL, credentials, niche summary, audience
- **Platform** — target platform name, post word range, carousel dimensions
- **Brand** — color palette, typography, semantic colors
- **Content** — category definitions, carousel templates, default CTAs
- **Schedule** — weekly content types, daily suggestions, suggested posting times, timezone
- **Feed categories** — category labels and descriptions for RSS feed classification
- **Scoring criteria** — relevance scoring thresholds and prompt templates

The rest of the codebase reads from this config automatically. `brand.py`, `config.py`, and `feeds.py` all derive their values from `business_config.json` at import time. The frontend loads config via `GET /api/config` on page load — category buttons, feed category dropdowns, platform name in scheduling UI, and timezone labels are all rendered dynamically from this endpoint.

### Prompt Template System

All 11 prompt files in `prompts/` use `{{key.subkey}}` template variables that are auto-filled from `business_config.json` at load time. For example, `{{owner.name}}` becomes "Dana Wang" and `{{platform.name}}` becomes "LinkedIn."

Each prompt file is divided into two types of sections, marked with HTML comments:

- **`<!-- TEMPLATED -->`** — Identity references (name, credentials, audience, platform) auto-filled from config. No manual editing needed when swapping businesses.
- **`<!-- AUTHORED SECTION -->`** — Domain-specific voice rules, examples, content arcs, and signature language. These must be manually written for each business domain.

Available template variables include: `{{owner.name}}`, `{{owner.title}}`, `{{owner.business}}`, `{{owner.credentials}}`, `{{owner.audience}}`, `{{owner.audience_examples}}`, `{{owner.specializations}}`, `{{owner.niche_summary}}`, `{{owner.client_outcomes}}`, `{{platform.name}}`, `{{content.default_ctas.tips}}`, and any other dot-notation path into `business_config.json`. List values render as comma-separated strings.

### Voice Profile

The voice rules live in `prompts/base_system.md`. The identity paragraph and credentials block are templatized; tone, signature language, hard rules, and structural guidelines are authored content that should be edited manually per business.

### Category Prompts

Each category has its own prompt file in `prompts/`:

- `category_pattern.md` — "I keep seeing..." framing
- `category_faq.md` — "A client asked me..." framing
- `category_noticed.md` — "I just noticed..." framing
- `category_hottake.md` — "Hot take" framing
- `autopilot.md` — Web search and synthesis instructions
- `url_react.md` — URL reaction instructions
- `feed_react.md` — Feed article reaction instructions (used by autopilot and article-specific generation)
- `carousel_tips.md` — Numbered Tips carousel content generation
- `carousel_beforeafter.md` — Before/After carousel content generation
- `carousel_mythreality.md` — Myth vs Reality carousel content generation

All prompt files use template variables for identity references and `<!-- AUTHORED SECTION -->` markers for domain-specific content that needs manual editing when adapting to a new business.

### Number of Drafts

The base system prompt requests 3 drafts. To change this, edit the output format section in `prompts/base_system.md`.

### Feed Sources

Edit `feeds.py` to change the default RSS feed list. Each feed has a URL, display name, category tag, and relevance weight (0.0-1.0). Feeds added via `POST /api/feeds` are stored in the database and won't be overwritten by changes to `feeds.py`.

Feed categories are defined in `business_config.json` under `feeds.categories`.

### Model

The default model is `claude-sonnet-4-20250514`. Override it by setting `ANTHROPIC_MODEL` in your `.env` file. `MAX_TOKENS` and `FLASK_PORT` are also overridable via environment variables.

## Troubleshooting

### "API key not configured"

Create a `.env` file in the project root directory (same folder as `app.py`) with:

```
ANTHROPIC_API_KEY=your-key-here
```

Then restart the app.

### "API key is invalid"

Verify your key at [console.anthropic.com](https://console.anthropic.com). Keys start with `sk-ant-`.

### Port already in use

Another app is using port 5000. Either stop that app, or set `FLASK_PORT` in your `.env` file.

### "Database is locked"

This can happen if two instances of the app are running. Stop all instances and restart with a single `python app.py`.

### Autopilot returns "Nothing compelling found"

This can happen when the autopilot falls back to web search (no unused feed articles available) and finds nothing compelling. Try refreshing feeds first (`POST /api/feeds/refresh`), or switch to manual mode.

### URL reaction fails

Some URLs are behind paywalls or block automated access. Try pasting the article text directly into the observation field instead.

### Slow generation

API calls typically take 5-15 seconds. Autopilot and URL reaction are slower (10-20 seconds) because they include web search. This is normal.

### Feed refresh is slow

A full feed refresh fetches 12 RSS feeds and then scores new articles via the Claude API. This typically takes 30-60 seconds. The startup auto-refresh runs in a background thread so it doesn't block the app.

### A feed stopped working

RSS feed URLs change over time. Use `GET /api/feeds` to check which feeds have errors. Disable broken feeds with `PUT /api/feeds/<id>` (`{"enabled": false}`) or delete them with `DELETE /api/feeds/<id>`. Add replacements with `POST /api/feeds`.
