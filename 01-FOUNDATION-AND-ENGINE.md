# Stage 1 — Foundation & Engine

**Prerequisites:** Read `00-PROJECT-OVERVIEW.md` first. It contains the full project context, voice profile, file structure, and database schema that this stage implements.

---

## Stage 1 Objective

Build the project foundation and core content generation engine. By the end of this stage, the app should be able to generate LinkedIn post drafts from a typed insight via API calls (testable with `curl` or a simple test script). No frontend yet — that's Stage 2.

## Deliverables

1. Project directory with all files in place
2. Flask app running on `localhost:5000`
3. SQLite database initialized with schema
4. Prompt system with base voice profile + 4 category templates
5. Content generation engine that accepts an insight and returns 3 post drafts
6. API routes for generating content and retrieving data
7. A test script or curl commands that demonstrate the engine working

## Step-by-Step Build Instructions

### Step 1: Project Setup

Create the project directory structure exactly as specified in the overview:

```
signal-and-stance/
├── app.py
├── config.py
├── database.py
├── engine.py
├── prompts/
│   ├── base_system.md
│   ├── category_pattern.md
│   ├── category_faq.md
│   ├── category_noticed.md
│   ├── category_hottake.md
│   ├── autopilot.md        # (placeholder — built in Stage 3)
│   └── url_react.md        # (placeholder — built in Stage 3)
├── static/
│   └── style.css
├── templates/
│   └── index.html          # (placeholder — built in Stage 2)
├── requirements.txt
├── schema.sql
└── README.md
```

**requirements.txt:**
```
flask>=3.0
anthropic>=0.40.0
python-dotenv>=1.0.0
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

### Step 2: Configuration (`config.py`)

```python
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
FLASK_PORT = 5000
DATABASE_PATH = "signal_stance.db"

# Weekly content schedule (0=Monday, 4=Friday)
CONTENT_SCHEDULE = {
    0: {
        "type": "Educational / Pattern",
        "suggestion": "Share a pattern or recurring mistake you see in your work"
    },
    1: {
        "type": "Tactical Tip",
        "suggestion": "Share a specific, actionable tip about resumes, LinkedIn, or job search"
    },
    2: {
        "type": "Deep Dive / Story",
        "suggestion": "Tell a story or go deeper on a topic with a client example"
    },
    3: {
        "type": "Thought Leadership / Hot Take",
        "suggestion": "Share a contrarian opinion or professional stance"
    },
    4: {
        "type": "Quick Win / Encouragement",
        "suggestion": "Share a quick tip or insight that builds confidence"
    },
}
```

Create a `.env` file (gitignored) in the project root:
```
ANTHROPIC_API_KEY=your-key-here
```

### Step 3: Database Layer (`database.py`)

Implement the SQLite database with the schema from the overview document. This module should provide:

**Initialization:**
- `init_db()` — Creates tables if they don't exist. Call this on app startup.

**Insight operations:**
- `save_insight(category, raw_input, source_url=None)` — Saves a new insight, returns its ID.
- `get_insights(limit=50)` — Returns recent insights in reverse chronological order.
- `mark_insight_used(insight_id)` — Sets `used=1` on an insight.

**Generation operations:**
- `save_generation(insight_id, draft_number, content)` — Saves a generated draft.
- `get_generations_for_insight(insight_id)` — Returns all drafts for an insight.
- `mark_generation_copied(generation_id)` — Sets `copied=1` and also marks the parent insight as used.
- `get_generation_history(limit=50)` — Returns recent generations with their parent insight data, ordered by most recent first.

**Implementation notes:**
- Use Python's built-in `sqlite3` module. No ORM needed.
- All functions should open and close their own database connections (or use a context manager). SQLite handles this fine for a single-user app.
- Return dictionaries (using `sqlite3.Row`) rather than tuples for readability.
- Handle the `created_at` timestamps in SQLite — use `datetime('now')` or let the DEFAULT handle it.

**schema.sql** (also execute this in `init_db()`):

```sql
CREATE TABLE IF NOT EXISTS insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    raw_input TEXT NOT NULL,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id INTEGER NOT NULL,
    draft_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    copied INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insight_id) REFERENCES insights(id)
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### Step 4: Prompt System (`prompts/` directory)

This is the most important part of the entire project. The quality of these prompts directly determines whether the tool produces content Dana uses or content she ignores. Spend time getting these right.

#### `prompts/base_system.md`

This is the base system prompt included in every API call. It establishes Dana's voice and the structural rules for LinkedIn posts. Write this as a complete system prompt — not a template with blanks, but a fully realized instruction set.

The base system prompt must cover:

