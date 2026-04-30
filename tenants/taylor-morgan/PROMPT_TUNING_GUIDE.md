# Taylor Morgan / Signal Stance — Prompt Tuning Guide

**Status:** All 10 prompts hand-tuned as of 2026-04-30. `base_system.md` was synthesized at intake; the remaining 10 (4 category, 1 autopilot, 2 react, 3 carousel) have all been hand-tuned and committed:

- `category_pattern.md` — `ca2a3d6`
- `category_faq.md` — `178e66d`
- `category_noticed.md` — `eed9227`
- `category_hottake.md` — `930edab`
- `autopilot.md` — `169b85d`
- `url_react.md` — `70016fa`
- `feed_react.md` — `3ab3de4`
- `carousel_tips.md` — `cd0b8c0`
- `carousel_beforeafter.md` — `81df79f`
- `carousel_mythreality.md` — `d1ce325`

The guide is preserved as a reference for: (a) future re-tuning if voice samples are updated and base_system is regenerated, (b) onboarding future tenants who need the same prompt-tuning shape, (c) reference material on the Signal Stance voice divergences from Dana (no engagement bait, AI-as-patterns-not-personal-practice).

**Audience for this document:** the human operator (Taylor) plus whatever Claude session is helping. A Claude session reading this cold should have everything it needs to draft a tuned prompt — voice rules, source intake, current prompt skeleton, and a worked example.

---

## 1. TL;DR for Claude

You are helping tune 10 prompt files for the Signal Stance tenant of an app called SignalStance. Each file is loaded at generation time and concatenated with `base_system.md` (which carries the voice). Your job in each file is to add **domain-specific structural guidance, examples, and tone calibration** that the base prompt doesn't cover.

The pattern, in one sentence: **keep the file's existing structural skeleton, replace every `<!-- AUTHORED SECTION -->` placeholder comment with substantive Signal Stance-specific guidance, and add at least one realistic worked example wherever the file has an example slot.**

The bar is "Dana Wang's prompts" (in `tenants/dana-wang/prompts/`) — same shape, but rewritten for Taylor's editorial voice and Signal Stance's audience (Director-level+ professionals, fractional executives, founders). One Dana before/after appears in §6 below.

---

## 2. What These Prompts Are and Where They Run

`framework/engine.py` loads `base_system.md` and one of the category/format prompts, concatenates them with a separator, and sends the result as the system prompt to Claude. So every word in these 10 files reaches the model on every generation. Anything left as a `<!-- DELETE THIS COMMENT -->` placeholder is sent verbatim to the model — it's not stripped.

Routing map (from `framework/engine.py`):

| User action in UI | Loaded prompt file | Engine fn |
|---|---|---|
| Pattern category card | `prompts/category_pattern.md` | `generate_drafts()` |
| FAQ category card | `prompts/category_faq.md` | `generate_drafts()` |
| Noticed category card | `prompts/category_noticed.md` | `generate_drafts()` |
| Hot Take category card | `prompts/category_hottake.md` | `generate_drafts()` |
| Autopilot button | `prompts/autopilot.md` | `generate_autopilot()` |
| URL React | `prompts/url_react.md` | `generate_url_reaction()` |
| Feed article React | `prompts/feed_react.md` | `generate_feed_reaction()` |
| Carousel: Tips | `prompts/carousel_tips.md` | `generate_carousel_content()` |
| Carousel: Before/After | `prompts/carousel_beforeafter.md` | `generate_carousel_content()` |
| Carousel: Myth/Reality | `prompts/carousel_mythreality.md` | `generate_carousel_content()` |

`{{owner.name}}`, `{{owner.audience}}`, `{{platform.name}}`, etc. are auto-substituted from `business_config.json` at load time — leave them as `{{...}}` in your output.

---

## 3. Source of Truth: Signal Stance Voice DNA

The voice is already locked in `prompts/base_system.md`. The category/carousel prompts must be **consistent with** this — never contradict it, never re-define it. Highlights to internalize:

**Tone:** Direct, confident, editorial. Serious peer talking to other serious peers — not guru, coach, or course seller. Commits to views and lets readers disagree rather than hedging every claim.

**Stance:** Operator with pattern recognition from real client work across many engagements. Sober middle market — between budget services and premium executive firms.

