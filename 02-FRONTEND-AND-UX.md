# Stage 2 — Frontend & UX

**Prerequisites:** Read `00-PROJECT-OVERVIEW.md` for full context. Stage 1 must be complete — the Flask backend, database, prompt system, and content generation engine should all be working and testable via curl/API calls.

---

## Stage 2 Objective

Build the single-page web interface that Dana interacts with daily. By the end of this stage, the full manual content generation workflow should work end-to-end in the browser: select a category, type an insight, generate drafts, copy the best one.

## Deliverables

1. A complete `templates/index.html` file with all UI components
2. Styling via `static/style.css` or inline styles
3. Working JavaScript for form submission, draft display, copy-to-clipboard, and regeneration
4. Today's content suggestion displayed at the top of the page
5. Loading states and error handling in the UI
6. The full manual workflow working end-to-end in the browser

## Design Principles

This is a tool Dana uses every morning for 3–5 minutes. The design should be:

- **Clean and calm.** No visual clutter. Generous whitespace. A tool that feels peaceful to open, not overwhelming.
- **Single-scroll.** Everything on one page, no navigation, no tabs (yet — Stage 3 adds the insight bank and history sections below the fold).
- **Instant feedback.** Loading states should be clear. The transition from "generating" to "here are your drafts" should feel smooth.
- **Keyboard-friendly.** Tab through the form, Enter to submit. Dana shouldn't need to reach for the mouse constantly.
- **Readable drafts.** The generated post text should be displayed in a way that mirrors how it'll look on LinkedIn — short paragraphs, clear line breaks, readable font size.

## UI Layout Specification

The page has a simple top-to-bottom flow:

```
┌─────────────────────────────────────────────┐
│  Signal & Stance                            │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│  Today's suggestion:                        │
│  "Wednesday — Deep Dive / Story"            │
│  Tell a story or go deeper on a topic       │
│  with a client example                      │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  What did you observe today?                │
│                                             │
│  ┌──────────┐ ┌──────────┐                  │
│  │ I keep   │ │ Client   │                  │
│  │ seeing   │ │ asked    │                  │
│  ├──────────┤ ├──────────┤                  │
│  │ Just     │ │ Hot      │                  │
│  │ noticed  │ │ take     │                  │
│  └──────────┘ └──────────┘                  │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ Your observation...                 │    │
│  │                                     │    │
│  │                                     │    │
│  └─────────────────────────────────────┘    │
│                                             │
│         [ Generate Posts ]                  │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  (Results appear here after generation)     │
│                                             │
│  ┌─ Draft 1 ───────────────────────────┐    │
│  │ Direct advice — leads with mistake  │    │
│  │                                     │    │
│  │ The resume isn't a history          │    │
│  │ lesson. It's a business case...     │    │
│  │                                     │    │
│  │                        [ Copy ]     │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─ Draft 2 ───────────────────────────┐    │
│  │ Story-driven — client scenario      │    │
│  │ ...                                 │    │
│  │                        [ Copy ]     │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─ Draft 3 ───────────────────────────┐    │
│  │ Data-driven — leads with metric     │    │
│  │ ...                                 │    │
│  │                        [ Copy ]     │    │
│  └─────────────────────────────────────┘    │
│                                             │
│         [ Regenerate ]                      │
│                                             │
└─────────────────────────────────────────────┘
```

## Detailed Component Specifications

### Header / Today's Suggestion

- App name "Signal & Stance" in a clean, professional font. Not large or showy — this is a tool, not a marketing page.
- Below it, today's content suggestion pulled from `GET /api/today` on page load.
- Display format: The day name and content type in a slightly emphasized style, with the suggestion text below in normal weight.
- On weekends, display a softer message like "It's the weekend — but if inspiration strikes, the engine is ready."

### Category Selector

