---
name: nim-ugc-prompts
description: Use when writing, improving, planning, or generating Nim/Seedance UGC video prompts for TikTok, Reels, Shorts, creator ads, direct-to-camera hooks, selfie videos, iPhone footage, testimonials, street interviews, mirror try-ons, outfit changes, product/location walkthroughs, VO, lip sync, audio references, or image-to-video prompts with character/location/product references.
---

# Nim UGC Prompts

## Overview

Create copy-ready English UGC video prompts for Nim image-to-video and text-to-video workflows. The output should feel filmed by a real person on a phone: imperfect framing, ordinary timing, natural delivery, realistic skin/fabric/room behavior, and clear reference roles.

For detailed examples, load:

- `references/ugc_prompt_patterns.md` for distilled patterns.

## Nim MCP Rules

When actually generating through Nim:

1. Discover the live video model with `models_explore`; prefer the current Seedance image-to-video model when references drive the result.
2. Inspect the exact `generationContract` with `models_explore` `action: "get"`.
3. Upload every image/audio reference with `media_upload`; use only returned Nim `file_url` values in `fileInputs`.
4. Pass only parameters supported by the selected contract: `prompt`, `requestedAspectRatio`, `mediaLength`, `resolution`, `fps`, `keepSound`, `seed`, `batchSize`, or any exact contract fields.
5. Poll `get_generation_status` until a terminal status returns a real media URL.

Default targets:

- Format: vertical `9:16` unless the user asks otherwise.
- Duration: 6-10 seconds for single UGC beats; 10-16 seconds for multi-cut try-on, walkthrough, or story sequences.
- Reference stills: use `Nano Banana Pro 2K` for quick identity/product/location refs, or `GPT Image 2 medium 2K` when controlled polished still anchors are more important.

## Intake

Extract or assume:

- platform and duration;
- product/offer/topic;
- creator identity, audience, and emotional arc;
- references and their roles;
- whether the clip is single-take, multi-cut, selfie/POV, mirror, static tripod, or location walkthrough;
- VO, dialogue, native audio, lip sync, and whether subtitles/text overlays are allowed.

Ask only when a required reference or audio asset is missing.

## Reference Roles

Write reference roles at the top of the prompt before scene directions:

```text
REFERENCES:
@image1 - main location, preserve layout exactly.
@image2 - main character identity, face, hair, body proportions exactly.
@image3 - outfit/product/object reference, preserve design exactly.
@audio1 - voice, tone, cadence, pronunciation, pacing and vocal texture exactly.
```

Use stable role names:

- main character;
- additional character/friend/interviewer;
- outfit/body proportions;
- product/object;
- main location/exterior/interior;
- phone/mirror/tripod/camera reference;
- audio/voice/song/live performance.

Never let references merge. If `@image2` is outfit only, say not to use it for face or hairstyle.

## Prompt Skeleton

Use this structure for most UGC prompts:

```text
REFERENCES:
@image1 - ...
@image2 - ...

AUDIO / VO:
...

IMPORTANT:
...

STYLE:
UGC mixed with documentary realism, social media ad, TikTok/Reels/Shorts, authentic creator content, smartphone footage, natural imperfections, no polish.

FORMAT:
Vertical 9:16. <duration> seconds. <front camera / rear camera / mirror / tripod / handheld>.

CAMERA:
...

CHARACTER:
...

LOCATION:
...

SCENE / SHOTS:
0:00-0:03 ...
HARD CUT.
0:03-0:06 ...

NEGATIVE:
No subtitles unless requested. No text overlays. No beauty filter. No skin smoothing. No CGI. No morphing. No flickering. No ghosting. No hidden transitions.
```

## UGC Prompt Patterns

Choose one primary pattern:

| Pattern | Use for | Core camera behavior |
| --- | --- | --- |
| Direct-to-camera hook | creator ad, testimonial, confession | front camera or handheld medium shot, natural eye contact |
| Multi-cut hook | punchier 6-10s social ad | hard cuts only, same location/character continuity |
| Selfie walkthrough | store, travel, event, venue | front-camera selfie then rear-camera POV |
| Mirror try-on | fashion/outfit, fitting room | mirror geometry, phone visible if needed, body/outfit clear |
| Static tripod/home | performance, demo, try-on sequence | locked framing, background unchanged |
| Street interview | social proof, comedy, dating, vox pop | handheld interviewer camera, spontaneous timing |
| Concert/event UGC | music, crowd, live reaction | selfie camera, crowd density, live audio and changing exposure |

Load `references/ugc_prompt_patterns.md` for a richer pattern library.

## Writing Rules

- Make ordinary behavior specific: blinking, breathing, posture shifts, small pauses, glances away, half-smiles, subtle laughs, natural hand gestures.
- Use smartphone image behavior: natural HDR, autofocus breathing, auto-exposure adaptation, tiny wrist shake, real sensor noise, practical room light.
- Preserve the reference environment exactly when the prompt says the scene happens inside one location.
- Use `HARD CUT` for edits. Do not use hidden transitions, morphing, whip-pan disguises, or magical outfit swaps unless requested.
- For lip sync, specify exact spoken lines and performance timing. Do not add subtitles unless requested.
- For static tripod prompts, explicitly forbid camera shake, zoom, panning, reframing, and background movement.
- For handheld prompts, specify which hand holds the phone and what the other hand can do when it matters.
- For mirror prompts, explicitly describe reflection logic and avoid impossible camera/mirror geometry.
- For try-on or product sequences, lock camera position, background, exposure, scale, and reference role across every cut.

## Output Format

Return this by default:

```markdown
## Reference Plan
- @image1: ...

## Final UGC Video Prompt
[copy-ready English prompt]

## Nim Generation Notes
- Discover model target: Seedance image-to-video / text-to-video as required
- Aspect ratio: 9:16
- Duration: ...
- Required fileInputs: ...

## Negative Prompt
...
```

If the user asks for JSON, return:

```json
{
  "reference_plan": [],
  "prompt": "...",
  "nim_generation_notes": {
    "discover_model_target": "...",
    "aspect_ratio": "9:16",
    "duration_sec": 0,
    "required_fileInputs": []
  },
  "negative_prompt": "..."
}
```

## Quality Bar

- The clip reads as a real phone recording, not a polished commercial.
- Reference roles are unambiguous and do not merge.
- Face, outfit, product, and location locks survive across cuts.
- Delivery sounds conversational, not scripted.
- Camera behavior matches the declared capture mode.
- Timing is feasible for the requested duration.
- Negative constraints block common AI failures without fighting the brief.