**Five recurring vantage points:**
1. Strategy before execution — the thinking that happens before any writing begins
2. Editorial craft — the content itself models the work the firm sells
3. Operator's view on AI in professional work — grounded, neither hype nor panic
4. The sober middle — between budget services and premium firms
5. Pattern recognition from real client work

**Signature framings:**
- Specific numbers when accurate ("In the last 50 senior professional resumes" beats "in many resumes")
- Anonymized client scenarios with enough texture to feel real ("Senior Director of Product at a mid-sized SaaS company. 14 years in.")
- Asymmetric structure — points lean toward a view rather than balancing every claim
- Ends on the insight or implication, never on engagement questions
- Frames AI behavior as "patterns you can identify" rather than personal practice

**Hard rules (never violate in any prompt example):**
- No engagement-bait endings ("Agree?" "What do you think?")
- No consulting jargon (leverage, synergy, ideate, thought leader, disruptive, paradigm)
- No AI's favorite words (crucial, myriad, plethora, tapestry, delve, navigate the landscape)
- No explicit mention of AI in personal work practice
- No claiming more than is accurate about firm size or reach
- No motivational posturing or generic encouragement
- No throat-clearing openers ("In today's digital landscape...", "Hey LinkedIn family!")

**Audience:** Director-level professionals and above at companies of 200–10,000 employees; solo consultants and fractional executives ($200K+); founders and small-business owners; established professionals (30s–50s).

**Examples of realistic personas to use in prompt examples:** Director of Engineering, VP of Product, Senior Director of Marketing, Fractional CFO, Founder of a B2B consultancy.

---

## 4. Calibrated Voice Samples (from intake `02-voice-samples.md`)

These four posts are the voice target — anything you draft as an example inside a prompt should sound like it came from the same writer.

### Sample A — Pattern post
> Most senior professional resumes I see open with some version of this line:
>
> "Strategic leader with 15+ years of experience driving transformation across multiple industries."
>
> This sentence is doing nothing.
>
> It could describe anyone. It signals that the writer didn't want to commit to specifics. And it wastes the most valuable six seconds on the resume — the time before a hiring manager decides whether to keep reading.
>
> What works better: lead with the specific. The exact role being targeted. The specific industry context. The kind of results produced, named concretely.

### Sample B — Case example (works as Pattern or FAQ)
> Worked on a resume last month for a Senior Director of Product at a mid-sized SaaS company. 14 years in, strong track record, looking to transition to VP roles.
>
> Her existing resume read as a list of responsibilities. What she managed, what she was accountable for, what teams reported to her.
>
> None of it answered the question a hiring manager at a growth-stage company actually asks: what business outcomes has she moved?

### Sample C — Hot Take
> Common LinkedIn advice: post every day.
>
> This is wrong for most professionals.
>
> The argument goes: consistency builds visibility, visibility builds authority, authority builds business. Therefore post daily.
>
> The missing piece: posting daily only works if each post meets a certain quality threshold. Below that threshold, more posts actively hurt you.

### Sample D — Noticed (AI observation)
> Most AI-generated LinkedIn content has a specific tell.
>
> It's not the one everyone talks about — not the "delve" or the "tapestry" or the excessive use of "moreover."
>
> It's structural. AI-drafted content tends toward perfect balance. Every argument gets both sides. Every claim gets a counterexample. Every point gets hedged with "while" and "although" and "that said."

---

## 5. The 10 Prompts to Tune — Inventory

Each prompt has a structural skeleton already in place. The work is filling in the placeholder sections with Signal Stance-specific guidance and examples.

