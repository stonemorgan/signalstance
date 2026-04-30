# 04 — Brand & Feeds

Visual identity for PDF carousels and the RSS sources the relevance
scorer pulls from. Drives `business_config.brand.*`, `feeds.json`,
and `business_config.feeds.categories`.

> **How to fill this in:** both halves of this file accept `auto` if
> the tenant doesn't have specifics yet. The script will fall back to
> sensible defaults (template colors / Helvetica) and propose feeds
> from topic hints.

---

## Brand colors

Either provide hex codes or write `auto` plus a one-line vibe note.

### Mode 1 — explicit hex codes

Provide values for each role. Anything omitted falls back to the
`_template` default for that role.

> *primary: #1B3A4B  — main brand color (carousel titles, accents)*
> *secondary: #4A90A4 — secondary accent*
> *accent: #D4A574 — highlight color, used sparingly*
> *background: #FFFFFF — slide background*
> *background_alt: #F5F3EF — alt slide background (paired layouts)*
> *text_dark: #1B3A4B — primary text on light backgrounds*
> *text_light: #FFFFFF — text on dark backgrounds*
> *text_muted: #6B7B8D — secondary/footer text*
> *divider: #E0DCD5 — thin lines and separators*
> *negative: #C0392B — error/contrast (rare)*
> *positive: #27AE60 — affirmative/contrast (rare)*

### Mode 2 — auto

Write `auto` and a one-line vibe note. The script proposes a palette
from defaults seeded by the vibe.

> *auto — warm, professional, executive (avoid pastels)*

## Brand fonts (optional)

ReportLab-compatible font names. Default: Helvetica family
(`Helvetica-Bold`, `Helvetica`, `Helvetica-Oblique`). Custom fonts
must be installed separately and confirmed with the carousel renderer.

> *heading: Helvetica-Bold*
> *body: Helvetica*
> *accent: Helvetica-Oblique*

---

## RSS feeds — known URLs

If the tenant already follows specific RSS feeds, list them here. One
feed per line. Optional: add `(category=<name>, weight=<0–1>)` to set
the relevance scorer's bucket and weight. Default weight is `1.0`.

```
https://hbr.org/big-ideas/feed (category=leadership, weight=1.0)
https://www.linkedin.com/blog/marketing/feed (category=linkedin, weight=0.8)
https://www.shrm.org/rss/all (category=hr_recruiting)
```

## RSS feeds — topic hints (if no URLs)

If the tenant doesn't have a feed list, list 5–10 topic areas they
want signal on. The intake script proposes candidate feeds; you
approve before they're written into `feeds.json`.

> *- Executive leadership and management strategy*
> *- ATS technology and recruiting software*
> *- LinkedIn algorithm changes and feature releases*
> *- Compensation and salary trends*
> *- Federal hiring policy and clearance changes*
> *- Senior career transitions and board placements*

## Feed categories

Map of category name → one-line description used by the relevance
scorer to decide whether an article belongs to a bucket. Either list
categories explicitly or write `auto` to derive them from the URLs
and topic hints above.

> *leadership: Executive leadership, management strategy, C-suite perspectives.*
> *careers: Career advice, job search strategy, professional development.*
> *executive_careers: Senior-level and executive career content specifically.*
> *hr_recruiting: Recruiting practices, hiring processes, what recruiters look for.*
> *linkedin: LinkedIn platform updates, algorithm changes, feature releases.*
> *compensation: Salary data, compensation trends, negotiation research.*

Or:

> *auto*
