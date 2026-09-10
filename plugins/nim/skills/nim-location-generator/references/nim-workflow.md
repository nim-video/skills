# Execution through Nim MCP

Scenario logic belongs in the skill; Nim creates the image. Do not carry over the archive's fal endpoints, Cloudflare Workflow, D1/R2, Gemini/OpenRouter, fixed dimension schemas, or automatic submission retries. The agent compiles the brief itself; no separate LLM service is required.

## 1. Prepare the contract

Do not run this workflow for concepts or prompts. For an actual image, first apply [model-routing.md](model-routing.md), then call `models_explore` with `action="get"` for the chosen model. Do not retrieve every model's contract without a purpose: summaries are sufficient for comparison.

Check all required fields, allowedValues, forbidden fields, minimum/maximum inputs, and output constraints. Verify the exact model/version/tier against the closed policy before submission. For Nano Banana Pro and GPT Image 2, require and send `resolution="2K"`; for GPT Image 2, verify the Medium variant and correct input mode despite its shared display name. Set `requestedAspectRatio` explicitly when a ratio is specified and supported, even if the model's default differs. Mentioning the ratio in the prompt does not replace the actual API parameter.

Execute only the scope authorized by the user. Default to one render. When a budget is specified, use the current price estimate and job count; if the price is unknown or the batch exceeds a hard limit, clarify before paid submission. An ordinary image request does not require a separate confirmation ritual; retain mandatory host approval mechanisms.

## 2. Prepare images

1. Visually inspect available references and assign roles. Every image supplied for the current generation counts as an input, including style, palette, and portrait references. Select a permitted Edit/image-input model accepting that full count; never silently omit an image to fit a contract. Do not upload in concept/prompt-only mode.
2. For a local file or attachment, call `media_upload`. Execute the returned `curl_example` procedure with the file's real absolute path and verify a successful JSON response. Calling `media_upload` only provides the upload procedure; it does not mean the bytes have been uploaded.
3. Pass the returned `file_url` to generation, not a local path, data URL, attachment path, upload URL, or invented Nim URL. Quote paths correctly when using a shell; do not add an unrelated Authorization header or expose signed upload links.
4. For a previously uploaded file or finished Nim result, use the available `file_url`/`mediaUrl` directly if the current contract accepts it. Do not substitute a project page or preview URL for the media itself.
5. An external link does not automatically become Nim-hosted. Use a documented import method if available. Otherwise, retrieve the file using a permitted tool and upload it through Nim, or request an accessible attachment. Do not bypass host restrictions on downloading media.
6. Check format and size against the current `media_upload` contract; do not apply the old UI's 10 MiB limit. If conversion or resizing is necessary, use an available permitted method, preserve the original, and disclose a meaningful loss of detail. If this is unavailable, request a compatible file.

The order of `fileInputs` must match the roles in the prompt. Do not silently change it between variations.

## 3. Generation parameters

Call `generate_image` only with fields permitted by both the current tool schema **and** the model's `generationContract`. Current shared fields include `model_id`, `model_name`, `prompt`, and sometimes `fileInputs`, `requestedAspectRatio`, `resolution`, `seed`, and `batchSize`. A field's presence in the tool does not make it valid for every model.

- `prompt` contains the finished prompt text, not a planning object or the original instruction to "compile a prompt".
- Do not pass `resolution` to Flux 2 Pro/Pro Edit when get forbids it. Do not describe such an output as guaranteed 2K/4K.
- Do not pass `fileInputs` to text-only Recraft V4.1 Pro or another text-only variant. A supplied image requires an approved Edit/image-input model; switching to text-only is unacceptable unless the user explicitly removes that reference requirement.
- For Nano Banana Pro/Pro Edit and both GPT Image 2 Medium input modes, send `resolution="2K"`; a prompt mention or default is insufficient. GPT Medium is currently selected through the model variant, not an invented `quality` argument. Do not use Low/High or 1K/4K to satisfy budget or quality requests.
- Do not invent `negative_prompt`, `style`, `quality`, `width`, `height`, `image_size`, `image_urls`, `strength`, a mask, or an arbitrary API endpoint. Style and lighting instructions belong in the prompt; masked edits and other specialized operations require a corresponding tool/contract.
- When seed is allowed, use the schema's type (currently a string). It is not a location-preservation mechanism. In current Nim, `batchSize > 1` creates separate workflows with randomized seeds.

