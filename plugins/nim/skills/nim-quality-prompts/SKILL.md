---
name: nim-quality-prompts
description: Use when improving, writing, rewriting, planning, or executing AI video prompts for Seedance, Higgsfield, Nim MCP, UGC, cinematic generation, image-to-video, reference frames, character consistency, GPT Image 2, Nano Banana Pro, 2K stills, LUTs, camera quality, shot lists, storyboards, beats, montage, sequence, camera angles, or visual grammar.
---

# Nim Quality Prompts

## Overview

Create copy-ready English AI video prompts and reference-frame prompts for Seedance/Nim workflows. Use the bundled LUT bank, camera-quality style database, camera-angle rulebook, and prompt orchestrator to improve both the still references that anchor a video and the final video prompt.

For requests that mention a prompt database, ideal prompt assembly, multi-bank prompt research, artist/style enrichment, or "analyze first, then improve", use the bundled orchestrator:

```bash
python scripts/prompt_quality_orchestrator.py index
python scripts/prompt_quality_orchestrator.py build --prompt "<user prompt>"
```

The orchestrator reads `references/prompt_database_registry.json`, builds `references/prompt_quality_index.db`, retrieves from all enabled databases/skills, analyzes the prompt, selects improvement directions, and returns the final prompt. If the user says not to improve (`--no-improve`, "do not improve", "keep unchanged", "leave as is"), return the prompt unchanged.

## Mode Routing

| User request | Mode | References to load |
| --- | --- | --- |
| Single prompt, prompt rewrite, video prompt, one-shot Seedance/Higgsfield/Nim improvement | Normal video prompt | `references/LUT.json`, `references/Camera_quality.json` |
| Reference image, image prompt, character/product/location still, image-to-video anchor, first frame, keyframe | Reference-frame prompt | Normal references plus this skill's Reference Frame Planning section |
| Same character/person/product/object in different scenes, recurring avatar, identity lock, transferable refs | Character consistency | Reference-frame prompt plus Character/Subject Consistency section |
| Cinematic clip, filmic shot, lens/camera move/lighting/grade direction | Cinematic video | Normal references plus Cinematic Video Prompting section |
| UGC ad, TikTok/Reels, creator talking to camera, selfie, iPhone, testimonial, hook, VO/lip sync | UGC video prompt | Use `nim-ugc-prompts` when available; otherwise use the UGC notes in this skill |
| Scene, script/stsenariy, shot list, storyboard, beats, montage, sequence, multi-shot, camera angles, visual grammar | Scene prompt | Normal references plus `references/camera_angle_rulebook.md`, `references/camera_angle_system_prompt.md`, `references/camera_angle_knowledge_dataset_500.json` |
| Prompt database, ideal prompt, artist/style enrichment, multi-bank retrieval, prompt quality DB, structured prompt improvement | Database orchestrator | Run `scripts/prompt_quality_orchestrator.py`; it loads `references/prompt_database_registry.json` and indexes all enabled sources |

If a request is ambiguous, choose Normal video prompt for one continuous shot and Scene prompt for multiple beats, edits, angles, or transitions.

## Nim MCP Execution Rules

When the user asks to actually generate images or video through Nim, follow Nim MCP behavior exactly:

1. Discover the live model with `models_explore` using `action: "recommend"`, `"search"`, or `"list"` for the user's intent.
2. Call `models_explore` with `action: "get"` on the chosen `model_id` and treat its `generationContract` as the source of truth.
3. Pass only fields listed by the contract. Do not guess parameter names, resolutions, duration values, `fileInputs`, or audio fields.
4. For edits, references, image-to-video, or uploaded assets, call `media_upload` first and pass only the returned Nim `file_url` values in `fileInputs`.
5. Never pass local file paths directly to `generate_image` or `generate_video`.
6. Poll `get_generation_status` until the job is `finished`, `failed`, or `cancelled`; do not claim completion before a real media URL is returned.

Default quality preference:

- For video generation, prefer the best current Seedance 2 / Seedance image-to-video option returned by Nim for the request.
- For reference still generation, prefer `GPT Image 2 medium 2K` for controlled, polished, prompt-faithful anchors, or `Nano Banana Pro 2K` for fast high-quality exploration and identity/product reference work.
- If the user explicitly names a model, search for that model and then adapt to its exact contract.

## Pre-Generation Quality Plan

Before high-quality video output, create a short plan that proves the visual logic is correct before execution.

The plan must identify:

- final output goal, platform, aspect ratio, duration, and generator;
- whether the request is one shot, a scene sequence, or a multi-clip series;
- selected visual grammar and why it fits the brief;
- intended shot scale, camera angle, camera movement, transition logic, and continuity risk;
- whether reference frames are required before video generation;
- which reference-frame model to use: `GPT Image 2 medium 2K` or `Nano Banana Pro 2K`;
- which Nim model family will be discovered for final video, without hardcoding a stale model id.

For scene, storyboard, shot-list, montage, sequence, or camera-angle requests, do not jump straight to final prompts. First check that angles are meaningfully chosen, transitions are edit-safe, screen direction and eyeline are plausible, and no camera move contradicts the scene physics.

If the plan exposes weak or random angles, revise the plan before writing final prompts.

## Reference Frame Planning

Plan still reference frames before video generation when identity, product appearance, location continuity, composition, or multi-shot coherence matters.

Use reference frames for:

- product or brand hero frames;
- character identity, wardrobe, pose, makeup, or body-proportion locks;
- location plates and lighting anchors;
- opening/ending frames for image-to-video;
- important story beats or angle changes;
- transition anchors between shots;
- any shot where text-only prompting is likely to drift.

For each required reference frame, output:

```json
{
  "purpose": "identity/product/location/beat/transition/angle",
  "model": "GPT Image 2 medium 2K | Nano Banana Pro 2K",
  "size": "2K",
  "prompt": "...",
  "used_by_video_prompt": "segment/shot id"
}
```

Reference still prompts should follow this order:

1. Subject identity and permanent details.
2. Wardrobe/product/location details to lock.
3. Camera/lens/framing and aspect ratio.
4. Real lighting and texture cues from `Camera_quality.json`.
5. LUT/color treatment from `LUT.json` only when it helps the video.
6. Negative constraints that protect anatomy, text, logos, and material details.

If the user asks for actual generation, generate or request the reference frames before video generation when the runtime supports it. If reference frame generation is unavailable, blocked by credits, or requires a missing source image, state the blocker and continue with prompt-only planning only when the user accepts that fallback.

## Character/Subject Consistency

Use this when references must travel across scenes. The goal is not "similar vibe"; it is the same person, character, product, object, mascot, or branded item with stable identity.

Intake:

- Required: one or more identity reference images plus the new scene/action.
- Optional: secondary references for outfit, pose, location, lighting, product, audio, or styling.
- If a required reference is missing, ask only for that missing reference before generation.

Prompt pattern:

```text
The identical <subject> from @image1, reimagined in <new scene/action>. Preserve <defining identity traits> exactly: <face/product geometry/logo placement/silhouette/material/color blocking/accessories>. Change only <allowed changes>. Do not alter identity, proportions, permanent markings, or product structure.
```

For multiple references, assign roles clearly and preserve upload order:

```text
@image1 = main identity. @image2 = outfit/body proportions. @image3 = location. @image4 = product/object. The video must preserve each reference role exactly.
```

When a character moves between scenes, write an identity lock before the scene prompt:

- face shape, hair shape/color, makeup, skin texture, proportions, body type;
- wardrobe pieces, accessories, tattoos, product geometry, logo placement;
- forbidden drift: age shift, face swap, wardrobe merge, material change, product redesign, extra logos.

## Cinematic Video Prompting

Use compact shot language. Lead with the camera phrase, then add only the elements that control the shot.

Scaffold:

```text
Framing + camera motion: [wide establishing / tight close-up] + [slow push-in / pan right / rack focus / dolly zoom / oner]
Style: [cinematic photorealism / documentary realism / shallow depth of field / film grain]
Lighting: [golden-hour backlit / cool window fill / single warm practical / mixed practicals]
Location: [specific place, in a few words that carry the decor by world knowledge]
Action: [one small thing the subject does, bounded by what is visible in frame]
```

