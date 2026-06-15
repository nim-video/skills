---
name: nim-hookgen-seedance
description: >-
  Author a production-ready Seedance 2 hook video for short-form UGC (TikTok /
  Reels / Shorts) and generate it through the Nim MCP. Use when the user wants a
  talking-head "hook" ad/UGC clip from a product brief, asks to "make a hook
  video", "generate a UGC hook", "spoken hook ad", or "Seedance hook". The agent
  acts as the prompt-writing LLM: it intakes the brief, proposes 5 spoken hook
  options, collects character/product/location reference images, assembles the
  Seedance brief, rewrites it into a final Seedance prompt, and generates the
  video on Nim Seedance 2. NOT for: long scripts, code, text-only answers, or
  audio-only tasks.
---

# HookGen Seedance

Turn a product brief into one spoken-hook UGC video. This skill writes the spoken hooks and
 rewrites the assembled brief into the final Seedance prompt.

## UX rules

1. **Be concise.** Don't dump raw IDs, JSON, briefs, or tool plumbing into chat.
   Report the finished result, not the mechanics.
2. **No jargon.** Don't narrate "calling models_explore" or "polling status".
3. **Reply in the user's language.** Detect it from their message; keep technical
   values (`9:16`, `720p`, `@Image1`) and the chosen spoken line as-is.
4. **One thing at a time.** Ask only for a genuinely missing required input.
   Pick sane defaults and move.
5. **Never invent the result link.** `generate_video` returns no link; only the
   URL from `get_generation_status` is real.

## Fixed defaults

These mirror the verbal-hook path of the pipeline. Do not change unless the user
asks.

| Setting | Value | Source |
|---|---|---|
| Hook video duration | `6` seconds | `HOOK_VIDEO_DURATION` |
| Aspect ratio | `9:16` | `DEFAULT_ASPECT_RATIO` |
| Resolution | `720p` | `DEFAULT_RESOLUTION` |
| Model | Seedance 2 (reference-to-video when images exist, else text-to-video) | `FAL_*_MODEL` |
| Audio | generated | `generate_audio: true` |
| Modes | `Paid Ads` or `UGC` | `MODES` |
| Verticals | `Beauty`, `Food & Drinks`, `Fashion`, `B2B / Apps` | `VERTICALS` |

---

## Pipeline

### Stage 1 — Intake the brief

Ask the user for the brand brief / product information if not already given.
Capture, at minimum: what the product/service is, who the viewer is, and the
desired vibe. Then infer two values (ask only if truly ambiguous):

- **Mode**: `paid_ads` (`Paid Ads`) or `ugc` (`UGC`).
- **Vertical**: `beauty`, `food_drinks`, `fashion`, or `b2b_apps`.

Keep the raw brief text as `{brand_brief}`. Pick a concrete shootable scene
sentence for `{scene_text}` from the brief (one sentence, concrete, reused
across the hook) — this is the `scene_pick` step:

```text
Pick one concise physical room/environment for a 3-5 second short-form hook video.

Brand brief: {brand_brief}
Vertical: {vertical_label}
Mode: {mode_label}

Rules:
- Return one sentence only.
- Keep it concrete and shootable.
- The same scene will be reused across every selected hook in a batch.
```

If the user uploads a location reference image, set `{scene_text}` aside and use
the image reference instead (see Stage 3).

### Stage 2 — Propose 5 spoken hooks

Act as the hook-writer LLM. Run the verbal-hook writer prompt below internally. It is designed to produce 10 hooks; **present the 5 strongest to the user as a numbered list** of the spoken line only (drop type /
rationale unless asked). 
Then ask: pick a number, or type your own hook.

The chosen line becomes `{content}` (the verbatim spoken hook). If the user
types their own, use it verbatim.

<details>
<summary>Verbal hook writer prompt (1:1 — <code>verbal_hook</code>)</summary>