| # | File | UI surface | Placeholders to fill | Priority | Status |
|---|------|------------|---------------------|----------|--------|
| 1 | `category_pattern.md` | Pattern card | Tone | High (Mon content) | **Done** — `ca2a3d6` |
| 2 | `category_faq.md` | FAQ card | Tone | High (Tue content) | **Done** — `178e66d` |
| 3 | `category_noticed.md` | Noticed card | Tone | High (Thu content) | **Done** — `eed9227` |
| 4 | `category_hottake.md` | Hot Take card | Tone | High (Fri flex) | **Done** — `930edab` |
| 5 | `autopilot.md` | Autopilot button | Search topics, evaluation criteria | High (no-input fallback) | **Done** — `169b85d` |
| 6 | `url_react.md` | URL React | Domain-specific reaction approaches | Medium | **Done** — `70016fa` |
| 7 | `feed_react.md` | RSS feed item React | Category-specific calibration | Medium (blocked on empty `feeds.json`) | **Done** — `3ab3de4` |
| 8 | `carousel_tips.md` | Carousel: Tips | Voice rules, worked example | Medium (when carousels go live) | **Done** — `cd0b8c0` |
| 9 | `carousel_beforeafter.md` | Carousel: Before/After | Voice rules, worked example | Medium | **Done** — `81df79f` |
| 10 | `carousel_mythreality.md` | Carousel: Myth/Reality | Voice rules, worked example | Medium | **Done** — `d1ce325` |

**Recommended order (historical, for reference):** 1 → 2 → 3 → 4 (the four categories Taylor would use immediately), then 5 (autopilot — high leverage when no insight is in-hand), then 6, then carousels last (8/9/10 only matter once Signal Stance starts producing carousels). All 10 shipped in this order on 2026-04-30.

---

## 6. Reference: Anatomy of a Tuned Prompt (Dana before/after)

This is the critical pattern reference. Below is the **template state** of `category_pattern.md` and Dana's **tuned version** of the same file. The transformation pattern is: keep the structural skeleton, expand each numbered step with concrete domain detail and examples, and replace the Tone placeholder with a fleshed-out paragraph.

### Template (what Taylor's currently looks like)

```markdown
<!-- TEMPLATED: Identity references use {{variable}} placeholders from business_config.json -->

## "I keep seeing..." — Pattern/Mistake Posts

{{owner.name}} has observed a recurring pattern in their work with {{owner.audience}}.

<!-- AUTHORED SECTION: Define the content arc for pattern posts in your domain -->
<!-- DELETE THIS COMMENT AND WRITE YOUR PATTERN POST STRUCTURE HERE -->

### Structure

1. **Hook**: State the pattern bluntly with a specific number or timeframe
2. **The pattern**: Describe the specific mistake with diagnostic detail
3. **Why it matters**: Connect to a real consequence in your domain
4. **The fix**: Concrete, actionable correction (not vague advice)
5. **Reframe**: Broader insight about what this pattern reveals
6. **CTA**: Question tied to the specific pattern

### Tone

<!-- AUTHORED SECTION: How should pattern posts sound? -->
<!-- DELETE THIS COMMENT AND DESCRIBE THE TONE HERE -->
<!-- Example: "Observational, clinical, empathetic about WHY people make the mistake" -->
```

### Dana's tuned version (the bar to clear)

```markdown
## Category: "I keep seeing..." — Pattern/Mistake Posts

<!-- TEMPLATED: Owner name auto-filled from business_config.json -->

You are writing a post based on a recurring pattern or mistake {{owner.name}} has observed in their practice. This is {{owner.name}} reporting from the field — they've seen this enough times that it's become a pattern worth sharing.

**Follow this arc:**

1. **Hook:** State the pattern bluntly with a specific number or timeframe. "I've reviewed X resumes this month. Y of them made the same mistake." or "Third executive this quarter who..." — ground it in real observation, not theory.

2. **The pattern:** Describe the specific mistake or trend with enough detail that the reader can self-diagnose. Be precise — "listing responsibilities instead of achievements" is better than "having a weak resume." The reader should be able to look at their own resume and know instantly if they're guilty.

3. **Why it matters:** Connect the mistake to a real consequence. ATS rejection. Recruiter pass in the 6-second scan. Getting screened out before a human ever reads it. Lost interviews. Underselling by $30-50k in salary negotiations. Make the stakes concrete.

4. **The fix:** Give a concrete, actionable correction — not vague advice like "make it better," but something the reader can do in the next 20 minutes...

5. **Reframe:** End with a broader insight about what this pattern reveals. Why do smart, accomplished people make this mistake? Usually because they're thinking about resumes wrong — as career histories instead of marketing assets...

6. **CTA:** A question tied to the specific pattern: "Have you checked your resume for this?" — not a generic "What do you think?"

**Tone:** Observational, almost clinical. {{owner.name}} is reporting what they see in the field. Not judgmental toward the people making the mistake — empathetic about *why* they make it, because it usually comes from a reasonable but wrong assumption. But firm about why it needs to change. Think: a doctor explaining a common health mistake — no blame, just clear diagnosis and treatment.
```

