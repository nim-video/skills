---
name: nim-template-runner
description: >-
  Find, inspect, and run Nim templates through the Nim MCP. Use only when the
  user explicitly asks for Nim templates, says "template" / "шаблон", asks to
  browse or recommend templates, or asks to run a specific named Nim template.
  Uses explore_templates, get_template, media_upload, and run_template. NOT for
  ordinary image/video generation requests; use nim-generate for those.
---

# Nim Template Runner

Browse and run Nim templates through the Nim MCP. Templates are a separate path
from ordinary image/video generation: use the template tools, not local runner
apps or hand-built HTML.

## UX Rules

1. **Use templates only on explicit intent.** The user must ask for a template,
   named template, or template browsing/recommendation.
2. **Stay concise.** Do not dump raw template contracts or JSON unless the user
   asks to inspect them.
3. **Reply in the user's language.** Keep technical values like `9:16` and
   `numOutputs` unchanged.
4. **Ask only for required missing inputs.** For optional inputs, ask only when
   they materially change the output.
5. **Never invent result links.** `run_template` starts an async job. Poll
   `get_generation_status` unless a Nim widget is actually rendered by the host.

## Workflow

1. **Find a template.**
   - If the user asks to browse or is unsure, call `explore_templates` with
     `action: "recommend"` and the user's creative task as `query`.
   - If the user names a template, call `explore_templates` with
     `action: "search"` and the name as `query`.
   - Present a short selectable list. Do not run a template until the user has
     picked one, unless the request clearly names a single template to run.
2. **Inspect the template.** Call `get_template` for the selected `slug` or
   `template_id`. Treat `templateContract` as the source of truth.
3. **Collect inputs.**
   - Collect every required input.
   - Ask about optional settings only when they affect the result in an obvious
     user-facing way, especially aspect ratio, number of outputs, number of
     visuals per output, and photo/style type.
   - Use contract labels when talking to the user; use contract names only in
     the `run_template` payload.
4. **Upload local files.** For local paths or attachments, call `media_upload`,
   run the returned `curl_example`, and pass the resulting `file_url` under
   `inputs.files`.
5. **Run the template.** Call `run_template` with namespaced inputs:
   - `inputs.prompts` for prompt/text inputs.
   - `inputs.files` for uploaded file inputs.
   - `inputs.urls` for URL branches of `url_or_files` inputs.
   - `inputs.fields` for checkbox/select values.
   - `inputs.settings` for aspect ratio and output counts.
6. **Poll, then deliver.** Poll `get_generation_status` with the returned
   `workflowId` / `promptId` until `finished`, `failed`, or `cancelled`, then
   deliver only the real final media URL(s).

## When uploading media

- Never pass local filesystem paths directly to `run_template`; use
  `media_upload` and pass the returned `file_url`.
- If a template input depends on a reference file and upload fails, stop before
  `run_template`. Do not run the template without the file just because the Nim
  MCP widget or template tool is available.
- In Claude Cowork, paths from the user's computer are never readable by the
  agent unless the file is in the current Cowork Working folder. If a file
  cannot be read, stop and ask the user to add it to the current Cowork Working
  folder, then retry from that accessible file.
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

## Failure Handling

- If `run_template` returns `insufficient_credits`, present the returned
  purchase/upgrade options and stop. Do not retry until credits are resolved.
- If generation fails, surface the returned `error` / `errorCode` plainly. Do
  not silently switch templates or change inputs without user confirmation.
- Never create local HTML artifacts, scripts, or mock runners instead of calling
  `run_template`.
