<!-- TEMPLATED: Identity references use {{variable}} placeholders from business_config.json -->

## Carousel Content: Myth vs Reality Format

Generate structured content for a multi-slide {{platform.name}} carousel PDF debunking common misconceptions.

### Output Format (strict — follow exactly)

TITLE: [Provocative title about misconceptions]
SUBTITLE: [Optional one-line subtitle]
MYTH 1: [Common misconception as people actually state it]
REALITY 1: [Expert correction, 1-2 sentences, under 35 words]
MYTH 2: [Common misconception]
REALITY 2: [Expert correction, under 35 words]
...continue for 4-6 myth/reality pairs...
CTA: [Specific call-to-action related to the topic]

### Rules

- Exactly 4-6 myth/reality pairs
- Myths must be things {{owner.audience}} actually believe (not strawmen)
- State myths the way people actually say them
- Realities must be specific and backed by expertise
- Tone: corrective but not condescending
- Ground in {{owner.name}}'s expertise: {{owner.specializations}}
- CTA must be specific to the topic

### Voice rules for slide format

This is not a text post. Every word must earn its place on the slide. Apply Signal Stance's voice with these myth/reality-specific adjustments:

1. **Myths must be ones the senior-pro / fractional / founder audience actually repeats.** Not strawmen. The reader should recognize themselves in 2–3 of the myths. Skip any myth that's clearly aimed at entry-level professionals.
2. **State the myth the way people actually say it.** "You need to post on LinkedIn every day" — not "the belief that consistent posting builds visibility." Quote the actual phrasing the audience hears from coaches, articles, and well-meaning peers.
3. **Realities commit to the read.** No "well, it depends." Each reality names the specific reason the myth is wrong and what's true instead. Asymmetric — leans toward the dissent the way Sample C does.
4. **Corrective, not condescending.** The myth is believed because the advice industry is full of conflicting advice — many of these myths come from sources that were partly right at one point and got copied without nuance. The reality respects that, then corrects it.
5. **No engagement bait.** No "Which one surprised you?" / "Comment your number." The carousel earns its weight through the realities landing.
6. **No AI's-favorite-words in realities.** Avoid "crucial," "delve," "tapestry," "myriad," "navigate the landscape." Cliches *can* appear in the myth column — that's what's being corrected.
7. **No "I use AI" framing.** If a myth/reality touches AI, frame patterns observable in the corpus or in others' work — never personal practice.
8. **CTA points to signalstance.com.** Per Signal Stance's mythreality default: "More writing at signalstance.com."

### Example output (for calibration)

```
TITLE: 5 LinkedIn Myths Senior Professionals Still Repeat
SUBTITLE: Common advice that quietly breaks at the senior level.

MYTH 1: You should post on LinkedIn every day to build your brand.
REALITY 1: Daily posting only works above a quality threshold. Below it, more posts hurt you — the algorithm learns your audience scrolls past, and they do.

MYTH 2: Just be authentic — that's what gets engagement.
REALITY 2: "Authentic" is the laziest piece of LinkedIn advice. Authenticity without strategy reads as oversharing. The voice that works is honest and chosen — picked deliberately for a specific reader.

MYTH 3: Your resume should tell your story.
REALITY 3: A resume is not autobiography. It's an argument for one specific role, scanned in six seconds. "Telling your story" is what costs senior professionals interviews.

MYTH 4: AI resume tools optimize your resume for better results.
REALITY 4: Most AI resume tools standardize phrasing toward a generic norm — the opposite of what wins at the senior level, where positioning and specificity are what get the interview.

MYTH 5: Your LinkedIn headline should describe your current job title.
REALITY 5: A title belongs in the experience section. The headline is positioning real estate — name the work, the buyer, or the specific value, not the job title the algorithm already knows.

CTA: More writing at signalstance.com
```

Do not include anything before "TITLE:" or after the CTA line in actual generations. Output only the structured content.
