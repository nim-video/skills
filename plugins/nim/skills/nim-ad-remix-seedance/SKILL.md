---
name: nim-ad-remix-seedance
description: Use when the user wants to remake an existing ad or video with Nim Seedance (2 or 2.5) — new people, new product, new background or setting, new outfits, new on-screen text, or any other change — while keeping the original shots, timing and camera. Triggers include "replace the person in this ad", "swap the actors", "replace these people with these photos", "put my product into this ad", "same ad, new cast", "move this ad to another location", "change the background", "dress them in X", "remake this ad". Handles one or many people, products, settings and text. Inputs are a source video, reference images (people, product, optional style), and optional extra directions. The user gets a link to the result. NOT for making ads from scratch without a source video (use nim-b-roll-seedance or nim-hookgen-seedance), and NOT for only swapping the people in the user's own video with characters from images (use nim-replace-character).
---

# Ad Remix with Seedance (Nim)

Remake an existing video: same shots, cuts, camera and timing, but with new people, a new
product, a new setting, new outfits, new text, or whatever else the user asks for.

## Tools

- `media_upload`, `models_explore`, `generate_video`, `get_generation_status`,
  optionally `generate_image`
- `build_guide_video`: prepares the source for Seedance so it knows who and what to replace.
  Returns a `guide` video, a `prompt_header`, a status per object, and (with `chunk_mode`)
  matching source/guide chunks
- `assemble_chunks`: joins the generated runs and adds the original audio

Talk to the user only about the source, the references, the plan, cost and the result.
Don't explain or mention how the guide is made. Everything stays on Nim as URLs; deliver
the result as a link. Looking at the original video locally (ffprobe, frames) is fine.

## 1. Understand and ask once

Upload the original video and the references (`media_upload`). Look at the source (size,
duration, cuts, who appears when, products, text) and at every reference image. Then ask
everything in **one message**, with a recommended default each:

1. **Model:** Seedance **2** (recommended) or **2.5** (single simple swaps only).
2. **Resolution:** 480p / 720p / 1080p. Offer a cheaper test first: the full video at 480p,
   or a ~5s cut of the hardest part at 480p.
3. **Who and what replaces whom** (judge identities from full-size frames; the same person
   can look like two people at different distances).
4. **Outfits:** keep the source clothes or take them from the reference photos.
5. **Setting / background** and any **extras** (costumes, props, style, mood).
6. **On-screen text:** keep, remove, or replace.

Warn about visible risks (cross-gender swaps, tiny background people, alcohol/tobacco/vape,
famous people or film footage), quote the cost, and wait for a go-ahead.

## 2. Prepare

Call `build_guide_video` with the `source` and one `object` per person or product that
changes: a short `name` and a visual description of the **original** (hair, build, position
and stable traits; clothing only if nobody else wears something similar). Add 2–3
alternative descriptions in `prompts` if one may not catch it everywhere. If the source is
longer than one run allows, pass `chunk_mode`: `seedance-2-guide` for Seedance 2,
`seedance-2.5-edit` for Seedance 2.5.

Check every object's status. If one isn't `ok`, follow its advice (usually a more specific
description) and call again before generating.

Skip this step for a single simple swap with Seedance 2.5; use `prepare_chunks` on the source
if it's longer than 30s.

## 3. Generate

Always `models_explore` → `get` the model first and use only params in its contract.

| | Seedance 2 Advanced (default) | Seedance 2.5 Advanced |
|---|---|---|
| Inputs | `referenceVideos: [source, guide]` + `fileInputs` | `sourceVideo` + `fileInputs` |
| Use for | remixes: several people, products, settings, outfits | a single simple swap |
| Limits | `mediaLength` and `requestedAspectRatio` required; up to 9 images | 4–30s, ≥854x480; up to 30 images |

Run one generation per chunk (or one for the whole video if there are no chunks), with each
chunk's `media_length_ms` as `mediaLength`, the same references and the same prompt; run
them in parallel. Poll `get_generation_status` in the background and keep each `mediaUrl`.
A `failed` status with no cause: retry once, then report the `promptId`. Then
`assemble_chunks` with the chunks (each with its result `video`) and the original as
`audio_from`; use it for a single run too, to restore the original audio.

References: pass the person and product photos as they are. Seedance tends to copy the
outfit a photo shows, so when clothes should be kept, say so in the prompt. Optional
keyframes (`generate_image` on a source frame) help for hard identities and big style
changes. Don't make keyframes of branded end cards or logos.

## Prompt

Start with the `prompt_header` exactly as returned; it refers to the source as `@Video1`
and the guide as `@Video2` and names every object. Then say what each named object becomes
and everything else that changes. Images are `@Image1`… in `fileInputs` order.

```text
<prompt_header>
TEXT: [keep all on-screen text unchanged | remove all text | replace with: "..."]. No other
text or watermarks.

Keep every shot, cut, camera move, gesture and action of @Video1. Change:
- <name> -> the [man/woman] in @Image1: [concrete traits]; [kept clothes | new outfit].
- <name> -> the product in @Image3: [shape, colours, label by look]. Hands handle it the
  same way.
- SETTING: [new location, ground, sky, light].
- EXTRAS: [costumes, style, mood as concrete visual instructions].

The photos provide identity [, wardrobe] and the product only. Adults only.
Throughout the video, characters with completely identical appearance, clothing, and
accessories are prohibited. Do not generate duplicate avatars or a twin effect.
```

Describe people by concrete traits (hair, skin, facial hair, marks with side), products by
look (don't quote small print), and extra directions as visual instructions.

## 4. Review and deliver

Look at result frames next to the source at key moments (group shots, product shots,
cuts). Report a short table: mapping, identity, outfits, product, setting/extras, timing,
text, audio, and "motion not verified" if you only checked stills. Deliver the result link
and the real cost. For a real defect, say what would fix it and what it costs, then ask
once; never rerun without approval.

Known limits: burned-in captions and logos are usually kept even when told to change;
small or background people are often left unchanged.

## Content filter

Jobs can be rejected after minutes of processing. Known triggers: famous people, film or
TV footage (ask for another source; don't work around it); alcohol, tobacco or vape and real
brands, especially in keyframes or text; people who could read as minors; revealing outfits.
Warn before running; on a rejection explain the likely trigger instead of retrying.

## Cost

Nim credits from the contract and `estimatedCreditCost` (reference videos add a duration
charge). Seen at 480p for a 7s chunk with source + guide: Seedance 2 ≈ 185, Seedance 2.5 ≈
280. Keyframes ≈ 25 each. Quote a range first; report the real charge.
