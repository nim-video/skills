# Depth reference provider

Everything provider-specific lives in this file plus `scripts/depth_map.py`.
Nothing else in this skill mentions fal, keys, or model names. That is what
makes the swap to a Nim-native `depth_map` tool a two-line change.

## Why depth instead of the raw clip

Handing the model the raw clip gives it everything at once - performer, wardrobe,
room, lighting - and the choreography competes with all of it for attention. A depth
map is pure spatial information over time, so the only thing left to transfer is motion.

The accuracy gain is not the model getting better; it is the model getting fewer
decisions to make. That is the whole argument, and it is worth stating plainly rather
than presenting depth as a compliance trick.

Two failures it prevents:

- **Appearance bleed.** The original performer's face, clothing, and surroundings
  reappear in the output. A depth-only reference removes that source of leakage.
- **Two-identity negotiation.** Once appearance data enters the motion channel, the model
  negotiates between the source performer and the identity reference, and identity stops
  being clean.

A third effect matters for anything published: source clips containing real faces or
recognizable material are commonly rejected by input review, while their depth versions
pass because they contain geometry rather than people. This abstracts likeness - it does
not transfer ownership of the choreography or the audio.

## Contract

The step this skill depends on, regardless of who implements it:

| | |
|---|---|
| Input | one video, given as a publicly reachable URL **or** a local file path |
| Output | one depth-only MP4 (H.264), same duration, same FPS |
| Side effects | none the caller must manage |

Written as a contract rather than a tool name so that today's script and
tomorrow's Nim tool are interchangeable.

## Audio

The default depth reference is SILENT. Preserve the original source file/audio locally,
then attach its track to the FINAL generated video using [final-audio.md](final-audio.md).
Do not upload the original sound to Seedance for this normal workflow. Set
`generateAudio: false` when permitted; otherwise discard generated sound during assembly.

| Command | Result |
|---|---|
| `depth_map.py source.mp4 depth.mp4` | Silent depth video (default) |
| `depth_map.py source.mp4 depth.mp4 --no-audio` | Explicitly silent depth video |
| `depth_map.py source.mp4 depth.mp4 --audio-out source.m4a` | Silent depth plus a locally extracted, stream-copied audio file |
| `depth_map.py source.mp4 depth.mp4 --attach-audio` | Explicit alternative: source audio inside depth, only when requested for reference guidance |

Reuse already calculated depth. A changed audio mode never warrants another paid depth
call: cached depth is reused and sound is processed locally. An existing depth video
with audio must be stripped locally before this workflow's upload. Do not reuse its
old audio-bearing upload URL and describe it as silent.

`ffmpeg` and `ffprobe` are needed for audio extraction/attachment; FFmpeg is also needed
to strip sound from an existing cached video. A newly computed silent depth video does
not require them. Preflight the tools required for final assembly before generation.
Original-audio requests require an actual source audio stream. If none exists, report
that rather than inventing sound. --attach-audio is not the default or an automatic
fallback for final-track copying.

## Local files

A local path is sent to fal inline as a `data:video/mp4;base64,...` URI. fal accepts
data URIs on file inputs for this model, so no upload step is needed and the
reference clip is never published anywhere.

That last part is the reason to prefer inline over fal's CDN upload. fal CDN files
are **public by default** - anyone holding the URL can download them. A client's
reference footage should not end up on a public URL just to compute a depth map.

Ceiling: **25 MB**, after which the script refuses and tells the user to trim. This
is deliberate. Reference clips are meant to be 3-8s, and an inline base64 body costs
~1.33x the file size. Past the ceiling the right answer is a shorter clip, not a
bigger POST. If clips ever routinely exceed it, add fal CDN upload
(`POST https://rest.alpha.fal.ai/storage/upload/initiate`, then PUT the bytes)
rather than raising the number.

## Cache identity

- URL source: the URL string.
- Local file: the **sha256 of the file contents**, so editing or re-exporting the
  clip invalidates the cache instead of silently reusing a stale depth map.

## Current implementation: fal.ai

Model: `fal-ai/depth-anything-video` (Video Depth Anything, CVPR 2025).
Cost: **$0.04 per second of input video** (a 15s reference costs $0.60).
Auth: `authorization: Key $FAL_KEY`, endpoint `https://fal.run/fal-ai/depth-anything-video`.

Parameters used, and why:

| Param | Value | Reason |
|---|---|---|
| `model` | `VDA-Small` | Apache-2.0. `VDA-Base`/`VDA-Large` are CC-BY-NC-4.0, and **the API default is `VDA-Large`** - omit this and you silently run on a non-commercial model. |
| `colormap` | `grayscale` | Raw normalized depth. The value is part of the cache key, so changing it never reuses an older cached depth clip. |
| `resolution` | `auto` | Preserves input, capped at 1080p. |
| `output_fps` | not set | Inherits the source FPS, which keeps motion timing intact. |

Deliberately not used:

- `resolution: "360p"` - 640x360 = 230,400 px. Seedance rejects reference video below
  **409,600 px**, so a 360p depth clip never reaches generation. 480p and up are safe.
- `include_raw_depths` - returns a `.npz`, useless to the pipeline.
- `side_by_side` - produces a "source | depth" comparison. Useful for human QC, unusable
  as a motion reference. Enable only when reviewing.

## Environment

`FAL_KEY` must exist in the shell environment of whoever runs the script.

- It is read once, used for the `authorization` header, and never printed.
- It must never appear in `SKILL.md`, in a payload, in a prompt, in a tool result,
  or in a URL query string.
- On HTTP errors the script prints status and body only, never request headers -
  an error path that echoes headers is a common way a key reaches a transcript.

## Returning the result to Nim

`generate_video` accepts only Nim `file_url` values, so the depth output is not
usable directly from fal:

1. `depth_map.py` writes the depth clip to a local path.
2. `media_upload`, then run the returned upload command against that path.
3. Use the returned `file_url` as the motion reference.

Do not pass the fal URL into `fileInputs` and do not pass a local filesystem path
to a generation tool.

For the production pipeline the URL form is still the one that matters, because
Nim references arrive as `file_url`. The local-file form exists so the depth step
can be iterated on during development without a round trip through Nim.

## Caching

A depth map is a property of the source clip, not of the character. One depth
clip serves every character and every wardrobe variant generated from it.

The script writes a `<out>.cachekey` marker next to its output and skips the
network call when the source URL and parameters are unchanged. Keep the depth
clip for as long as the source clip is in play - re-running it is pure waste.

## Migration to a Nim-native tool

When Nim ships `depth_map`, the swap is:

1. In `SKILL.md`, take branch 1 of the provider resolution order instead of branch 2.
2. Delete `scripts/depth_map.py` and the "Current implementation" section above.
3. Keep the contract table, the Nim return step, and the caching rule - they still apply.

If the Nim tool returns a `mediaUrl` rather than a local file, the Nim return step
collapses into the tool call and `media_upload` is no longer needed for this step.
