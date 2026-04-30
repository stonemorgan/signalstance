# Tenant Intake Template

Drop-in starter for onboarding a new tenant. Fill in these four
files with everything specific to a person/business, and a future
`intake_tenant.py` script will read this directory and produce a
ready-to-run tenant under `tenants/<name>/`.

> **Status:** intake schema only. The extraction script does not
> exist yet — these files are the contract it will read against.

## Workflow (planned)

```
1. Copy this directory to a working location:
     cp -r tenants/_intake_template intake/<tenant-name>

2. Fill in the four markdown files for the new tenant.

3. Run the intake script:
     python intake_tenant.py <tenant-name> --from intake/<tenant-name>

4. Script produces tenants/<tenant-name>/ with:
     - business_config.json   (extracted from intake docs)
     - feeds.json             (URLs, or proposed from topic hints)
     - prompts/base_system.md (synthesized from voice samples)
     - prompts/*.md           (copied from _template, lightly tuned)

5. Script prints a readiness report flagging anything auto-generated
    or sparse. Review before running the tenant in production.
```

## Files

| File | What it captures | Maps to |
|---|---|---|
| `01-identity.md` | Name, business, niche, audience, credentials | `business_config.owner.*`, `scoring.*` |
| `02-voice-samples.md` | Sample posts, voice notes, anti-patterns | `prompts/base_system.md` |
| `03-content-rhythm.md` | Categories, weekly cadence, CTAs | `business_config.content.*`, `business_config.schedule.*` |
| `04-brand-and-feeds.md` | Colors, fonts, RSS feeds, feed categories | `business_config.brand.*`, `feeds.json`, `business_config.feeds.categories` |

## Required vs. optional

**Required for a usable tenant:**
- `01-identity.md` — all sections except `Client outcomes`.
- `02-voice-samples.md` — at least 5 sample posts under §Sample posts.

**Optional / `auto` accepted:**
- `02-voice-samples.md` — voice notes, topics-to-avoid.
- `03-content-rhythm.md` — entire file can be `default` to keep
  template categories, schedule, and CTAs.
- `04-brand-and-feeds.md` — both halves accept `auto`.

A tenant with only the required sections filled in will run, but the
voice profile will be shallower and the feed list will be empty until
RSS sources are added manually.

## Conventions

- **Headings are load-bearing.** Don't rename the `## Section` headings
  in any file — the script keys off them. Subheadings (`###`) are
  parsed where indicated.
- **Italicized examples are placeholders.** Delete them when filling
  in your own content. They're prefixed with `> *` so they render as
  italic blockquotes.
- **`default` and `auto`** are the two reserved values: `default`
  means "keep the `_template/` value for this field," `auto` means
  "let the LLM propose a value."
