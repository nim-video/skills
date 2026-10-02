---
name: nim-motion-transfer
description: Use when the user wants a performance from their own clip - a dance, fight, sports move, gesture, walkthrough or presenter take - replayed by a different character from a reference image, optionally in a new setting, with Nim Seedance 2. Triggers include "make my character do this dance", "transfer this motion", "same moves but a different person", "recreate this clip with my character", "the original performer keeps showing up". Keeps the original movement, timing, camera and sound; clips from 4 s to 5 min (longer ones are split and joined). The user gets a link and the video file. NOT for replacing the people in the user's own video while keeping its scene and camera (use nim-replace-character), NOT for remaking an existing ad with a new cast, product or setting (use nim-ad-remix-seedance), and NOT for restyling a clip or making motion from text alone.
---

# Motion Transfer with Seedance (Nim)

Replay a performance on a new character: the source clip gives the movement, timing, camera
and framing; the reference images give the face, body, outfit and, optionally, the place.

## Tools

- `media_upload`, `models_explore`, `generate_video`, `get_generation_status`
- `motion_prepare_video`: brings the source within the provider limits (size, fps, pixels);
  returns a silent clip and `long_source`
- `motion_prepare_images`: pads reference images to the accepted aspect range
- `motion_prepare_chunks`: splits the prepared clip into runs of 4–15 s (one chunk for a short
  clip) with `media_length_ms` per chunk
- `motion_estimate_depth`: turns a chunk into the motion reference for Seedance
- `motion_assemble`: joins the generated runs, adds the original audio and exports a
  compatible MP4

Talk to the user only about the source, the references, the plan, cost and the result. Don't
explain or mention how the motion reference is made. Everything stays on Nim as URLs; looking
at the source locally (ffprobe, frames) is fine.

## 1. Understand and ask once

Without a source clip or a character image, ask for them: a 4 s+ clip with one clearly visible
performer, and one or more images of the character (full body when the clip shows full body).
A location image is optional.

Upload the source and the images (`media_upload`). Look at the source (duration, size, cuts,
who moves, camera) and at every image. Then ask everything in **one short message**, with a
recommended default each: resolution (480p / 720p recommended / 1080p), aspect ratio (the
source's, recommended), setting (location image, a description, or a neutral studio) and sound
(original, recommended, or silent). Warn about visible risks: several people in the source,
famous people or film footage, motion that depends on a prop or another person, fast hand or
face detail. Quote the cost and wait for a go-ahead. Ask nothing else afterwards.

## 2. Prepare

1. `motion_prepare_video` on the source. `too_short`: ask for a longer clip (never loop or slow
   it); `needs_trim`: ask which part to keep; `too_large`: ask for a shorter segment.
2. `motion_prepare_images` on the images: the character first, then the location.
3. `motion_prepare_chunks` on the prepared clip, also for a short one.
4. `motion_estimate_depth` on every chunk's `source_path`. Keep each `depth_url`; one depth per
   chunk serves every later recast of the same clip.

## 3. Generate

Always `models_explore` → `get` the Seedance 2 Advanced Mode entry that takes reference videos,
and use only params in its contract.

| Param | Value |
|---|---|
| `referenceVideos` | `[depth_url]` of the chunk: motion only |
| `fileInputs` | the prepared character image(s), then the location image |
| `mediaLength` | the chunk's `media_length_ms` |
| `requestedAspectRatio` | the nearest to the source; never against the source's shape |
| `resolution` | as agreed |
| `generateAudio` | `false`; the original sound is added at assembly |

Run one generation per chunk with the same references in the same order, in parallel. Poll
`get_generation_status` and keep each `mediaUrl`. A `failed` status with no cause: retry once,
then report the `promptId`. Then `motion_assemble` with the chunks (each with its result
`video`), the original upload as `audio_from` (not the prepared clip, which is silent), the
resolution, and `aspect_ratio` `16:9`, `9:16` or `preserve`.

## Prompt

Prompt less: the motion reference carries the movement, so the text says what to take from
where and what must stay. With several chunks, copy the identity block verbatim into every
prompt and write the scene line fresh from each chunk's own frames.

```text
[duration] s, [aspect ratio], photorealistic [one style noun].

REFERENCE PRIORITY
1. @Video1 = motion, timing, camera and framing only. Do NOT take appearance, costume or
   environment from @Video1.
2. @Image1 = sole identity reference: face, hair, body proportions and the complete outfit
   ([concrete traits]), the same from first frame to last.
3. @Image2 = environment only: layout, light and palette of [the place]; nothing in it is a
   person.

The character from @Image1 performs in [the setting]. Preserve every body movement, pose,
action beat, screen position, camera move, framing change and timing from @Video1.

PRESENCE: the only person on screen is the character from @Image1.
PHYSICS: natural weight, ground contact and shadows.
EXCLUSIONS: no drift, no identity flicker, no duplicated limbs, no extra or missing fingers,
no face morphing, no text overlays, no watermarks, no background music.
```

Use two or three style words at most; more makes the motion drift. Never negate a visible
object ("no red car"); say what is there instead. For a non-human character add: "Adapt the
motion to this body plan: [arms, legs, tail]; no duplicate limbs, no broken joints."

## 4. Review and deliver

Look at result frames next to the source at key moments: identity and outfit from every
angle, hands and feet, nothing of the original performer, no invented action after the source
motion ends, joins between chunks. Keep the review to yourself.

Deliver the result both ways: the link to the final video from `motion_assemble`, and the
file itself in the chat (download it and attach it with the host's file tool, such as
`SendUserFile` with `display: "render"` or `present_files`; link only when there is none).
Then one or two lines: the video is ready and the real cost. Never show the motion
reference, the silent runs or the chunks. Mention a defect only when a requirement is clearly
unmet: say what would fix it and what it costs, then ask once; never rerun without approval.

Known limits: finger detail, facial expression and cloth motion follow the reference only
loosely; props held or touched in the source detach easily.

## Content filter

Jobs can be rejected after minutes of processing. Known triggers: famous people, film or TV
footage (ask for another source; don't blur or work around it); people who could read as
minors; revealing outfits. A moderation rejection: one retry with the audio line removed and
`generateAudio: false` kept, then explain the likely trigger instead of retrying.

## Cost

Nim credits from the contract and `estimatedCreditCost`; the reference video adds a duration
charge on top of the per-second price. Seen at 720p for a 10 s run with one reference video and
two images: Seedance 2 base 300, `estimatedCreditCost` 400. Each chunk is billed for its whole
padded seconds. Quote a range first; report the real charge.
