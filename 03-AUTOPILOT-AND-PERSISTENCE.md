# Stage 3 — Autopilot & Persistence

**Prerequisites:** Read `00-PROJECT-OVERVIEW.md` for full context. Stages 1 and 2 must be complete — the Flask backend, content generation engine, and frontend should all be working. Dana should be able to generate posts manually through the browser interface.

---

## Stage 3 Objective

Add the features that make the tool truly low-effort: autopilot content generation (so Dana can produce posts even without personal insights), a URL reaction feature (so passive reading becomes active content), an insight bank (so ideas are never lost), and a generation history (so Dana can see what she's been producing). This stage transforms the tool from "useful" to "indispensable."

## Deliverables

1. "Generate an idea for me" button and autopilot backend logic
2. "React to this URL" input field and reaction backend logic
3. Two new prompt files: `prompts/autopilot.md` and `prompts/url_react.md`
4. Insight bank section in the frontend (browse and reuse past insights)
5. Generation history section in the frontend (see past outputs)
6. Updated API routes for autopilot and URL reaction
7. Final polish: README with setup instructions, edge case handling, and overall UX refinement

## Part 1: Autopilot — "Generate an Idea for Me"

### What It Does

Dana clicks a single button. The system searches the web for current career, hiring, resume, or job market news, selects something relevant to Dana's niche, synthesizes an insight from it, and generates 3 post drafts — all in one action. Dana reviews the drafts and decides if any are worth posting.

This is for mornings when Dana has no specific observation from her work but still wants to maintain her posting cadence.

### Backend Implementation

**New route: `POST /api/generate/autopilot`**

No request body needed (or an empty JSON body). This endpoint:

1. Calls the Anthropic API with the autopilot prompt and **web search enabled**
2. Claude searches for current career/hiring/resume news, selects the most relevant item, and generates an insight + 3 post drafts
3. The insight is saved with `category='autopilot'` and the raw_input set to a summary of what Claude found
4. All 3 drafts are saved to the database
5. Returns the same response structure as `/api/generate`

Response (JSON):
```json
{
    "success": true,
    "insight_id": 15,
    "source_summary": "BLS reported executive job transitions hit a 3-year high in Q1 2026",
    "source_url": "https://...",
    "drafts": [
        {
            "id": 45,
            "draft_number": 1,
            "content": "Something is shifting in the executive job market...",
            "angle": "Trend analysis — opens with the data"
        },
        ...
    ]
}
```

**API call structure:**

The autopilot API call differs from the standard generation call because it uses the web search tool. Here's how to structure it:

```python
def generate_autopilot():
    base_prompt = load_prompt("prompts/base_system.md")
    autopilot_prompt = load_prompt("prompts/autopilot.md")
    
    system_prompt = f"{base_prompt}\n\n---\n\n## Autopilot Instructions\n\n{autopilot_prompt}"
    
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search"
            }
        ],
        messages=[
            {
                "role": "user",
                "content": "Find a current, relevant career/hiring/resume topic and generate LinkedIn posts about it. Search for recent news first, then write the posts."
            }
        ]
    )
    
    # Extract text content from the response
    # The response may contain multiple content blocks (tool_use, tool_result, text)
    # Concatenate all text blocks to get the full response
    full_text = ""
    for block in response.content:
        if block.type == "text":
            full_text += block.text
    
    drafts = parse_drafts(full_text)
    return drafts, extract_source_info(full_text)
```

**Important: Handling web search responses.** When the API uses web search, the response contains multiple content blocks — `tool_use` blocks (the search query), `tool_result` blocks (search results), and `text` blocks (Claude's written response). You need to extract only the text blocks and concatenate them. The draft parsing logic from Stage 1 should work on the concatenated text.

### Autopilot Prompt (`prompts/autopilot.md`)

This prompt must be precise about what makes a topic worth covering and how to synthesize it into Dana's voice.

The prompt should instruct Claude to:

**Search strategy:**
- Search for recent news (last 7 days) related to: executive hiring trends, resume and career advice, ATS and recruiting technology, LinkedIn platform changes, salary and compensation data, major layoffs or hiring surges, remote work and workplace policy shifts, or career transitions and pivots
- Prioritize data-driven stories (BLS reports, surveys, research) over opinion pieces
- Prioritize stories Dana's specific audience (VPs, directors, C-suite, board members) would care about
- Avoid stories that are too generic ("jobs are hard to find") or too niche ("a specific small company's hiring")

**Synthesis rules:**
- After finding a relevant topic, determine which of Dana's 4 insight categories fits best:
  - If it's a recurring trend → frame as "I keep seeing..."
  - If it addresses a common misconception → frame as "A client asked me..."
  - If it's breaking news or a new observation → frame as "I just noticed..."
  - If Dana would disagree with the prevailing narrative → frame as "Hot take"
- Generate the insight observation first (what Dana would have thought if she'd seen this news)
- Then generate 3 post drafts following all the voice and structural rules from the base system prompt and the appropriate category instructions

**Quality gate:**
- If Claude cannot find anything genuinely relevant and interesting in the search results, it should say so rather than forcing a weak topic. The response should indicate: "Nothing compelling found today — try again later or switch to manual mode."
- The bar for "compelling" is: would Dana read this news and immediately think "I need to post about this"?

**Output format:**
- Start with a brief summary of the source material: what was found, where it came from, why it's relevant
- Then the 3 drafts in the standard format (Draft 1 / Draft 2 / Draft 3 with angle descriptions)

### Frontend Changes for Autopilot

Add to the input section of the page, below the textarea:

- A visual separator: a line with "— or —" centered in it
- A button: "Generate an idea for me"
- Subtitle text beneath it: "Finds current career news and writes a post for you"

**Button behavior:**
- Clicking this button bypasses the category selector and textarea entirely
- Shows the same loading state as regular generation, but with different loading text: "Searching for content ideas..." (since it takes longer — web search adds 5–10 seconds)
- When results arrive, display them the same way as manual generation, but add a source summary above the drafts: "Based on: [summary of what was found] — [link to source]"
- The source summary helps Dana verify the content is accurate before posting

**UX note:** The autopilot button should feel like an easy escape hatch, not the primary workflow. Visual hierarchy should make it clear that typing your own insight is the preferred path, and autopilot is for "I've got nothing today" days. Place it below the main input area, slightly de-emphasized.

## Part 2: URL Reaction — "React to This"

### What It Does

Dana pastes a URL to an article, LinkedIn post, or report she found interesting. The system reads the content and generates a reaction post in Dana's voice — not a summary of the article, but Dana's professional take on it.

### Backend Implementation

**New route: `POST /api/generate/react`**

Request body:
```json
{
    "url": "https://example.com/article-about-hiring-trends"
}
```

This endpoint:

1. Validates the URL (basic format check)
2. Calls the Anthropic API with the URL reaction prompt and **web search enabled** (so Claude can fetch and read the URL content)
3. Claude reads the article, determines what Dana's angle would be, and generates 3 post drafts
4. The insight is saved with `category='url_react'`, `raw_input` set to a brief summary of the article, and `source_url` set to the provided URL
5. All 3 drafts are saved
6. Returns the standard response structure with the added `source_url` field

**API call structure:**

```python
def generate_from_url(url):
    base_prompt = load_prompt("prompts/base_system.md")
    url_react_prompt = load_prompt("prompts/url_react.md")
    
    system_prompt = f"{base_prompt}\n\n---\n\n## URL Reaction Instructions\n\n{url_react_prompt}"
    
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search"
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Read this article/post and generate LinkedIn reaction posts from Dana's perspective:\n\n{url}"
            }
        ]
    )
    
    # Same text extraction as autopilot
    full_text = ""
    for block in response.content:
        if block.type == "text":
            full_text += block.text
    
    drafts = parse_drafts(full_text)
    return drafts, extract_source_info(full_text)
```

### URL Reaction Prompt (`prompts/url_react.md`)

This prompt instructs Claude to react to external content as Dana would.

The prompt should cover:

**Reading the content:**
- Fetch and read the content at the provided URL
- Identify the core claim, finding, or argument of the piece
- Determine what aspect Dana would have the strongest professional reaction to

**Reaction types (Claude should pick the most appropriate):**
- **Agree and amplify:** The article confirms something Dana already tells her clients. She adds her perspective, a specific example, and deepens the point.
- **Respectfully disagree:** The article gives advice Dana thinks is wrong or incomplete. She pushes back with her own evidence and experience.
- **Add the missing piece:** The article is good but misses something important. Dana adds the dimension the author overlooked (usually the resume/ATS/executive angle).
- **Apply to her niche:** The article is about general business/career trends. Dana translates the implications specifically for executives, VPs, and board-level professionals.

**Critical rules:**
- This is NOT a summary of the article. Dana is not a book reviewer. She's a professional with an opinion who happened to read something that sparked a thought.
- The post should stand alone — someone who never reads the original article should still get full value from Dana's post.
- Dana may reference the article briefly ("I read something this morning that got me thinking...") but the post is about HER insight, not the article's content.
- Do not quote the article extensively. One short reference at most.
- If crediting the source, a simple "h/t [author]" at the end is sufficient. Don't make the post feel like a reshare.

**Output format:** Same as all other categories — 3 drafts with angle descriptions.

### Frontend Changes for URL Reaction

Add to the input section, between the textarea and the autopilot button:

- A visual separator: "— or —"
- A URL input field: `<input type="url" placeholder="Paste a URL to react to...">`
- No separate submit button — the main "Generate Posts" button handles both text input and URL input. The logic:
  - If a category is selected AND text is entered → standard insight generation
  - If a URL is entered (regardless of category/text) → URL reaction
  - If nothing is entered but autopilot button is clicked → autopilot
  - URL input takes priority over text input if both are filled (with a note explaining this)

**When displaying URL reaction results:** Show the source URL as a clickable link above the drafts so Dana can reference the original article.

## Part 3: Insight Bank

### What It Does

A section below the main generation area showing all past insights Dana has entered (or that autopilot generated). Each insight can be clicked to pre-fill the generation form and create new drafts from it.

### Backend

The API route from Stage 1 (`GET /api/insights`) already returns saved insights. It may need enhancements:

**`GET /api/insights?unused=true`** — Filter to show only insights that haven't been used (no draft was copied from them). These are the "banked" ideas waiting to be turned into posts.

**`GET /api/insights?limit=50&offset=0`** — Pagination for when the bank grows large.

Response format:
```json
{
    "insights": [
        {
            "id": 12,
            "category": "pattern",
            "raw_input": "Executives burying board experience as a bullet point",
            "source_url": null,
            "created_at": "2026-03-12T14:30:00",
            "used": false
        },
        ...
    ],
    "total": 47
}
```

### Frontend

Add a collapsible section below the results area:

**"Insight Bank" header** with a count badge showing unused insights: "Insight Bank (12 saved)"

**List of insights** displayed as compact cards or rows:
- Category shown as a small tag/pill (color-coded to match the category selector buttons)
- The raw input text, truncated to ~100 characters with "..." if longer
- Relative timestamp: "2 days ago", "Last week", etc.
- A "Use this →" button on each row

**"Use this" button behavior:**
- Clicking it scrolls up to the input area
- Pre-selects the matching category
- Pre-fills the textarea with the insight's raw_input text
- Dana can then click Generate to create new drafts from this insight
- This is a reuse flow — it creates a new set of generations linked to the original insight

**Visual treatment:**
- The insight bank should feel secondary to the main generation area — it's a reference, not the primary workflow
- Used insights (where at least one draft was copied) should be visually dimmed or have a "✓ Used" indicator
- Keep it simple: no search, no filters (those are Phase 2 enhancements). Just a scrollable list of past ideas.

## Part 4: Generation History

### What It Does

A section showing Dana's recent content generation activity — what she generated, when, and whether she used it. This is a lightweight activity log that helps her see her content output patterns.

### Backend

The `GET /api/history` route from Stage 1 should return recent generations with their parent insight data:

Response format:
```json
{
    "history": [
        {
            "insight_id": 12,
            "category": "pattern",
            "raw_input": "Executives burying board experience...",
            "generated_at": "2026-03-12T14:30:00",
            "drafts": [
                {"id": 34, "draft_number": 1, "copied": true, "content": "..."},
                {"id": 35, "draft_number": 2, "copied": false, "content": "..."},
                {"id": 36, "draft_number": 3, "copied": false, "content": "..."}
            ]
        },
        ...
    ]
}
```

### Frontend

Add a collapsible section below the Insight Bank:

**"History" header** with a count or date range: "History — Last 30 days"

**List of past generation sessions** displayed as expandable rows:
- Collapsed view shows: date, category tag, truncated insight text, and a usage indicator (✓ if any draft was copied, — if none were)
- Expanding a row reveals the 3 drafts from that session, each with its own "Copy" button (so Dana can revisit and use past drafts she initially skipped)

**Visual treatment:**
- Even more secondary than the insight bank — this is reference/analytics, not workflow
- Sessions where a draft was copied should show which specific draft was used
- Keep the list to the most recent 30 sessions by default; add a "Load more" button if needed

## Part 5: Final Polish & Hardening

### Error Handling Improvements

Review and strengthen error handling throughout:

- **API key missing:** On app startup, check for the API key. If missing, the main page should show a friendly setup message instead of the generation form. Include the exact steps: "Create a `.env` file in the project root with `ANTHROPIC_API_KEY=your-key-here`"
- **API rate limits:** If the Anthropic API returns a 429 (rate limited), display "You're generating too quickly — wait a moment and try again" rather than a generic error.
- **Network errors:** If the API is unreachable, display "Can't reach the Anthropic API. Check your internet connection."
- **Empty/bad responses:** If the API returns a response that can't be parsed into 3 drafts, display whatever was returned in a single card with a note: "Got an unexpected response format. Here's what was returned:"
- **URL reaction failures:** If the URL can't be fetched (404, paywall, etc.), display "Couldn't read that URL. It may be behind a paywall or unavailable. Try pasting the article text into the observation field instead."

### README.md

Create a comprehensive README with:

**Setup instructions:**
1. Prerequisites (Python 3.11+, pip)
2. Clone/download the project
3. Install dependencies: `pip install -r requirements.txt`
4. Create `.env` file with API key
5. Run: `python app.py`
6. Open `http://localhost:5000`

**Usage guide:**
- Brief walkthrough of the daily workflow
- Explanation of each input mode (manual, URL, autopilot)
- Tips for writing good insights (short and specific beats long and vague)

**Customization:**
- How to modify the content schedule (edit `config.py`)
- How to adjust Dana's voice (edit prompts in `prompts/`)
- How to change the number of drafts generated (note in engine.py)

**Troubleshooting:**
- Common issues (API key errors, port conflicts, database locked)

### UX Refinements

Go through the complete app and verify/improve:

- **Tab order:** Can Dana tab through category → textarea → generate without touching the mouse?
- **Auto-focus:** When the page loads, should the textarea be focused? (Probably yes, since the first action is typing.)
- **Scroll behavior:** After generating, does the page scroll to show the results? (It should, smoothly.)
- **Mobile/tablet:** Does the layout work on a tablet screen? (Category buttons should wrap, textarea should be full-width.)
- **Empty states:** What does the insight bank look like when it's empty? ("No saved insights yet. Generate your first post to start building your bank.")
- **Long content:** What happens if a generated draft is unusually long? (The card should expand naturally, not overflow or clip.)
- **Quick generation:** What if Dana wants to generate → copy → generate again quickly? (The form should remain filled after copying so she can immediately regenerate.)

### Performance

- The main bottleneck is the API call (5–15 seconds). Everything else should be near-instant.
- Page load should fetch today's suggestion, but NOT pre-load the insight bank and history — those can load lazily when Dana scrolls to them or clicks to expand them.
- Database queries are fast on SQLite for this data volume — no optimization needed.

## Stage 3 Completion Checklist

This is the final stage. After completion, the full MVP is ready for daily use.

- [ ] "Generate an idea for me" button works and produces relevant, on-brand content
- [ ] Autopilot searches the web for current news and synthesizes insights in Dana's voice
- [ ] Autopilot results display the source summary and link above the drafts
- [ ] When autopilot finds nothing compelling, it says so clearly rather than forcing weak content
- [ ] URL reaction input field accepts a URL and generates reaction posts
- [ ] URL reaction posts are opinionated reactions, NOT article summaries
- [ ] URL reaction handles failures gracefully (paywalls, 404s, unreadable content)
- [ ] Insight bank displays past insights with category tags and usage status
- [ ] "Use this" button in insight bank pre-fills the form and scrolls to the input area
- [ ] Generation history shows past sessions with expandable draft details
- [ ] Past drafts in history can be copied (with tracking)
- [ ] Error handling covers: missing API key, rate limits, network errors, parse failures, URL errors
- [ ] README has complete setup instructions, usage guide, and troubleshooting
- [ ] The complete daily workflow works end-to-end in under 5 minutes:
  - Open app → see today's suggestion → choose input method → generate → copy → post
- [ ] The app feels polished, responsive, and professional
- [ ] Dana can maintain a 3–4 post/week LinkedIn cadence using this tool with minimal effort
