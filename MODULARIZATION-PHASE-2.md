# Phase 2: Prompt Templating & Engine Decoupling

**Goal:** Convert the 11 prompt `.md` files to use `{{variable}}` placeholders filled from `business_config.json`, and move all remaining business-specific strings out of `engine.py` into prompt files or config.

**Prerequisite:** Phase 1 complete (`business_config.json` and `business_config.py` exist and are wired up)
**Estimated effort:** 6-8 hours
**Impact:** Converts prompt files from "must rewrite from scratch" to "review and adjust domain-specific sections." Reduces cross-domain swap effort from ~35 hours to ~15-20 hours.

---

## Context

After Phase 1, identity/brand/schedule values live in `business_config.json`. But the 11 prompt files in `prompts/` still contain 600+ lines of deeply authored content with Dana-specific references baked into the prose. This phase:

1. Adds a template engine to `engine.py`'s `load_prompt()` function
2. Converts templatizable sections of each prompt to use `{{owner.name}}`, `{{platform.name}}`, etc.
3. Clearly marks sections that are domain-specific "authored content" vs. templatizable infrastructure
4. Moves the remaining hardcoded user messages from `engine.py` into the prompt files themselves

**Important caveat:** Only ~40-50% of prompt content is templatizable. Voice rules, signature language, content arcs, examples, and scoring rubrics are creative work that must be manually authored per business domain. This phase makes the templatizable parts configurable and clearly separates them from the parts that need manual authoring.

---

## Step 1: Add template rendering to `engine.py`'s `load_prompt()`

**Edit file:** `signal-and-stance/engine.py`

The current `load_prompt()` function (lines 20-23) simply reads a file:

```python
def load_prompt(filepath):
    prompt_path = os.path.join(os.path.dirname(__file__), filepath)
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
```

Replace it with a version that performs `{{variable}}` substitution using business config:

```python
import re as _re
from business_config import BUSINESS

_TEMPLATE_CACHE = {}

def _flatten_config(d, prefix=""):
    """Flatten nested dict to dot-notation keys: {'owner.name': 'Dana Wang', ...}"""
    flat = {}
    for k, v in d.items():
        key = f"{prefix}{k}" if prefix else k
        if isinstance(v, dict):
            flat.update(_flatten_config(v, f"{key}."))
        elif isinstance(v, list):
            flat[key] = ", ".join(str(i) for i in v)
        else:
            flat[key] = str(v)
    return flat

_FLAT_CONFIG = _flatten_config(BUSINESS)


def load_prompt(filepath):
    """Load a prompt .md file and substitute {{key}} placeholders from business config."""
    prompt_path = os.path.join(os.path.dirname(__file__), filepath)
    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Replace {{key.subkey}} with values from flattened business config
    def _replacer(match):
        key = match.group(1).strip()
        return _FLAT_CONFIG.get(key, match.group(0))  # Leave unreplaced if key not found

    return _re.sub(r"\{\{(.+?)\}\}", _replacer, template)
```

This handles:
- `{{owner.name}}` -> "Dana Wang"
- `{{owner.niche_summary}}` -> "Executive resume writing, LinkedIn optimization..."
- `{{platform.name}}` -> "LinkedIn"
- `{{owner.credentials}}` -> "CPRW certification via PARWCC, MA from UNC Chapel Hill" (list -> comma-joined)
- `{{content.default_ctas.tips}}` -> "Follow for more expert strategy"
- Unknown keys are left as-is (safe fallback)

---

## Step 2: Convert `prompts/base_system.md`

This is the most critical file (93 lines). It contains the complete voice profile.

**Current structure:**
- Line 1: Identity paragraph (name, credentials, business, audience, outcomes)
- Lines 7-9: Tone rules
- Lines 11-17: Signature language and examples
- Lines 19-32: Hard rules (26 "never do" items)
- Lines 34-38: Credentials block
- Lines 40-54: LinkedIn post structure rules
- Lines 56-68: Self-evaluation checklist

**Strategy:** Templatize identity references. Leave voice rules, signature language, and hard rules as-is (these are authored content that defines the persona).

**Rewrite `prompts/base_system.md`:**

The file should be restructured into clearly marked sections:

