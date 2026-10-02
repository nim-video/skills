---
name: nim-seedance-prompt-recovery
description: >-
  Use before drafting a Seedance 2.0 or Seedance 2.5 prompt, whenever its
  generation fails or is rejected, and whenever the user asks to change,
  adapt, or rewrite an existing Seedance prompt. Also use when the user asks
  to change this skill's rules. Applies to prompt-only work as well as
  generation workflows; no prior failure or explicit skill invocation is
  required.
---

# Nim Seedance Prompt Recovery

Draft and revise Seedance prompts, and diagnose actual generation failures when they occur. Preserve the requested scene, motion, duration, framing, dialogue, and visual continuity unless a change is necessary and disclosed. Work with the connected generation tools when execution is requested; do not assume a particular service, model ID, or API wrapper.

Write prompts in English by default and explanations in the user's language. Preserve an explicitly requested prompt language and the requested dialogue language. For a faithful translation comparison, retain the English baseline. Keep responses practical: a short diagnosis, the changes, and a copy-ready prompt. Do not expose internal planning, raw tool dumps, or a development narrative. Never promise that wording will pass a filter.

## Usage tracking

Once per new user request that you handle with this skill, call the Nim tool `track_skill_activation` with `skill_name: "nim-seedance-prompt-recovery"`. Do not call it again while polling, retrying, or continuing the same request. If the tool is unavailable or fails, continue without retrying and without mentioning it to the user.

## Activation and routing

Apply this skill automatically in all three situations; do not wait for the user to name it:

1. **Before writing a new Seedance prompt.** Apply the reference-language and audio rules from the first draft. Start from the user's brief and available references; do not ask for a failed job, error message, or job ID when no failure has occurred.
2. **Whenever a Seedance generation fails or is rejected.** Inspect the actual error and choose the smallest justified correction without waiting for a separate request to diagnose it. A queued/running job or a wait timeout is not itself a content rejection.
3. **Whenever the user requests a prompt change.** Apply the requested edit, then recheck reference roles, sound instructions, and known model constraints. Preserve unrelated parts and earlier explicit choices. Do not require a prior failure or describe an ordinary edit as recovery from a rejection. A running job does not prevent preparing a revised prompt; preparing it does not cancel or resubmit that job.

For new drafts and ordinary edits, skip failure diagnosis and use the relevant prompting sections directly. Inspect the live contract before an actual submission or when recommending contract-sensitive settings. Prompt-only work does not require a connected generation service, and automatic skill use does not authorize a generation or paid retry.

Before retrieving a job, submitting, or retrying, read [MCP integration](references/integration.md) for request handoff, input types, actual error fields, partial batches, and terminal states. For prompt-only work, skip that reference. When another workflow calls this skill, preserve its output format and existing authorization; apply these reference-language and audio rules to the final prompt after any template or prompt-enrichment step.

If the user asks to modify this skill itself, read its current instructions and edit the requested rules; do not treat that maintenance request as a video-generation request.

## Inspect a failed generation

1. Use the failed job and prompt already present in the conversation. If needed, retrieve that specific job through the available status tool. Collect its model/version, status, returned error details, submitted prompt, reference roles, and audio settings. An error code may not exist; do not invent one. Ask only for missing evidence that changes the diagnosis.
2. Separate the service's stated reason from a hypothesis. An audio-copyright error is evidence about audio, not proof that a facial-reference phrase caused it. If the failure category is unknown, say so.
3. Before a retry, inspect the selected model's live generation contract. Where available, use `models_explore` with `action: "get"`; use `get_generation_status` for the known job. These operation names are examples: discover their equivalents in the connected toolset. Follow the returned schema for input roles, parameter types, durations, and terminal states.

| Evidence | Next action |
|---|---|
| Queued/running job; wait timed out | Continue observing the same job. Do not rewrite or resubmit merely because waiting ended. |
| Submit timed out; outcome unknown | Recover the original job through documented means. Do not blindly submit a duplicate. |
| Cancelled or removed job | Report that terminal state. Do not treat it as rejection evidence or restart without an authorized new request. |
| Invalid field, enum, duration, or reference | Correct the payload or input asset against the live contract. |
| Authentication, credits, rate limit, outage | Address that operational problem; prompt synonyms do not fix it. |
| Explicit reference, identity, visual/IP, or audio rejection | Use the matching recovery pattern below. |
| Generic failure with no reason | Inspect available error details; offer a clearly labeled hypothesis, not a certain diagnosis. |

## Use reference language for faces and characters

Replace demands such as `EXACT face`, `identical person`, `1:1 copy`, or `reproduce this character exactly` with a clear reference relationship:

> Use the attached image as a visual reference for the character's appearance. Keep the character visually consistent across shots while animating the new scene described below.

