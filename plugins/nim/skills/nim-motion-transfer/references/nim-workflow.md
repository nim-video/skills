# Execution through Nim

Scenario logic belongs in the skill; Nim renders the clip, and the depth step runs
outside Nim. Use current Nim MCP contracts and job states. Do not substitute
provider-specific endpoints, assume fixed dimensions or durations, or retry
submissions automatically. The agent compiles the brief itself; no separate LLM
service is required.

## 1. Prepare the contract

Do not run this workflow for concepts or prompts. For an actual clip, first apply
[model-routing.md](model-routing.md), then call `models_explore` with `action: "get"`
for the chosen model. Do not retrieve every model's contract without a purpose;
summaries are enough for comparison.

Check all required fields, `allowedValues`, forbidden fields, minimum and maximum file
inputs, supported aspect ratios, supported durations, and output constraints. Set the
aspect ratio explicitly when one is required and supported, even if the model default
differs. Mentioning the shape in the prompt does not replace the actual parameter.

Execute only the requested scope. Apply the count, cost, and selection rules below.

## 2. Cost and variant count before submission

Before each paid stage, follow [pricing.md](pricing.md), obtain the current model
estimates and `get_credit_balance`. Catalog output pricing may exclude video-reference
charges: never announce that base as a confirmed total. Distinguish a full quote from
an empirical estimate and obey hard spending limits.
Use the single combined confirmation in SKILL.md before paid work. Include all
charges without explaining preprocessing. If full pricing is unavailable, disclose
uncertainty briefly and follow [pricing.md](pricing.md). Reuse existing approval
for the same settings and cost; do not ask separately for provider uploads.

Variants default to 1. A request for "a few options" means distinct prompts or a
supported `batchSize`, not an invented multiplier: batching repeats one prompt with
different seeds and can return near-identical clips. Different characters, wardrobes,
or languages are separate generations with separate prompts.

A multi-shot source does not automatically require multiple jobs. Honor one-pass
requests and use the full depth reference when it fits the contract. Only an authorized
split workflow multiplies job count; price each actual submitted duration, including
minimum-duration padding. Read [scenarios.md](scenarios.md) before deciding.

Fit the current stage to the available balance, without automatically withholding
credits for later stages. Let `B` be the lesser of available credits and the user's
remaining spending limit. For equal clip price `p > 0`, submit
`K = min(requested_count, max(0, floor(B / p)))`, using reference-inclusive prices. Keep separately billed depth-provider currency
out of this Nim-credit balance. An explicit user instruction to
reserve credits takes priority. Include the affordable count and cost in the single
confirmation; explain a shortfall only if it affects the request. After approval,
launch that count without further routine permission questions. If not even one clip is
affordable, start no job and explain the shortfall.

Keep unfunded requested work pending and clearly named. Do not silently drop it,
downgrade resolution, buy credits, or claim the whole task is complete.

## 3. Prepare the references

1. **Build the depth reference first.** Follow the contract in
   [depth-provider.md](depth-provider.md). One depth clip per source clip, reused across
   every character and wardrobe variant. For exact original soundtrack requests, use
   the post-generation path in [final-audio.md](final-audio.md); reuse silent depth
   or create it with `--no-audio`. Audio references guide performance, not exact copying.
2. **Upload the depth clip** with `media_upload` and execute its returned
   `curl_example` procedure with the file's real absolute path. Calling `media_upload`
   only returns the upload procedure; it does not mean the bytes have been uploaded.
   Verify a successful JSON response.
3. **Upload the identity and optional references** the same way.
4. **Pass only returned Nim `file_url` values** in `fileInputs`, in role order. A local
   path, data URI, attachment path, signed upload link, or invented Nim URL is not a
   `fileInput`. Quote paths correctly when using a shell, and do not add unrelated
   authorization headers.
5. For a reference that is hosted elsewhere, use a documented import method if one exists.
   A URL does not automatically become Nim-hosted. Do not pass a private URL that
   requires authentication headers; Nim's runner fetches inputs without them.

The order of `fileInputs` must match the roles in the prompt. Do not silently change it
between variants.

## 4. Generation parameters

Call `generate_video` only with fields permitted by both the current tool schema and the
model's `generationContract`. Current shared fields include `model_id`, `model_name`,
`prompt`, `fileInputs`, `requestedAspectRatio`, `mediaLength`, `resolution`, `fps`,
`keepSound`, `seed`, and `batchSize` - but a field's presence in the tool does not make
it valid for every model.

- `prompt` contains the finished prompt text, not a planning object or a request to
  compile a prompt.
- `mediaLength` is in milliseconds on the surfaces that use it. Match it to the usable
  motion in the source, not to the source file's total length.
- Do not pass resolution or aspect values the contract does not offer, and do not
  describe an upscale or a preset as an exact pixel guarantee.
- When a seed is allowed, use the schema's type. A seed reproduces a take; it is not an
  identity-preservation mechanism.

## 5. Asynchronous jobs

Record every returned `workflowId` / `promptId`, variant number, and chosen model
immediately after submission. A submission response is not a finished clip.

If a Nim widget is actually displayed and shows progress, use its normal behavior. Do
not promise a widget based on the client's name. Otherwise call `get_generation_status`
for each ID until `finished`, `failed`, `cancelled`, or `removed`.

Pace polling according to the tool's guidance and `estimatedDurationMs`; that estimate
covers processing, not queue wait. Exceeding it is not itself an error. Do not poll
every second. During long processing, give occasional meaningful updates only.