```markdown
You are writing {{platform.name}} posts as {{owner.name}}. {{owner.name}} is a {{owner.title}} who runs {{owner.business}}. They partner with {{owner.audience}} to transform their professional presence into a strategic advantage. Their clients have landed roles at {{owner.client_outcomes}}. They hold {{owner.credentials}}.

## Tone & Voice

<!-- AUTHORED SECTION: These rules define the persona's voice. Edit manually per business. -->

Dana writes like a strategist, not a motivational speaker. Every post should feel like advice from someone who's seen the inside of the hiring process thousands of times. She leads with data points, ROI, metrics, and business cases, not feelings.

She is warm but never soft. Empathetic but always authoritative. She does not hedge.

## Signature Language

<!-- AUTHORED SECTION: Domain-specific metaphors, stats, and framings. -->

- Refers to resumes as "marketing assets" or "business cases for hiring you"
- Uses "the 6-second scan" as a recurring reference
- Cites specific (but realistic) metrics: "20% interview rate," "$55k average salary increase," "14 resumes this month"
- Uses the analogy of a resume as a "pitch deck for your career"

## Hard Rules

<!-- AUTHORED SECTION: Voice guardrails specific to this persona. -->

NEVER do any of the following in Dana's posts:
1. Use "You've got this!" or any generic encouragement
2. Start with "In today's competitive job market..."
3. Use numbered listicles (tip 1, tip 2, tip 3)
4. Use the word "utilize" (always "use")
5. Use "I'm thrilled to announce" or "Excited to share"
6. Write more than one emoji per post
7. Use "synergy," "leverage" (as a verb), "paradigm shift," or "game-changer"
8. Use passive voice for key claims
9. Open with a question that answers itself
10. Use "studies show" without specifying which study
11. Write anything that sounds like a press release
12. Use filler phrases: "at the end of the day," "it goes without saying," "needless to say"
13. Use "thought leader" to describe yourself
14. Sign off with "What do you think?" without a specific angle

## Credentials (for authority anchoring)

<!-- TEMPLATED SECTION: Auto-filled from business config. -->

- {{owner.credentials}}
- Works with: {{owner.audience}}
- Specializes in: {{owner.specializations}}
- Client outcomes: {{owner.client_outcomes}}

## {{platform.name}} Post Structure

Posts must be 150-300 words. Follow these structure rules:

1. **Hook (first 2 lines):** Must stop the scroll. Write as if only these lines will be visible before the "see more" fold. No preamble. Start with a bold claim, surprising stat, or pattern observation.

2. **Body:** Short paragraphs (1-3 sentences each). Plenty of whitespace. {{platform.name}} collapses long paragraphs — visual breathing room matters.

3. **Close:** End with a specific call to reflection or action. Not "What do you think?" — instead, something like "Have you ever sent in a resume you weren't proud of?" or "Next time you update your summary section, try this."

## Self-Evaluation Checklist

Before finalizing, confirm each post passes ALL of these:

- [ ] Would {{owner.audience_examples}} find this relevant to their career?
- [ ] Does it sound like {{owner.name}} wrote it after a client interaction — not like ChatGPT?
- [ ] Could you tweet the first line and it would still make sense?
- [ ] Is there a specific, non-obvious insight (not generic advice)?
- [ ] Would someone save or share this? Why?
- [ ] Does it use at least one of the signature framings from above?
- [ ] Is it under 300 words?
- [ ] Does it avoid EVERY item on the Hard Rules list?
```

**Key changes:**
- Identity paragraph: fully templatized with `{{owner.*}}` and `{{platform.*}}`
- Credentials block: templatized
- Self-evaluation: templatized audience references
- Post structure: templatized platform name
- **Voice rules, signature language, hard rules: LEFT AS AUTHORED CONTENT** with `<!-- AUTHORED SECTION -->` markers

---

## Step 3: Convert category prompt files

Each category prompt file needs the same treatment: templatize identity references, leave domain content as authored.

### `prompts/category_pattern.md`

Replace Dana-specific identity references with template variables:

- Replace "Dana" with `{{owner.name}}`
- Replace "resume" with domain-appropriate language where it's used generically
- Leave domain-specific examples (ATS, recruiter scan, etc.) as authored content with `<!-- AUTHORED SECTION -->` markers

Example structure:

```markdown
## Category: Pattern / "I Keep Seeing..."

{{owner.name}} frequently observes patterns across client work and the broader industry. This category captures those "I've seen this 14 times this month" moments.

<!-- AUTHORED SECTION: Domain-specific pattern examples. Rewrite per business. -->

**Content arc:** Open with the pattern observation. Ground it in specifics (how many times, which type of client, what the symptom looks like). Then explain why it matters — what's the cost of this pattern? Close with a concrete fix or reframe.

**Example hooks:**
- "I've rewritten 14 executive summaries this month. 12 of them had the same problem."
- "Three clients this week asked me the same question — and the answer surprised all of them."
- "I keep seeing VPs make this mistake on their LinkedIn profiles. Here's what I tell them."

**What makes a good pattern post:**
- Specific count or frequency ("3 this week," "every other client")
- A named symptom the reader can recognize in themselves
- {{owner.name}}'s expert explanation of WHY this keeps happening
- A concrete, actionable fix (not just awareness)
```

