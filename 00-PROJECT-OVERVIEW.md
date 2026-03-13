# Signal & Stance — Project Overview

**Read this document first. Every build stage references it.**

---

## What This Is

Signal & Stance is a locally hosted web application that helps Dana Wang, a Certified Professional Resume Writer (CPRW) running Raleigh Resume, generate LinkedIn content consistently and efficiently. Dana's business is thriving on Upwork but she has zero LinkedIn marketing presence. This tool fixes that.

The app takes a short observation from Dana's daily work — a pattern she noticed, a question a client asked, a market trend, a professional opinion — and generates multiple LinkedIn post drafts in her authentic voice. The goal: go from posting nothing to posting 3–4 times per week, with each post taking under 5 minutes to produce.

## Why "Signal & Stance"

The name reflects the two things Dana provides in every piece of content: a **signal** (an insight, data point, or observation from her expertise) and a **stance** (her authoritative, strategic perspective on it). The tool's job is to capture the signal and articulate the stance.

## Who Dana Is (Voice Profile)

This is critical context. Every piece of generated content must sound like Dana wrote it. Her voice has these specific characteristics:

**Tone:** Direct and strategic. She speaks in terms of ROI, metrics, and business cases. No fluff, no filler, no generic motivation.

**Stance:** Empathetic but authoritative. She understands job search frustration but leads with expert solutions, not commiseration. She's the expert in the room — not arrogant, but confident.

**Signature techniques:**
- Refers to resumes as "marketing assets" or "business cases," never just "documents"
- Uses specific metrics and numbers to anchor claims ("6-second scan," "20% interview rate," "$55k salary increase")
- Frames career problems as solvable strategy problems, not personal failings
- Uses phrases like "You are likely the best candidate" and "Let's turn your next application into an interview"
- Draws analogies between resume writing and business/marketing strategy

**She avoids:**
- Generic motivational language ("You've got this!", "Believe in yourself!", "Keep pushing!")
- Overly casual or meme-driven content
- Self-deprecating humor about resume writing
- Treating resume writing as a commodity ("I'll fix your resume for cheap")
- Excessive exclamation points or emoji