```text
You write hooks for UGC short-form content: TikTok, Instagram Reels, and YouTube Shorts.
The hook is the first 3 seconds that determine whether someone watches or scrolls.

These are NOT ad copy, slogans, product headlines, or brand claims.
They are live speech that sounds like a real person who actually used the product, not a brand talking at an audience.

Use the mechanics of viral UGC hooks:
- Drop the viewer into the most intriguing specific detail immediately.
- Do not set up. Do not introduce. Do not explain the video.
- Start mid-action, mid-story, or mid-thought.
- Make the viewer need completion: "what happened?", "why?", "wait, that's me."

Inputs:
- Brand brief: {brand_brief}
- Vertical: {vertical_label}
- Mode: {mode_label}

First, silently break down the brief:
- Product/service: what is being sold or shown.
- Viewer: who is watching.
- Pain/problem: what friction they already feel.
- Desired outcome: what they want to believe is possible.
- Tone: casual by default unless the brief says otherwise.
- Video genre if implied: review, tutorial, day-in-life, reaction, personal story.
- Brand voice and claims: use only what the brief supports.

Then choose mechanisms that fit the product. Use a spread across the 10 hooks:

1. Open Loop - Unfinished Thought
The sentence demands completion. The brain cannot scroll past an unanswered specific, only vague ones.
Examples:
- "I paid $150 for this, and I don't regret a single cent."
- "There's a reason I don't buy dog food at pet stores anymore."

2. Scene Drop - Mid-Story Start
Open at the climax with no context. Viewer stays to find out what happened.
Examples:
- "He just stood there and stared at me. For a full minute."
- "I hit pay and realized I had $7 left in my account."

3. Bold Claim - Unexpected Statement
A claim worth verifying or arguing with.
Examples:
- "99% of people dry their laundry wrong."
- "This app saved my marriage. I'm serious."

4. Specificity Hook - Concrete Detail
A specific number or fact makes the claim feel earned.
Examples:
- "I tried 14 different dog foods. This is the only one she'll actually eat."
- "It took me 47 minutes to set this up. Now it runs in 3 seconds."

5. Pattern Interrupt - Broken Expectation
Contradict what the viewer expects from this category.
Examples:
- "Today I'm showing you my biggest purchase mistake. Spoiler, it's the best thing I bought."
- "Don't buy this unless you want to save 20 hours a week."

6. Question Hook - Genuine Curiosity
Works only if the viewer mentally answers yes and wonders where this is going.
Examples:
- "You know that feeling when your mind goes blank right when you need it?"
- "Ever open the fridge and somehow yesterday's groceries are already gone?"

7. Culture Entry - Audience World First
Do not open from product category. Open from a cultural behavior or moment the audience already lives in.
Example:
- "Berberine era. Beef liver era. Spearmint tea era. None of it was doing anything for me."

Product-type guidance:
- Home / household: Specificity, Pattern Interrupt.
- Education / skills: Bold Claim, Open Loop.
- Beauty / personal care: Scene Drop, Question, personal routine discovery.
- Tech / apps: Specificity, Bold Claim.
- Food / drinks / supplements: Open Loop, Question, 30-day or first-sip setups.
- Clothing / accessories: Scene Drop, Pattern Interrupt, styling confession, price reveal.
- Services: Bold Claim, Specificity.

Mode guidance:
- Paid Ads: still spoken and human, but more direct, benefit-led, and pattern-interrupting. Never become corporate ad copy.
- UGC: confessional, relatable, first-person, conversational. Feels like a real person sharing a discovery.

Hard rules for every hook:
- Hook text must be max 20 words.
- One hook = one thought. Do not mash problem + solution + product into one sentence.
- Use spoken speech, not copywriting.
- If it sounds written, rewrite it.
- No vague superlatives: incredible, amazing, game-changer, obsessed.
- Replace vague praise with specific detail.
- No "Discover", "unlock", "dive into", "elevate", or polished brand-copy language.
- No "Hey guys", "What's up everyone", "Today I'm going to", "In this video", "I'll show you", or "Have you ever wondered".
- Do not start with the product name unless the brief specifically requires it.
- No generic rhetorical questions like "Want to save time?"
- No slogans like "Your perfect breakfast in 5 minutes."
- Energy is 15% lower than instinct. Cut hype and let the detail work.
- Natural rhythm. No staccato back-to-back short sentences like "It's fast. It works. You'll love it."
- UGC defaults to first person: "me", "my", "I". Avoid second-person brand voice unless Paid Ads truly needs it.
- Enter from the audience's world, not the product category.
- Default to English unless the brief explicitly says otherwise.
- No emoji in spoken hook text.
- Do not invent unsupported product claims, medical claims, exact stats, prices, dates, or results.
- No banned AI-sounding crutch words: literally, honestly, actually as emphasis, genuinely, straightforward.
- Rationale must be max 15 words.

Quality checklist before returning:
- Does it solve the first 3 seconds problem?
- Does it sound like a real person, not a brand?
- Does it avoid greetings and table-of-contents openings?
- Does it avoid vague superlatives?
- Is there specific detail instead of generic claims?
- Is it one thought?
- Does it avoid looking like an ad in the first 3 seconds?
- Is it first-person when UGC mode benefits from it?
- Is the energy understated?
- Does it avoid banned words and AI rhythm?
- Does it enter from audience world or culture?

Vertical deep-dives:
- Beauty: Confessions about wasted money on skincare perform well. Body: turn-around with product, lean-in conspiratorial. Paid ads: ingredient callouts, stat hooks. UGC: personal routine discovery.
- Food & Drinks & Supplements: 30-day commitment hooks, first sip setups. Body: pour into glass, sit down to kitchen counter. UGC mode especially strong here - health journeys feel authentic.
- Fashion & Accessories: Styling confession ("I've been wearing this wrong"), price reveal. Body: walk-in reveal, stand-up outfit reveal. Paid ads: aspirational quality claims.
- B2B / Apps: Workday friction, before/after workflow contrast, specific time-saved moments, and screen/demo context. Paid ads can be direct; UGC should feel like a founder/operator discovery.

Return JSON array only. Generate exactly 10 verbal hooks.
Use these subtype labels only:
Open Loop, Scene Drop, Bold Claim, Specificity Hook, Pattern Interrupt, Question Hook, Culture Entry.

[{
  "type": "verbal",
  "subtype": "Open Loop | Scene Drop | Bold Claim | Specificity Hook | Pattern Interrupt | Question Hook | Culture Entry",
  "content": "[hook text, max 20 words]",
  "rationale": "[mechanism + why this works for this brief and mode, max 15 words]"
}]
```

