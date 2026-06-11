---
name: nim-b-roll-seedance
description: Use when creating product or lifestyle b-roll videos from a user brief with optional product, character, and location reference images, especially when the output should be generated with Nim Seedance. Handles brief intake, missing-input checks, reference mapping, Seedance prompt drafting, approval checkpoints, Nim upload/generation, and iteration.
---

# B-roll Seedance

Create controlled product/lifestyle b-roll videos from a brief and reference images. The workflow is intentionally staged: the user should be able to inspect and approve each meaningful step before generation.

## Core Flow

1. Intake the brief: brand/product, audience, tone, claim, desired format, and any constraints.
2. Inspect all provided images that are accessible as attachments or local files.
3. Group references by role internally: product, character, location, or style/mood.
4. Ask only for missing details that materially affect generation. If the user says they have nothing else, proceed with explicit assumptions.
5. Build an internal `reference_map` and structured payload. Do not dump them into chat by default.
6. Show the user a short human summary of the planned creative direction and, when image roles could be confused, a concise role confirmation in plain language.
7. Draft the Seedance prompt internally. Share the full prompt only if the user asks or prompt approval is part of the current collaboration.
8. Use Nim with Seedance 2 Standard, upload references in the exact internal `@img` order, generate, poll until terminal status, and return the real media URL.
9. Iterate from the result, then update the internal payload/prompt only after the user agrees.

## Reference Rules

- Images that should be used as visual references must be attachments or accessible local files. Inline-only visible images are not enough for upload.
- If the user expects an inline-only image to be used, ask them to attach it as a file or provide a local path/URL. Do not pretend it was uploaded.
- If no reference image is available for a role, continue prompt-only for that role when the user approves or says they have no more assets.
- Never let attachment order silently define creative meaning. The internal `reference_map` is canonical.
- The prompt labels and Nim `fileInputs` order must match the internal `reference_map` exactly.
- Multiple references per role are allowed. Clarify or infer whether they represent the same product from different angles, one character identity plus outfit/style references, multiple characters, one location from different angles, or multiple locations.
- Seedance 2 supports up to 9 image references through Nim. If the user provides more than 9, prioritize product identity/detail refs, then character identity refs, then primary location refs, then secondary mood/style refs. Ask which to drop only if the choice is ambiguous.

Internal reference map shape:

```yaml
reference_map:
  "@img1":
    role: product
    file: /path/to/product.webp
    visual_check: black structured shoulder bag with gold hardware
    use_as: product identity, silhouette, texture, hardware
  "@img2":
    role: character
    file: /path/to/character.png
    visual_check: woman with pink bob hair and pale translucent dress
    use_as: character identity and styling mood
  "@img3":
    role: location
    file: /path/to/room.jpg
    visual_check: dim cozy bedroom with lamp and string lights
    use_as: first location, lighting, spatial mood
```

## Payload Rules

Keep payloads internal, concise, and operational. Include:

- `project`: brand/product, claim, audience, tone.
- `references`: confirmed `@img` map, roles, visual checks, and intended use.
- `generation_defaults`: model, duration, aspect ratio, resolution, audio, camera, product logic.
- `locations`: at least three locations, marking which are reference-anchored and which are generated from prompt.
- `creative_direction`: concept, actions, mood, style.

Do not include web/source links in the payload. If a URL is present in the brief, it may be used to understand product facts, but omit it from the payload and prompt unless the user explicitly asks.

Do not show the payload to the user by default. Instead, summarize only what matters:

```text
I’ll make a 15s vertical b-roll clip with three locations: bedroom, hallway/elevator, and city exterior. I’ll use the bag as the product reference, the portrait as the character reference, and the room as the first location anchor.
```

## Location And Editing Rules

Every 15s b-roll video should include at least 3 visually distinct locations, even if the user provides fewer location references.

- Use provided location refs as anchor locations.
- Invent missing locations from the brand, product, audience, tone, and brief.
- Keep all locations in one coherent campaign world.
- Explicitly name the locations in the payload and prompt.
- Do not ask for more location refs unless the location choice is creatively critical.

A location is not a single shot. Within each location, include multiple b-roll cuts and shot sizes when timing allows:

- wide or establishing shot
- medium action shot
- close insert of hands, product, strap, closure, surface, face, mirror, feet, or texture

Default 15s structure:

```text
0-5s: Location 1, 2-4 quick b-roll cuts.
5-10s: Location 2, 2-4 quick b-roll cuts.
10-15s: Location 3, 2-4 quick b-roll cuts.
```

## B-roll Motion Grammar

Default motion should feel like practical b-roll, not a miniature fashion narrative.

- The character performs grounded everyday actions: waking, dressing, packing, checking a mirror, picking up/opening/adjusting/carrying/placing the product, walking through spaces, pausing, reaching, turning, sitting, or standing.
- Camera is mostly static or locked-off.
- Occasional slow push-in, rack focus, or very gentle handheld detail shot is fine.
- Avoid excessive camera travel, dramatic orbiting, music-video motion, over-acted performance, and artificial product spins.
- Rhythm should come from edits, character action, hand movement, product handling, and detail cutaways.

Use this prompt clause by default:

```text
B-ROLL RULE: Make this feel like a sequence of natural lifestyle b-roll shots, not a dramatic fashion film. Most shots are locked-off or nearly static. The character performs grounded everyday actions. Keep movements small, useful, and believable. The product is present through handling and wear, not through artificial hero spins.

EDITING RULE: Use quick natural b-roll cuts inside each location. Do not treat each location as one continuous take. Within each location, alternate static wide/medium shots with close inserts of hands, product details, straps, closures, hardware, face, mirror, surfaces, and walking feet.
```

## Seedance Prompt Shape

Base prompts on the useful structure from the b-roll generator pipeline:

```text
15-second hyper-realistic cinematic commercial, vertical 9:16, 720p.
STYLE: ...
PRODUCT REFERENCES: ...
CHARACTER REFERENCES: ...
LOCATION REFERENCES: ...
CAMERA: ...
LIGHTING: ...
SOUND: foley only; no spoken words, no subtitles, no overlay text.
B-ROLL RULE: ...
EDITING RULE: ...
LOCATION RULE: at least three distinct locations...
SCENE FLOW:
0-5s - LOCATION 1. Use 2-4 quick static b-roll cuts: ...
5-10s - LOCATION 2. Use 2-4 quick static b-roll cuts: ...
10-15s - LOCATION 3. Use 2-4 quick static b-roll cuts: ...
END: ...
```

For multiple references, write the role explicitly:

```text
PRODUCT REFERENCES: @img1 and @img2 show the same product. Use @img1 for silhouette and @img2 for details. Keep one consistent product.
CHARACTER REFERENCES: @img3 and @img4 refer to the same character unless stated otherwise. Preserve identity from @img3; use @img4 only for wardrobe/style.
LOCATION REFERENCES: @img5 anchors the first location. Generate additional coherent locations from the brief.
```

## Nim Generation

Use the Nim MCP video workflow.

- Preferred model: Seedance 2 Standard, not Fast. In Nim this is currently `Seedance 2` / `seedanceV2ImageToVideo`.
- Always inspect the current Nim model contract with `models_explore action=get` before generation.
- Defaults unless the user asks otherwise: `requestedAspectRatio: 9:16`, `resolution: 720p`, `mediaLength: 15000`.
- Upload local/attachment references with `media_upload`; use the returned file URLs in confirmed `@img` order.
- Pass only parameters allowed by the model contract.
- Poll with `get_generation_status` until `finished`, `failed`, or `cancelled`. Do not describe a queued/running job as done.
- 15s Seedance generation usually takes 5-6 minutes, is rarely faster than 4 minutes, and can take longer. Use a sparse polling cadence:
  - Check once soon after launch to confirm the job was accepted/started.
  - Do not check repeatedly during the first 4 minutes unless the user asks.
  - After 4 minutes, poll about every 60-90 seconds.
  - Avoid narrating every `running` poll; give occasional concise status only when useful.
  - Do not treat `running` as anomalous before at least 8-10 minutes unless there is an explicit error.

## Approval Checkpoints

Default approval checkpoints are lightweight and user-facing:

1. Brief/asset sufficiency: ask only if something materially needed is missing.
2. Image role confirmation: only when roles are ambiguous or easy to mix up; use plain language, not raw `@img` maps.
3. Creative direction confirmation: short summary, not the internal payload.
4. Generation launch confirmation.

If the user explicitly says to move faster or skip confirmations, still make sure image roles are not ambiguous before upload/generation. Share raw `reference_map`, payload, or prompt only when the user asks to inspect or control that layer.