### What changed (the pattern to replicate)

1. The placeholder HTML comments are **gone**.
2. Each numbered step is **expanded with concrete examples in the persona's voice** (Dana uses ATS, recruiter scans, salary numbers — Taylor's equivalents would be six-second scan, executive search firm screen-outs, fractional rate compression, brand authority, pipeline impact).
3. The Tone section is a **fleshed-out paragraph** with a metaphor (Dana: "doctor explaining a common health mistake"). Taylor's tone metaphors should align with the voice DNA: think editor reviewing a manuscript, or operator reporting from the field.
4. **CTA guidance is calibrated to the persona.** Note: Signal Stance's intake explicitly says posts end on insight, not engagement questions — so for Taylor, the CTA step should say *"End on the insight or implication — not on a question. The final line crystallizes the takeaway or broader principle."* (This is **different from Dana's** — important divergence.)

---

## 7. Per-Prompt Drafting Briefs (paste into Claude)

Each brief below is a ready-to-paste prompt for a Claude session. Paste sections 3–4 of this guide as context first (the voice DNA + samples), then paste one of these briefs, then paste the current contents of the relevant prompt file.

### Brief 7.1 — `category_pattern.md`

> Tune `tenants/taylor-morgan/prompts/category_pattern.md` for Signal Stance. Keep the 6-step structural skeleton (Hook → Pattern → Why it matters → Fix → Reframe → CTA) but expand each step with concrete language calibrated to senior professional / fractional executive / founder audience. Replace the Tone placeholder with a fleshed-out paragraph using a metaphor consistent with the editorial-operator voice (e.g., editor reviewing a manuscript, operator reporting from the field — not "doctor" since Dana already uses that). **Critical divergence from Dana:** the CTA step must say "End on the insight or implication — not on a question. The final line should crystallize the takeaway." (Signal Stance never asks engagement questions.) Use Sample A from §4 as the calibration target. Output the full file content.

### Brief 7.2 — `category_faq.md`

> Tune `tenants/taylor-morgan/prompts/category_faq.md` for Signal Stance. The category in business_config.json is labeled "FAQ" with prompt label "Client asked..." and placeholder asking for craft questions about professional presentation. Expand each step of the 6-step skeleton with senior-level craft examples (LinkedIn headline mechanics, resume opening lines, bio positioning, executive summary structure). Tone should feel like a craft conversation between practitioners — direct, specific, willing to commit. Replace the CTA step with Signal Stance's no-engagement-bait rule (end on insight, not on a question). Output the full file content.

### Brief 7.3 — `category_noticed.md`

> Tune `tenants/taylor-morgan/prompts/category_noticed.md` for Signal Stance. This category covers operator observations on AI and professional work, and subtle shifts in how the work is changing. Use Sample D from §4 as the calibration target. The hook should grab a specific, recent observation; the body should connect dots others can't see; the close should land on the implication. **Hard rule:** the prompt must instruct the model to frame AI behavior as "patterns you can identify" rather than personal practice — never write "I use AI" or similar. Replace the CTA step with the no-engagement-bait rule. Output the full file content.

### Brief 7.4 — `category_hottake.md`

> Tune `tenants/taylor-morgan/prompts/category_hottake.md` for Signal Stance. Use Sample C from §4 as the calibration target — it's a model "common advice X is wrong" hot take. Expand the structural steps with Signal Stance-appropriate language: contrarian only when conventional wisdom is genuinely wrong, never contrarian for its own sake. The Tone section should describe a confident-but-honest register that fairly states the mainstream view before dissenting. **Critical:** the existing template's CTA step says "Explicitly invite disagreement or debate" — replace that entirely. Signal Stance hot takes still end on insight, not on "what do you think?" Output the full file content.

### Brief 7.5 — `autopilot.md`