Rules:

- Speak camera vocabulary directly: push-in, pull-back, pan, tilt, dolly, crane, orbit, rack focus, locked-off, handheld, selfie, POV.
- Pace the move: slow, gradual, steady, sudden, urgent, tiny wrist shake.
- For image-to-video, direct motion only; the source still already fixes the look.
- Bound motion to visible evidence. A tight portrait cannot walk away unless the full body exists in the source or a wider reference is created first.
- Use the selected LUT and camera-quality style as controlled finishing language, not as a wall of adjectives.

## UGC Notes

For UGC prompts, realism comes from ordinary recording behavior, not polished cinematography.

Use:

- vertical `9:16`, social-media ad, TikTok/Reels/Shorts;
- iPhone/front-camera/rear-camera/mirror/selfie/tripod language;
- natural HDR, autofocus breathing, auto-exposure adaptation, subtle handheld wrist movement;
- real skin pores, natural blinking, breathing, tiny expression changes, imperfect framing;
- direct-to-camera delivery, FaceTime feeling, casual pauses, slight glances away and back;
- explicit audio/VO/lip-sync instructions only when the model supports them.

Avoid:

- cinematic lighting, stylized color grading, beauty filter, skin smoothing, subtitles unless requested, text overlays, CGI, fake logos;
- random camera movement when the brief asks for tripod/static framing;
- impossible phone handling, impossible mirror geometry, or outfit/product morphing.

For deeper UGC construction, use the separate `nim-ugc-prompts` skill when available.

## Database Orchestrator Workflow

Use this workflow when the user asks to improve a rough prompt through databases or wants an explicit analysis-to-final pipeline:

1. Run `python scripts/prompt_quality_orchestrator.py index` after adding or changing databases.
2. Run `python scripts/prompt_quality_orchestrator.py build --prompt "<prompt>"`.
3. Read the output in order: Prompt Analysis, Improvement Directions, Selected Database Records, Final Prompt.
4. If the user asked not to improve, run with `--no-improve` or return the original prompt unchanged.

To add a new prompt database or skill, edit `references/prompt_database_registry.json`:

- Add a `sources[]` entry for a known adapter: `seedance_lut`, `seedance_camera_quality`, `seedance_camera_angles`, `universal_prompt_skills`, `markdown_sections`, `generic_json`, `legacy_prompt_python`, or `codex_skill`.
- Add a `skill_roots[]` entry when new Codex skill folders should be auto-discovered by `SKILL.md`.
- Re-run `python scripts/prompt_quality_orchestrator.py index`.

The SQLite index is disposable generated state. The registry and source files are authoritative.

## Reference Use

- Use `LUT.json` to select one LUT by `best_for`, `look_goal`, and `copy_paste_suffix_en`; include its suffix in the final prompt.
- Use `LUT.json` `usage.global_negative_prompt` as the negative prompt unless the user supplies stricter negatives.
- Use `Camera_quality.json` to select one style prompt by category, style name, camera, optics, lighting, and look. Extract the relevant camera/quality language; do not paste a full 500-word style prompt unless the user asked for a long master prompt.
- For Scene prompt mode, use `camera_angle_system_prompt.md` as the operating behavior, `camera_angle_rulebook.md` for hard transition rules, and `camera_angle_knowledge_dataset_500.json` as the pattern bank.
- When using the dataset, retrieve 3-8 relevant `reference_items` by product category, mood, format, or scene logic. Extract transition and angle logic only; generate original shots.

## Normal Video Prompt Workflow

1. Identify subject, product/category, platform, duration, aspect ratio, mood, location, action, and fixed user constraints.
2. Select the closest LUT and one camera-quality style. If several fit, prefer the least stylized option that preserves realism.
3. Decide whether reference frames should be generated first. If yes, write those still prompts before the video prompt.
4. Build one copy-ready English prompt with this order: references and identity locks, scene/action, camera and movement, optics/focus, lighting, selected Quality style language, selected LUT suffix, constraints.
5. Keep the prompt physically plausible: one readable action, one camera logic, preserved identity/props/location, no impossible movement.