**Identity and context:**
- You are writing LinkedIn posts for Dana Wang, a Certified Professional Resume Writer (CPRW) who runs Raleigh Resume
- Dana partners with high-level professionals (VPs, C-suite, Board members) to transform career documents into strategic assets
- Her clients have secured roles at Fortune 30 companies, high-growth startups, and Board seats
- She holds a CPRW from PARWCC and an MA from UNC Chapel Hill

**Voice rules:**
- Write in first person as Dana
- Tone is direct, strategic, and metrics-oriented
- Empathetic but authoritative — she understands the frustration but leads with expertise
- Use analogies: resumes are "marketing assets" or "business cases," not just documents
- Reference specific numbers and metrics where possible (even illustrative ones)
- Use confident framing: "Here's what's actually happening" rather than "I think maybe..."
- No generic motivational language, no "In today's competitive market...", no filler
- No exclamation points in excess (1 max per post, and only if genuinely emphatic)
- No emoji unless strategically placed (rare)
- No hashtags in the post body (if used at all, a small cluster at the very end is acceptable)

**LinkedIn post structure rules:**
- The first line is the hook. It must stop the scroll. It should be surprising, specific, or counterintuitive. Never generic.
- Use short paragraphs: 1–3 sentences max per paragraph
- Insert a blank line between every paragraph (LinkedIn collapses text without line breaks)
- Total length: 150–300 words (this is the sweet spot for LinkedIn engagement)
- End with a clear CTA or thought-provoking question that invites comments — but make it genuine, not formulaic
- The post should feel like a conversation with a smart peer, not a broadcast from a brand
- Never start with "I'm excited to share..." or "I've been thinking about..." or "Happy [day of week]!"

**Post quality checklist (include this in the prompt so Claude self-evaluates):**
- Does the hook make you want to read the next line?
- Is there a specific, concrete insight (not vague advice)?
- Would a VP of Marketing or a Director of Engineering find this relevant?
- Does it sound like Dana wrote it at her desk after a client call, not like a content mill produced it?
- Is there a reason someone would comment on this post?

**Output format instructions:**
- Generate exactly 3 distinct draft variations
- Each draft should take a different angle or framing on the same core insight
- Label them "Draft 1:", "Draft 2:", "Draft 3:" with a blank line between each
- After each draft, include a short italicized note in brackets explaining the angle: e.g., [Direct advice angle — leads with the mistake] or [Story-driven — opens with a client scenario]
- Do not include any preamble or commentary before Draft 1

#### `prompts/category_pattern.md`

This is appended to the base system prompt when the user selects "I keep seeing..."

The category-specific prompt should instruct Claude on the structure and approach for this type of post:

**Pattern/mistake posts follow this arc:**
1. Hook: State the pattern bluntly ("I've reviewed X resumes this month. Y of them made the same mistake.")
2. What the pattern is: Describe the specific mistake or trend with enough detail that the reader can self-diagnose
3. Why it matters: Connect the mistake to a real consequence (ATS rejection, recruiter pass, missed interviews)
4. The fix: Give a concrete, actionable correction — not vague advice, but something the reader can do today
5. Reframe: End with a broader insight about how this pattern reflects a misunderstanding about resumes/careers
6. CTA: A question like "Have you checked your resume for this?" or "What patterns are you seeing?"

**Tone for this category:** Observational, almost clinical. Dana is reporting what she sees in the field. Not judgmental toward the people making the mistake — empathetic to why they make it, firm about why it needs to change.

#### `prompts/category_faq.md`

This is appended when the user selects "A client asked me..."

**FAQ/myth-busting posts follow this arc:**
1. Hook: State the question directly, or the assumption behind it ("A VP asked me last week: 'Is a two-page resume really okay?' Here's what I told them.")
2. The common answer vs. the real answer: Acknowledge what most people believe, then correct it with specificity
3. Why the misconception exists: Show empathy — the wrong answer makes intuitive sense, which is why everyone believes it
4. The expert answer with evidence: Dana's actual recommendation backed by how ATS systems work, how recruiters scan, or what hiring data shows
5. The nuance: Any caveats or "it depends" factors that make the answer more sophisticated
6. CTA: "What's a resume question you've been afraid to ask?" or similar

**Tone for this category:** Teacher mode. Patient, clear, authoritative. Dana is the expert answering a question she's answered a hundred times — but she makes it fresh because she genuinely cares about getting the answer right.

#### `prompts/category_noticed.md`

This is appended when the user selects "I just noticed..."