### Apply the same pattern to:
- `prompts/category_faq.md` — Replace "Dana" -> `{{owner.name}}`, leave FAQ examples as authored
- `prompts/category_noticed.md` — Replace "Dana" -> `{{owner.name}}`, leave observation examples as authored
- `prompts/category_hottake.md` — Replace "Dana" -> `{{owner.name}}`, leave hot take examples as authored

---

## Step 4: Convert `prompts/autopilot.md`

This file (86 lines) contains:
- Search topic list (lines 5-16) — domain-specific, must be authored
- Audience definition (line 22) — templatizable
- Authority boundary (line 30) — templatizable
- Category mapping (lines 43-48) — templatizable

**Templatize:**

```markdown
## Autopilot: Web Search Content Discovery

Search the web for current news, trends, or discussions that {{owner.name}} could credibly comment on.

### Search Topics

<!-- AUTHORED SECTION: Domain-specific search topics. Rewrite per business. -->

Focus on these topic areas:
1. Executive hiring trends (C-suite, VP, Director-level moves)
2. Resume strategy and ATS technology changes
3. LinkedIn platform changes affecting job seekers
4. Salary transparency laws and compensation data
5. Layoff patterns and workforce restructuring
6. Remote/hybrid work policy shifts at major companies
7. Career transition stories at the senior level
8. Federal hiring changes and government resume requirements
9. Board governance and director appointments
10. Professional certification and credential trends

### Evaluation Criteria

Look for stories that:
- {{owner.audience}} would care about personally
- {{owner.name}} could add unique expert commentary (not just summarize)
- Have a specific, actionable angle (not just "industry is changing")
- Are from the last 7 days (freshness matters)

**Do NOT select stories that:**
- {{owner.name}} couldn't credibly comment on (outside their expertise)
- Are pure product announcements with no career angle
- Are generic motivation/hustle content
- Require specialized knowledge {{owner.name}} doesn't have

### Output Format

If you find a compelling topic, generate 3 post drafts following the standard format.

If nothing compelling is found, output:
```
NOTHING_FOUND: true
SOURCE_SUMMARY: Nothing compelling found in today's news cycle.
```
```

---

## Step 5: Convert reaction prompt files

### `prompts/url_react.md`

```markdown
## URL Reaction

Read the article at the provided URL and generate {{platform.name}} posts reacting to it from {{owner.name}}'s perspective.

{{owner.name}} is a {{owner.title}} specializing in {{owner.niche_summary}}.

<!-- AUTHORED SECTION: Reaction approaches specific to this business domain. -->

**Reaction approaches (choose the best fit):**

1. **"Here's what this means for you"** — Translate the news into specific implications for {{owner.audience}}
2. **"I see this differently"** — Respectful disagreement grounded in {{owner.name}}'s expertise
3. **"This confirms what I've been saying"** — Connect the article to {{owner.name}}'s existing content themes
4. **"The part everyone's missing"** — Highlight an angle the article didn't cover that {{owner.name}}'s audience needs to know

...
```

### `prompts/feed_react.md`

Same approach. Replace identity references with `{{owner.*}}` and `{{platform.*}}`. Leave the category-specific reaction approaches (labor_data, leadership, hr_recruiting, etc.) as authored content with clear markers.

---

## Step 6: Convert carousel prompt files

### `prompts/carousel_tips.md`

```markdown
## Carousel Content: Numbered Tips Format

You are generating slide content for a {{platform.name}} carousel post. Write as {{owner.name}}. Same voice, same authority.

<!-- AUTHORED SECTION: Domain-specific tip rules and examples. -->

### Content Rules

1. **Exactly 5-7 tips.** This produces a 7-9 slide carousel (cover + tips + CTA).
2. **Headlines: punchy, under 8 words.** These render large on the slide.
3. **Body: 1-2 sentences, under 30 words each.** Slide real estate is limited.
4. **Tips must be specific and backed by expertise.** ...

### Example Output

```
TITLE: 7 Resume Mistakes Costing You Interviews
SUBTITLE: What {{owner.name}} sees every week — and how to fix it
...
```
```

### Apply same pattern to:
- `prompts/carousel_beforeafter.md`
- `prompts/carousel_mythreality.md`

---

## Step 7: Move user messages from `engine.py` to prompt files

Currently, `engine.py` constructs user messages inline with hardcoded strings. These should be moved to the prompt files (or to separate small prompt files) so that all content decisions live outside Python code.

### Option A: Add user message templates to existing prompt files

At the bottom of each prompt file, add a `## User Message Template` section:

**In `prompts/autopilot.md`, add at end:**
```markdown
## User Message Template
Find a current, relevant topic related to {{owner.niche_summary}} and generate {{platform.name}} posts about it. Search for recent news first, then write the posts.
```