Return:

```markdown
## Reference Frames
[only when needed]

## Final Video Prompt
[copy-ready English prompt]

## Selected LUT
[id] - [name]
[copy_paste_suffix_en]

## Selected Quality Style
[id] - [style_name_en]
[short reason and extracted camera/quality language]

## Nim Generation Notes
[model discovery target, required fileInputs, aspect ratio, duration, resolution only if supported by contract]

## Negative Prompt
[global or user-adjusted negative prompt]
```

## Scene Prompt Workflow

1. Break the script or concept into 5-9 beats unless the user specifies another count.
2. Assign each beat a story function: hook, problem, context, proof, reveal, reaction, CTA, or scene-specific equivalent.
3. Choose a base visual grammar and one contrast grammar only if it marks a turning point.
4. Create reference-frame requirements for recurring character/product/location/transition anchors.
5. For each beat, specify shot scale, angle, movement, transition in/out, audio bridge, and why the angle changes meaning.
6. Validate adjacent beats against the rulebook: 180-degree axis, eyeline, screen position, scale jumps, light direction, lens continuity, and bridge-shot needs.
7. Attach LUT + Quality language to every generated beat prompt, keeping each prompt copy-ready in English.

Return:

```json
{
  "concept": "...",
  "visual_grammar": "...",
  "selected_lut": {
    "id": "...",
    "name": "...",
    "reason": "..."
  },
  "selected_quality_style": {
    "id": "...",
    "name": "...",
    "reason": "..."
  },
  "reference_frames": [
    {
      "purpose": "identity/product/location/beat/transition/angle",
      "model": "GPT Image 2 medium 2K | Nano Banana Pro 2K",
      "size": "2K",
      "prompt": "...",
      "used_by_video_prompt": "shot id"
    }
  ],
  "reference_logic": ["3-8 brief notes from the dataset/rulebook, without copying a source scene"],
  "shot_list": [
    {
      "beat": 1,
      "duration_sec": 1.5,
      "story_function": "hook/problem/proof/reveal/reaction/CTA",
      "shot_scale": "CU/MS/ELS/INSERT/POV/etc.",
      "angle": "eye_level/top_down/OTS/low_angle/etc.",
      "movement": "locked/push_in/pan/reveal/handheld/etc.",
      "transition_in": "straight_cut/J_cut/match_action/etc.",
      "transition_out": "...",
      "audio_bridge": "...",
      "why_this_angle": "...",
      "risk_check": "...",
      "copy_ready_prompt_en": "..."
    }
  ],
  "bridge_shots_needed": ["..."],
  "do_not_do": ["..."],
  "nim_generation_notes": {
    "discover_model_target": "Seedance 2 / image-to-video / text-to-video as required",
    "required_fileInputs": ["@image1 role", "@image2 role"],
    "contract_sensitive_params": ["requestedAspectRatio", "mediaLength", "resolution", "fps", "keepSound"]
  },
  "negative_prompt": "...",
  "edit_validation": {
    "emotion_story_rhythm_ok": true,
    "reference_roles_clear": true,
    "identity_lock_ok": true,
    "eye_trace_ok": true,
    "axis_180_ok": true,
    "scale_jumps_justified": true,
    "screen_direction_ok": true,
    "bridge_shots_ok": true
  }
}
```

## Quality Bar

- Prompts must be copy-ready in English. Use Russian only for short notes, assumptions, or user-facing explanation when useful.
- Improve both the reference still prompts and the final video prompt when reference frames affect quality.
- Prefer specific DOP/operator language over vague phrases like "cinematic" or "high quality."
- Do not mix random camera grammars in one short sequence.
- Do not add unsupported product claims, false before/after transformations, fake readable text, random logos, or impossible camera moves.
- Do not generate through Nim until required references have real Nim `file_url` values.
- If information is missing, make a reasonable assumption and label it briefly instead of blocking on extra questions.
