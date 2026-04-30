# 03 — Content Rhythm

What this person posts and when. Drives `business_config.content.*`
and `business_config.schedule.*`.

> **How to fill this in:** the content categories and weekly schedule
> in the existing `_template/business_config.json` are sensible
> defaults. If those work, write `default` under any section and the
> script keeps the template values. Customize only what differs.

---

## Content categories

The template ships with four buckets: **Pattern**, **FAQ**,
**Noticed**, **Hot Take**. For each, write one sentence on what that
bucket means *for this person*. Skip categories that don't fit by
writing `skip` — the script drops them from the UI.

### Pattern
What recurring thing in this person's work or industry would they
share under "I keep seeing..."?

> *Mistakes I see across executive resumes — the same gaps that show
> up in 80% of senior-level submissions.*

### FAQ
The "Client asked..." bucket. What questions does this person field
constantly that would make good content?

> *Questions clients ask in discovery calls — pricing, ATS myths,
> "do I need a cover letter?"*

### Noticed
The "Just noticed..." bucket. What does this person spot that others
miss?

> *Subtle shifts in recruiter behavior, LinkedIn algorithm tells, ATS
> changes that affect senior candidates.*

### Hot Take
The "Hot take..." bucket. What contrarian opinions does this person
hold that they're willing to defend?

> *Opinions on resume length, AI-generated cover letters, why "passionate"
> is a tell, why some advice in this industry is just wrong.*

## Posting cadence

Which weekdays does this person post, and what content type fits
each day? Format: `Day — Content Type. "One-line suggestion prompt
shown in the calendar UI."`

Default rhythm (Mon–Fri, weekdays only) lives in
`_template/business_config.json`. Override per-day if needed; write
`default` to keep the template.

> *Monday — Educational / Pattern. "Share a recurring mistake you see
> in exec resumes."*
> *Tuesday — Tactical Tip. "Share a specific tip about resumes,
> LinkedIn, or job search."*
> *Wednesday — Deep Dive / Story. "Tell a story or go deeper with a
> client example."*
> *Thursday — Thought Leadership / Hot Take. "Share a contrarian
> opinion."*
> *Friday — Quick Win / Encouragement. "Share a quick tip that builds
> confidence."*

## Posting times

Time of day per posting weekday, plus timezone. Used by the calendar
UI and any future scheduler.

> *Mon 8:30 AM, Tue 9:00 AM, Wed 8:30 AM, Thu 9:00 AM, Fri 10:00 AM
> — EST*

## Default CTAs (optional)

End-of-post call-to-action for each carousel template
(`tips`, `beforeafter`, `mythreality`) plus a `general` fallback.
Leave any field blank or write `auto` to let Claude propose one
from the niche.

> *tips: "Follow for more executive career strategy"*
> *beforeafter: "Save this for your next resume update"*
> *mythreality: "Follow for more myth-busting resume strategy"*
> *general: "Follow for more career strategy"*

## Platform settings (optional, almost never customized)

Defaults: LinkedIn, 150–300 words per post, 1080×1080 carousel
slides. Override only if this tenant publishes elsewhere.

> *Platform: LinkedIn*
> *Post word range: 150–300*
> *Carousel dimensions: 1080×1080*
