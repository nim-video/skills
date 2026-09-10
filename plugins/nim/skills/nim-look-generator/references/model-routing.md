# Automatic Nim Model Selection

This policy selects Nim **image renderers**. The current assistant performs styling, prompt construction, checks, and MCP orchestration; do not select a Nim image model to perform the assistant's system-prompt logic. **Nano Banana Pro is the primary outfit renderer**, with its Edit variant for reference input. This is the user's preference policy, not a comparative benchmark. Obtain UUIDs, `modelValue`, prices, and capabilities from the live Nim MCP catalog.

## Algorithm

Apply this algorithm separately to casting and outfits. **Casting is pinned to Recraft V4.1 Pro** under [face-first.md](face-first.md); automatic alternatives and cheapest-model rules below apply to outfit jobs, not to this mandatory portrait. Only an explicit user override changes the casting model. Check both stages before paying for either.

1. Identify hard requirements: output=image; text or reference input; number of photos **actually submitted**; exact clothing/identity; aspect ratio; resolution, if specified; and budget. In the standard casting path, every new person-bearing outfit has the generated portrait as one required identity input. Explicit identity/no-casting overrides use the actual references established under `face-first.md`. Editing requires a reference even when the instruction is textual, such as "change the background."
2. If the user names a model, find its exact variant and check compatibility. With photos, "Nano Banana Pro" means Nano Banana Pro Edit, while "Flux2" means the compatible Flux 2 Edit variant. A host-assistant model selection is separate from an image-renderer preference. If the user pins an incompatible image endpoint, explain the limitation and offer a concrete alternative before spending.
3. In auto mode, begin with `models_explore(action="search", query="Nano Banana Pro", type="image")`. Add the correct `input` when known; match the exact Pro or Pro Edit name rather than another Nano Banana variant. Inspect `inputTypes`, `maxFileInputs`, aspect ratios/resolutions, and `unsupported`. Paginate when necessary. Use the supported 2K outfit default unless the user specifies another resolution; the current contract always governs.
4. Choose compatible Nano Banana Pro / Pro Edit using the table below. Neither `isChatRecommended` nor first position overrides this policy. Reject `matchesConstraints=false`; if absent, explicitly check every constraint. The Pro default does not require an additional request for premium quality.
5. If Nano Banana Pro cannot satisfy the requirements, or the user explicitly requests another model or a lower-cost option, search compatible Flux 2/Recraft fallbacks. For photographic/person edits consider Flux 2 Edit; for text-only stylized output consider Recraft. Never use text-only Recraft for a required identity image. If needed, use `recommend` with the concrete task, `input`, `referenceImageCount`, `aspectRatio`, and requested `resolution`. Search/list further when recommendations are incompatible. Prioritize identity preservation when required. Explain a material fallback; an exact model pin requires the user's choice before substitution.
6. Call `get` for the final candidate using the ID returned by the catalog. Check `generationContract.required`, `.optional`, `.forbidden`, allowed values, min/maxItems, and final cost/capability constraints. If the summary and contract disagree, follow the contract and select another candidate. Do not fetch every model's full details in advance.
7. Before the first job, briefly name the model and the material reason for choosing it or departing from the preferred families. A price is a current estimate, not a fixed promise. Auto-routing to a compatible model within the known budget does not require separate confirmation.

## Preference Matrix

| Requested result | First compatible choice | Next choice |
|---|---|---|
| Initial face for a new visual series | Exact Recraft V4.1 Pro | No automatic substitution; follow the face-stage blocker/override rules |
| Photographic lookbook/new adult person | Nano Banana Pro Edit using the completed casting portrait | Compatible Flux 2 Edit/Pro Edit, then another image-input model |
| Explicitly skip casting; first person-bearing outfit without any references | Nano Banana Pro text-input; its first outfit establishes identity | Compatible Flux 2, then another text-input model; subsequent looks use the first output as a reference |
| Outfit-only / ghost / flat lay without exact photo references | Nano Banana Pro text-input | Compatible Flux 2 for photographic output or Recraft for stylized output |
| Person-free fashion illustration, form/color study, stylized outfit | Nano Banana Pro text-input | Compatible Recraft, then Flux 2 |
| Stylized look preserving the cast character | Nano Banana Pro Edit with the portrait | Another compatible image-input model; never drop identity for text-only Recraft |
| One reference input: face, clothing, or existing image | Nano Banana Pro Edit | Compatible Flux 2 Edit/Pro Edit, then another image-input model |
| Multiple mandatory photos | Nano Banana Pro Edit within the live input limit | A compatible fallback, preserving every required reference and identity |
| Specified spending limit | Nano Banana Pro if the complete pipeline fits | A compatible lower-cost outfit model if needed; the mandatory casting model remains fixed |
| Explicit cheapest-option request | Lowest current estimate among suitable outfit models, checking Flux 2/Recraft | Another compatible family; count casting separately and retain all hard requirements |
| 2K/4K or an unusual aspect ratio | Compatible Nano Banana Pro / Pro Edit | Another compatible model; an agreed upscale/crop as a separate operation |
| User names any other Nim model | That model, if compatible | Only an alternative authorized by the user |

