# Shot planning rules

Details for Stage 0, step 4 of SKILL.md. For every shot write down its subject and every other
replaced person visible in any way; then group by these rules.

- One group per subject: all shots with the same subject go together (a dialogue that
  alternates between two faces is two groups; shots that look alike belong together anyway);
  their order in the group is their order in the video.
- **Every replaced person visible in a group's shots is replaced in that generation** — also
  the one standing with their back to the camera. Each gets a line in `{REPLACE}` (with
  `{WHERE}`: e.g. "seen from behind in the LEFT foreground") and their image in that group's
  `fileInputs`. A group's characters are its subject plus those extras: the fewest the video
  allows; never add a person who is not visible in the group's shots.
- **Camera moves between people count as wide shots.** A pan, slide or wipe that carries the
  view from one person to another (a quick sideways wipe between two musicians, a camera sweep
  inside a car) shows both people, so it goes into a **two-person
  group** of its own, with all such blocks of the video together. The detector finds many
  false "cuts" inside one (a hit every ~3 frames): judge them by looking at the frames and
  put the whole animation into one shot with `--cuts`. In the prompt (`{ORDER}` in
  `video_prompt.md`) say for every such part **who appears first and who second**, each with
  his `@Image`, and the part's times on the group's clip — otherwise the model may swap them. **Caution:** a long `{ORDER}` text (many parts, "never show…" lines) can lose
  the swap; keep `{ORDER}` to one short sentence per part and check the result.
  Take the part times for `{ORDER}` and `{WHEN}` from `groups.json` → `times`, not from the
  sheets: they are the shots' positions on the group's own clip (with the separators counted),
  which is the timeline the model sees; the sheets show the source video.
- A shot with **no replaced person at all** (empty room, insert, only unlisted people, a
  cutaway) goes into no group: it is not sent and comes back from the original video.
- An unlisted person who shares a shot with a replaced one stays in that shot (`{KEEP}`).
- The clip length limit of the model (15 s) applies to each group: a longer group is
  split into parts (`A1`, `A2`) at shot boundaries.
- A single shot longer than the model's limit (a 27 s dance take, a long monologue) is cut
  into parts at a **calm moment** (feet planted, facing the camera, no fast motion) with
  `--cuts` in step 3: the parts are ≤ 15 s each and the seam is a hard cut in the result.
  Expect a small jump of the new person's look at that frame.
- A run shorter than about 1 s that opens a clip with two people may stay unreplaced (a 0.6 s
  wide shot keeps the original faces): put such a shot into a clip after a longer shot of the
  same people, or keep it out and mention it in the question as "may stay unchanged".
- Keep each clip short: up to about 8 s and 3 runs (a run = a stretch of neighbouring shots).
  A long clip with many runs can come back with a run unreplaced and separators lost;
  the same people in two shorter clips come back complete. If a run is not replaced, split
  that group in two and rerun only it (a new paid step).
