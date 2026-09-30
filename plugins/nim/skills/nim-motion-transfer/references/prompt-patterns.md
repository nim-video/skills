# Prompt patterns

The source clip already carries the motion. Resist describing it. Describe what to
replace, then fence the change by naming everything that must survive.

> Prompt less. The clip handles motion - your text tells the model what to keep
> versus what to reinterpret.

## Role assignment first

Every reference gets exactly one job. Say which is which before saying what happens.
A reliable way to do this is to number the inputs by priority.

```text
REFERENCE PRIORITY
1. @vid1 = motion, timing, camera and framing only.
   Take body positions, movement speed, weight shifts, gesture emphasis, rhythm,
   camera path, framing, and all physical contact from @vid1.
   Do NOT take appearance, costume, or environment from @vid1.
2. @img1 = sole identity reference. Preserve face, body proportions, hair, and the
   complete outfit. @img1 is the final authority on who this is.
3. @img2 = environment only. Use it for layout, light, and palette; nothing in it is a person.
```

Rules that hold across every pattern below:

- **Cite by position, not by tag alone.** `@img1` says which face; "the fighter on the
  left", "the taller one" says which body. Automatic mapping is real but it needs both.
- **The reference count must equal the number of distinct people.** One character image
  against a two-performer clip casts one character; the second performer is not cast.
- **Order is array order.** Keep one fixed casting order across a whole batch so prompts
  stay copy-pasteable.

## The prompt skeleton

```text
[FORMAT]      duration, aspect ratio, and the one visual style noun
[REFERENCES]  what each @vid and @img carries
[AUDIO]       what the soundtrack should be, always stated
[TIMELINE]    only if the source has distinct beats worth naming
[CONTINUITY]  what must not change
[PHYSICS]     weight, contact, gravity, ground contact
[EXCLUSIONS]  what must never appear
```

Keep the whole thing short. Two or three style adjectives maximum; more causes motion
drift. Do not say "make it like the reference" - that grants permission to copy
everything. Say what to copy and what to replace.

## Audio direction

For exact original audio, use [final-audio.md](final-audio.md). Disable audio generation
when supported and restore the source track as AAC-LC in the final MP4 afterwards. A prompt or
audio reference does not guarantee an unchanged soundtrack. For requests that actually
need synthesized audio, specify the intended track. For example (guidance only):

```text
AUDIO: keep the source track exactly as recorded - the speaker's voice, room tone,
and the music bed. Do not add narration, captions, or a new soundtrack.
```

Adjust for the job:

| Goal | Audio line |
|---|---|
| Keep the original soundtrack exactly | Post-generation source soundtrack encoded as AAC-LC; disable generated audio if supported |
| Recast with a different language | `keep the source music and room tone; overdub the dialogue in [language] with [accent and delivery]` |
| New soundtrack | `replace the audio with [music direction]. Keep natural room tone under it` |
| No audio wanted | Disable generated audio if supported; otherwise remove every audio stream from the final file |

When the audio travels in the depth clip rather than as its own reference, the prompt
still needs this line: the reference carries the track, it does not carry the intent.

## Preserve list

The single highest-value clause. Without it the model edits more than asked.

Reuse this vocabulary rather than inventing new words each time:

```text
Preserve every body movement, pose sequence, action beat, screen position,
camera move, framing change, cut, and timing from the source.
```

Add only what this specific shot needs: `weight shifts`, `landings`, `wall contact`,
`gesture emphasis`, `speaking cadence`, `moments of emphasis toward camera`.

## Anatomy adaptation

Required whenever the target is not a human body plan. Depth transfers motion between
similar structures; the further the anatomy is from the source, the more the model
invents. Name the inventing explicitly instead of leaving it to chance.

```text
Adapt the source motion cleanly onto this body plan. This is an anthropomorphic
[species], not a human in costume. The movement must feel natural for its design:
[body plan list]. Exactly 2 arms, 2 legs, 2 feet, 1 tail. No duplicate limbs,
no broken joints, no extra or missing fingers.
```

## Exclusions

**Never negate a visible object.** `no extra people` produces extra people. Negation
works only on three targets:

| Target | Works | Example |
|---|---|---|
| A reference (what not to take from it) | yes | `Do not use the people in @img2.` |
| A generated default track | yes | `no background music, no text overlay, no captions` |
| A manufacturing defect | yes | `no drift, no deformation, no flickering` |
| A visible object or attribute | **no, backfires** | ~~`no red car`~~ → describe what IS there |
| An image defect | **no, backfires** | ~~`no blur`~~ → `sharp, in focus, high clarity` |

So the exclusion block is mostly about defects and defaults, and any "must not be
present" statement about *content* gets rewritten positively:

```text
EXCLUSIONS (defects and defaults only):
no drift, no identity flicker, no duplicated limbs, no extra or missing fingers,
no face morphing, no floating, no clipping through surfaces, no camera invention,
no text overlays, no watermarks, no background music.
```

And the content side, stated positively:

```text
PRESENCE: Every person on screen is @img1. The shot contains no one else.
```

Do not let the exclusion list grow into a second prompt. Keep it to failures that
would make the clip unusable.

## Multi-subject sources

Map by position or distinguishing feature, never by tag number alone:

```text
@img1 takes the performer on the left; @img2 takes the taller one throwing the kick.
Both keep their own likeness for the whole clip. Swap no identities between them.
```

Expect 2-4 regeneration cycles on multi-performer shots: two performers of similar
build sometimes trade identities between renders. Verify on a contact sheet before
calling it done.

## Recasting variants

Same source performance, different identity, one variable changed per request.

Wardrobe or identity swap: swap `@img1`, change nothing else.

Localization - one performance across several markets:

```text
Recreate the exact performance from @vid1, cast with the character in @img1.
Preserve every beat and the exact lip-sync duration of every phrase.
Speaks fluent [language with accent and delivery], [tone].
```

Name the language with an accent and a delivery, not just a country. "Fluent Parisian
French, warm and unhurried" holds better than "in French", and the cue carries into
the generated audio track.

## Timeline block

Only add timestamps when the source genuinely has separate beats and duration allows
it. One action per segment; do not stack narrative turns into one window.

```text
0-2s: [setup and end state of the first beat]
2-4s: [the change]
4-6s: [changed end state]
```

## Failure signatures

| Symptom | Likely cause | First repair |
|---|---|---|
| Performer drifts toward the source appearance | Appearance data entered the motion channel | Depth reference, and `Do NOT take appearance from @vid1` |
| Cloned or duplicated performers | Guidance layers overlaid into one input instead of separate inputs | Keep motion and identity inputs isolated |
| Choreography correct but timing off | Reference longer than the rendered clip, or pacing not pinned | Match duration to usable source length; add the preserve list |
| Camera wanders | Several moves requested, or no endpoint | One move, with a start and a finish |
| Prop detached at contact | Depth does not carry object interaction | Reduce reliance on props, or state contact explicitly |
| Face unstable on an anime target | Model expects a body plan it can map | Anatomy adaptation block |
| Output looks generic | Style stacked in adjectives, action unspecified | One style noun, physical verbs, named end state |