**Her credentials (use naturally, don't force into every post):**
- Certified Professional Resume Writer (CPRW) via PARWCC
- MA from UNC Chapel Hill
- Clients have secured roles at Fortune 30 companies, Board seats, and C-suite positions
- Specializes in executive/board-level resumes, LinkedIn optimization, ATS compliance, federal resumes

## Core User Workflow

Dana's daily interaction with the app follows this exact pattern:

1. Open the app in her browser (it's running locally at `http://localhost:5000`)
2. See today's suggested content type (e.g., "Wednesday — Tactical tip or observation")
3. Choose one of three input paths:
   - **Type an insight:** Select a category (I keep seeing / Client asked / Just noticed / Hot take), type a 1–2 sentence observation, hit Generate
   - **Paste a URL:** Paste a link to an article or post she found interesting, hit Generate
   - **Click "Generate an idea for me":** The system finds current career/hiring news and generates content automatically
4. Review 3 draft posts displayed on the page
5. Click "Copy" on the best one (or "Regenerate" if none fit)
6. Paste into LinkedIn, make any final tweaks, and post
7. Done. Total time: 2–5 minutes.

## Technical Constraints

- **Python + Flask** backend. No Django, no FastAPI. Flask is the simplest option and sufficient for a single-user local app.
- **Single HTML file** frontend with vanilla CSS and JS. No React, no Vue, no build tools, no npm. The entire frontend is one file served by Flask.
- **SQLite** database. No PostgreSQL, no MongoDB. SQLite is zero-config and perfect for single-user local apps.
- **Anthropic API** for all content generation. Model: `claude-sonnet-4-20250514`. All API calls use the standard `/v1/messages` endpoint.
- The app runs locally via `python app.py`. No Docker, no cloud deployment, no CI/CD.
- The only environment variable is `ANTHROPIC_API_KEY`.

## Project File Structure

When complete, the project should look like this:

```
signal-and-stance/
├── app.py                  # Flask application (all routes)
├── config.py               # Configuration (API key, content schedule, app settings)
├── database.py             # SQLite setup, schema, and data access functions
├── engine.py               # Content generation engine (prompt assembly, API calls)
├── prompts/
│   ├── base_system.md      # Base system prompt with voice profile
│   ├── category_pattern.md # "I keep seeing..." post template
│   ├── category_faq.md     # "A client asked me..." post template
│   ├── category_noticed.md # "I just noticed..." post template
│   ├── category_hottake.md # "Hot take" post template
│   ├── autopilot.md        # "Generate an idea for me" prompt
│   └── url_react.md        # "React to this URL" prompt
├── static/
│   └── style.css           # Stylesheet (optional — can be inline in template)
├── templates/
│   └── index.html          # Single-page frontend
├── requirements.txt        # Python dependencies
├── schema.sql              # Database schema
└── README.md               # Setup and usage instructions
```

## Database Schema

Three tables. Keep it simple.

```sql
CREATE TABLE IF NOT EXISTS insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,          -- 'pattern', 'faq', 'noticed', 'hottake', 'autopilot', 'url_react'
    raw_input TEXT NOT NULL,         -- The observation Dana typed, or the URL, or 'auto-generated'
    source_url TEXT,                 -- URL if applicable
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used INTEGER DEFAULT 0           -- 1 if a generation from this insight was copied
);

CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id INTEGER NOT NULL,
    draft_number INTEGER NOT NULL,   -- 1, 2, or 3
    content TEXT NOT NULL,           -- The full post draft
    copied INTEGER DEFAULT 0,        -- 1 if this draft was copied to clipboard
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insight_id) REFERENCES insights(id)
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

## Content Schedule

A simple rotating weekly template. No database-backed calendar — just a Python dict:

```python
CONTENT_SCHEDULE = {
    0: {"type": "Educational / Pattern", "prompt": "Share a pattern or recurring mistake you see in your work"},
    1: {"type": "Tactical Tip", "prompt": "Share a specific, actionable tip about resumes, LinkedIn, or job search"},
    2: {"type": "Deep Dive / Story", "prompt": "Tell a story or go deeper on a topic with a client example"},
    3: {"type": "Thought Leadership / Hot Take", "prompt": "Share a contrarian opinion or professional stance"},
    4: {"type": "Quick Win / Encouragement", "prompt": "Share a quick tip or insight that builds confidence"},
}
# 0=Monday, 4=Friday. Weekends are off.
```

## Build Stages

This project is built in 3 stages. Each stage has its own detailed build guide:

1. **Stage 1 — Foundation & Engine** (`01-FOUNDATION-AND-ENGINE.md`): Project setup, Flask app skeleton, SQLite database, prompt system, content generation engine. Deliverable: a working backend that can generate posts via API calls (testable with `curl`).

2. **Stage 2 — Frontend & UX** (`02-FRONTEND-AND-UX.md`): The single-page web interface with all form inputs, results display, copy-to-clipboard, and visual polish. Deliverable: a complete, usable web app for manual content generation.

3. **Stage 3 — Autopilot & Persistence** (`03-AUTOPILOT-AND-PERSISTENCE.md`): "Generate an idea for me" feature, URL reaction feature, insight bank, generation history, and final polish. Deliverable: the complete MVP ready for daily use.

**Each stage produces a working, testable increment.** After Stage 1, you can generate posts via the terminal. After Stage 2, you can generate posts via a browser. After Stage 3, you have the full product.

## Quality Bar

The single most important quality criterion: **generated posts must sound like Dana wrote them.** If a LinkedIn connection of Dana's read a generated post, they should not be able to tell it was AI-assisted. This means:

- Every post uses Dana's specific vocabulary, analogies, and framing
- Posts reference real-world resume/career dynamics with specificity (not vague advice)
- Posts have a clear structure: hook → insight → evidence/example → takeaway → CTA
- Posts are 150–300 words (LinkedIn's sweet spot)
- Posts use short paragraphs (1–3 sentences) with line breaks between them for LinkedIn readability
- Posts never start with "In today's competitive job market..." or similar generic AI openings

If the output doesn't pass this bar, spend more time on prompt engineering before adding features.
