# 02 — Voice Samples

The most important file in the intake. The script uses this to
synthesize `prompts/base_system.md` — the persona definition Claude
follows for every generated post. Sample quality bounds output quality:
sparse or generic samples produce a sparse or generic voice profile.

> **How to fill this in:** paste real writing under §Sample posts.
> Add free-form notes under §Voice notes if there's anything that
> wouldn't be obvious from the samples alone. List anti-patterns
> under §Anti-patterns. Leave headings intact.

---

## Sample posts (5–10 required)

Paste 5–10 actual posts this person has written. Raw text only — no
commentary, no "this one was good because…" framing. Separate posts
with `---` on its own line.

More variety is better than more volume:
- Mix categories: a Pattern post + an FAQ post + a Hot Take + a Story.
- Include at least one short post (under 100 words) and one long.
- Include posts that did well *and* posts that flopped — flops reveal
  voice tics that wins can hide.

If fewer than 5 high-quality samples exist, the script will warn and
ask you to either add more or hand-write the voice profile directly.

```
[paste post 1 here]

---

[paste post 2 here]

---

[paste post 3 here]
```

## Voice notes (optional, high-leverage)

Free-form notes about *how* this person writes — anything a reader
wouldn't pick up from samples alone after one pass. Recurring metaphors,
favorite framings, structural habits, words they refuse to use.

The dana-wang base prompt has a "Signature Language" section built
from notes like these:

> *Refers to resumes as "marketing assets" or "business cases for
> hiring you." Frames career moves as portfolio decisions, not job
> hunts. Avoids the word "passionate."*

If left blank, the script infers signature language from samples
alone — usable but shallower.

## Anti-patterns (what they would NEVER post)

Bullet list. The voice profile inverts these into the "Hard Rules"
section that Claude treats as non-negotiable.

> *- Generic motivational language ("you've got this," "believe in yourself")*
> *- Humble brags disguised as gratitude posts*
> *- Closing with "thoughts?" or "what do you think?"*
> *- Engagement-bait questions that have no real answer*

## Topics to avoid (optional)

Subjects this person specifically stays out of, even when adjacent to
their niche. Used by the relevance scorer's `scoring_low` field.

> *- Entry-level resume advice (we serve senior+ only)*
> *- Career change for early-career professionals*
> *- Generic LinkedIn profile tips not tied to executive positioning*
