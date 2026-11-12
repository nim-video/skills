---
name: nim-defaults
description: >-
  Single source of default models and generation parameters for the Nim skills
  (Nano Banana, GPT Image, Seedream, Seedance) and the precedence between an
  explicit user choice, personal defaults and these defaults. Use whenever a Nim
  skill needs to pick an image or video model or a resolution and the user has
  not named one.
---

# Nim Defaults

Used by the other Nim skills when the user has not named a model or resolution.
Always still discover the model with `models_explore` and follow its live
`generationContract`; pass only parameters the contract allows.

## Precedence

1. **Explicit user choice** in the current conversation: any supported model, version, tier,
   resolution or draft/final choice. Always wins, including Nano Banana Pro.
2. **Personal defaults**: preferences the user has saved (their CLAUDE.md or memory, a
   "Nim defaults" note). Use them in place of the plugin defaults below.
3. **Plugin defaults** (table below).

## Plugin defaults

| Family | Default model | Resolution / mode |
|---|---|---|
| Nano Banana | Nano Banana 2.1 (text / Edit variants) | `2K`, passed explicitly (model default is `1K`) |
| GPT Image | GPT Image 2.5 Sunburst, Medium variant | `2K` |
| Seedream | Seedream 4.5 (Edit variant for image inputs) | none: the contract has no `resolution` |
| Seedance | Seedance 2.5 (Standard, not Fast) | draft mode: `draft: true` (480p). Do not send `resolution` with `draft` |

## Confirm before generating

Before every generation call (`generate_image`, `generate_video`, `render_video_draft`,
`run_template` and any other paid Nim generation), always:

1. Tell the user, in one short plain-language message, what will run: the model, the
   resolution or mode (for example "Seedance 2.5, draft 480p" or "GPT Image 2.5 Sunburst
   Medium, 2K"), aspect ratio, duration or batch size, and the credit estimate when known.
2. Ask them to confirm and start only after a clear yes. A "go ahead" given before the
   settings were shown does not count, even if the user named the model themselves.
3. Ask again when any of these settings change, including a switch from a draft to the
   final render. One confirmation covers exactly the settings shown, including a batch
   quoted in the same message.

This is a settings check, not a prompt-approval round: do not show the full prompt unless
the user asks.

## Rules

- Nano Banana Pro is never picked or recommended automatically; use it only when the user names it.
- Seedance never goes to `720p`, `1080p` or `4k` automatically. The final 1080p comes from
  `render_video_draft` on the finished draft (available for 168 hours), or from an explicit
  `resolution`, and only when the user asks or approves the draft.
- Skill-specific settings (aspect ratio, duration, batch size, a skill's own model pinned for
  a documented reason) stay in that skill; these defaults apply only where a skill gives none.