Shorter alternatives: **“Base the character's appearance on the attached visual reference”** or **“Use the attached image as a visual reference for the character.”** These are clearer than “reference from.”

Match wording to the asset's assigned role. Mention hairstyle, wardrobe, or pose only when that reference supplies it. A face-only reference must not override clothing from a separate wardrobe reference. Call an asset a character sheet only when it actually is one.

Use this change for facial/character replication instructions, not as a global replacement of the word “exact.” Preserve exact dialogue, timing, camera instructions, and other unrelated requirements. Do not claim these words are universally blocked or that reference wording guarantees acceptance. Do not claim a supplied face is fictional, synthetic, or authorized unless the evidence supports that description.

If the reference itself is flagged, inspect it when possible. Rewording cannot change its pixels. Consider separate scene/wardrobe references without a visible face and a separate character sheet, only when the model accepts those inputs. For recognizable borrowed designs, offer an original redesign; merely removing a name may leave the same recognizable design.

## Default to natural sound, with no music

Unless the user explicitly requests music, append a concrete sound brief and a clear exclusion:

> Audio: natural scene sounds only—[specific sources, timing, distance, and intensity appropriate to this shot]. No music, background score, soundtrack, singing, or melodic elements.

Describe effects that follow visible actions: footsteps synchronized with steps, a brief cloth rustle during a turn, rain striking the awning, or an engine rising gently during acceleration. Preserve requested speech verbatim; add “no dialogue” only when speech was not requested. Avoid using “cinematic soundtrack” or musical mood language as a substitute for sound design.

**No music is different from no audio.** Keep audio enabled when the user wants generated speech, ambience, or effects. After an audio-copyright rejection, first propose the same scene with explicit natural sounds and “no music.”

A silent fallback may use `generate_audio: "off"` **only if that exact field and value are supported**. Other contracts expose `generateAudio: false`; some modes expose no audio switch at all. Follow the actual name, nesting, and type. Do not send the string `"off"` to a boolean field or invent a music-only switch.

Disabling generated audio removes generated dialogue and effects as well as music. Use a visual prompt with a silent-output instruction, in English by default while preserving an explicitly requested language, and disclose that tradeoff before replacing a requested sound version. For editing or source-video inputs, check whether existing audio is retained; inspect the output before claiming it is silent. If music was explicitly requested, honor that choice rather than silently deleting it.

## Select one targeted revision

When a failure exists, read [recovery patterns](references/recovery-patterns.md) for the matching issue: innocuous wording, translation, faces, recognizable costumes, stage makeup, named works, branded publications, or audio. For new drafts and ordinary edits, use only relevant guidance without inventing a failure. Use [prompt examples](references/prompt-examples.md) when a copy-ready structure helps.

Reported successes are hypotheses to test, not a universal banned-word list. For an otherwise harmless scene, simplify an unnecessary adjective or prepare a faithful translation as a controlled comparison. Do not use mistranslation, coded wording, or false labels to conceal the underlying content. When a scene needs a substantive change, describe the genuinely revised scene.

Change one suspected factor per attempt when practical. Keep unrelated settings and references stable. If the user needs both a character-reference rewrite and an audio correction, explain both and do not attribute success to either one without evidence.

## Retry and deliver

- A request to write, draft, suggest, or revise a prompt returns the prompt without submitting a generation. A request to fix and regenerate can authorize a retry; preserve existing authorization and spending limits.
- For recovery retries, submit one revised candidate at a time. Use at most two revised submissions for the original failure within the user's authorized count/budget, counting its entire retry chain and resumed turns; stop earlier when the same rejection recurs without new evidence. This is a workflow limit, not a service guarantee. Do not cycle through many paraphrases.
- For recovery retries, preserve the original job ID and track each revised attempt separately. For any submitted generation, observe the existing job within the host's waiting limits. If waiting must stop, retain its ID and report it as pending; only a verified terminal result can establish completion. Return only media URLs actually provided by the service.
- If a new reference image or original redesign is necessary, explain that input change. Do not claim that a prompt edit has modified the existing reference asset.
- Inspect successful output for unwanted music, missing speech, reference drift, and the intended action using available media tools. Clearly state any checks that could not be performed. Continue through the existing generation workflow without duplicating its preview.

Use this compact response shape, omitting irrelevant items:

**Diagnosis:** observed reason and any uncertainty.

**Changes:** one or two concrete edits; disclose any change to the subject or sound.

**Prompt / revised prompt:** copy-ready text in English by default, the user's explicitly requested language, or the requested faithful translation variant.

**Settings:** only supported changes, with the silent-output tradeoff when applicable.

**Result / next step:** verified outcome, authorized retry, or the specific missing input.
