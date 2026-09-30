# Long source clips (over 15 seconds)

One Seedance 2 job renders at most **15 seconds**. A source clip longer than 15 s is
therefore always processed as several parts and stitched. This is the default
behaviour, not an option: do not shrink the clip, do not refuse it, and do not ask the
user to trim it. The part-by-part result is delivered as ONE final video with sound;
the parts are never shown (see "Deliver" in [SKILL.md](../SKILL.md)).

The 15-second limit is the contract's `mediaLength` ceiling for the chosen model. Re-read
it from `models_explore get` instead of trusting this number.

## Model

Use **Seedance 2** (the Advanced Mode entry for Seedance 2, found with `models_explore`) for every part. Do not switch to Seedance 2.5 just because it allows
longer single clips, and do not mix models between parts: a different model per part
changes the look between parts. The exception is an explicit user request for another model.

## Split plan

1. Measure the source duration and detect scene cuts (e.g. `ffmpeg -vf "select='gt(scene,0.3)',showinfo"`).
2. Choose `N = ceil(duration / 15)` parts and cut at the scene cut nearest each ideal
   boundary (duration / N). A cut on a shot boundary is preferred: the part starts
   with a fresh composition and the seam is invisible. If there is no cut near a
   boundary, cut on a quiet moment in the motion, never mid-gesture.
3. Every part must be 4 to 15 s (the contract's allowed `mediaLength` values). A leftover
   shorter than 4 s is merged into the previous part when that part stays at or below
   15 s, otherwise rebalance all boundaries. Prefer equal-length parts.
4. Set each part's `mediaLength` to the nearest allowed whole second that does not exceed
   the part's real length. Losing a fraction of a second at the end is fine, padding with
   invented motion is not.
5. Cut every part from the original with video only (`-an`) and a re-encode, so cuts
   are frame-accurate. Keep the original file untouched for the audio step.

Example: a 26 s clip with a cut at 12.9 s gives 2 parts of about 13 s.

## One depth reference per part

Run the depth step per part, not on the whole clip (a part must be uploaded as its own
reference). Depth is billed per second of input video, so the total depth cost equals the
source duration, the same as for one pass. Reuse cached depth when re-running a part.

## Keep the parts consistent

- The same `@img` identity references in the same order for every part.
- **Write a separate prompt for every part. Never reuse one prompt for all parts.** Scene
  context, action, framing and who is where change between parts, so each prompt is
  written from that part's own frames: look at the part's contact sheet (and its depth
  clip) before drafting it.
- Every part's prompt has two blocks:
  1. **Shared identity block, copied verbatim** into all parts: reference priority, each
     character's look and fixed outfit, body plan, style nouns, exclusions, audio line.
  2. **Part-specific scene block, written fresh per part:** the location and set dressing
     visible in this part, the props that appear, shot order with rough timestamps,
     framing (wide, close-up, macro on the mouth), who stands or sits where, and the
     key action beats. Take it from what the part actually shows, not from the first part.
- Describe role mapping by position or distinguishing feature inside each part,
  because who stands where can change between parts.
- Keep the scene blocks consistent with each other where the set is the same (same room,
  same palette), and change them where the scene changes.
- Name the wardrobe of each character explicitly and state that it never changes. Outfit and
  body-plan drift is the most common failure on long clips.
- Submit all parts in one go (they are independent) and poll them together.

## Cost warning (mandatory, before any spending)

Long clips multiply cost, so the single combined confirmation from SKILL.md must also show:

- number of parts and each part's length (e.g. "2 части по 13 с");
- Nim credits: the sum over parts of the full job price, from the live contract and
  the current `estimatedCreditCost` rules in [pricing.md](pricing.md). Reference charges
  are not in the catalog base price, so label the figure approximate unless a full quote
  exists. Reference: one 13 s, 720p, 16:9 job with one depth reference and two images
  was estimated at 520 credits on 2026-09-30, and this is an empirical guide, not a formula;
- the depth-processing charge in dollars, about $0.04 per second of the whole source;
- the current balance, and whether it covers every part;
- the warning that a retry or a repair of a bad part is another paid job per part.

Example: "Ролик 26 с: 2 части по 13 с, Seedance 2, 720p, 16:9, оригинальный звук.
Примерно 1040 кредитов Nim + около $1.04 за обработку. Повтор одной части стоит ещё
~520 кредитов. Запускать?"

If the balance covers only some parts, say so and start none until the user decides.
Never start a subset silently. A hard user budget is checked against the total of all parts.
Wait for the user's explicit answer; do not treat a silent pause or a background
notification as approval.

## Assembly

1. Download every generated part and review each one (nim-generation-qa).
2. Trim each part to its planned length and concatenate only the picture, in order,
   into one silent file at a common size. Use one re-encode with a concat filter, not raw
   stream copy.
3. Attach one continuous original soundtrack for the whole duration through
   [final-audio.md](final-audio.md) (`restore_source_audio.py` with the full duration). Never
   concatenate generated audio beds; generate parts with `generateAudio: false`.
4. Verify the seam timing against the source cuts and check the contact sheet around
   each seam for a jump in identity, outfit or set.
5. Deliver the single final MP4 only. Report a bad part in words (which time range, what
   is wrong) and offer a repair of that part; do not show the part itself.

## Repairing one part

Regenerate only the failing part. Keep the passing parts and their depth references.
Sharpen the prompt for the failure (for example "stuffed plush doll, never a live human,
short soft mitten arms, same outfit in every frame"), and ask before paying for it. After a
repair, rebuild the final file and show only that.
