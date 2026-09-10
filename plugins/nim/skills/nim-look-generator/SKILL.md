---
name: nim-look-generator
description: Use when a user wants fashion looks, outfit ideas, a lookbook, wardrobe styling, virtual try-on, exact clothing from photos, or outfits inspired by images through Nim, including capsule wardrobes and follow-up outfit edits. Recognize natural requests across languages. Includes advice and prompt-only requests. Excludes location-only images, unrelated portraits, shopping searches, and finished video production.
---

# Nim Look Generator

Turn the user's wishes into concrete fashion looks and, when visualization is requested, create them through **Nim MCP**. Respond in the user's language. Write production image prompts in English unless the user chooses another language. **Every new visual look series starts with an original, distinctive face generated through Recraft V4.1 Pro.** Then use that completed portrait as the identity reference for looks rendered by **Nano Banana Pro**, selecting **Nano Banana Pro Edit** when references are present. This face stage is mandatory, not an optional quality upgrade.

## Model responsibilities

The **current assistant model running this Skill** performs the stylist and system-prompt logic: understand the user's wishes, inspect references, resolve controls, design the wardrobe, assemble and check the production prompts, select valid tool arguments, call Nim MCP, and review results. Do this work in the current conversation; do not introduce a separate fixed language model or a paid Nim text-generation step.

**Recraft V4.1 Pro renders the initial face. Nano Banana Pro renders the outfits.** These are image backends called by the assistant, not replacements for the assistant that follows the Skill. Give each image call the resolved visual prompt and relevant references, not the full Skill, system conversation, or an instruction to act as the wardrobe planner. Nim receives only fields exposed by its current contract; do not invent a `system_prompt` parameter.

## Activation and delivery

Recognize intent semantically across languages, without requiring the word "Nim" or an intake form for every setting:

- "Create/show/generate an outfit," "try this on me," "make a lookbook" → images.
- "What should I wear," "suggest combinations," "evaluate this outfit" → advice or an outfit plan; do not start paid generation without a visualization request.
- "Only the prompt," "do not generate," "ideas first" → text, without uploads or generation jobs.
- "Three more," "the same outfit from behind," "more natural," "remove the bag" → continue the current brief, changing only the named conditions.

**When `Prompt only` explicitly names the style setting in the current request, such as "Generate in Prompt only mode," it means free styling without presets (`styleMode=free`). Standalone "prompt only" means text without generation (`delivery=prompts`), including a later message that overrides an earlier generation request.** An explicit "do not generate" determines text delivery regardless of the style setting.

See [scenarios.md](references/scenarios.md) for the complete intent map. Do not activate from an isolated word such as "look" or "style" when the request concerns code, food, interiors, or another unrelated task. If explicitly invoked without a fashion task, clarify only the subject of the request.

## Build the brief from context

Capture delivery (`advice`, `prompts`, `generate`, `edit`), outfit count, free/general/specific styling, required items, exclusions, reference roles, subject mode, presentation, format, model preference, and budget. Read [brief-and-controls.md](references/brief-and-controls.md) for control semantics and precedence.

When a reasonable solution is possible, proceed with briefly stated assumptions. A bare "make an outfit" needs only one wearable free-style look. Ask one focused question only for a real conflict, an unavailable required file, or unclear identity assignment. A photo explicitly supplied as a garment for the outfit is already a mandatory product reference; do not ask again whether to preserve it.

Defaults: one outfit; `styleMode=free`; neutral clothing presentation; all additional controls OFF; a new fictional adult wearing the look; 16:9 lookbook sheet. For an explicitly requested single full-body image, default to 9:16; for a flat lay, 1:1. The user's explicit format overrides defaults but must be supported by the model. No selfie is needed to create a new character.

## Mandatory face stage

Read [face-first.md](references/face-first.md) before preparing a new visual series. Preflight the complete face-plus-outfits workload, then make the **first generation call** a single casting portrait through the exact **Recraft V4.1 Pro** model. Wait for its finished image and inspect it before submitting dependent outfit jobs. Do not substitute Recraft standard, Flux, a face description, or a reused seed for this stage.

Create one distinctive identity per new series, using concrete, coherent facial traits instead of a generic beauty formula. Keep it across all looks, front/back views, retries, and ordinary follow-ups. Generate additional faces only when the user requests different people or a new casting. Use actual image references to preserve identity; a prompt alone is insufficient.

Text-only delivery starts no jobs. An explicit request to preserve the user's supplied identity, reuse an existing character, or skip portrait generation overrides fictional casting; record the reason. An outfit-only/flat-lay format keeps the initial casting portrait as a separate asset and excludes people from the outfit images; it does not silently remove the face stage. See the reference for exact exceptions, costs, and dependency handling.

