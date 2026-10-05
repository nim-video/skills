# Automatic model selection

## Closed model policy

Use only the following image models and configurations. Flux 2 Pro and Recraft V4.1 Pro have priority when compatible with the brief. FLUX 3 is a separate location option for explicit selection, comparisons, or constraints the preferred models cannot meet. Nano Banana Pro and GPT Image 2 Medium remain additional permitted choices for explicit requests, reference capacity, or task requirements. This is a routing policy, not a claim that one model always produces better images. FLUX 3's location detail and proportions do not establish better requirement adherence or justify making it a default for locations or other workflows.

| Approved model | Text-only generation | Generation with input images | Required configuration |
|---|---|---|---|
| Flux 2 Pro | Flux 2 Pro | Flux 2 Pro Edit | Only parameters exposed by its current contract; do not invent resolution control |
| Recraft V4.1 Pro | Recraft V4.1 Pro | The exact corresponding Pro Edit version only if verified in Nim; none found in the current catalog | Preserve V4.1 and Pro; current text model supports 2K |
| FLUX 3 | FLUX 3 | FLUX 3 Edit | Select the correct input mode; use a resolution and ratio permitted by both the live contract and generation tool schema |
| Nano Banana Pro | Nano Banana Pro | Nano Banana Pro Edit | Explicitly set `resolution="2K"` in both modes |
| GPT Image 2, Medium | GPT Image 2 text-input Medium variant | GPT Image 2 image-input Medium variant | Explicitly set `resolution="2K"`; select the Medium model variant |

Exclude base Flux 2, base Recraft, other Recraft versions, Nano Banana, Nano Banana 2, Nano Banana Lite, GPT Image 1/1.5, GPT Image 2 Low/High, and every unlisted family. Nano Banana Pro and GPT Image 2 must not switch to 1K/4K. Generic requests such as "best", "cheaper", "auto", or "use a template" do not relax these restrictions. Only an explicit request to change the configured policy broadens it.

## Decision order

First determine whether the user wants text or actual images. Concepts and prompts never trigger uploads or generation. For a render, identify reference count, aspect ratio, required resolution, budget, and any exact model choice; then filter the approved candidates for every hard constraint.

| Task | Automatic decision |
|---|---|
| Photographic interior, street, natural UGC background; no image supplied | Flux 2 Pro when compatible; otherwise consider Recraft V4.1 Pro and the permitted 2K alternatives |
| Sculptural editorial scene, expressive composition, illustration; no image supplied | Recraft V4.1 Pro when compatible; otherwise another approved candidate |
| One input image: preserve a room, change light/angle, or use visible design cues | Prefer Flux 2 Pro Edit if compatible; otherwise Nano Banana Pro Edit at 2K or GPT Image 2 image-input Medium at 2K |
| Multiple input images, exact product/character references, or a composite | Use an approved image-input candidate that accepts all references; Nano Banana Pro Edit is a useful first alternative when Flux cannot accept the count; compare GPT Image 2 Medium where compatible |
| Dense exact lettering or complex instruction-following is central to the location | Consider Nano Banana Pro 2K or GPT Image 2 Medium 2K; use their image-input versions if references are supplied; inspect lettering afterward |
| Strict 4:5, 2K, or another output constraint | Use an approved candidate supporting every condition; a text model cannot bypass the reference rule |
| FLUX 3 requested for a location or comparison | Select FLUX 3 for text-only input or FLUX 3 Edit for all supplied images; retain the brief's resolution/ratio and compare current costs |
| Native 4K or reference-based 4:5 that preferred models cannot satisfy | Consider FLUX 3 / Edit when its current contract and the generation tool accept every constraint; preserve all references |
| "Cheapest", "fast", a credit ceiling | Compare current estimates only within compatible approved configurations; do not lower the Pro/Medium tier or locked 2K resolution; do not invent speed guarantees |
| A named approved model | Use its exact approved configuration and the required input mode; explain an incompatibility before submission |
| No approved candidate fits | Prepare the prompt and explain the specific conflict; ask which constraint or policy may change; do not submit a substitute |

When multiple candidates fit equally well, retain Flux 2 Pro for realism and Recraft V4.1 Pro for art direction. Briefly explain a switch to FLUX 3, Nano Banana Pro, or GPT Image 2 using the actual task requirement, such as an explicit model choice or accepting all references. An explicit cheapest-model request may select a less costly compatible approved candidate even when a preferred family also fits.

## Input images always select image mode

