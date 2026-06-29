---
name: nim-generate
description: >-
  Generate or edit images and videos with Nim. Use when the user says "generate
  an image", "make a picture / poster / logo / wallpaper", "edit / restyle /
  remix this image", "make a video", "animate this photo", "image-to-video",
  "turn this into a clip", "give me variations / options", or asks for any visual
  asset from a prompt or a reference. Discovers the right Nim model with
  models_explore, follows its generationContract exactly, uploads references with
  media_upload, and submits with generate_image / generate_video. Supports
  text-to-image, image editing, text-to-video, and image-to-video. NOT for: code,
  text/chat answers, or audio-only tasks.
---

# Nim Generate

Generate and edit images and videos through the Nim MCP. One skill for both: model
discovery is shared, and the only real branch is image vs. video.

## UX rules

1. **Be concise.** Don't dump raw IDs, JSON, or tool plumbing into the chat — report the
   finished result, not the mechanics.
2. **No jargon.** Don't narrate "calling models_explore" or "polling status."
3. **Reply in the user's language.** Detect it from their message; keep technical values
   (`16:9`, `1080p`) as-is.
4. **Pick a sane default and move.** Don't interrogate. Ask one thing at a time, and only
   when a required input is genuinely missing.
5. **Don't pre-optimize for cost.** Prefer the quality default first; only weigh cheaper
   models if the user asks. Check `get_credit_balance` before a deliberately expensive
   run (high resolution, long video, large `batchSize`).
6. **Never invent Nim URLs.** `generate_image` / `generate_video` return no link. Get the
   result by polling `get_generation_status` and report only the URL it actually returns.
7. **No upload, no reference generation.** For any edit, image reference, or
   image-to-video request, do not call `generate_image` / `generate_video` until
   every reference has a real Nim `file_url` from a successful `media_upload`
   upload. MCP generation tools and widgets do not upload local files for you.

## Workflow

1. **Pick the model.** The Nim catalog is live — discover, don't hardcode.
   - Unsure which model fits → `models_explore` with `action: "recommend"`, the user's
     intent as `query`, `type: "image"` or `"video"`, and `input: "image"` when a
     reference will be supplied. For video, pass `minDurationMs` if the user named a
     length.
   - Comparing options → `action: "search"` / `"list"`.
   - Then `action: "get"` on the chosen `model_id` to read its exact
     `generationContract`. This is the source of truth for which params are allowed.
2. **Prepare references.** For image editing, image references, or image-to-video, the
   reference must be a Nim file URL first:
   - Call `media_upload`, run the returned `curl_example` against the local path or
     Claude attachment, then pass the response `file_url` in `fileInputs`.
   - Never pass a local filesystem path straight to a generation tool.
   - If the file is not actually readable by the agent, follow
     [When uploading media](#when-uploading-media).
3. **Generate.** Call `generate_image` or `generate_video` and pass **only** params the
   `generationContract` allows. Submit `model_name` alongside `model_id` for clearer
   user-facing status.
4. **Poll, then deliver.** `generate_image` / `generate_video` start an async job and
   return no result and no link. You are running in a **terminal client (Claude Code /
   Codex) that does NOT render the Nim generation widget** — so you must poll
   `get_generation_status` with the returned `workflowId` / `promptId` until `finished` /
   `failed` / `cancelled`, then deliver the final media URL from that response.
   - **Never** tell the user the result "will appear in a widget" — it will not appear
     here. Never describe a queued job as done.
   - The Nim widget only renders in MCP-Apps hosts (claude.ai, ChatGPT, Claude Desktop),
     which connect to the MCP directly rather than through this skill. Ignore it here.

## Image vs. video — quick routing

- Still asset, edit, restyle, logo, poster, character art → **image** (`generate_image`).
- Motion, clip, animation, or "make this image move" → **video** (`generate_video`).
- "Animate this photo" / "image-to-video" → video with the reference in `fileInputs`
  (choose an image-input video model via `input: "image"`).

## Inputs

Pass a param only when the selected model's `generationContract` lists it.

| Param | Applies to | Notes |
|---|---|---|
| `prompt` | both | Required. Carry the full creative intent. |
| `model_id` | both | Required. Always from `models_explore`. |
| `fileInputs` | both | Nim file URLs from `media_upload`. Required for edit / image-input / image-to-video models. |
| `requestedAspectRatio` | both | e.g. `16:9`, `9:16`, `1:1`. |
| `resolution` | both | e.g. `1080p`, `2K` — only values the contract offers. |
| `mediaLength` | video | Input duration in **ms** (`5000`, `8000`). |
| `fps`, `keepSound` | video | Only when the model supports them. |
| `seed` | both | Omit or `-1` to randomize; reuse a value to reproduce. |
| `batchSize` | both | 1–4 variations in one call. Use for ideation / options. |

## When uploading media

- Never pass local filesystem paths directly to `generate_image` or
  `generate_video`; use `media_upload` and pass the returned `file_url`.
- If a request depends on a reference file and upload fails, stop before
  generation. Do not call `generate_image` or `generate_video` without the
  reference just because the Nim MCP widget or generation tool is available.
- In Claude Cowork, paths from the user's computer are never readable by the
  agent unless the file is in the current Cowork Working folder. If a referenced
  file cannot be read, stop and ask the user to add it to the current Cowork
  Working folder, then retry from that accessible file.
- Inline previews or images visible in chat are not always uploadable files. If
  no actual file path/attachment/source is available, ask for one before upload.
- If `media_upload` returns an upload URL but the actual upload is blocked by
  DNS, network egress, CSP, sandboxing, or allowlist restrictions, stop. Do not
  try alternate domains, proxy URLs, guessed endpoints, custom upload formats,
  or invented `fileInputs` values such as `upload:/path`, local paths, or
  placeholder URLs. Do not claim the Nim widget can upload the file directly.
  Tell the user to add `*.nim.video` to their allowlist; the setup page is
  `https://nim.video/mcp`. Retry only after they confirm the environment is
  fixed.

## Variations & ideation

When the user wants options, directions, or "a few ideas," set `batchSize` (2–4) so Nim
returns several takes from one request, each with a randomized seed. Present them as a
set to compare, not as a single answer.

## When a generation fails

Surface the returned `error` / `errorCode` plainly. Don't silently retry with changed
params — ask the user first, unless they already told you to iterate.