**Observation/market posts follow this arc:**
1. Hook: State the observation as a discovery ("Something shifted in the job market this month that nobody is talking about.")
2. The observation: What Dana noticed, with specific context (which industry, what platform, what data)
3. What it means: Dana's expert interpretation — why this matters for job seekers and career professionals
4. The implication: What the reader should do differently because of this observation
5. Prediction or question: Where Dana thinks this trend is heading, or an open question for discussion
6. CTA: "Are you seeing this too?" or "What's changed in your industry?"

**Tone for this category:** Sharp, timely, insider. Dana is sharing intelligence from the front lines. She's the person who notices things before everyone else because she's in the trenches daily.

#### `prompts/category_hottake.md`

This is appended when the user selects "Hot take"

**Hot take / contrarian posts follow this arc:**
1. Hook: State the contrarian position boldly ("Unpopular opinion: 'Follow your passion' is the worst career advice for anyone over 35.")
2. The conventional wisdom: Acknowledge what most people/experts say and why it sounds reasonable
3. The dissent: Why Dana disagrees, with specific reasoning grounded in her experience
4. The evidence: Real examples, client outcomes, or market data that support her contrarian position
5. The nuance: Where the conventional wisdom does have merit (this prevents the post from feeling like clickbait)
6. CTA: Explicitly invite disagreement — "Change my mind" or "Am I wrong about this?" — hot takes that invite debate get the most engagement

**Tone for this category:** Bold, confident, but intellectually honest. Dana isn't being contrarian for attention — she's sharing a genuinely held professional opinion that happens to go against the grain. She's willing to be wrong and says so.

#### `prompts/autopilot.md` and `prompts/url_react.md`

Create these files as placeholders with a comment noting they'll be built in Stage 3:

```markdown
# Autopilot Prompt — To Be Built in Stage 3
# This prompt will instruct Claude to use web search to find current career/hiring news
# and generate an insight + post drafts based on what it finds.
```

```markdown
# URL Reaction Prompt — To Be Built in Stage 3
# This prompt will instruct Claude to read content at a given URL
# and generate a reaction post in Dana's voice.
```

### Step 5: Content Generation Engine (`engine.py`)

This module handles prompt assembly and Anthropic API calls. It should provide:

**`generate_posts(category, raw_input, source_url=None)`**

This is the core function. It:

1. Loads the base system prompt from `prompts/base_system.md`
2. Loads the category-specific prompt from the appropriate file
3. Assembles the full system prompt by concatenating: base + category template
4. Constructs the user message incorporating the raw insight input
5. Calls the Anthropic API with the assembled prompts
6. Parses the response to extract the 3 individual drafts
7. Returns a list of 3 draft strings

**Implementation details:**

```python
import anthropic
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MAX_TOKENS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

CATEGORY_FILE_MAP = {
    "pattern": "prompts/category_pattern.md",
    "faq": "prompts/category_faq.md",
    "noticed": "prompts/category_noticed.md",
    "hottake": "prompts/category_hottake.md",
}

def load_prompt(filepath):
    with open(filepath, "r") as f:
        return f.read()

def generate_posts(category, raw_input, source_url=None):
    base_prompt = load_prompt("prompts/base_system.md")
    category_prompt = load_prompt(CATEGORY_FILE_MAP[category])
    
    system_prompt = f"{base_prompt}\n\n---\n\n## Category-Specific Instructions\n\n{category_prompt}"
    
    user_message = f"Here is the insight/observation to turn into LinkedIn posts:\n\n\"{raw_input}\""
    if source_url:
        user_message += f"\n\nSource URL for reference: {source_url}"
    
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    full_response = response.content[0].text
    drafts = parse_drafts(full_response)
    return drafts

def parse_drafts(response_text):
    """Parse the API response into 3 separate draft strings."""
    # Split on "Draft 1:", "Draft 2:", "Draft 3:" markers
    # Handle variations in formatting (with/without newlines, etc.)
    # Return a list of 3 strings, each containing the full draft text
    # If parsing fails, return the full response as a single draft
    # (graceful degradation)
    ...
```

**Important: Draft parsing logic**

The `parse_drafts` function needs to reliably split Claude's response into 3 separate drafts. The response will look something like:

```
Draft 1:

The resume isn't a history lesson...

[Direct advice angle — leads with the mistake]

Draft 2:

I reviewed 12 executive resumes this week...

[Story-driven — opens with a real scenario]

Draft 3:

Your resume has 6 seconds...

[Data-driven — leads with the metric]
```

Use a regex or string split approach to separate these. Handle edge cases where the format varies slightly. If parsing fails entirely, return the full response as a single draft rather than crashing.

Separate the bracketed angle description from the draft body — store/display them separately so the frontend can show the angle note in a distinct style.

