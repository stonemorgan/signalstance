# Signal & Stance

A locally hosted web app that helps generate LinkedIn content in a consistent, authentic voice. Built for daily use — go from insight to published post in under 5 minutes.

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

### Daily Workflow

1. Open the app and check today's content suggestion in the banner
2. Choose one of three input methods:

**Manual (recommended):** Select a category, type a 1-2 sentence observation from your work, and click Generate. This produces the most authentic content.

**URL Reaction:** Paste a link to an article or post that sparked a thought. The tool reads the content and generates your professional reaction — not a summary.

**Autopilot:** Click "Generate an idea for me" when you have no specific observation. The tool searches current career/hiring news and generates posts based on what it finds.

3. Review the 3 draft variations
4. Click "Copy" on the best one
5. Paste into LinkedIn, make any final tweaks, and post

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

### Content Schedule

Edit the `CONTENT_SCHEDULE` dict in `config.py` to change the daily content type suggestions. Days are numbered 0 (Monday) through 4 (Friday).

### Voice Profile

The voice rules live in `prompts/base_system.md`. Edit this file to adjust tone, signature phrases, hard rules, and structural guidelines.

### Category Prompts

Each category has its own prompt file in `prompts/`:

- `category_pattern.md` — "I keep seeing..." framing
- `category_faq.md` — "A client asked me..." framing
- `category_noticed.md` — "I just noticed..." framing
- `category_hottake.md` — "Hot take" framing
- `autopilot.md` — Web search and synthesis instructions
- `url_react.md` — URL reaction instructions

### Number of Drafts

The base system prompt requests 3 drafts. To change this, edit the output format section in `prompts/base_system.md`.

### Model

The model is set in `config.py` as `ANTHROPIC_MODEL`. Default is `claude-sonnet-4-20250514`.

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

Another app is using port 5000. Either stop that app, or change `FLASK_PORT` in `config.py`.

### "Database is locked"

This can happen if two instances of the app are running. Stop all instances and restart with a single `python app.py`.

### Autopilot returns "Nothing compelling found"

This is intentional — the quality gate prevents weak content. Try again in a few hours when new news may be available, or switch to manual mode.

### URL reaction fails

Some URLs are behind paywalls or block automated access. Try pasting the article text directly into the observation field instead.

### Slow generation

API calls typically take 5-15 seconds. Autopilot and URL reaction are slower (10-20 seconds) because they include web search. This is normal.
