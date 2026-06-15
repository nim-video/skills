---
name: nim-human-generation
description: Use when generating believable editorial young-adult human portraits or fashion/UGC character images with Nim, especially Gen-Z fashion casting, model/person look development, aesthetic human references, or prompt-driven human generation. Asks for age or age range, sex/gender presentation, ethnicity/look, and additional notes; defaults to Nano Banana Pro in 9:16, but supports user-specified models such as GPT Image 2 by discovering the live Nim model contract.
---

# Nim Human Generation

Generate aesthetic, believable editorial young-adult humans through the Nim MCP. The goal is a castable, specific, modern person with distinctive grooming, posture, attitude, and subtle subculture styling.

## Intake

Ask only for missing details that materially affect the person:

1. Age or age range.
2. Sex or gender presentation.
3. Ethnicity/look.
4. Additional notes: styling, vibe, subculture, wardrobe, location, body type, hair, makeup, pose, expression, constraints, or avoid items.

If the user says to decide, make tasteful assumptions and state them briefly before generation. Do not ask for every optional styling detail.

## Safety And Age Rules

- Do not generate sexualized minors. If the requested age is under 18, keep the image non-sexual, age-appropriate, and fashion/editorial without adult framing.
- If the user asks for "young adult" without an exact age, use `age 21-25` by default.
- Keep beauty direction flattering and believable. Do not use degrading language or intentionally ugly framing.
- Avoid face-smoothing artifacts, plastic skin, over-sharpened eyes, distorted hands, and exaggerated body proportions.

## Default Nim Settings

Use Nim image generation.

- Default model: Nano Banana Pro.
- Default search target: `Nano Banana Pro` / text-to-image.
- Default aspect ratio: `9:16`.
- Default resolution: use the model default, normally `2K`, unless the user asks otherwise.
- Default batch size: `1`. Use `2-4` only when the user asks for options.

Always discover the current model with `models_explore` and inspect the exact model contract with `models_explore action=get` before generation. Pass only parameters allowed by the returned `generationContract`.

If the user requests another model, search for that model by name, get its contract, and adapt the allowed parameters. Examples: `gpt image 2`, `Seedream`, `Flux`, or another Nim catalog model.

## User-Facing Flow

1. Collect required human inputs.
2. Summarize the planned person in one short paragraph if assumptions were made.
3. Generate unless the user asked to approve the prompt first.
4. Poll until `finished`, `failed`, or `cancelled`.
5. Return the real media URL and key settings used.

Do not dump raw JSON, internal IDs, or long prompt mechanics unless the user asks.

## Prompt Base

Use this source prompt as the core style system:

```text
Create an aesthetic, believable, editorial young adult for a Gen-Z fashion. The person should feel cast, specific, and modern, with distinctive grooming, posture, attitude, and subtle subculture styling. Do not create an ugly person; balance the appearance parameters finely.

natural skin texture, subtle film grain, shallow depth of field, cinematic realism like a 50mm lens at f/2.0.

COLOR GRADE / LUT STYLE: TikTok Beauty Soft LUT, soft lifted shadows, low contrast, pastel warmth, pink-beige undertone, clean bright face exposure, soft whites, natural lips and cheeks, flattering modern beauty UGC. Add 50D ultra-fine film grain at very low opacity, minimal halation on glossy product edges, soft cosmetic highlight glow. Camera enhancers: stabilized creator camera, clean eye autofocus, slight exposure breathing, soft lens diffusion, realistic compression texture, preserved skin pores. No plastic skin, no face smoothing artifacts, no over-sharpened eyes.
```

## Prompt Shape

Build concise prompts with this structure:

```text
Vertical 9:16 editorial portrait / fashion UGC image.
PERSON: age <age or range>, <sex/gender presentation>, <ethnicity/look>. Specific castable face, modern Gen-Z styling, distinctive grooming, posture, attitude, and subtle subculture cues.
WARDROBE / STYLING: <user notes or tasteful assumption>.
SCENE: <location/background if specified or a simple editorial setting>.
CAMERA: cinematic realism, 50mm lens at f/2.0, shallow depth of field, clean eye autofocus, stabilized creator camera feel.
LIGHTING: flattering bright face exposure, soft whites, pastel warmth, pink-beige undertone, low contrast, soft lifted shadows.
TEXTURE: natural skin texture, preserved pores, subtle 50D ultra-fine film grain, realistic compression texture, soft lens diffusion, minimal halation on glossy edges.
MOOD: believable, specific, aesthetic, modern, editorial, not generic.
CONSTRAINTS: no plastic skin, no face smoothing artifacts, no over-sharpened eyes, no distorted hands, no fake text, no watermark.
```

## Defaults For Missing Styling

Use these only when the user leaves styling open:

- Wardrobe: modern Gen-Z fashion with subtle subculture styling; avoid costume-like exaggeration.
- Pose: relaxed editorial posture with quiet confidence, not over-posed.
- Expression: natural, composed, slightly aloof or self-possessed.
- Setting: simple urban interior, street-edge backdrop, bedroom mirror light, studio corner, or soft daylight wall.
- Makeup/grooming: distinctive but believable; preserve skin texture.

## Variations

When generating multiple options, vary one or two controlled axes only:

- Hair and grooming.
- Subculture styling.
- Wardrobe silhouette.
- Pose/expression.
- Setting/light.

Keep age, sex/gender presentation, and ethnicity/look consistent unless the user asks to explore those.

## Example Intake Reply

```text
Got it. I need four details before generating: age or age range, sex/gender presentation, ethnicity/look, and any extra styling notes. If you want me to decide, say "choose for me" and I will use tasteful Gen-Z editorial defaults.
```

## Example Prompt

```text
Vertical 9:16 editorial portrait / fashion UGC image.
PERSON: age 22-25, female-presenting, mixed Mediterranean and Eastern European look. Specific castable face, modern Gen-Z styling, distinctive dark micro-bob haircut, minimal silver piercings, relaxed posture, self-possessed attitude, subtle art-school streetwear cues.
WARDROBE / STYLING: cropped charcoal knit, low-rise washed black denim, narrow belt, understated glossy lip, natural cheeks.
SCENE: soft daylight apartment wall with a slightly messy mirror edge and muted fashion-magazine realism.
CAMERA: cinematic realism, 50mm lens at f/2.0, shallow depth of field, clean eye autofocus, stabilized creator camera feel.
LIGHTING: flattering bright face exposure, soft whites, pastel warmth, pink-beige undertone, low contrast, soft lifted shadows.
TEXTURE: natural skin texture, preserved pores, subtle 50D ultra-fine film grain, realistic compression texture, soft lens diffusion, minimal halation on glossy edges.
MOOD: believable, specific, aesthetic, modern, editorial, not generic.
CONSTRAINTS: no plastic skin, no face smoothing artifacts, no over-sharpened eyes, no distorted hands, no fake text, no watermark.
```