- Four buttons in a 2×2 grid or a single row (whichever fits the viewport better).
- Each button shows the category label:
  - "I keep seeing..." 
  - "A client asked me..."
  - "I just noticed..."
  - "Hot take"
- Selecting a category visually highlights it (subtle background color change or border). Only one can be selected at a time.
- Below each label, a short helper text in smaller/muted type:
  - "I keep seeing..." → "A pattern or recurring mistake"
  - "A client asked me..." → "A question or common misconception"
  - "I just noticed..." → "A market trend or platform change"
  - "Hot take" → "A contrarian opinion or professional disagreement"

### Text Input Area

- A `<textarea>` with 3–4 rows visible, expandable.
- Placeholder text that changes based on selected category:
  - Pattern: "e.g., Third VP this month with no metrics on their resume despite managing $50M+ budgets"
  - FAQ: "e.g., Client asked if they should include a photo on their executive resume"
  - Noticed: "e.g., Seeing a spike in Chief AI Officer postings — none of them list resume requirements"
  - Hot take: "e.g., Cover letters are NOT dead for executive roles, despite what LinkedIn says"
- If no category is selected yet, use a generic placeholder: "Select a category above, then describe your observation..."
- The textarea should have a comfortable font size (16px minimum to avoid mobile zoom issues).

### Generate Button

- A single prominent button: "Generate Posts"
- Disabled state when: no category is selected, or the text input is empty.
- Loading state during API call: button text changes to "Generating..." with a subtle animation (CSS spinner or pulsing dots). The button is disabled during generation to prevent double-submission.
- Keyboard shortcut: Ctrl+Enter (or Cmd+Enter on Mac) should trigger generation when the textarea is focused. Display this shortcut as a hint near the button in muted text.

### Results Area

- Hidden by default. Appears with a smooth transition after generation completes.
- Shows 3 draft cards stacked vertically.

**Each draft card contains:**
- A header with the draft number and the angle description: "Draft 1 — Direct advice angle"
- The angle text should be in a muted/italic style to distinguish it from the post content.
- The full post content, displayed with preserved line breaks. This is critical — LinkedIn posts use single line breaks between short paragraphs, and the display should mirror this exactly so Dana can see how the post will look.
- A "Copy" button at the bottom-right of each card.

**Copy button behavior:**
- On click, copies the draft content to clipboard (just the post text, not the angle description or "Draft 1" label).
- Button text briefly changes to "Copied ✓" for 2 seconds, then reverts.
- Simultaneously sends a POST to `/api/copy` with the generation ID to track usage.
- Only the post content should be copied — no metadata, labels, or angle descriptions.

