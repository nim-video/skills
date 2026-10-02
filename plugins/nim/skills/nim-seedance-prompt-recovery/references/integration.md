# MCP integration

Read this when executing, inspecting, or retrying a generation. Prompt-only drafting needs no MCP connection. This skill supplies agent instructions, not an MCP server or a new endpoint.

## Handoff from the calling workflow

Apply the prompt rules before the first Seedance draft and again after requested edits, template assembly, prompt enrichment, or a quality-review rewrite. On a failed submission or job, diagnose from the actual response. A defect in successfully generated media is a prompt revision, not evidence of a service rejection.

Before submission, retain the latest brief, exact prompt, discovered model ID/name, submitted settings, ordered reference-role map, successful upload URLs, and remaining authorized attempts/budget. Status responses may omit reference assets or audio settings. Keep the original request and each revision separately; this is local workflow state, not an extra API payload.

When another workflow calls this skill, preserve its presentation and reuse its completion review when available. For standalone use, follow this skill's response format and completion checks. Preserve reference identifiers, upload order, exact dialogue, segment boundaries, and earlier accepted outputs. Apply this skill's facial-reference and sound rules to the final prompt without changing unrelated requirements. For a chain or batch, work on the affected item and retain successful siblings.

## Bind to the connected contract

Discover the available tools and inspect their current schemas. The operation and field names below describe a compatible connector shape; use them only when the connected tool exposes them. Do not send these names unchanged to a different adapter.

For a template-backed job, retain the template's own invocation and contract. Apply this skill when metadata or the actual job identifies Seedance; do not guess a hidden backend. Revise only exposed prompt/input fields and supported settings. If the needed control is unavailable, report that limit rather than inventing a field or switching to raw generation. The model-discovery and `generate_video` steps below apply to direct generation.

| Step | Contract and data to carry forward |
|---|---|
| Select | Discover the model for the requested Seedance version and input mode. Use the returned ID in `models_explore(action: "get", model_id: ...)` when available. Read `generationContract.required`, `optional`, `forbidden`, and conditional descriptions. |
| Upload | Use the supported upload/import operation. If `media_upload` returns upload instructions, perform the actual upload and obtain its successful `file_url` before submission. An upload instruction alone is not an uploaded asset. |
| Submit | Build `generate_video` from the intersection of its tool schema and the selected model's contract. Pass only supported generation fields, preserving units, types, prompt length, reference counts and mode-specific exclusions. |
| Track | Record every returned `workflowId` / `promptId` immediately. For a batch, track every entry in `workflows`, not just the top-level ID. |
| Observe | Use `get_generation_status` with a returned `workflowId` or `promptId`. Never substitute an upload ID, project ID, media URL, or guessed job ID. |
| Deliver | Collect actual media from `outputs` when present and top-level `mediaUrl` / `downloadUrl`; avoid showing the same output twice. A `generationUrl` is a job page, not proof of a finished media file. |

### References and audio

- For the connector shape above, `fileInputs` contains uploaded image references; advanced modes may expose separate `referenceVideos` and `referenceAudios`. Preserve order within each type and match the prompt's reference roles. Do not put voice audio into an image-only array.
- Audio references may require at least one image or video reference. Discover a compatible mode before upload/submission; do not silently drop a required voice reference or invent another asset to satisfy the contract.
- A tool-level optional field is not necessarily allowed by the chosen model. For example, `generateAudio` is a boolean on compatible advanced modes; ordinary text/image modes may forbid it. Only use `generate_audio: "off"` with an adapter whose own schema exposes that exact enum. Neither spelling is a universal switch.
- With generated speech/effects requested, keep supported audio generation enabled and express “no music” in the prompt. There may be no music-only parameter. Do not turn all audio off to implement a music-only exclusion.
- For a Seedance 2.5 edit contract exposing `sourceVideo`, inspect its conditional rules. In the connector shape above, supplying it preserves source duration/aspect ratio and excludes `referenceVideos`, `referenceAudios`, `mediaLength`, and `requestedAspectRatio`; `fileInputs` may supply additional image references. Do not blindly copy settings from a new-video request into edit mode. Verify source-audio retention separately.

## Submission and job outcomes

Distinguish MCP transport/tool errors from job state. A tool-level `isError` or lost response does not establish that no chargeable job started.

| Observed response | Action |
|---|---|
| `queued` with `workflows` | Save and observe every accepted job. No finished output exists yet. |
| Accepted workflows plus `failedCount` / `errors` | Preserve accepted jobs and report the unaccepted portion. Diagnose the returned errors; never retry the whole batch automatically. A later attempt covers only the authorized failed portion. |
| `insufficient_credits` with `message` and no job | Report the operational blocker and any returned options. A wording edit cannot fix it; do not purchase credits or invent an ID to poll. |
| Validation/authentication/rate-limit/service error | Use the actual returned details. Correct only an evidenced payload/input problem or address the operational blocker. Do not infer a content rejection from an unrelated error. |
| Submit timeout or lost response | If an ID is known, poll it. Otherwise use documented lookup/recovery; if unavailable, disclose the unknown outcome and stop duplicate submission. Do not invent an idempotency parameter. |
| `queued` / `running` status | Observe the same ID. Pace polling with the tool's guidance and estimate; exceeding `estimatedDurationMs` is not rejection evidence. |
| `failed` status | Read `errorCause` when that field exists; it can be null. Retain any other actual diagnostic fields. Do not assume an `errorCode`, retryable flag, or structured moderation category is available. |
| `cancelled` / `removed` status | Treat as terminal without a rejection diagnosis. A new generation requires an authorized new request. |
| `finished` with actual output media | Proceed to the completion checks below, reusing the calling workflow's media review when available. |
| `finished` without usable output media | Recover output through documented means or report an incomplete result. Do not fabricate a URL, restart the job, or claim delivery. |

A wait cutoff belongs to the host workflow, not the model's moderation result. If the host must yield while the job is pending, preserve its ID for resumption and say it is pending. Do not promise background observation without a real supported mechanism.

## Bounded correction and completion

For a diagnosed failure, prepare the revised prompt, precise setting/input changes, and smallest retry scope before seeking any missing authorization. Existing authorization remains valid; diagnosis alone does not authorize a chargeable retry. Follow the main skill's limit of at most two revised submissions for the original failure within the remaining authorized budget. Count the whole retry chain across resumed turns; new retry IDs and partial batches do not reset that limit. If the previous submission's outcome is unknown, resolve it before another submission.

On success, reuse the calling workflow's existing media QA when available; otherwise perform these checks directly. Inspect each new output revision once, including successful batch siblings. Verify the intended action, reference continuity, requested dialogue and absence of unwanted music with available inspection tools. A status or audio-stream flag alone cannot prove those properties. Record any unverified checks. Avoid duplicate previews, repeated reviews on unchanged status polls, and recursive review of analysis-tool outputs.