## Reference Limits

Count every photo actually submitted: base edit, identity, products, and visual inspirations. One file containing several items may be one input, but the prompt must list every mandatory item. Several views of one item mean one item and several inputs.

The casting portrait is an actual input even when the user supplied no photos. Portrait alone means one input; portrait plus one exact product photo means two. Both fit the checked 1–14 image-input Nano Banana Pro Edit contract when the other requested parameters are supported. The one-image Flux 2 Edit limit matters only when considering that fallback or an explicit Flux request. Recraft's text-only endpoint may create the initial portrait or a person-free outfit fallback, but cannot receive the portrait to preserve identity in a person-bearing look. Do not replace an identity image with its textual description.

Do not shorten the mandatory photo list, turn an exact product/identity reference into a textual description, or silently combine photos into a contact sheet to fit a limit. If an extra photo is only loose inspiration, you may first translate its visible fashion cues into text and omit it from downstream inputs; record that choice in the brief. This is allowed when the user requested inspiration, not preservation of an exact composition. A textual blend of this kind makes Recraft usable without reference inputs. If `maxFileInputs` is unknown, do not assume unlimited capacity: check the final contract. If no limit is published anywhere, compatibility with the input count remains unconfirmed; choose a documented candidate or obtain clarification from the service before submission.

## Verified Catalog Snapshot, 2026-09-09

These data came from read-only `models_explore search/recommend`; Nano Banana Pro and Pro Edit were also checked with final `get` contracts. They are neither API constants nor generation test results.

| Nim catalog model | Input / maximum photos | Aspect ratios / resolution shown by the catalog | Estimated credits at the returned default |
|---|---|---|---|
| Nano Banana Pro | text | 16:9, 9:16, 1:1, 4:3, 3:4, 3:2, 2:3; 1K/2K/4K, default 2K | 25 |
| Flux 2 | text | 16:9, 9:16, 1:1, 4:3, 3:4, 3:2; resolution not published | 3 |
| Flux 2 Edit | image / 1 | Same aspect ratios; resolution not published | 3 |
| Flux 2 Pro | text | Same aspect ratios; resolution not published | 6 |
| Flux 2 Pro Edit | image / 1 | Same aspect ratios; resolution not published | 6 |
| Recraft V4.1 | text | Also 2:3, 5:4, 4:5; 1K | 7 |
| Recraft V4.1 Pro | text | Same Recraft aspect ratios; 2K | 40 |
| Nano Banana Pro Edit | image / 14 | 16:9, 9:16, 1:1, auto, 4:3, 3:4, 3:2, 2:3; 1K/2K/4K | 25 |
| Seedream 4.5 Edit | image / 6 | 16:9, 9:16, 1:1, auto, 4:3, 3:4 | 10 |
| Seedream 5 Lite Edit | image / 10 | Same Seedream aspect ratios | 7 |

In the checked results, even a recommendation request for four photos at 4:5 returned three edit models with `unsupported=["aspect ratio 4:5"]`. Do not submit them as a ready solution for 4:5. Continue searching; if no compatible model exists, offer a supported aspect ratio or a separately agreed crop. Changing the prompt text alone does not establish 4:5 support.

When `resolution` is not published, do not add the parameter automatically. The source application displayed "2K" for Flux, but that does not establish that `resolution="2K"` is available in Nim. Recraft does not guarantee SVG/transparency and does not accept `style_id`, `negative_prompt`, or other external API parameters unless the current Nim contract exposes them.

A supported aspect ratio is a model request, not proof of exact output pixel geometry. When exact geometry matters, inspect the delivered width and height: models may quantize dimensions. Report the actual dimensions and agree on any necessary crop instead of claiming exact conformance from `requestedAspectRatio` alone.
