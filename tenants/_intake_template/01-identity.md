# 01 — Identity

Who this person is and what they do. The intake script extracts the
fields below into `business_config.json` (`owner.*` and `scoring.*`).

> **How to fill this in:** replace the prompt text under each heading
> with your own answer. Leave headings intact — the script keys off them.
> Examples (in italics) come from the `dana-wang` tenant; delete them
> before saving.

---

## Name & Business

Full name, professional title, business name. One line each.

> *Name: Dana Wang*
> *Title: Certified Professional Resume Writer (CPRW)*
> *Business: Raleigh Resume*

## Links

LinkedIn URL plus any other public profile or website. One per line.
Used in `owner.url` (primary link) and stored verbatim — no scraping.

> *linkedin.com/in/danaxwang*

## Credentials

Bullet list. Certifications, degrees, professional memberships. The
script copies these into `owner.credentials` and into the voice profile.

> *- CPRW certification via PARWCC*
> *- MA from UNC Chapel Hill*

## Niche (one paragraph)

What this person does, in one paragraph. This text is quoted back to
Claude when scoring articles for relevance, so be specific about
domain and the *kind* of work — not just the title.

> *Executive resume writing, LinkedIn optimization, ATS compliance,
> career coaching for senior professionals.*

## Audience

Who this person writes for. Two parts:

1. One-line description of the audience.
2. 3–5 example job titles.

> *Description: VPs, Directors, C-suite leaders, Board members.*
> *Examples: VP of Marketing, Director of Engineering, CFO, Board Director.*

## Specializations

Bullet list — narrower and more concrete than the niche paragraph.
These show up in the voice profile as "Specializes in" and help the
relevance scorer distinguish "directly applicable" from "tangentially
related."

> *- executive and board-level resumes*
> *- LinkedIn profile optimization*
> *- ATS compliance*
> *- federal resumes*
> *- salary negotiation positioning*

## Client outcomes (optional)

One line on the kind of results clients see. Used for tone calibration
in the voice profile (specific outcomes → more grounded posts).

> *Fortune 30 companies, high-growth startups, Board seats.*
