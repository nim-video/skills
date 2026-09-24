# Report and repair

## User-facing report

Use the user's language and proportional detail.

**Verdict:** [pass / acceptable with notes / needs revision / incomplete].
**Inspected:** [version; full playback + audio / frames only / image; preview or master].
[Eight-row table: criterion | status | evidence/timecode.]

**Priority findings:** [expected vs observed behavior and its practical effect].
**Prompt patch:** Before: [actual wording or missing]. After: [replacement]. Why: [reason, explicitly hypothetical when needed].
**Revised prompt:** [complete copy-ready text, inline or saved and linked].
**Rerun proposal:** [whole result / segment / edit, settings, references, live cost or estimate unavailable].
**Unverified:** [checks and reasons].
[One concrete question for approval, only when this retry is not already authorized.]

Present the accessible result together with the review. Follow host media-display rules. A generation widget reporting finished does not mean QA passed.

## Repair patterns

Prefer observable positive action over a long list of negative adjectives:
- Contact: specify starting support, contact point, force direction and resulting motion.
- Missing action: reserve enough time and define visible beginning/middle/end. Simplifying concurrent actions is a disclosed tradeoff.
- Mirrored branding: specify unmirrored saved camera output and normal reading direction while preserving the design.
- Prop resets: define states per beat and allowed changes.
- Identity drift: clarify reference roles and persistent traits.
- Unclear limbs/tails: establish attachment and silhouette before occlusion; not every blur is a defect.
- Contradictory reference: propose a corrected reference/edit. Repeating no-cap text may not overcome a capped image.
- Speech: exact line, utterance interval, voice and unobstructed mouth. Never certify lip sync from a transcript.
- Technical output: distinguish preview vs master before proposing upscaling; resizing adds no native detail.

Keep unchanged strengths. Link each substantive patch to a finding; label additional creative choices as optional.

## Structured handoff, when useful

No fixed storage implementation is required. Record:
- review_key: workflow/output/revision or equivalent source identity.
- source: real URL/file, preview/master/export status, approved brief, submitted prompt/settings, reference-role map, observed metadata.
- requirements: id, source, expectation, importance, result.
- coverage: full/partial/none; playback, frame sampling, image inspection, listening/audio-model analysis flags; limitations.
- criteria: all eight IDs, status, evidence, limitations.
- findings: id, type, criterion, severity, confidence, requirement_id, expected, observed, time_range_seconds or image_region, evidence_source.
- verdict: pass/acceptable_with_notes/needs_revision/incomplete.
- repair: scope, patches with finding IDs, complete revised prompt, reference changes, cost estimate/source, approval and authorized retry limit.

Use null or unverified for missing information, not zero or pass. Keep direct observations separate from auxiliary model descriptions and inferred causes.