## 4. Asynchronous jobs

Record every returned `workflowId`/`promptId`, variation number, and selected model immediately after submission. A submission response is not a finished image.

If a Nim widget is actually displayed and shows progress/results, use its normal behavior. Do not promise a widget based on the client's name. If no widget is displayed, call `get_generation_status` for each ID until `finished`, `failed`, `cancelled`, or `removed`.

Pace polling according to the tool's guidance and `estimatedDurationMs`; this estimates processing time without queue wait. Exceeding the estimate is not itself an error. Do not poll every second. During long processing, provide occasional meaningful updates and observe host waiting limits. If an external limit interrupts execution, preserve the ID and clearly state that the job is unfinished; on continuation, check that job instead of creating a new one.

`insufficient_credits` means the job did not start. Show the actual options from the response when relevant. An image request does not authorize a purchase or upgrade. Obtain a checkout link through `purchase_credits` only when the user asks.

If the submission response is lost, do not blindly repeat `generate_image`: that may create a second paid job. Check using the returned ID. If no ID is available and the tool offers no way to determine the outcome, disclose the uncertainty and wait for a decision about resubmission. For a validation error before job creation, correcting the parameters and retrying once is acceptable; a repeated identical rejection requires investigation. A terminal failure does not justify endless cycles of new generations.

## 5. Verify the result

For `finished`, obtain real `mediaUrl`/`downloadUrl` values and `outputs` entries when present. If a URL is missing, do not guess an address; inspect the status/response. Account for every requested result, not only the first.

When visual inspection is available, check:

- The place, art direction, framing, and key requirements.
- The clear character staging area and correct foreground treatment.
- People, including reflections, text, and unintended dominant objects.
- Geometry, perspective, furniture support, shadows, and reflections.
- For edits/series: the positions of windows, doors, furniture, and recognizable details.
- Actual pixel dimensions from output metadata or the displayed image, including both resolution and aspect ratio. Compare width/height with the requested ratio; an accepted `requestedAspectRatio` or a reported `resolution` label is not proof of exact output dimensions.

If actual dimensions differ from a requested format, report the requested ratio and actual pixel size. Do not silently call an approximate preset an exact ratio or crop/pad the original to conceal the mismatch. When an exact delivery canvas is required, resolve the sizing step explicitly using the user's constraints and available permitted tools.

If the image cannot be inspected, report that the job finished but visual compliance was not checked. Do not claim corrected details without viewing the result. A quality issue does not authorize many additional paid attempts: use the permitted iteration count or prepare a specific edit for the next request.

## 6. Delivery and saving

Keep delivery concise: result/link → model, aspect ratio, variation number → material caveat, if any. Do not expose the full internal brief or a long prompt without a request.

Follow the host's media rules. If the Nim widget already displays the result, use it. Without a widget, return a real `mediaUrl`/`downloadUrl` as a normal link, without inline `![](...)` for an external Nim URL. In Codex, format it as `[Open image](actual URL)`. Do not download an image solely to bypass an external-embedding restriction.

"Download/save" is a separate user intent: use the real download URL and available host capabilities. If local saving is unavailable, return an accessible link and state the limitation honestly. Saving the original does not imply converting PNG to JPEG; preserve the available original format. Never describe a cloud link as a permanent local archive.

For continuation, retain the mapping `variation → brief/settings/references → model → workflowId/promptId → mediaUrl` in context. When previous references are unavailable, request them again; "reuse settings" does not restore a missing image.

## Integration basis

The package is a standalone skill folder suitable for `plugins/nim/skills/nim-location-generator/` in [nim-video/skills](https://github.com/nim-video/skills). It does not require the original web application or other Nim skills.

Conventions were checked against [nim-generate](https://github.com/nim-video/skills/blob/main/plugins/nim/skills/nim-generate/SKILL.md), and reference-role separation against [nim-character-consistency](https://github.com/nim-video/skills/blob/main/plugins/nim/skills/nim-character-consistency/SKILL.md). Obtain exact fields and limits from the connected MCP at execution time.