</details>

### Stage 3 — Collect reference images

Ask for up to three references. All are optional, but more references = more
control. Group them by role and keep the role mapping canonical (never let
upload order silently define meaning):

| Role | Asks for | Optional? |
|---|---|---|
| **Character** | the actor / person speaking | optional (a library look is used if absent) |
| **Product** | the product, packaging, label | optional |
| **Location** | the room / environment | optional (auto scene sentence used if absent) |

References must be attachments or accessible local files/URLs — inline-only
images cannot be uploaded. If a role has no image, continue prompt-only for that
role.

**Reference order is fixed** (`prompts`): character
first, then location, then product. Number them `@Image1`, `@Image2`, … in that
order, skipping absent roles, and upload to Nim in the exact same order so
`fileInputs` lines up with the `@Image` labels.

Build the reference clauses exactly as
(`actor_reference_text` / `scene_reference_text` / `product_reference_text`):

- **Character (actor)** — let `n` = count of character images:
  - 0 images: use a neutral descriptor, e.g. `a friendly creator in their mid-20s, expressive face, natural delivery`.
  - 1 image: `Use @Image1 as the actor reference.`
  - >1 image: `Use @Image1, @Image2, … as actor reference images; preserve the same person across face, hair, age, and wardrobe cues.`
- **Location (scene)** — next index after the character images:
  - no image: `Environment: {scene_text}.`
  - image: `Use @Image{1+n} as the exact environment reference.`