> Tune `tenants/taylor-morgan/prompts/autopilot.md` for Signal Stance. Two placeholder sections to fill:
>
> **Step 1 search topics:** Use the 10 feed categories already defined in `business_config.json` under `feeds.categories` (leadership, careers, personal_brand, linkedin, ai_professional, content_strategy, hiring_senior, fractional_market, compensation, workplace_research). Translate each into a concrete search-topic phrase the way Dana's autopilot.md does (see `tenants/dana-wang/prompts/autopilot.md` for shape).
>
> **Step 2 evaluation criteria:** Prioritize: data-driven stories (BLS, surveys, compensation studies, research) over opinion; stories the Director-level+ / fractional executive / founder audience would care about; stories that challenge conventional career or LinkedIn wisdom. Skip: entry-level career content, generic "job market is tough" framing, anything Taylor couldn't credibly comment on as an operator in the senior career and visibility services space, anything requiring inside knowledge of a named company.
>
> Step 4 category mapping should reuse the same pattern/faq/noticed/hottake mapping Dana's file uses, lightly reworded for Signal Stance topic territory. Output the full file content.

### Brief 7.6 — `url_react.md`

> Tune `tenants/taylor-morgan/prompts/url_react.md` for Signal Stance. The single placeholder section asks for "domain-specific reaction approaches." Add a paragraph or short list calibrated to Signal Stance's vantage points: how to react when an article is about LinkedIn mechanics, executive hiring data, AI in knowledge work, fractional/consultant economics, or career-strategy advice. The reaction should always pull the article through one of the five Signal Stance vantage points (strategy-before-execution, editorial craft, AI operator view, sober middle market, pattern recognition). Reinforce the "1 sentence max referencing the source — Taylor's take is what matters" rule already in the file. Output the full file content.

### Brief 7.7 — `feed_react.md`

> Tune `tenants/taylor-morgan/prompts/feed_react.md` for Signal Stance. The placeholder asks for category-specific calibration across feed categories. Use the 10 feed categories from `business_config.json` (`feeds.categories`) and write a one-line stance for how to react to an article in each category — e.g., "leadership: connect the leadership trend to how it shapes a senior professional's positioning or career strategy"; "ai_professional: pattern-recognition framing, never personal practice"; "compensation: ground in fractional / senior-pro rate dynamics, not entry-level pay." Note: this prompt is lower priority until `feeds.json` is populated (currently empty). Output the full file content.

### Brief 7.8 — `carousel_tips.md`

> Tune `tenants/taylor-morgan/prompts/carousel_tips.md` for Signal Stance. The strict output format (TITLE / SUBTITLE / TIP N HEADLINE / TIP N BODY / CTA) must stay exactly as-is — it's machine-parsed. The placeholder section needs (a) Signal Stance voice rules adapted for slide-format scannability, (b) one full worked example carousel in the output format. The example should be a tips carousel that fits Signal Stance's territory — e.g., "7 Things Senior Professional Resumes Get Wrong" or "6 Signals a LinkedIn Profile Is Doing the Wrong Job." 5-7 tips, 6-word headlines max, under-30-word bodies. CTA must point to signalstance.com (not "follow for more"). Use Dana's `carousel_tips.md` as a structural reference — same shape, Signal Stance content. Output the full file content.

### Brief 7.9 — `carousel_beforeafter.md`

> Tune `tenants/taylor-morgan/prompts/carousel_beforeafter.md` for Signal Stance. Same constraints as 7.8 — keep the strict output format, add voice rules and one worked example. The example should be a before/after carousel showing common writing/positioning mistakes vs. Signal Stance-quality rewrites. Realistic before examples for senior professionals: weak LinkedIn headline ("Strategic leader driving transformation"), responsibility-listing resume bullet ("Managed cross-functional teams"), generic bio opener ("Passionate about helping companies grow"). Strong "after" rewrites that model Signal Stance editorial craft. 4-6 pairs. Output the full file content.

### Brief 7.10 — `carousel_mythreality.md`

> Tune `tenants/taylor-morgan/prompts/carousel_mythreality.md` for Signal Stance. Same constraints as 7.8 / 7.9. Worked example should debunk common LinkedIn or career misconceptions held by the senior professional / fractional / founder audience. Candidate myths to draw from: "post every day on LinkedIn" (see Sample C), "be authentic" as advice, "your resume should tell your story," "AI-optimized resume tools improve outcomes," "your headline should describe your job." 4-6 myth/reality pairs, realities under 35 words each. Output the full file content.