### Step 6: Flask Application (`app.py`)

Implement the Flask app with these routes:

**`GET /`** — Serves the main page (placeholder for now — return a simple "Signal & Stance is running" message or the template if it exists).

**`POST /api/generate`** — The core generation endpoint.

Request body (JSON):
```json
{
    "category": "pattern",
    "raw_input": "Third VP this month with no metrics on their resume"
}
```

Response (JSON):
```json
{
    "success": true,
    "insight_id": 1,
    "drafts": [
        {
            "id": 1,
            "draft_number": 1,
            "content": "The resume isn't a history lesson...",
            "angle": "Direct advice angle — leads with the mistake"
        },
        {
            "id": 2,
            "draft_number": 2,
            "content": "I reviewed 12 executive resumes...",
            "angle": "Story-driven — opens with a real scenario"
        },
        {
            "id": 3,
            "draft_number": 3,
            "content": "Your resume has 6 seconds...",
            "angle": "Data-driven — leads with the metric"
        }
    ]
}
```

Processing logic:
1. Validate the request (category must be one of the 4 valid categories, raw_input must be non-empty)
2. Call `engine.generate_posts(category, raw_input)`
3. Save the insight to the database via `database.save_insight()`
4. Save all 3 drafts to the database via `database.save_generation()`
5. Return the structured response

**`POST /api/copy`** — Marks a draft as copied.

Request body:
```json
{
    "generation_id": 3
}
```

This calls `database.mark_generation_copied()` which also marks the parent insight as used.

**`GET /api/today`** — Returns today's content suggestion.

Response:
```json
{
    "day": "Wednesday",
    "type": "Deep Dive / Story",
    "suggestion": "Tell a story or go deeper on a topic with a client example"
}
```

Uses Python's `datetime.today().weekday()` to look up the schedule from `config.py`. Returns a "no suggestion" message on weekends.

**`GET /api/insights`** — Returns saved insights for the insight bank (Stage 3 will build the UI for this).

**`GET /api/history`** — Returns generation history (Stage 3 will build the UI for this).

**Error handling:** All routes should catch exceptions and return structured error responses:
```json
{
    "success": false,
    "error": "Description of what went wrong"
}
```

**App initialization:**
```python
from flask import Flask
from database import init_db

app = Flask(__name__)

# Initialize database on startup
init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

### Step 7: Testing

Create a test script (`test_engine.py`) or document curl commands that verify:

1. **Database initialization:** Run the app, check that `signal_stance.db` is created with the correct tables.

2. **Content generation:** Make a POST request to `/api/generate` with a test insight:
```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"category": "pattern", "raw_input": "Third VP this month with no quantified achievements on their resume despite managing $50M+ budgets"}'
```

3. **Verify 3 drafts are returned** and each sounds like Dana's voice.

4. **Test all 4 categories** with realistic inputs:
   - Pattern: "Executives keep listing responsibilities instead of achievements"
   - FAQ: "Client asked if they should include a photo on their resume"
   - Noticed: "Seeing a spike in Chief AI Officer job postings this quarter"
   - Hot take: "Cover letters are not dead for executive roles despite what LinkedIn influencers say"

5. **Test the copy endpoint:** Mark a draft as copied and verify the database is updated.

6. **Test today's schedule:** Hit `/api/today` and verify it returns the correct day's suggestion.

**Voice quality check:** After generating test posts, read them critically against Dana's voice profile in the overview document. The most common problems to watch for:

- Too generic (sounds like any career advice, not Dana specifically)
- Too formal (sounds like a corporate memo, not a LinkedIn post)
- Missing her signature analogies (resume as marketing asset, etc.)
- Weak hooks (starting with setup instead of a punchy opening line)
- Too long (over 300 words) or too structured (numbered lists, headers)
- Generic CTAs ("What do you think?" instead of something specific to the post's topic)

If the output has these problems, revise the prompts before moving to Stage 2. The prompts are the foundation — everything else is built on top of their quality.

## Stage 1 Completion Checklist

Before moving to Stage 2, verify:

- [ ] `python app.py` starts the Flask server without errors
- [ ] SQLite database is created automatically on first run
- [ ] POST to `/api/generate` with each of the 4 categories returns 3 drafts
- [ ] Drafts are saved to the database
- [ ] POST to `/api/copy` marks drafts as copied
- [ ] GET to `/api/today` returns the correct day's content suggestion
- [ ] GET to `/api/insights` returns saved insights
- [ ] GET to `/api/history` returns generation history
- [ ] Generated content sounds authentically like Dana (the most important check)
- [ ] Error handling works (invalid category, empty input, API errors return structured error responses)