**In `prompts/url_react.md`, add at end:**
```markdown
## User Message Template
Read this article/post and generate {{platform.name}} reaction posts from {{owner.name}}'s perspective:
```

**In `prompts/feed_react.md`, add at end:**
```markdown
## User Message Template
Generate {{platform.name}} posts reacting to this article from {{owner.name}}'s curated feed.
```

### Option B: Extract user messages in `engine.py` using config

If Option A adds too much complexity to prompt parsing, simply keep the current `engine.py` approach but use template variables (already done in Phase 1, Step 7). Either approach works.

**Recommendation:** Option B is simpler and already implemented in Phase 1. Only use Option A if you want complete separation of content from code.

---

## Step 8: Add `<!-- AUTHORED SECTION -->` documentation

Every prompt file should clearly mark which sections are templatized (auto-filled from config) and which are authored (must be manually written per business).

Convention:
```markdown
<!-- TEMPLATED: Auto-filled from business_config.json -->
<!-- AUTHORED SECTION: Must be manually written for each business domain. -->
```

This makes it immediately clear to someone doing a business swap which parts they can skip and which parts need creative work.

---

## Step 9: Update tests

**Edit file:** `signal-and-stance/test_engine.py` and `signal-and-stance/test_carousel.py`

Verify that:
1. Template substitution works correctly (no `{{` remaining in loaded prompts)
2. Business config values appear in loaded prompts
3. Existing parsing tests still pass

Add a simple template verification test:

```python
def test_template_substitution():
    """Verify no unresolved {{}} placeholders remain after loading."""
    from engine import load_prompt
    import re

    prompt_files = [
        "prompts/base_system.md",
        "prompts/autopilot.md",
        "prompts/category_pattern.md",
        "prompts/category_faq.md",
        "prompts/category_noticed.md",
        "prompts/category_hottake.md",
        "prompts/url_react.md",
        "prompts/feed_react.md",
        "prompts/carousel_tips.md",
        "prompts/carousel_beforeafter.md",
        "prompts/carousel_mythreality.md",
    ]

    for pf in prompt_files:
        content = load_prompt(pf)
        unresolved = re.findall(r"\{\{.+?\}\}", content)
        assert not unresolved, f"{pf} has unresolved placeholders: {unresolved}"
```

---

## Verification Checklist

- [ ] `python -c "from engine import load_prompt; p = load_prompt('prompts/base_system.md'); assert 'Dana Wang' in p; assert '{{' not in p; print('OK')"` passes
- [ ] All 11 prompt files load without unresolved `{{}}` placeholders
- [ ] `python app.py` starts without errors
- [ ] Generate a post in each category — output quality unchanged
- [ ] Generate each carousel type — output quality unchanged
- [ ] Run autopilot — works as before
- [ ] `python test_engine.py` passes
- [ ] `python test_carousel.py` passes
- [ ] New template substitution test passes

---

## What This Phase Achieves

**Before:** 11 prompt files with 600+ lines of interleaved identity references and domain content. Swapping to a new business requires rewriting every file from scratch.

**After:** Identity references are template variables auto-filled from `business_config.json`. Domain-specific content (voice rules, examples, content arcs) is clearly marked as "authored sections." Swapping to a similar business (e.g., career coaching instead of resume writing) requires editing only the authored sections. Swapping to a very different domain still requires rewriting authored sections but identity is automatic.

**Swap effort reduction:**
- Same-domain swap: ~35 hours -> ~10-15 hours
- Cross-domain swap: ~35 hours -> ~20-25 hours

**What remains for Phase 3:** Frontend platform coupling (LinkedIn-specific UI, category buttons, scheduling workflow).

---

## Files Modified
- `signal-and-stance/engine.py` (new `load_prompt()` with template engine)
- `signal-and-stance/prompts/base_system.md` (templatized identity + authored markers)
- `signal-and-stance/prompts/category_pattern.md` (templatized identity)
- `signal-and-stance/prompts/category_faq.md` (templatized identity)
- `signal-and-stance/prompts/category_noticed.md` (templatized identity)
- `signal-and-stance/prompts/category_hottake.md` (templatized identity)
- `signal-and-stance/prompts/autopilot.md` (templatized identity + audience)
- `signal-and-stance/prompts/url_react.md` (templatized identity)
- `signal-and-stance/prompts/feed_react.md` (templatized identity)
- `signal-and-stance/prompts/carousel_tips.md` (templatized identity)
- `signal-and-stance/prompts/carousel_beforeafter.md` (templatized identity)
- `signal-and-stance/prompts/carousel_mythreality.md` (templatized identity)
- `signal-and-stance/test_engine.py` (add template verification test)