## Design the outfit

1. Separate image roles: **identity → exact product → inspiration**. Assign base-edit/background roles separately when requested. Inspect available images. Preserve every required item; text about the same item specifies its use instead of creating a duplicate. Translate inspiration palettes, textures, geometry, and rhythm into 2–4 coordinated clothing decisions.
2. For a general or specific preset, read selected entries from [style-library.json](references/style-library.json); selection rules and groups are in [style-catalog.md](references/style-catalog.md). Do not introduce presets into a free-style request. Concrete items, exclusions, and current wishes outrank every style menu.
3. Establish the closed clothing inventory before styling and accessories. Specify cut, material, color, fit, construction, and wearing method. Vary different outfits along unlocked axes; views of one outfit preserve the same inventory.
4. Prepare the internal plan and image prompt using [prompt-contract.md](references/prompt-contract.md). Keep JSON, technical fields, and reference indices out of ordinary user-facing replies. In prompts mode, deliver production prompts and a readable reference map. In advice mode, deliver concrete combinations and their rationale. Text-only modes finish here.

## Select the model automatically

Read [model-routing.md](references/model-routing.md) before generation or editing. Use current `models_explore` results, not provider names and limits copied from the original application.

Select image models separately from the host assistant. The face stage is pinned to **Recraft V4.1 Pro** unless the user explicitly overrides it. **Nano Banana Pro is the default outfit renderer**, including ordinary requests with no explicit quality upgrade. For outfit jobs, decision order is **hard requirements → explicitly selected model → compatible Nano Banana Pro variant → compatible fallback**. Respect the total budget throughout.

- Face, product, or base-image references present → **Nano Banana Pro Edit**, preserving the exact ordered reference roles. This includes new looks using the generated portrait, try-on, and follow-up edits.
- No image references in the outfit job → **Nano Banana Pro** text-input variant. This includes person-free flat lays and the explicit no-casting path without supplied images.
- Start at supported **2K** for outfits unless the user specifies another size; get the current contract and estimate first. Do not confuse Nano Banana Pro with Nano Banana, Nano Banana 2, or Lite because they share a family label.
- Flux 2 and Recraft are preferred fallback families only when Nano Banana Pro cannot satisfy the requirements or an explicit user preference/cost request calls for them. Recraft's text-only variant cannot preserve a face image. If those families also fail the hard constraints, find a compatible Nim model; do not discard mandatory references.

Catalog snapshot, not a promise: on 2026-09-09, Nano Banana Pro Edit accepted 1–14 image inputs and supported 1K/2K/4K; its text variant forbade image inputs. Recraft V4.1/Pro were text-only. Even a recommended model can return `matchesConstraints=false`. Check the constraints.

## Execute through Nim

Read [nim-workflow.md](references/nim-workflow.md) before the first generation/edit/upload operation in a task. Tool names may use prefixes such as `mcp__nim__...` or `mcp__codex_apps__nim_...`; discover callable tools instead of inventing a namespace.

1. Compare `models_explore` summaries (`search/list/recommend`), then call `get` only for each chosen stage model. Follow its `generationContract` exactly. Check the combined cost and downstream reference capacity before paying for casting.
2. Upload required local references through `media_upload` and execute its returned upload procedure. Use `file_url` from the upload response and preserve input order. Local paths are not `fileInputs`.
3. Generate the casting portrait first, wait for its completed `mediaUrl`, inspect it, and bind it to the series. Then call `generate_image` for the outfits with live model fields and only permitted parameters. Include the portrait in `fileInputs` for every new person-bearing outfit. Different outfits require separate prompts; `batchSize` provides variations of one prompt, not a list of different outfits.
4. Track every job through `get_generation_status` unless a real Nim widget displays its result. Accepted submission is not completion. Do not duplicate jobs still running.
5. Inspect completed images with an available viewing tool. Check garments, face, hair, outfit count, format, and continuity. State when visual inspection is unavailable. Follow the workflow's bounded correction/retry rules and budget constraints.

## Deliver the result

Use an existing native widget/media display; otherwise provide a clickable link to the actual `mediaUrl` or download result in the host's supported format. Do not embed external Nim URLs as inline images when the host blocks them. Name each variant and briefly explain differences. For partial success, deliver finished variants and identify failures separately.

Keep settings and job IDs in context for follow-up work. Use the scenarios and workflow for exports, retries, favorites, and upscaling. Do not promise a database, gallery, or cross-session persistence without a real saved file or available tool. Hand video work to an available Nim video workflow only when explicitly requested.

Sources and intentional differences from the web application: [provenance.md](references/provenance.md).
