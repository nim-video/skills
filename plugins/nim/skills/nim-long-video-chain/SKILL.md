---
name: nim-long-video-chain
description: >-
  Use when the user asks for a video longer than Nim's single-clip cap — a
  duration roughly between 15 seconds and 5 minutes ("1 minute video", "30
  second video", "90 sec clip", "2 minutes long"), or asks for a format that
  implies more than one clip's worth of content without giving an exact
  number: "YouTube Shorts", "Reels", "TikTok", "a short film", "an episode",
  "a series". Nim's Seedance video generation is maximum 15 seconds per
  clip. This skill is NOT for single clips of 15 seconds or less — use
  nim-generate / nim-b-roll-seedance / nim-hookgen-seedance for those.
---

# Long Video Chain (Nim multi-segment Seedance)

Turn a "make me a 1-minute video" request into a chain of 15-second Nim Seedance2 clips that tell one continuous story, then hand the generated videos to the user, offering FFMpeg stitching script.

## When this triggers

- An explicit duration longer than 15 seconds and up to roughly 5 minutes:
  "1 minute video", "30 second clip", "2 minutes", "90 sec".
- Format names that imply longer-than-one-clip content without a stated
  number: "a short film", "an episode", "a series", "a multi-part video".
- A brief whose described content clearly won't fit one 15-second clip (a full story arc, several distinct scenes, a multi-beat product story), even if the user never states a duration — infer that it needs more than one segment and confirm the assumed length before planning further.

Requests for 15 seconds or less stay on the normal single-clip skills
(`nim-generate`, `nim-b-roll-seedance`, `nim-hookgen-seedance`). Don't chain
for those.

## Fixed defaults

| Setting | Value | Notes |
|---|---|---|
| Per-segment duration | `15` seconds (`mediaLength: 15000`) | Nim's current single-generation cap. |
| Max segments generated per batch | `3` | Never queue more at once, regardless of total segment count. |
| Aspect ratio | `9:16` | Default for Shorts/Reels/TikTok; ask if the target platform differs. |
| Model | Seedance2 | Regular, not 'Fast' version! |
| Stitching | User-side, via `ffmpeg` | Never merged on our side — see Step 6. |


## Step 1 — State the limit, then ask questions.

Before writing any prompt or touching Nim, tell the user plainly, in their own input language:

- Interact with user as a story writer and narrative director, who is responsible for the output visuals and who tend to help bring the user idea to life in best way possible using your knowledge (and this skill).
- The single Nim video generation is **15 seconds** using Seedance 2 model (not 'Fast' version of it).
- A longer video is made as a **sequence of 15-second clips** that continue one story, which can then be joined into one file.
- Ask whether they want to proceed this way.

Example (en):

> Current technical limitation is a 15 seconds per one video. I can help to build a longer video as a sequence of 15-second clips that shares the same story, and smoothly developing the scenario across the multiple video-clips.

Do not plan segments or call Nim until the user agrees. If they'd rather have something that fits one clip instead, drop this skill and treat it as a normal single-clip request.

**Questions to ask:**
1. If the user is acknowledged about the video limitation and that the proceeding will produce multiple video generations.
*yes/no if it fits for the current client — a simple two-option question ("Let's do it as multiple videos" / "Let's shorten the scenario down to fit idea into one video")*
2. Draft version (480p) or Quality version (720p) video is required.
3. Style or purpose, 9:16 vertical or 16:9 horizontal aspect ratio (If those were not provided in the user input).
{writing and generation steps}
4. Ask if clips stitching script for FFMpeg is required after the generation process is complete and user is satisfied.

Use `ask_user_input_v0` to ask questions.

## Step 2 — Turn duration into a segment plan

```
segment_count = ceil(requested_duration_seconds / 15)
```

- Each segment is a fixed 15s Nim clip, so the assembled runtime is always a multiple of 15s. When the requested duration isn't ("40 seconds" → 3 segments → 45s), mention the rounding once, briefly, and move on. Exact multiples ("1 minute" → 4 segments → 60s) need no comment.
- If `segment_count` is large (rough guide: more than ~8 segments, i.e. above ~2 minutes of story), say so and confirm the user still wants the full length — generation time and Nim credits scale linearly withsegment count. This isn't a hard blocker, just something to flag once; batching (Step 4) keeps it manageable either way.
- Treat "5 minutes" (20 segments) as the practical ceiling for this workflow. Above that, say this approach isn't a good fit and suggest trimming the target duration or splitting the idea into separate videos.

## Step 3 — Write one continuous multi-segment scenario

This step produces `segment_count` complete Seedance prompts from the user's idea. 

Use `ask_user_input_v0` to ensure/define desired video style and mood (e.g., if the video is an AD or UGC or cinematic series) to use it as primary driver while writing scenes. 

Write the entire story as one continuous, seamless shot list first, as if it were a single long take with no segment boundaries — do not let the number of segments dictate the number of acts or beats. Only after the full continuous shot list exists, cut it into segment_count pieces wherever the 15-second/shot-count limit forces a cut, even mid-beat or mid-act; a beat, an act, or even a single character's action may span across a segment boundary or shift earlier/later than a round act-per-segment split would suggest.
Author them internally following the rules below, then show the user a short plain-language summary of the planned segments (one line each) — not the raw prompts, unless they ask to see the full text.

Confirm the built scenario with user before proceeding with generation

Summarize the continuous plan, not the segments as separate stories: describe the story once as a single throughline, then note only where it gets physically cut into clips (a timestamp-like marker, not a new scene/act). Avoid describing each clip as if it were its own self-contained scene (e.g. never "Clip 1: her day life / Clip 2: her night life") unless the user's own idea is literally structured that way — the split point should fall wherever the continuous story naturally lands at 15s, not at a convenient narrative boundary.

Use `ask_user_input_v0` to proceed with generation or adjust details. 
Proceed to Generation step (Step 4) ONLY if user agrees with the outlined plan.

### 3.1 Role and Story structure across segments

When writing the scenario and the segment prompts, act as a video director and montage editor who uses modern and innovative techniques to create engaging, visually appealing videos — drawing on the techniques of Luc Besson, Christopher Nolan, Alberto Mielgo, Patrick Clair & Raoul Marks, Tarsem Singh, Denis Villeneuve, Quentin Tarantino, Martin Scorsese, Bong Joon-ho, Park Chan-wook, Stephen Norrington, Robert Valley, David Fincher, M. Night Shyamalan, Ridley Scott.

Build the narrative from the user's (possibly sparse) input using the three-act structure, mapped onto `segment_count` positions instead of onto shots inside a single clip:

- Exposition — an introduction to the characters and the world.
- Rising action — the event that triggers the main conflict.
- Development — a series of obstacles and struggles.
- Climax — the peak of tension.
- Resolution — the resolution of the conflict and the conclusion.

Build the shared exposition following 3.2 below.

### 3.2 Shared exposition (written once, reused everywhere)

Before any segment prompt, define the shared world once, in three sections.
Write each one with the same verbatim, concrete-detail discipline used for shots (3.3) — describe only what would actually be visible on screen, never a figurative or emotional shorthand a video model would render literally ("fire in her eyes" becomes literal fire). Each section should read as directly usable image/video-generation description, not as a summary or a mood board:

- **General exposition** (2-4 sentences) — name what the piece is (genre, format, register — e.g. "anime intro", "noir short", "product spot"), its energy level, and the overall visual framing/choreography style that will recur across every segment. This is the one-line pitch a director would give before blocking anything, made concrete enough to constrain later
  choices.
- **Environment** (2-5 sentences) — the physical world: location(s), background elements, atmosphere (weather, particles, light quality), color palette, and any recurring visual motifs (symbols, textures, props in the background). Describe it as a place a camera could actually be set up in, not as a vibe.
- **Characters look** (1-3 sentences per character) — for every character who appears anywhere in the chain, concrete wardrobe, physical traits, and posture/energy. If the user supplied `@Image` references, follow 3.5: state only *what* each reference is (role, name) — never redescribe physical traits already contained in the image, since conflicting text description will corrupt the image reference instead of using it.

Every segment prompt carries this shared context forward **unchanged** — each segment is a separate Nim generation with no memory of the others, so the shared block is the only thing holding the world together. A segment may add environment detail specific to its own beat (3.3's "plus anything specific to this beat"), but it must never contradict or rewrite the shared general exposition or an established character's look — extend, don't replace.

### 3.3 Rules for writing each segment prompt

Each segment is its own **complete, self-contained definition of exposition, scenes, shots and subshots** — never a single shot fragment that assumes/reference context from another segment. 
A single segment is a 15-second *video*, and a video is made of **multiple shots**, exactly like the reference example (the "office warriors" intro).

**A segment must contain multiple scenes and multiple shots, never 1.** 
A single shot held for the full 15 seconds reads as static and undermines the entire point of chaining clips together .
Fine pace is 3-4 scenes with 2-4 subshots per scene within a single 15 seconds segment of the video; 
Faster pace can do up to 12 subshots total.

**Example Structure:**
```
SegmentA
 - Scene 1
   - <subshot>
   - <subshot>
 - Scene 2
   - <subshot>
   - <subshot>
   - <subshot>
   - <subshot>
 - Scene 3
   - <subshot>
 ...
```

One scene in a single segment(video) could share multiple subshots (e.g., Scene in flat displayed in 2 shots: from kitchen and from bedroom, with 3 subshots each, displaying the actions happening from different angles and perspectives; Resulting in total 6 subshots).
More shots and more subshots per segment will make the scene more dynamic, while less shots produces slower pace videos;
Never ship a segment with only one shot.

Structure every segment prompt with these sections:

- general exposition (shared block, verbatim)
- environment (shared block, verbatim, plus anything specific to this beat)
- characters look (shared block, verbatim for every character on screen)
- shots: 3-7 numbered shots, each as `<shot type, angle>` followed by its description — shot type first, then what happens in this shot. Vary shot size and angle between consecutive shots (e.g. wide → medium → close-up, or medium → low-angle → over-the-shoulder) the same way the reference example escalates from wide establishing action into a tighter, more
  dramatic final beat.

Each shot within the segment must still read as the next logical beat of that segment's action — building within the segment the same way segments build across the whole chain (Step 3.3). Don't repeat the same action from a different angle; each shot should advance the moment forward.

Shot-writing rules (apply inside every shot):

- 2 sentences per each new shot/perspective. Pay attention to directions and
  composition.
- Write verbatim: describe only what is literally on screen during the shot.
  Bring emotions to the characters through facial expressions and physical detail. Avoid figurative emotional descriptions like "fire in her eyes" — the model takes these literally and her eyes will be set on fire. Definition of emotions characters should product can be defined with emojis: model is clearly undestands it.
- Always pay attention to: emotions on the face, the facial expressions, lens and shot type selection, camera movement if required, shots and scenes separation only if required.
- Phrasing like "Camera drifts behind and beside her, maintaining constant distance as she trudges through snow leaving footprints, sparse birch trees flanking the path." is the target register — it gives strong dynamic for handheld tracking-type shots.
- One shot = one physically plausible camera move = one readable action with a beginning/middle/end.
- Do not include timestamps inside the prompt text.
- No voice-over or music unless the user asked for it.
- Output in English (regardless of the conversation language), minimal markdown, no preambles or opinions — just the final prompt text per segment, delivered as clearly delimited blocks
  (`SEGMENT 1 (0:00-0:15)`, `SEGMENT 2 (0:15-0:30)`, …; the timing lives in the block label only, never inside the prompt).

### 3.5 Reference image rules (`@Image` tags)

- Do not add `@` references unless the user asked to or actually provided
  reference images.
- Every referenced image already contains the required visual details, so never re-describe its visuals in text — only state *what* it is (what person, what object). E.g. if `@Image1` is an old woman with dark hair, writing "young woman with red long hair @Image1" will break the output; the proper use is just "woman @Image1".
- Usually a single reference image is provided (a product or a person); use it as `@Image1` unless the user assigns roles differently.
- Use `@CharacterName`, `@LocationName`, `@PropName` element tags for named entities. Preserve identity, outfit, proportions, location geography, prop geometry, and color palette everywhere a tag appears.
- Keep every tag **identical, word-for-word, across every segment prompt**. Tag consistency is the main mechanism holding identity, wardrobe, and location together across separate generations.

### 3.6 Per-segment craft template

For each segment, define these layers explicitly (skip a layer only when it's genuinely irrelevant to the beat):

- **camera** — mount, camera height, movement, operator language, parallax, occlusion, screen direction.
- **optics** — focal length, lens family, aperture/T-stop, filtration, focus behavior, bokeh, flare, falloff.
- **lighting** — motivated key/fill/back/rim/practicals, modifiers, grip tools, contrast ratio, falloff, color temperature, negative fill or bounce.
- **constraints** — close every segment prompt with: no scene change, no extra characters, no fake text/logos, no distorted hands, no melting props, no plastic skin, no impossible movement.

### 3.7 Professional vocabulary

Draw camera, lens, lighting, and texture wording from these blocks — they are the register Seedance responds to best:

- **camera packages**: large-format digital cinema body, Super 35 digital cinema body, Super 16 inspired digital capture, compact documentary cinema body, bodycam simulation, dashcam simulation, consumer camcorder simulation, motion-control tabletop rig, vehicle suction mount, Technocrane, Steadicam, gimbal, shoulder rig, locked-off sticks, fluid-head tripod, slider, low dolly, hostess tray car mount, pursuit vehicle rig.
- **shot sizes and angles**: establishing wide, medium-wide, medium close-up, close profile, extreme close-up, over-the-shoulder, POV, high corner surveillance angle, low bumper angle, tabletop macro height, waist-level western angle, shoulder-level vérité, eye-level neutral, slight low-angle power imbalance, symmetrical institutional wide, long-lens observation.
- **movement terms**: slow push-in, lateral dolly, slider creep, tracking shot, crab move, locked-off hold, whip settle, pedestal rise, crane drop, Steadicam drift, gimbal walk-through, handheld shoulder bounce, body-mounted vibration, PTZ surveillance movement, motion-control repeatability, reactive reframing, beat-synced push, glacial long take.
- **lens and focus terms**: anamorphic prime, spherical prime, vintage glass, macro lens, telephoto compression, rectilinear wide angle, oval bokeh, field curvature, edge falloff, barrel distortion, focus breathing, rack focus, deep focus, zone focus, close minimum focus, split attention between foreground and background, natural focus recovery, soft corners, halation around practicals, controlled flare, low-con diffusion.
- **lighting units and sources**: tungsten practical, sodium vapor streetlamp, fluorescent tube, LED tube, moving head, strobe, neon sign, CRT glow, console bounce, headlight, flashlight, headlamp, candle cluster, fireplace ember, moon source, overcast sky key, window key, book light, softbox strip, octa key, hard fresnel-like source, overhead fluorescent grid, table lamp, porch light.
- **gaffer and grip terms**: key light, fill light, backlight, rim light, kicker, edge light, negative fill, black solids, duvetyne, floppy flag, cutter, topper, egg crate, grid cloth, silk, book light, bounce muslin, ultrabounce, bead board, black wrap, snoot, cookie / cucoloris, DMX cue, practical dimmer, wet-down, haze, rain bars, atmosphere, interactive light.
- **contrast ratio examples**: 1.5:1 polished commercial fill, 2:1 clean interview or comedy, 3:1 soft dramatic modeling, 4:1 prestige drama, 6:1
  noir or thriller, 8:1 horror or night exterior, 12:1 survival night or
  emergency realism, 20:1 club/strobe silhouette.
- **color and texture terms**: cyan shadows, amber highlights, sodium vapor amber, dirty green fluorescent, blue-hour ambience, warm tungsten, moonlit silver, cream highlights, graphite blacks, lifted blacks, protected highlights, soft highlight rolloff, subtle film grain, gate weave, VHS chroma smear, compression artifacts, rain speculars, dust in beams, wet asphalt reflections, skin pores, halation, bloom, motion blur, high ISO noise, controlled saturation.
- **AI video constraints** (bake into every segment's closing constraints):
  one action only, no new characters, no sudden scene change, no fake readable text, no random logos, no plastic skin, no extra fingers, no duplicate faces, no warped architecture, no melting props, no impossible camera move, no unmotivated orbit, no digital zoom, preserve identity, preserve wardrobe, preserve prop geometry, preserve screen direction, physically plausible movement.

### 3.8 Optional visual continuity technique

If tag consistency alone isn't tight enough for the user's needs: after a segment finishes generating, its last frame can be pulled and added as an extra image reference for the next segment's `fileInputs`, so the following clip visually starts from where the previous one ended. Only offer this when the generated clip is actually reachable to download from the sandbox; if it isn't, fall back to plain tag-based continuity and don't block progress on it.

## Step 4 — Generate in batches of up to 3

Never queue more than 3 segments at once, even when `segment_count` is larger.

1. Follow the same Nim workflow as `nim-generate` / `nim-b-roll-seedance`:
   `models_explore` (`action: "recommend"`, `type: "video"`, `input: "image"` if references exist) → `action: "get"` on the chosen model to read the live `generationContract` → `media_upload` any reference images once and reuse the resulting file URLs across every segment that needs them → `generate_video` per segment with `mediaLength: 15000` and whatever aspect ratio/resolution fits the target platform.
2. Submit the current batch's `generate_video` calls (up to 3), then poll `get_generation_status` for each until `finished` / `failed` / `cancelled`. A single 15s Seedance generation usually takes 4-6 minutes; a batch of 3 can take a while — poll sparingly (confirm each job started, then check every 60-90s) rather than narrating every `running` result.
3. Deliver the real media URL for each finished clip in the batch. Never invent a link, and never describe a queued or running job as done.

## Step 5 — Check in after every batch

After delivering a batch — whether it's 1, 2, or 3 clips — stop and ask the user before touching the next batch:

- continue with the next batch, following the story onward, or
- fix something in the clips just generated, or
- stop here (fine even if `segment_count` isn't fully generated yet).

Example (ru):

> Готовы клипы 1–3 из {segment_count}. Продолжаем дальше по сюжету, что-то
> правим, или на этом остановимся?

If the user asks for a fix, only touch the affected segment(s): rewrite that segment's prompt, regenerate just that one, and keep the rest of the chain as it is. If they say continue, repeat Step 4 for the next up-to-3 segments,
carrying the same shared exposition, characters, and location tags forward. Repeat until either all segments are generated or the user says to stop.

## Step 6 — Hand off stitching to the user (ffmpeg, not server-side)

Once the user is happy with the generated clips — whether that's all of them or a subset they're satisfied with — don't stitch them together here. Give the user the clips in order plus a ready-to-run local command.

Default, when every clip came from the same Nim model/settings (same codec and parameters — the common case):

```bash
# 1) list the clips in order, one per line
cat > clips.txt << 'EOF'
file 'segment_1.mp4'
file 'segment_2.mp4'
file 'segment_3.mp4'
EOF

# 2) concatenate without re-encoding
ffmpeg -f concat -safe 0 -i clips.txt -c copy final_video.mp4
```

Tell the user to download each clip first, keep the filenames in the right order, and run one of the two commands locally (or use any GUI video editor if they'd rather not use a terminal). Mention this once, plainly — don't turn it into a full tutorial unless they ask for more detail.

## UX rules

1. Be concise: report finished segments and the next checkpoint question, not tool plumbing or raw JSON/prompt text.
2. Reply in the user's language; keep technical values (`9:16`, `720p`, `mediaLength`, `@CharacterName`) as-is. Segment prompts themselves are always in English per 3.3.
3. One question at a time. The two required checkpoints are: (a) agreeing to the segmented approach in Step 1, and (b) continue / fix / stop after every batch in Step 5. Everything else uses sane defaults without asking.
4. Never claim more than 3 segments generated at once, and never call a batch done while any of its jobs are still `running` or `queued`.
5. Never stitch clips together or promise a merged file from this side — the deliverable is the ordered clips plus the ffmpeg command from Step 6.
   


------------
## Example INPUT
(ONE COMPOSED SEGMENT COULD FOLLOW THIS LOGIC)

```
SCENE: Four characters appear one by one on a bold red Anime-style background — each in a martial arts pose with their "weapon": Accounting with a calculator raised like a sword, HR with a clipboard, Sales with a phone, Marketing with a laptop. Background symbols/glyphs like in the original (can use custom versions). Characters in office clothes.

I'll provide references to the characters, so point it like that:

@Image1 - Accounting
@Image2 - HR
@Image3 - Sales
@Image4 - Marketing
```

## Example OUTPUT (for one segment) reflecting this user input:

```
# GENERAL EXPOSITION

Anime intro. Four office warriors showcased individually. Bold red gradient background with ancient-looking departmental glyphs radiating golden light. Each character demonstrates their elemental office power through explosive martial arts sequences. High-energy anime choreography with dramatic camera angles.

# ENVIRONMENT

Deep crimson-to-scarlet gradient background fills entire frame. Floating golden glyphs orbit in slow rotation: calculator symbols, clipboard icons, phone signals, laptop screens rendered in ancient runic style with subtle particle glow. Atmospheric dust motes catch backlight. Ground plane suggested by subtle shadow beneath each character.

# CHARACTERS LOOK

@Image1 - Accounting warrior in navy business attire, glasses, determined expression, calculator held overhead like sacred weapon
@Image2 - HR defender in light blue shirt and khakis, clipboard gripped firmly, stance protective and grounded
@Image3 - Sales champion in teal blazer and dark pants, phone wielded with precision, athletic confidence
@Image4 - Marketing strategist in coral hoodie and cargo pants, laptop open displaying glowing screen, eager intensity

---

## SHOT 1: ACCOUNTING INTRODUCTION
<wide shot, eye-level, locked-off>

@Image1 materializes from golden particle burst center-frame. She executes hard karate forward stance, left leg bent, right leg extended back, calculator raised overhead with both hands like sword preparing downward strike. Papers explode upward from ground impact, swirling in vortex around her legs. Calculator screen flashes with rapid number sequences casting golden light on her face.

<medium shot, slight low angle>

@Image1 pivots into horse stance, calculator now horizontal at chest level, thumbs hammering keys in lightning-fast jujitsu hand strikes. Each keypress generates visible shockwave ripples in air. Receipts and ledger pages materialize and orbit her torso. Her glasses reflect scrolling numbers. Sharp exhale, focused intensity.

<close-up, dramatic low angle>

@Image1 executes overhead axe-kick, right leg arcing high while calculator remains gripped in left hand. As foot descends, golden energy trail follows arc. Impact generates expanding ring of numerical symbols and percentage signs exploding outward. Her expression fierce, hair whipping from force. Background glyphs pulse brighter.

---

## SHOT 2: HR INTRODUCTION
<wide shot, eye-level, locked-off>

@Image2 emerges from blue-tinted energy wave, immediately dropping into deep defensive stance, clipboard held horizontal like shield before chest. Flying documents—policy papers, forms, memos—swirl defensively around him forming protective barrier. His planted feet create small dust clouds. Calm, unmovable presence.

<medium shot, shoulder-level tracking right>

@Image2 performs wide sweeping arc with clipboard, tai chi-inspired circular motion from left to right. Motion trail of blue energy follows clipboard edge. Papers caught in wake organize themselves into neat floating stacks. He transitions smoothly into one-legged crane stance, clipboard now vertical beside head. Glasses catch light, expression serene but alert.

<medium-wide shot, slight high angle>

@Image2 lunges forward into deep front stance, thrusting clipboard outward like spear thrust. Impact point generates expanding blue force field that deflects incoming chaos—crumpled papers bounce off invisible barrier. His back leg locked straight, front knee bent ninety degrees. Exhale visible as slight mist. Authority and protection embodied.

---

## SHOT 3: SALES INTRODUCTION
<wide shot, eye-level, locked-off>

@Image3 bursts onto screen from left with explosive orange energy, immediately executing flying knee strike while holding phone aloft. Mid-air rotation, curly hair trailing motion. Phone screen blazes with white light casting dramatic rim on her silhouette. Yellow sticky notes and red tape ribbons spiral chaotically in her wake.

<medium shot, dynamic tilted angle>

@Image3 lands in wide power stance, immediately whipping phone in horizontal slash from right to left. Movement creates arc of electric-blue signal waves. She follows through with spinning back-fist using free hand. Sticky-note gremlins materialize and get blown away by force of strike. Her expression fierce joy, teeth showing in competitive grin.

<close-up, low angle, slight push-in>

@Image3 drops into breakdancing-style floor sweep, phone still gripped, spinning on ball of foot while free arm extended. Rotation generates tornado of business cards and colorful price tags swirling upward around her body. Phone screen trails light painting spiral in air. She rises from spin into victorious fist-pump, phone held high, triumphant shout.

---

## SHOT 4: MARKETING INTRODUCTION
<wide shot, eye-level, locked-off>

@Image4 materializes from teal-and-coral particle storm, laptop already open in hands. She executes high sidekick while maintaining laptop horizontal—screen faces camera, displaying rapidly changing graphs and charts glowing bright. Kick generates upward burst of colorful data visualization particles—pie charts, bar graphs, icons—exploding toward top of frame.

<medium shot, eye-level tracking left>

@Image4 transitions into low snake-style stance, laptop now held vertically like shield at angle. She performs rapid three-punch combination with free hand—jab, cross, uppercut—each punch releasing wave of holographic interface elements. Her teal hair bounces with each strike. Cargo pant pockets release floating marker pens. Expression determined focus, slight smile.

<medium-wide shot, slight low angle>

@Image4 springs into butterfly kick—legs scissoring through air in spectacular athletic display—while laptop remains perfectly level in her grip, defying physics. Screen casts rainbow gradient light across her spinning form. She lands in hero pose: one knee down, other leg extended, laptop displayed proudly forward showing triumphant "GOAL ACHIEVED!" checkmark. Green and orange energy sparkles settle around her like victorious confetti. Thumbs-up with free hand.

---

# BACKGROUND GLYPHS SPECIFICATION

Accounting zone: Golden calculator keys, percentage symbols, balance scale icons, numerical sequences in circular mandala formation
HR zone: Blue clipboard checkmarks, policy shield emblems, handshake symbols, protective barrier patterns
Sales zone: Orange-yellow phone signal bars, lightning bolt close icons, upward arrow graphs, target crosshairs
Marketing zone: Teal-coral laptop screen frames, pie chart segments, lightbulb ideas, campaign flag banners

All glyphs rendered in ancient runic aesthetic with subtle animation—gentle rotation, pulsing glow, particle emission—maintaining constant presence throughout all shots.
```