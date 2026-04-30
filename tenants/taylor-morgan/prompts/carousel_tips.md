<!-- TEMPLATED: Identity references use {{variable}} placeholders from business_config.json -->

## Carousel Content: Numbered Tips Format

Generate structured content for a multi-slide {{platform.name}} carousel PDF. Each tip gets its own slide.

### Output Format (strict — follow exactly)

TITLE: [Must include a specific number, e.g., "7 Mistakes..." or "5 Ways..."]
SUBTITLE: [Optional one-line subtitle]
TIP 1 HEADLINE: [6 words maximum]
TIP 1 BODY: [1-2 sentences, under 30 words]
TIP 2 HEADLINE: [6 words maximum]
TIP 2 BODY: [1-2 sentences, under 30 words]
...continue for 5-7 tips...
CTA: [Specific call-to-action related to the topic]

### Rules

- Exactly 5-7 tips
- Title MUST include the specific number
- Headlines: 6 words maximum — punchy and scannable
- Bodies: under 30 words — one key insight per tip
- Order by impact (most impactful first)
- Use {{owner.name}}'s voice and expertise
- CTA must be specific to the topic, not generic

### Voice rules for slide format

This is not a text post. Each tip becomes a visual slide with large text — every word must earn its place. Apply Signal Stance's voice with these slide-format adjustments:

1. **Direct, editorial, no throat-clearing.** Headlines like "Stop listing responsibilities" or "Cut the strategic-leader opener" — not "Why your resume isn't working." Verbs and specifics over abstractions.
2. **Asymmetric — commit to the read.** Each tip should commit to a position rather than hedging. "Quantify or cut it" beats "Consider quantifying when possible."
3. **Senior-professional / fractional / founder calibration.** Examples and reference points must fit the audience tier — Director-level resumes, fractional pricing pages, executive bios, LinkedIn profiles for Senior VP candidates. No entry-level framing.
4. **No engagement bait.** No "Which one are you guilty of?" / "Comment your number." The carousel earns its weight from the tips landing, not from prompting reactions.
5. **No AI's-favorite-words.** Avoid "crucial," "delve," "tapestry," "myriad," "navigate the landscape." If a tip uses one, rewrite.
6. **No "I use AI" framing.** If the carousel topic touches AI, frame patterns observable in the corpus or in others' work — never personal practice.
7. **CTA points to signalstance.com.** Per Signal Stance's default: "More writing at signalstance.com" (or topic-specific variant: "Read the longer essay at signalstance.com/blog"). Do NOT use "Follow for more" or generic engagement asks.

### Example output (for calibration)

```
TITLE: 6 Signals a LinkedIn Profile Is Doing the Wrong Job
SUBTITLE: A senior-pro profile should land meetings, not just describe a job.

TIP 1 HEADLINE: Named the title, not the work
TIP 1 BODY: "VP, Product" describes the role. "Product leader who turns roadmap chaos into shipping velocity" describes the work — and earns the click.

TIP 2 HEADLINE: About section reads as biography
TIP 2 BODY: A senior About section should argue, not narrate. Open with the specific value the reader gets from the next conversation, not "I am a passionate leader with 15+ years."

TIP 3 HEADLINE: Featured section is empty or random
TIP 3 BODY: This is the credibility surface above the fold. Curate it: a recent talk, a case study, a piece of writing — not the auto-pulled latest post.

TIP 4 HEADLINE: Skills list reads like job board
TIP 4 BODY: 50 generic skills signals nothing. 10 specific ones — endorsed by people who'd actually know — signals positioning.

TIP 5 HEADLINE: Recommendations all sound the same
TIP 5 BODY: "Great to work with" is filler. Ask recommenders for one specific moment where the work changed an outcome. That's the recommendation a serious reader believes.

TIP 6 HEADLINE: No clear next step
TIP 6 BODY: A serious profile makes it obvious how to engage — book a call, read more, see the work. If a hiring manager or prospect has to guess, they leave.

CTA: More writing at signalstance.com
```

Do not include anything before "TITLE:" or after the CTA line in actual generations. Output only the structured content.