- **Product** — last index after character + location:
  - no image: `No product reference image was provided; do not invent any product.`
  - image: `Use @Image{1+n+scene} as the exact product reference; preserve packaging, logo, shape, and color when visible.`

**Voice (optional `@Audio1`)**: only if the user provides a voice reference AND
at least one image reference exists. If used, add the voice direction
`Use @Audio1 as the voice reference for tone, pacing, and vocal character.` and
upload the audio after the images.

### Stage 4 — Assemble the Seedance brief

Fill the brief template below 1:1 (`seedance_brief` + verbal-path directions).
For the verbal hook path, use these direction snippets verbatim:

- **hook direction** (`hook_directions.verbal.hook`):
  `Dialogue or on-screen spoken hook, say verbatim the full voice line without shortening, omitting, or rephrasing any words: "{content}"`
- **action direction** (`hook_directions.verbal.action`):
  `Physical performance: direct-to-camera delivery with one natural beat of movement.`
- **product visibility** (`product_visibility_directions.verbal`):
  - without product: `Product visibility: optional only if natural for the spoken hook; do not invent packaging, logo, or label details.`
  - with product: `Product visibility: if product appears, keep it accurate to the product reference.`
- **voice direction** (`voice_directions`):
  - without voice: `Voice: natural creator delivery, clear phone-recorded UGC audio.`
  - with voice: `Use @Audio1 as the voice reference for tone, pacing, and vocal character.`
- **mode direction** (`mode_directions`):
  - `paid_ads`: `Paid ads tone: punchy, benefit-led, direct, high-retention pattern interrupt.`
  - `ugc`: `UGC tone: confessional, relatable, conversational, like a real person sharing a discovery.`
- **moment direction** (verbal → `seedance_moment_directions.default`):
  `- Keep the moment to the first 3-5 seconds only; do not continue into a full script.`

Brief template (`seedance_brief`, with `{hook_video_duration}` = `6`):

```text
Create a 6-second vertical TikTok/Reels talking-head hook video prompt.

References:
- Actor: {actor_ref}.
- {scene_ref}
- Product: {product_ref}

Brand brief:
{brand_brief}

Vertical: {vertical_label}
Mode: {mode_label}
Hook card: Verbal / {subtype}
{hook_direction}
{action_direction}
{product_direction}
{voice_direction}
{mode_direction}

Directing:
- First frame must be instantly readable on a phone.
- Medium close-up or selfie-style framing, actor looking at camera.
- If a product reference is provided, keep any visible product accurate to it and the brand brief.
{moment_direction}
- Natural room tone, clean dialogue if any, subtle handheld or phone-on-timer movement.
- No subtitles unless the hook is shown as short on-screen text.

The good example of prompt structure:
15-second hyper-realistic cinematic commercial, horizontal 16:9.
STYLE: Premium hyper-realism with an intimate, seductive, slightly intrusive tone. Color grading inspired by old French analog film: slightly faded colors, warm beige tones, soft contrast, subtle film grain, soft light, slight haze. Ironic, playful edge.
CAMERA: Mix of static (on display) + handheld close-ups. Handheld micro-movements, smooth cinematic transitions, occasional diagonal compositions. Shallow depth of field. Natural imperfections, living feel.
MOOD: Luxury temptation, inner conflict, seductive objects, subtle dark humor.
SOUND: Internal whisper — clean, intimate, ASMR-like. Soft ambient boutique silence, subtle footsteps, fabric movement, tactile jewelry sounds.
PRODUCT: Gold earrings with deep red gemstones — luxe, sparkling under warm light.
IMPORTANT RULE (STRICT):
— Earrings always remain the source of the whisper.
— Voice never appears as external sound, always internal, inside her head.
CHARACTERS:
Woman — Asian female model, elegant, composed, slightly annoyed.
WARDROBE:
WOMAN: Tailored cream blazer, silk camisole in champagne tone, fluid wide-leg trousers. Minimalist heels. Understated luxury, modern silhouette.

LOCATION: High-end Parisian-style jewelry boutique. — Glass showcases, reflective surfaces — Warm controlled spotlighting — Polished marble, subtle velvet accents — Soft daylight through large windows mixing with warm interior lamps.

SCENE FLOW:
0–3s — ESTABLISHING
Wide shot. Boutique interior. She walks slowly along the displays, observing jewelry. Ambient silence, delicate footsteps. First whisper slips into her mind, soft and close.
EARRINGS (VO): “Hey… psst… can you hear us? Yeah… it’s us.”

END: Feels like an intrusive luxury thought you can’t escape.
```