An `insufficient_credits` response with no accepted workflow means no job started. A
partial batch can still contain accepted workflows: preserve and poll all of them, and
report `failedCount` and errors separately. Do not replay an entire batch, resubmit an
uncertain job, or automatically fill failed slots with new paid calls. If the submission
response is lost, establish the status of the accepted job before doing anything else; a
blind repeat creates a second paid job.

## 6. Verify the result

For `finished`, obtain the real `mediaUrl` / `downloadUrl` values. If a URL is missing,
inspect the status response rather than guessing an address. Account for every requested
result, not only the first.

With visual inspection available, check the criteria in the skill's verification
section. Two failure modes are specific to this pipeline:

- **Appearance bleed.** If the source performer's face, wardrobe, or environment
  reappears, appearance data entered the motion channel. Rebuild the depth reference
  from a clean source rather than adding adjectives to the prompt.
- **Tail improvisation.** If the last second or two contains actions the source never
  performed - an invented prop, a lost character, a solo pose out of nowhere - the
  output ran past the reference's usable motion. Shorten the duration.

If the clip cannot be inspected, report that the job finished but visual compliance was
not checked. Do not claim corrected details without viewing the result. A quality issue
does not authorize many additional paid attempts.

## 7. Delivery and saving

When original audio is requested, generation completion is not task completion. Follow
[final-audio.md](final-audio.md): restore the original soundtrack as AAC-LC in the final MP4, verify
timing, codec profile and playback, then deliver that file. The Nim URL is the raw
generation and is internal: download it, inspect it, assemble the final file from it,
and do not show the URL to the user.

Keep delivery minimal: one link to the final local MP4 (stitched, with sound) and at
most one short sentence. Include only a material caveat, if needed. Omit model,
settings, cost breakdown, job identifiers and internal prompts unless the user asks.

Deliver only the final file. Never surface raw `mediaUrl` / `downloadUrl` / `previewUrl`,
silent generated clips, depth clips or individual parts of a split job in chat, on the
first take or on retries. This overrides generic "share the mediaUrl" guidance from other
skills. Downloading the generation for assembly and review is required, not a workaround.
Attach the local final file in the chat with the host's file tool (`SendUserFile` with
`display: "render"`, or `present_files`), as `nim-replace-character` does; use a normal local file
link only when no file tool exists. No inline `![](...)` for external URLs.

An explicit user request for an intermediate (for example "give me the raw clip" or
"send part 1") is the only case for providing one, and then provide what was asked, not
everything. Never describe a cloud link as a permanent local archive.

For continuation, retain the mapping
`variant -> prompt/settings/references -> model -> workflowId/promptId -> mediaUrl`, plus the
path of the depth clip. When a reference is no longer available, request it again;
"reuse settings" does not restore a missing file.

## 8. Errors and continuation

| Event | Next action |
|---|---|
| Nim MCP unavailable | Prepare the prompt and the depth plan as text; explain that a connected Nim service is required. Do not silently switch services |
| Not authenticated | Let the user complete the standard sign-in flow; do not search local files for tokens |
| Depth step key missing | Tell the user how to export it, then stop. Never ask for the key in the conversation |
| Depth step failed on an unusable source | Report the specific problem: multi-shot, below the pixel floor, unreadable motion, or a fetch failure. Fix the source, not the prompt |
| `media_upload` blocked by allowlist or egress rules | Stop before generation. Do not try alternate domains, proxy URLs, or invented `fileInputs` values. Report the blocker |
| Model not found or schema changed | Repeat discovery; do not guess an ID |
| Contract rejects the reference count or format | Reduce optional roles or convert the file. Never drop the motion reference or the identity reference to make a call succeed |
| Insufficient credits | Announce the revised affordable count based on full prices or documented bounds, or explain the shortfall. Do not lower quality, buy credits, or claim completion. Show `purchaseOptions`; the `nim-credits` skill handles buying |
| `Failed to register input media with the provider` / provider says the video is unreadable | The reference video is outside the provider limits (pixels, size, format). Rerun `scripts/prepare_video.py`, rebuild the depth reference from the prepared file; never blur |
| Image aspect-ratio error (`... between 2:5 and 5:2`) | Rerun `scripts/prep_images.py` and use its PNGs |
| Error text names moderation / safety / content / copyright | One retry of that job with a silent, music-free prompt line and `generateAudio: false` (the source soundtrack is restored later anyway). Never blur the source or the character images. A second rejection: tell the user which input is likely the cause, ask for another |
| `failed` a few seconds after the start (about 17 s), `errorCause` null, and the source shows recognizable real faces (film, TV) | The source was refused at intake. Blurring passes intake but the blur stays in the result. Tell the user this clip cannot be used and ask for another |
| `failed`, `errorCause` null, anything else | Tell the user, with the `promptId`. No blind retry |
| Contract rejects a parameter | Re-read `generationContract` with `models_explore` `get` and fix the call |
| Job queued or running | Keep tracking the same ID. Exceeding the estimate is not a failure |
| Submission outcome unknown | Establish the accepted job's status first; never submit a duplicate |
| Appearance bleed in the output | Rebuild the depth reference. Do not patch it with prompt adjectives |
| Invented action at the tail | Shorten the duration to the usable motion and regenerate only that clip |
| Output audio does not match the source | For an exact source soundtrack, replace generated audio after generation using [final-audio.md](final-audio.md); do not spend on regeneration to repair audio |
| Room tone changes at every cut | The fragments each generated their own audio. Reassemble with one audio bed instead of per-fragment audio slices |
