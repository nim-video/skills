# Coordinator and sub-agents (one chat)

## Split

| Job | Coordinator | Sub-agent (`Agent` tool, ≤4 at once) |
|---|---|---|
| one video | brief, facts, script, VO + `words.json`, art direction, storyboard, people cutouts, timeline, transitions, packshot, QA, render | **one scene each**: design frame → sheet + plate → items → layerize → actions → `scene_NN.json` → stills + gate |
| a series | shared art direction, people cutouts, shared fonts / palette, final QA | **one video each**: everything from facts to final MP4, using this skill |

Start: one tiny probe agent loads `get_credit_balance` and `generate_image` (no generation). If the Nim
tools do not load for workers, the coordinator runs every paid call (batch) and workers only split, layerize
and animate from the downloaded files.

## Brief to a worker (paste, filled)

```
Skill: <path>/references/worker.md (the only file to read). Model: Sonnet is enough for a scene worker.
Scene: s03 "And some do the hard work: writing laws that make life better." words 4.70-7.90 s
  (t0 "@hard", t1 "@The#2"), words.json: <path>.
Format: 1080x1920. Art direction: <path>/art.md (STYLE BLOCK, CLOSER, palette, fonts).
Storyboard row: hero = Scott Wiener (cutout <path>), title "THE HARD WORK" (THE HARD = ink, WORK = accent),
  name plate "Scott Wiener, State Senator", objects: California Capitol, palm, banker's lamp, tied documents,
  glasses, fountain pen, coffee, pocket watch. Actions: lamp switches on at "work", watch swings at "hard".
Folder: <project>/scenes/s03/. Budget: 30 credits (3 GPT Image 2.5 Flare Medium calls + 1 retry).
Deliver: row.json + scene_03.json (built with scene_build.py, layers relative to the folder), lay_check.jpg, a test timeline that includes only this
  scene + its gate sheet (PASS), stills start/mid/end, gen_log.json [{what, endpoint, workflowId, credits}].
Do not render the full video, do not touch other scenes, no em dashes in any text.
```

## Hand-back format

`scenes/sNN/` with `design.png`, `plate.png`, `items/`, `lay.json`, `lay_check.jpg`, `scene_NN.json`,
`scene_test.json` + `scene_test_gate/`, `gen_log.json`; final message: 5 lines (gate numbers, credits, actions
used, anything the coordinator must decide).

## Seams (coordinator)

- One camera, one desk, one palette, one rim/shadow setting: workers never set `background`, `camera`,
  `palette`, `captions`; only layers.
- Each fragment gets its z band from its order in `scenes` (1000 x n), so the next plate always covers.
- Transitions are the coordinator's: plate entrance direction alternates, whoosh on the cut word, nothing exits.
- Word references: workers use `@word#N` when a word repeats (the engine warns about ambiguous refs).

## Failures

- Worker stops or returns a failing gate: read its `gen_log.json`; reuse what was generated (frame, sheet,
  plate) and finish the scene yourself, or resend one precise fix ("the cup hint is 120 px too high; the title
  must fill the slot"). Max one retry per scene, then do it yourself.
- A paid call fails: check `get_generation_status` once (it may still be running), then retry once.
- Nim queue slow: `nim_fetch.py --timeout 900`; never start duplicate generations.

## Batching paid calls

The coordinator may collect all scenes' design-frame prompts and launch them in one go (one OK for
the total), and hand the downloaded frames to workers. That is the fastest path when the
storyboard is final: generation becomes one ~1.5 min wait for the whole video.
