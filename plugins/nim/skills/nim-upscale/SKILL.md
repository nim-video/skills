---
name: nim-upscale
description: >-
  Improve image or video quality with Nim upscalers. Use when the user asks to
  make an existing image or video better, higher quality, sharper, clearer,
  cleaner, higher resolution, less blurry, less pixelated, enhanced, restored,
  upgraded, upscaled, 4K, HD, 60fps, smoother, or otherwise improved in visual
  quality without requesting a creative restyle or new generated content. Routes
  images to upscale_image and videos to upscale_video. Uses bytedance by default
  for video upscaling and asks for missing source/target details before running.
---

# Nim Upscale

Improve existing image or video quality through Nim. This skill is for
enhancement/upscaling, not creative generation. Preserve the source content
unless the user explicitly asks for a different look.

## UX Rules

1. **Treat quality language as upscaling.** If the user says "make this better,"
   "enhance," "sharpen," "make HD/4K," "fix blur/pixels," or similar for an
   existing image/video, use an upscaler instead of an image/video generation
   model.
2. **Do not restyle by default.** Upscaling should preserve identity, framing,
   colors, text, labels, and motion as much as possible.
3. **Keep tool details quiet.** Do not dump raw JSON, internal IDs, or upload
   mechanics. Report the final media URL and the meaningful settings used.
4. **Do not run defaults for vague requests.** Before running, identify the
   source media and the requested target: scale, resolution, FPS, or "use the
   recommended setting." If the user only says "make this better" and no target
   is clear, ask a concise choice question instead of launching.
5. **Poll to completion.** Upscaling is async. Poll `get_generation_status`
   until `finished`, `failed`, `cancelled`, or `removed`, then return the real
   final URL.

## Routing

- Existing still image, photo, render, artwork, product shot, poster, logo, or
  frame that should look sharper/cleaner/higher resolution -> `upscale_image`.
- Existing video, clip, animation, product video, footage, reel, ad, b-roll, or
  generated video that should look sharper/cleaner/higher resolution/smoother ->
  `upscale_video`.
- If the user wants new content, a different scene, a background swap, a visual
  restyle, or text/prompt-based creation, use a generation/editing skill instead.
- If the request combines creative edits with better quality, do the creative
  edit/generation first, then upscale the finished output only if the user asked
  for final quality or high resolution.

## Preflight Gate

Do not call `upscale_image` or `upscale_video` until these are known:

1. **Source media.** The image/video to improve is available as a Nim URL,
   attachment, local path, or external URL. If not, ask for the file or URL.
2. **Media type.** Know whether the source is an image or a video. If the URL or
   attachment name is ambiguous, ask.
3. **Target setting.** Know what "better" means operationally:
   - image: `2x`, `4x`, `6x`, `8x`, or `10x`;
   - video: target resolution (`1080p`, `2k`, `4k`) and whether to keep `30fps`
     or make it `60fps`.

If the user gives a vague request like "make this better" and provides media,
ask one short question adapted to the media type:

```text
For an image: What scale should I use: 2x quick cleanup, 4x high quality, or a specific factor?
For a video: What target should I use: 1080p cleanup, 2K/4K, or 60fps smoother video?
```

Ask only the relevant version. If the user says "use defaults," "whatever you
recommend," "go ahead," or equivalent, use the defaults below.

## Source Media Handling

Nim upscalers require Nim-hosted media:

- If the source is already a Nim `file_url` from `media_upload` or a finished
  generation `mediaUrl`, pass it directly. Do not re-upload Nim-hosted media.
- If the source is a local path or attachment, call `media_upload`, run the
  returned upload command with the actual file path, and use the returned
  `file_url`.
- If the source is an external URL, upload/import it first when the tool flow
  requires a Nim-hosted URL. Do not pass arbitrary non-Nim URLs directly to
  upscalers.
- Never pass local filesystem paths directly to `upscale_image` or
  `upscale_video`.

## Image Upscaling

Use `upscale_image`.

Defaults:

| Setting | Default | Notes |
|---|---:|---|
| `model` | `seedvr2` | Current Nim image upscaler. |
| `upscale_factor` | `2` | Use only after the user asks for `2x`, generic cleanup, or approves defaults. |

Choose the factor from the user's answer:

- "make it bigger," "high resolution," "HD," generic cleanup, or approved
  default -> `2x`
- "4K," "print quality," "much larger," or clearly low-res source -> `4x`
- Specific request for `6x`, `8x`, or `10x` -> use that factor if appropriate

Call shape:

```json
{
  "file_url": "<nim-hosted-image-url>",
  "model": "seedvr2",
  "model_name": "SeedVR2",
  "upscale_factor": 2
}
```

## Video Upscaling

Use `upscale_video`.

Defaults:

| Setting | Default | Notes |
|---|---:|---|
| `model` | `bytedance` | Default video upscaler; Topaz is overkill unless requested. |
| `resolution` | `1080p` | Use only after the user asks for HD/1080p/generic cleanup or approves defaults. |
| `fps` | `30` | Preserve normal cadence unless the user asks for smoother motion or 60fps. |
| `keepSound` | `true` | Preserve source audio unless the user asks otherwise. |

Bytedance is the default for video because it balances quality and cost. Use
another model only when the user explicitly asks:

- `bytedance`: default video upscaler. Use `resolution` (`1080p`, `2k`, `4k`).
  Use `fps: 60` when the user asks for smoother motion, frame interpolation, or
  60fps.
- `topaz`: use only when the user explicitly asks for best/max quality, Topaz,
  premium upscale, or accepts the higher cost. Use `upscale_factor` `2` or `4`;
  output is capped at 4K.
- `standard`: use only when the user explicitly wants the cheapest/basic option.

Choose parameters:

- Approved default or "HD/1080p" -> bytedance, `resolution: "1080p"`, `fps: 30`,
  `keepSound: true`.
- "2K" -> bytedance, `resolution: "2k"`.
- "4K" -> bytedance, `resolution: "4k"`.
- "Make it smoother" / "60fps" -> bytedance with `fps: 60` and the selected
  resolution.
- "Topaz" / "best possible" / "maximum quality" -> Topaz, usually `2x` unless
  the user asks for `4x`.

Call shape for the default path:

```json
{
  "file_url": "<nim-hosted-video-url>",
  "model": "bytedance",
  "model_name": "Bytedance",
  "resolution": "1080p",
  "fps": 30,
  "keepSound": true
}
```

## Cost And Confirmation

- Check `get_credit_balance` before long videos, Topaz video upscales, 4K video,
  60fps interpolation, or any request that appears expensive.
- If the upscaler returns `estimatedCreditCost`, mention it before proceeding
  only when a confirmation step is needed or the cost is unusually high.
- If the tool returns `status: "insufficient_credits"`, present the returned
  purchase options and do not retry.

## Completion

After calling `upscale_image` or `upscale_video`, poll `get_generation_status`
with the returned `workflowId` or `promptId` until terminal status.