- An image supplied for the current generation must reach an approved Edit/image-input model, including a moodboard, palette reference, portrait, room photo, or product photo. References reused from an earlier turn or a verified master frame also use image mode. Do not silently reduce a supplied image to a text description and call a text-only model.
- Roles control what transfers, not whether the image is submitted: geometry references preserve openings/furniture; style references transfer only visible motifs and may lead to new geometry. A portrait used to design a background contributes palette, textures, or shapes; explicitly exclude the person from the generated location unless inclusion is requested. Do not infer biography from appearance.
- Include every image supplied for the current task in the reference count. A room photo plus a palette moodboard counts as two inputs. Unrelated older attachments and images the user explicitly says to ignore are excluded. In concept/prompt-only mode, inspect references without uploading or generating.
- Do not drop a reference, make a collage, or chain edits as a purported equivalent to simultaneous multi-reference input. If none of the approved models accepts the count, resolve the conflict with the user.
- If the user requires Recraft V4.1 Pro for an image-based request and no verified corresponding Edit model exists, explain the conflict and offer an approved image-input candidate. Do not invent a Recraft Edit ID or silently create a new interpretation from text.
- If FLUX 3 Edit is unavailable or cannot accept the full reference count, consider Flux 2 Pro Edit, Nano Banana Pro Edit at 2K, or GPT Image 2 image-input Medium at 2K against all constraints. A hard FLUX 3 requirement must be resolved with the user before substituting another model. Do not fall back to text-only FLUX 3 or discard references.

## Discovery and exact variant selection

1. Use `models_explore(action="search", query=..., type="image", input=...)` for the relevant approved models. Search results may include unrelated models: filter them against the closed policy. For text-only requests, omit `referenceImageCount`; some connector versions reject zero. For image mode, supply the actual positive count in actions supporting that constraint.
2. Compare `inputTypes`, `capabilities.matchesConstraints`, `unsupported`, `maxFileInputs`, supported resolutions/ratios, and current price estimates. A missing limit is not unlimited capacity. Follow `next_page_token` when the needed variant is not in the current page. A recommendation result is subject to the same allowlist; it cannot authorize another model.
3. Resolve the exact version, tier, and input mode from returned metadata. FLUX 3's discovered selectors are `runwareFlux3ImageTextToImage` and `runwareFlux3ImageEdit`; verify the returned input mode and use the returned `model_id`, not a stored UUID or Flux 2 record from the same search. GPT Image 2 variants currently share one display name: name matching alone cannot distinguish Low, Medium, High, or image input. The discovered Medium selectors are `gptImage2TextToImageMedium` and `gptImage2ConsistencyMedium`. Use them to identify the returned records, then use their returned IDs. If metadata no longer establishes Medium, do not guess from price or name. Nano Banana Pro is a different model from Nano Banana 2 despite similar internal naming.
4. Call `get` only for the final candidate with actual constraints, including `resolution="2K"` for Nano Banana Pro/GPT Image 2. Check `generationContract.required`, `.optional`, `.forbidden`, allowed values, and input count. Medium is currently encoded in the selected GPT model variant, not an extra `quality` parameter; do not invent that argument.
5. Before `generate_image`, recheck the exact approved model/variant, input mode and all reference URLs, fixed 2K settings where required, aspect ratio, count, and budget. Pass the discovered `model_id` and actual `model_name`. If the contract conflicts with this policy, stop or select another compatible approved candidate; never omit a hard requirement just to make a call succeed.

Use the actually available tool name and schema, which may have a server prefix. Do not hardcode UUIDs or infer Nim capabilities from another provider's API.

For FLUX 3, preserve an explicitly requested resolution; otherwise use its live default. The 2026-10-05 catalog/contract exposes `0.75K`, `1K`, `2K`, and `4K`, with `1K` as default, but the current `generate_image` schema accepts only `1K`, `2K`, and `4K` among those values. Do not submit `0.75K` merely because discovery advertises it. If it is required, explain the schema conflict; do not silently replace it. Recheck both interfaces at execution time. FLUX 3 text forbids `fileInputs`; FLUX 3 Edit requires them.

## Verified guidance, not a static contract

Capability guidance as of 2026-09-09:

| Approved variant | Input | Significant constraints |
|---|---|---|
| Flux 2 Pro | text | No exposed resolution selector |
| Flux 2 Pro Edit | image | At most one image; no exposed resolution selector |
| Recraft V4.1 Pro | text | 2K; no corresponding Edit model found |
| Nano Banana Pro / Pro Edit | text / image respectively | 2K supported; Edit accepts at most 14 images |
| GPT Image 2 Medium, text / image variants | text / image respectively | 2K supported; image variant accepts at most 10 images; all quality variants share a display name |

FLUX 3 guidance verified on 2026-10-05:

| Approved variant | Input | Significant constraints |
|---|---|---|
| FLUX 3 | text | Selectable 1K/2K/4K through the current generation tool; default 1K; supports 4:5 and 21:9; `fileInputs` forbidden |
| FLUX 3 Edit | image | Requires 1–10 images; selectable 1K/2K/4K; supports 4:5, 21:9, and `auto` |

An input photo plus exact 4:5 is now compatible with FLUX 3 Edit when its current contract and tool schema still support those constraints. Text-only Recraft's 4:5 support cannot resolve a reference-input conflict. Recheck MCP before every actual run; current contracts and tool schema take precedence over these dated capability snapshots, while the closed model policy remains in force. Verify actual output dimensions separately; an accepted ratio is not proof of exact pixels.
