# Scene worker: everything one scene needs

You build one scene of a vox-video from a brief (subagents.md). Read only this file and the brief. Work in
`scenes/sNN/`. Paths below are relative to the skill folder `<skill>`.

## 1. Generate (skip what the coordinator already generated)

1. Design frame: `generate_image` with GPT Image 2.5 Flare Medium text-to-image (`models_explore`, follow its
   `generationContract`), `resolution: 2K`, `requestedAspectRatio` of the video. Prompt from the brief (layout + STYLE BLOCK +
   CLOSER). Keep the result's `mediaUrl`.
2. With that `mediaUrl` in `fileInputs`, fire both edits at once (the GPT Image 2.5 Flare Medium edit model
   from `models_explore`):
   - sheet, `requestedAspectRatio: "1:1"`: "Using this collage as the reference, lay out each of its story objects
     separately on one seamless flat pure magenta chroma-key background (#FF00FF), in a loose 3x3 grid with wide
     empty gaps between items. Each object complete and uncropped, with exactly the same design, colours,
     materials, lighting and top-down angle as in the collage, flat even light, no cast shadows, no paper rims.
     Objects: 1 [..], 2 [..] ... Do not include the grey silhouette, the yellow or cream strips or the background
     papers. No text."
   - plate, the video's ratio: "Edit this collage: remove every story object, the grey silhouette and the yellow
     and cream paper strips. Keep only the background layer exactly as it is, in the same positions. Fill the
     areas where objects were with the same background papers. No objects, no people, no text."
3. Download without polling: `uv run <skill>/scripts/nim_fetch.py <id1>=design.png <id2>=sheet.png <id3>=plate.png`.
Budget: 24 cr per scene + one retry. Log every call in `gen_log.json` `[{what, model, promptId, credits}]`.

## 2. Split and place

```
uv run <skill>/scripts/pack_split.py sheet.png items --mode key
```
Open `items/_sheet.jpg` (small), rename files to nouns of the phrase (`lamp.png`), delete crumbs.
```
uv run <skill>/scripts/layerize.py design.png items lay.json --size 1080x1920 --plate plate.png \
  --hero <person_cut.png> --scene scene_NN.draft.json --id sNN --t0 @first --t1 @next [--hints hints.json]
```
Items printed `UNMATCHED` or with `agree` < 0.35: write `hints.json` `{"cup": [x, y, width, rot]}` (video px,
width as drawn in the design) and run again once. Open `lay_check.jpg` (design | rebuilt | difference).

## 3. Build the scene (no hand-written build scripts)

Write `row.json` next to the draft and run `uv run <skill>/scripts/scene_build.py row.json`:
```json
{"draft": "scene_03.draft.json", "lay": "lay.json", "out": "scene_03.json", "plate_from": "left",
 "title": ["THE HARD", "WORK"], "title_at": "@hard",
 "name": {"text": "Scott Wiener, State Senator", "x": 540, "y": 1735, "rot": -2, "at": "@hard+0.1"},
 "hero_at": "@And#1",
 "enter": {"pen": "@do", "glasses": ["@do-0.1", "pop"]},
 "actions": {"lamp": {"glow": "@work"}, "watch": {"swing": "@hard", "until": "@writing"}},
 "add": []}
```
- Assembly is the default: plate slides over the previous scene and lands just before the first word, objects
  land with it back to front 0.12 s apart (near an edge: `slide`, large: `drop`, small: `pop`), hero on its word,
  title `wipe` on its key word, marks 0.2-0.3 s after.
- Actions only where a word asks: `glow` (lamp on), `swing` (watch, sign), `rise` (rocket, along a path), `roll`
  (train, cable car), `slam` (stamp), `drop` (newspapers onto a pile). Others: counters, highlights, arrows go in
  `add` as engine layers (examples in `<skill>/references/actions.md` only if you need one).
- Word references: `@word`, `@word#2` when it repeats, offsets `@word+0.15`.
- Title: two colours (ink + accent), sized to the yellow slot by the script. Name plate in Special Elite.
- Never set `background`, `camera`, `palette`, `captions`: they belong to the coordinator.

## 4. Check

Make `scene_test.json`: the coordinator's timeline header with `"scenes": [{"src": "scenes/sNN/scene_NN.json"}]`.
```
uv run <skill>/scripts/vox_engine.py scene_test.json --check     # layout OK, no EMPTY PLATE
uv run <skill>/scripts/vox_engine.py scene_test.json --gate      # PASS: fill >= .55, empty <= .07, match >= .45
uv run <skill>/scripts/vox_engine.py scene_test.json --stills scenes
```
Open the gate sheet and the stills sheet once each. Gate fails: fix the cause (missing object, wrong scale, an
empty area the design does not have, hero too small), at most two rounds. Do not render the video.

## 5. Hand back

Folder with `design.png`, `plate.png`, `items/`, `lay.json`, `lay_check.jpg`, `row.json`, `scene_NN.json`,
`scene_test_gate/`, `gen_log.json`. Final message, 5 lines: gate numbers, credits, actions used, anything the
coordinator must decide. No em dashes in any text.
