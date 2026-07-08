---
name: nim-character-consistency
description: >-
  Create new Nim images of an existing character, person, product, object,
  mascot, avatar, or branded item while preserving visual identity across
  scenes, poses, lighting, outfits, or artistic media. Use for character
  consistency, consistent character images, identity-preserving edits, product
  consistency, same person/object in a new scene, or variants from one or more
  reference images. Discovers the current Nim model with models_explore, follows
  its generationContract exactly, uploads references with media_upload, and
  submits with generate_image.
---

# Nim Character Consistency

Create new images of an existing subject while keeping its visual identity
stable. Use Nim image generation with reference images and return only the
finished media URL plus key settings unless the user asks for implementation
details.

## UX rules

1. **English only by default.** Use English for all user-facing messages from
   this skill unless the user explicitly requests another language.
2. **Keep updates tiny.** Interim updates should be one short sentence,
   preferably under 12 words.
3. **Do not narrate plumbing.** Do not explain model discovery, contract checks,
   uploads, or polling unless the user asks.
4. **Use terse progress copy.** Prefer `Generating.`, `Still working.`, or
   `Done.` for normal progress.
5. **Return the result.** Final response should be the real media URL plus key
   settings used.

## Intake

Required:

- Reference image(s): one or more images of the subject.
- Suggestions: what should be depicted in the new image.

Optional:

- Number of images: default to `1`; use `2-4` only when the user asks for
  options, variations, or multiple outputs.
- Secondary images for objects, locations, poses, mood, lighting, or style.

If either reference image(s) or suggestions are missing, ask only for the
missing input before generating.

## Default Nim settings

Use Nim image generation.

- Default model: Nano Banana Pro Edit.
- Default search target: `Nano Banana Pro` with image input / edit capability.
- Default resolution: use the model default, normally `2K`, unless the user asks
  otherwise.
- Default batch size: `1`.

Always discover the current model with `models_explore`, then inspect the exact
model contract with `models_explore` using `action: "get"` before generation.
Pass only parameters allowed by the returned `generationContract`.

If the user requests another model, search for that model by name, get its
contract, and adapt to its allowed parameters. Examples include `gpt image 2`,
`Seedream`, `Flux`, or another Nim catalog model.

## Workflow

1. Collect the required inputs.
2. Upload each reference image with `media_upload` and keep the uploaded order
   stable. Use the returned Nim file URLs in `fileInputs`; do not pass local
   paths directly to `generate_image`.
3. Discover and get the model contract. Use only contract-supported generation
   parameters.
4. Build the identity-preserving prompt. If the user asked to approve the prompt
   first, show the prompt and wait. Otherwise, generate immediately.
5. Poll with `get_generation_status` until `finished`, `failed`, or `cancelled`.
   Do not describe the work as complete before a finished status returns real
   media.
6. Return the real media URL and key settings used: model name, resolution if
   set, aspect ratio if set, and number of images.

Do not dump raw JSON, internal IDs, workflow IDs, prompt IDs, upload URLs, or
long prompt mechanics unless the user asks.

## Prompt pattern

Start from this schema and fill it with concrete subject details inferred from
the reference images and the user's suggestions:

```text
The identical <subject> from @image1, reimagined in a <new scene, pose, lighting, or artistic medium>. The <defining identity traits: face, hair, key details> must remain exactly the same.
```

When multiple images are uploaded, reference them in upload order as `@image1`,
`@image2`, etc. This ordering is important so the model can distinguish one
image from another.

For multiple identity references of the same subject, name them together:

```text
The identical <subject> from @image1 and @image2, reimagined in <suggestions>. The <defining identity traits> must remain exactly the same.
```

For secondary references, specify their role:

```text
The identical <subject> from @image1, reimagined in the location from @image2 with the lighting style of @image3. The <defining identity traits> must remain exactly the same.
```

Preserve permanent identity traits such as face shape, facial features, hair
shape/color, markings, proportions, silhouette, logo placement, product geometry,
material finish, color blocking, and distinctive accessories. Let requested
scene, pose, environment, medium, camera angle, wardrobe, and lighting change
only when doing so does not overwrite the subject's identity.
