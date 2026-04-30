# 03 — Content Rhythm

> **Decision flag for review:** the Signal Stance playbook organizes
> content around **5 thematic pillars** and **6 post formats**. The
> existing app schema uses **4 fixed UI categories** (`pattern`, `faq`,
> `noticed`, `hottake`) keyed off `business_config.content.categories`.
> Below the 4 categories are mapped to the 4 most-aligned pillars from
> the playbook. Pillar 4 (Strategy Before Execution) doesn't have a
> direct UI bucket — it surfaces inside both `pattern` and `noticed`
> framings. If we want a true 5-bucket UI, the framework needs a small
> change to support a variable category list. See notes at the bottom
> of this file.

## Content categories

### Pattern
Patterns from real client work — observations across many engagements that nobody else has visibility into. The "I keep seeing..." bucket maps to Pillar 2 of the playbook. Aggregated and anonymized always; never identifies real clients. Examples: "In the last 50 senior professional resumes I've worked on, there's a pattern in what's missing." "A pattern in founder resumes: overclaiming on some dimensions, underclaiming on others."

### FAQ
The craft questions about professional presentation that come up repeatedly in client work. Maps to Pillar 1 (The Craft of Professional Presentation). The "Client asked..." or "Question I keep getting..." bucket. Examples: "What's the actual job of a LinkedIn headline?" "Why is 'results-oriented' the weakest phrase on most resumes?"

### Noticed
The "Just noticed..." bucket — operator observations on AI and professional work, plus subtle shifts in how the work is changing. Maps primarily to Pillar 3 (AI and Professional Work). Examples: "Most AI-generated LinkedIn content has a specific tell." "The resume tools that promise 'AI-optimized' are usually optimizing the wrong thing."

### Hot Take
Direct contrarian takes — challenges to conventional LinkedIn and career wisdom where the common advice is wrong, oversimplified, or missing context. Maps to Pillar 5 (Contrarian Takes and Reframes). Contrarian only when the common wisdom is actually wrong; never contrarian for its own sake. Examples: "The 'write every day on LinkedIn' advice is wrong for most professionals." "'Be authentic' is the most unhelpful piece of professional advice currently in circulation."

## Posting cadence

The Signal Stance playbook sets cadence at **3–4 posts per week** on personal LinkedIn (Taylor's primary content channel). The dana-wang template uses Mon–Fri (5 days). For Taylor, schedule 4 days and treat Friday as flex / review.

Monday — Patterns from Client Work (Pillar 2). "Share an anonymized observation from recent engagements. What's the pattern across many clients?"
Tuesday — Craft of Professional Presentation (Pillar 1). "Specific observation on resume, LinkedIn, or bio craft. Pick one mechanic."
Wednesday — Strategy Before Execution (Pillar 4). "The thinking that has to happen before any writing. Positioning, identity, professional brand."
Thursday — AI and Professional Work (Pillar 3). "Operator observation on what AI is and isn't useful for. Never state we use it."
Friday — flex. Default to Contrarian Take (Pillar 5) when an idea is ready; skip if not. Better to skip than post filler.

## Posting times

Mon 8:00 AM, Tue 8:00 AM, Wed 8:00 AM, Thu 8:00 AM, Fri 9:00 AM — EST

> *Note:* the playbook doesn't specify times — these are sensible
> LinkedIn-optimal slots that match the dana-wang pattern. Confirm or
> adjust.

## Default CTAs (optional)

The Signal Stance playbook explicitly avoids "follow for more" and similar engagement CTAs — posts end on insight, not on prompts. Recommended approach: leave CTAs empty or set to `auto` for the extraction script to skip CTA injection. Carousel deliverables can carry a tasteful end-card link to signalstance.com without a "follow me" framing.

tips: auto
beforeafter: auto
mythreality: auto
general: auto

> *If a CTA is required by the carousel renderer, prefer:* "More writing
> at signalstance.com" *or* "Read the longer essay at signalstance.com/blog"
> *— pointing readers to owned surfaces rather than chasing follows.*

## Platform settings (optional, almost never customized)

Platform: LinkedIn
Post word range: 200–500 (the playbook spans 200–400 for Observations, 250–400 for Case Examples, 200–350 for Contrarian Takes, 300–500 for Frameworks — wider than dana-wang's 150–300)
Carousel dimensions: 1080×1080

---

## Architectural note (for the extraction script / framework owner)

The Signal Stance content framework is richer than the existing 4-category UX supports:

- **5 pillars** (Craft, Patterns, AI, Strategy, Contrarian) vs. **4 UI categories**.
- **6 formats** (Observation, Framework, Case Example, Contrarian Take, Behind-the-Work, Long-Form Essay) vs. **3 carousel templates** (`tips`, `beforeafter`, `mythreality`) — formats and carousel templates aren't 1:1 either.
- The playbook explicitly forbids the engagement-style CTAs the current `default_ctas` field assumes.

Two paths forward:

1. **Map and squeeze** — collapse 5 pillars into 4 buckets (as done above), accept that Strategy-Before-Execution shows up split across `pattern` and `noticed`. Lower-effort, ships today. Loses one pillar's distinct identity in the UI.
2. **Generalize the schema** — let `content.categories` be a variable-length object so each tenant can declare 3, 4, 5, or 6 buckets with their own keys. Touches the SPA (category-card rendering), `engine.py` (prompt resolution), and the prompt files (one per category). Higher-effort but matches the data model the playbook implies.

Recommend Path 1 for the Taylor intake (ship the tenant) and Path 2 as a follow-up if Taylor's content rhythm ends up fighting the 4-bucket UX in practice.