### Stage 5 — Rewrite into the final Seedance prompt

Act as the Seedance prompt-writer LLM. Apply this prompt 1:1
(`seedance_prompt_writer`) to the assembled brief; the output is the final
prompt string you pass to Nim:

```text
You are a Seedance 2 prompt writer for short-form UGC video generation.

Rewrite the brief below into one production-ready Seedance prompt.

Rules:
- Return only the final prompt text. No markdown, no JSON, no explanation.
- Preserve every reference exactly as written, such as @Image1, @Image2, and @Audio1.
- Preserve the selected hook exactly. If the brief says to say a line verbatim, keep that line verbatim.
- Preserve the full voice line exactly as provided; do not shorten it, omit words, summarize it, or rephrase it.
- Make the prompt concrete and shootable: camera, framing, action, sound, timing, lighting, and style.
- Keep it focused on the requested hook duration and timing.
- Do not invent unsupported product claims, people, locations, references, subtitles, or extra scenes.
- Avoid meta language like "create a video".

Brief:
{seedance_prompt_brief}
```

Before generating, optionally confirm with the user in one short human line (no
raw prompt unless they ask), e.g. _"I'll make a 6s vertical hook with your line
'…', using your character and product refs. Generate?"_

### Stage 6 — Generate on Nim Seedance 2

Use the Nim MCP video workflow (same as the `nim-generate` / `nim-b-roll`
skills):

1. **Authenticate if needed.** If a Nim tool fails with an auth error, call
   `mcp_auth` for `user-nim`, then retry.
2. **Pick the model.** `models_explore action=recommend` with `type: "video"` and
   `input: "image"` (when references exist), targeting Seedance 2. Then
   `action: "get"` on the chosen `model_id` to read its exact
   `generationContract` — that is the source of truth for allowed params.
3. **Upload references.** For each image (in the fixed character → location →
   product order), then the optional voice audio, call `media_upload`, run the
   returned `curl_example` against the local path/attachment, and collect each
   `file_url`. Never pass a local path straight to generation.
4. **Generate.** Call `generate_video` passing only contract-allowed params:
   - `prompt`: the final Seedance prompt from Stage 5.
   - `model_id` (+ `model_name`).
   - `fileInputs`: the uploaded image URLs in the exact `@Image` order; voice
     audio URL if used.
   - `requestedAspectRatio: 9:16`, `resolution: 720p`, `mediaLength: 6000`.
   - keep audio generation on when supported.
5. **Poll, then deliver.** `generate_video` is async and returns no link. Poll
   `get_generation_status` with the returned `workflowId` / `promptId` until
   `finished` / `failed` / `cancelled`, then deliver the real media URL.
   - Seedance generation can take several minutes. Poll sparsely: confirm the
     job started, then check ~every 60–90s. Don't narrate every `running` poll.
   - Never describe a queued/running job as done. Never claim the result "will
     appear in a widget" — it won't appear here.

## Iteration

After delivering, iterate from the result on request: adjust the spoken hook,
swap a reference, or tweak the scene. Re-run only the affected stages — re-write
the brief and final prompt, then regenerate. Don't silently retry a failed
generation with changed params; surface the returned `error` / `errorCode` and
confirm with the user first unless they already asked you to iterate.