---

## 8. Workflow

1. **Open this file plus `tenants/_template/prompts/<file>.md`** (the current state of whichever prompt you're tuning) in a Claude session. The template file IS what's in `tenants/taylor-morgan/prompts/<file>.md` today — they're byte-identical.
2. Paste sections 3 (Voice DNA), 4 (Voice Samples), and 6 (Dana before/after pattern) into the session as context.
3. Paste the relevant brief from §7 plus the current prompt file content.
4. Review Claude's draft. Verify against the checklist in §9.
5. Save the tuned content to `tenants/taylor-morgan/prompts/<file>.md`.
6. **Smoke-test** — run the app on the taylor-morgan tenant (`python run.py --tenant taylor-morgan`), trigger the relevant generation, and verify the output sounds like Sample A/B/C/D. If the output drifts (hedging, engagement bait, AI tells), the prompt needs another pass.
7. Commit one prompt at a time so any drift is bisectable.

**Per the existing workflow memory:** work one prompt at a time and commit between each, with explicit handoff to the user before moving to the next.

---

## 9. Validation Checklist (run before committing each tuned prompt)

Structural:
- [ ] All `<!-- AUTHORED SECTION -->` and `<!-- DELETE THIS COMMENT -->` placeholder comments are gone
- [ ] All `{{owner.*}}`, `{{platform.*}}`, etc. variables are still in `{{...}}` form (not hardcoded)
- [ ] For carousel prompts: the strict output format (TITLE: / TIP N HEADLINE: / etc.) is unchanged from template
- [ ] Word/length limits stated in the file are unchanged (the SPA / parser may rely on them)

Voice consistency:
- [ ] No engagement-bait language anywhere in the prompt or its examples ("Agree?", "What do you think?", "Let me know in the comments")
- [ ] No consulting jargon (leverage, synergy, ideate, thought leader, disruptive, paradigm)
- [ ] No AI's-favorite-words in any example text (crucial, myriad, plethora, tapestry, delve, navigate the landscape)
- [ ] Examples use anonymized senior-level personas (Director, VP, Fractional CFO, Founder of B2B consultancy) — not entry-level
- [ ] If the prompt is for hottake or noticed, it doesn't tell the model to write "I use AI" or similar
- [ ] CTA guidance reflects "end on insight, not engagement question" (this is a Signal Stance divergence from Dana — Dana's CTA steps explicitly invite questions)

Smoke test (after writing):
- [ ] Generate at least one draft using the tuned prompt
- [ ] Compare against Sample A/B/C/D — does it sound like the same writer?
- [ ] Does it commit to a view rather than hedging both sides?

---

## 10. Open Items / Caveats

- **`feeds.json` is empty.** `feed_react.md` won't fire in production until feeds are populated (per `intake/taylor-morgan/04-brand-and-feeds.md` topic hints). Tune this prompt anyway, but smoke-testing it requires adding feeds first.
- **Voice samples are Playbook examples, not real published Taylor posts.** Sample A/B/C/D came from the Signal Stance Content Playbook's "Good Examples" section. Once Taylor has 5+ real posts he's happy with, swap them into `intake/taylor-morgan/02-voice-samples.md` and consider re-running the intake — but note that re-running with `--force` will also regenerate `base_system.md` non-deterministically. Prefer hand-tuning over re-generation if base_system is locked in.
- **Source-of-truth for Signal Stance content lives outside this repo** — there's a Signal Stance Content Playbook directory the user maintains separately. If you change voice rules during tuning that should propagate back, update the Playbook first, then this tenant.
- **`category_*.md` and the "Strategy Before Execution" pillar.** Signal Stance has 5 content pillars but the app schema has 4 category buckets. The Strategy-Before-Execution pillar (Pillar 4) is split across `pattern` and `noticed` framings. When tuning those two prompts, leave room in the structural guidance for strategy-framed insights, not just pattern-from-clients or AI-observation insights.
- **Carousel prompts are lowest priority.** Signal Stance hasn't committed to carousel deliverables yet — tune these last, once it's clear they'll be used.
