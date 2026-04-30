# 04 — Brand & Feeds

## Brand colors

Mode 1 — explicit hex codes (per the SignalStance Strategy doc, "Visual Identity" section).

primary: #2D4A57 — Signal Stance deep teal accent (modern, strategic). Used for headlines and brand accents on carousels.
secondary: #4A6B7A — softer teal, derived from the primary for secondary headings and supporting elements.
accent: #C9A96E — warm muted gold, used sparingly for emphasis on key takeaways and decorative dividers.
background: #FAF8F4 — warm off-white (the shared neutral across both Signal Stance and Raleigh Resume).
background_alt: #F0EBE2 — slightly deeper warm neutral for paired layouts and secondary slides.
text_dark: #1A1A1A — near-black (the shared neutral). Primary text on light backgrounds.
text_light: #FAF8F4 — warm off-white for text on dark backgrounds.
text_muted: #6B6B6B — secondary/footer text, captions, attribution.
divider: #D9D2C5 — thin lines and slide separators, harmonized with the warm neutral.
negative: #9A4A3C — Raleigh Resume's terracotta, repurposed here as the contrast/negative color (avoids introducing a fifth hue).
positive: #4A7A5C — muted forest, harmonized with the editorial palette (no saturated greens).

> *Note:* the strategy document specifies the primary teal (#2D4A57)
> and the shared "warm off-white, near-black" neutrals but doesn't pin
> exact hex codes for the supporting roles. The values above are
> proposals harmonized with the stated palette. Confirm or adjust.

## Brand fonts

Per the strategy doc's "Shared design DNA": **Fraunces (display) + Inter (body)**. ReportLab is the carousel renderer in `framework/carousel_renderer.py` — Fraunces and Inter are not part of ReportLab's built-in Type 1 fonts and would need to be registered as TrueType fonts via `pdfmetrics.registerFont`. Until that's set up, fall back to the Helvetica family.

heading: Helvetica-Bold (target: Fraunces, when font registration is wired up)
body: Helvetica (target: Inter, when font registration is wired up)
accent: Helvetica-Oblique (target: Fraunces Italic)

> *Note for the framework owner:* registering Fraunces + Inter is a
> small follow-up — `pdfmetrics.registerFont(TTFont(...))` once at module
> import in `carousel_renderer.py`, plus the `.ttf` files committed to
> a `framework/fonts/` directory. Worth doing for visual fidelity if
> Signal Stance carousels are part of the deliverable.

---

## RSS feeds — known URLs

> *Status: none provided.* The strategy and playbook describe content
> consumption ("review LinkedIn posts," "monitor industry conversation")
> but don't list specific RSS feeds. Treating this as the topic-hints
> path below.

## RSS feeds — topic hints

The Signal Stance reader is a Director-level+ professional in their 30s–50s with calibrated skepticism about career content. The relevance scorer should pick up signal on these areas (derived from the five content pillars):

- Executive career strategy and senior-level career transitions
- Personal branding, professional identity, positioning theory
- LinkedIn platform — algorithm changes, feature releases, behavioral shifts
- Content strategy and editorial craft (not LinkedIn-influencer content)
- AI in professional writing and knowledge work — what it changes, what it doesn't, failure modes
- Recruiting and hiring practices at the senior level (Director and above)
- The professional services industry (consulting, fractional executive market, solopreneur economics)
- Compensation trends for senior professionals and fractional executives
- Workplace and organizational research relevant to senior-career decision-making
- Founder and small-business operator perspectives on visibility and pipeline

> *Avoid:* entry-level career advice feeds, "side hustle" / "passive
> income" content, generic motivational/leadership-influencer content,
> resume template aggregators.

## Feed categories

leadership: Executive leadership, senior management strategy, perspectives from Director-level and above.
careers: Senior-level career strategy, transitions, and positioning. Excludes early-career and entry-level content.
personal_brand: Personal branding theory and practice for serious professionals — substance over performance.
linkedin: LinkedIn platform mechanics, algorithm changes, feature releases, behavioral shifts on the platform.
ai_professional: AI in professional writing and knowledge work — operator-level analysis, not hype or panic.
content_strategy: Editorial content strategy, longform and short-form mechanics, craft observations.
hiring_senior: Recruiting practices specifically at Director-level and above. Distinct from entry-level hiring trends.
fractional_market: The market for fractional executives, solo consultants, and independent professional services.
compensation: Compensation data and trends for senior professionals, with an emphasis on fractional and consultant rates.
workplace_research: Organizational research relevant to senior-career decision-making — not employee-engagement filler.