**Regenerate button:**
- Appears below the 3 draft cards.
- Clicking it re-submits the same category and input to generate 3 new drafts.
- The new drafts replace the old ones (the old ones are still saved in the database — they're just no longer displayed).
- This calls the same `/api/generate` endpoint, which creates a new insight entry and new generations. This is fine — the history will show multiple generation attempts, which is useful data.

### Loading State

During the API call (which takes 5–15 seconds depending on response length), the UI should:

1. Disable the Generate button and show "Generating..."
2. Show a loading indicator in the results area. Avoid a generic spinner — something like a pulsing text that says "Writing your drafts..." feels more appropriate for this tool.
3. Keep the form visible but dimmed slightly so Dana knows her input was received.
4. Scroll the page down to the results area so the loading indicator is visible.

### Error States

If the API call fails, display an error message in the results area:
- "Something went wrong generating your posts. Check your API key and try again."
- Include a "Try Again" button that re-submits.
- Don't lose the user's input — the category selection and text should remain intact.

If the API key is missing or invalid, display a setup message:
- "Set your Anthropic API key in the .env file to get started."

## JavaScript Implementation Notes

All JavaScript should be in a `<script>` tag at the bottom of `index.html` or in a separate file. No framework — vanilla JS only.

**Key functions to implement:**

```javascript
// Page load: fetch today's suggestion
async function loadTodaySuggestion() { ... }

// Category selection: highlight button, update placeholder
function selectCategory(category) { ... }

// Form submission: validate, call API, display results
async function generatePosts() { ... }

// Copy to clipboard: copy content, flash button, track usage
async function copyDraft(generationId, content) { ... }

// Regenerate: re-submit with same inputs
async function regenerate() { ... }
```

**Fetch calls should:**
- Use `fetch()` with `Content-Type: application/json`
- Handle network errors gracefully
- Parse JSON responses and check `success` field

**Copy to clipboard:**
- Use `navigator.clipboard.writeText()` (works in all modern browsers on localhost)
- Fallback for older browsers: create a temporary textarea, select, execCommand('copy')

## Styling Guidance

The aesthetic should be professional, minimal, and calming. Reference points: Notion's simplicity, Linear's clean forms, iA Writer's focused interface.

**Color palette suggestion (keep it simple):**
- Background: white or very light warm gray (#FAFAF8 or similar)
- Text: near-black (#1a1a1a)
- Muted text: medium gray (#6b6b6b)
- Accent: a single muted professional color for buttons and selected states — something like a deep teal (#1a7f6d), slate blue (#4a5e78), or warm charcoal (#3d3d3a). Pick one and use it consistently.
- Draft cards: white background with a very subtle border (1px solid #e5e5e3)
- Copied state: a brief green flash (#2d8a6e)

**Typography:**
- System font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Or a clean sans-serif like Inter (loadable from Google Fonts if desired, but system fonts are simpler and faster)
- Body: 16px, line-height 1.6
- Draft content: 15–16px, line-height 1.7 (slightly more generous for readability)
- Muted/helper text: 13–14px

**Spacing:**
- Generous padding throughout. The page should not feel cramped.
- Max-width on the main content: 680–720px, centered. This mirrors LinkedIn's post width and helps Dana see how the content will actually appear.
- 24–32px vertical spacing between major sections.

**Responsive considerations:**
- This is primarily a desktop tool (Dana uses it at her desk), but it should look reasonable on a tablet in case she uses it on an iPad.
- The 2×2 category grid should remain usable down to ~375px width.

## Flask Template Integration

The `index.html` file should be a Jinja2 template served by Flask, but in practice it won't need much templating — almost everything is handled by JavaScript fetching from the API routes.

The main page route in `app.py`:

```python
@app.route("/")
def index():
    return render_template("index.html")
```

The template itself is a static HTML file with JavaScript that calls the API endpoints.

**Serve static files:** Make sure Flask is configured to serve the `static/` directory for CSS (if using a separate file):

```html
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
```

Or keep all styles in a `<style>` tag inside `index.html` for simplicity. For an MVP with one page, inline styles are perfectly fine and reduce the number of files to manage.

## Stage 2 Completion Checklist

Before moving to Stage 3, verify:

- [ ] Opening `http://localhost:5000` in a browser shows the complete UI
- [ ] Today's content suggestion displays correctly (and handles weekends)
- [ ] All 4 category buttons work and visually indicate selection
- [ ] Placeholder text in the textarea changes based on selected category
- [ ] Generate button is disabled until both category and text are provided
- [ ] Clicking Generate calls the API and displays 3 draft cards
- [ ] Loading state shows during generation (button disabled, loading indicator visible)
- [ ] Each draft card shows the angle description and full post content
- [ ] Line breaks in the post content are preserved and displayed correctly
- [ ] Copy button copies the post text to clipboard and shows "Copied ✓" feedback
- [ ] Copy action is tracked in the database (via `/api/copy`)
- [ ] Regenerate button generates new drafts with the same inputs
- [ ] Error states display clearly when API calls fail
- [ ] The page looks clean, professional, and is comfortable to use
- [ ] Ctrl/Cmd+Enter shortcut works for generating
- [ ] The full workflow takes under 60 seconds: open page → select category → type insight → generate → copy → done
