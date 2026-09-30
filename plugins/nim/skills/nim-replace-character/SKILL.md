---
name: nim-replace-character
description: Replace the user (or the people) in their video with characters from their images — through Nim. The agent prepares the video, splits it into shots, groups similar shots so each generation replaces as few people as possible (a dialogue that alternates between two people becomes two clips), sends every group plus the character images to the Replacing Character Pipeline, puts the shots back in their original order frame for frame, lays the original sound on top and hands the finished video file to the user in the chat. Takes the user's own video and swaps the people in it (unlike motion transfer, which moves a performance onto a new character). Use this skill whenever the user uploads a video and one or more character images and asks to "replace me with this character", "swap me in this video", "put this character in my place", "turn us into these characters", or mentions the Replacing Character Pipeline — even if they phrase it loosely or do not describe the steps.
compatibility: Requires the Nim MCP connector (media_upload, models_explore, generate_video, get_generation_status), ffmpeg/ffprobe (libx264), Pillow and OpenCV (cv2).
---

# Replace people in a video with characters (Nim)

The user gives a **video** and **one or more character images** and says "replace me with this
character" (or several people with several characters). The user does not write prompts or
pick settings — the agent does.

Seedance handles several people in one clip badly (often only one is replaced). So the video is
cut into **shots**, the shots are **grouped** by who is in them, and each group is stitched into
its own clip — ideally with one replaced person. Shots with no replaced person are not sent.
Each clip goes through its own generation; when the results are back, every shot returns to
its original frames, the source audio goes on top, and the finished file goes to the user.

```
video ─► prepare_video.py ─► split_shots.py (sheets: who is in which shot)
character images ─► prep_images.py ─► shot plan (groups)
   build_groups.py ─► g_A.mp4, g_B.mp4 …  (one clip per group)
   media_upload ─► generate_video ×N in parallel (clip + only its characters)
                ─► assemble.py (shots back in original order, frame-exact)
                ─► finalize.py (source audio) ─► result.mp4 to the user as a file
```

Invoking this skill counts as the user choosing Nim; Nim tools may be called directly.
Pass `skills: ["nim-replace-character"]` on every Nim call that accepts it.
Work in one scratch folder (called `WORK` below — e.g. `/home/claude/rcp` or the session
scratchpad).

## Model

Seedance 2.0 Advanced Mode, reference-video mode. This is the only model and the only prompt
(`references/video_prompt.md`).

| Parameter | Value |
|---|---|
| `model_id` / `model_name` | `advanced:seedance:v2fal:standard` / `Seedance 2 Advanced Mode` |
| `referenceVideos` | `[group clip URL]` — a new video that follows the clip (no edit mode) |
| `fileInputs` | the character image URLs of that group, up to 9 |
| `mediaLength` | the clip length in ms, whole seconds 4000–15000 (`groups.json` → `media_length_ms`) |
| `requestedAspectRatio` | the nearest of `16:9 9:16 1:1 4:3 3:4 21:9` to the clip |
| `resolution` | from the option (480p / 720p) |
| `generateAudio` | `false` |
| `batchSize` | `1` |

Do not pass `fps`, `keepSound`, `sourceVideo`. Read the model's `generationContract`
(`models_explore action=get`) before the first call.

## What the user sees

The user is buying a finished video, not following the pipeline. So:

- **Deliver the file, not a link.** The deliverable is `result.mp4` with the source audio,
  attached in the chat with the host's file tool (`present_files`, `SendUserFile`, or copying it
  to the outputs folder the host shows). Raw `mediaUrl`s, `file_url`s, storage/bucket links and
  `nim.video/explore` pages are internal plumbing — they carry the silent raw renders or the
  uploads, so never paste them into the chat.
- **No verdicts.** Do not grade the result ("both swaps worked", "one defect: …", model A vs
  model B). The user judges the video themselves; an opinion from the agent is noise at best and
  wrong at worst.
- **The setting stays as it is in the video** unless the user asked to change it: the prompts
  say so explicitly (`{SETTING}`); only a user's wish for another place replaces that line.
- **No pipeline narration.** No moderation refusals, face blurring, model or vendor names. In
  user-facing text the stage is the **Replacing Character Pipeline** («пайплайн замены
  персонажа»). The only thing said about the split is the one line in the question ("N parts").
- **One question per paid step** — the choice of the run (Stage 0, step 6) and, after a 5 s
  check, whether to make the full video (Stage 2, step 4). Nothing else is asked, whatever the
  character image shows (drawn, photo, animal, object). One hard limit: a recognizable public
  figure is never put into a video.

## Inputs

| Input | Required | Source |
|---|---|---|
| Video | yes | user |
| Character image(s) | yes | user; 1–4 per character, several angles or a character sheet help |
| Who becomes whom | if >1 person or >1 character | asked inside the Stage 0 question |
| Extra wishes | no | user |

If the video or the character images are missing, show "Короткая памятка" from
`references/user_guide.md` (in the user's language) and wait.

## Stage 0 — Prepare, split, plan, confirm (free)

1. **Prepare the video.** Everything after this uses the prepared file.
   ```bash
   python scripts/prepare_video.py <video> WORK/driving.mp4
   ```
   - 4–30 s. Under 4 s → exit 2 `rejected`: ask for a longer video (no looping or slowing).
     Over 30 s → exit 2 `needs_trim`: ask which part to keep (suggest the first 30 s), rerun
     with `--start S --end E`. The length is kept exactly; `result.media_length_ms` is it.
   - Fixes small frames (provider minimum 409 600 px and 854×480), converts to 24 fps H.264
     with even sides, fits the 20 MB upload cap. Exit 3 `too_large` → ask for a shorter segment.
   - Heavy sources can take minutes: run with a timeout or in the background.
2. **Prepare the character images** — Seedance accepts aspect ratios 2:5…5:2 only; wider or
   taller images are padded, never cropped:
   ```bash
   python scripts/prep_images.py WORK/refs <image1> <image2> …
   ```
   Use the `out` PNGs from here on.
3. **Split into shots and read the video to 0.1 s.**
   ```bash
   python scripts/split_shots.py WORK/driving.mp4 WORK/sp
   ```
   Writes `shots.json` and the sheets in `WORK/sp/`: `timeline_N.png` (one frame every 0.1 s
   with its time, 5 s per sheet), `sheet_N.png` (first / middle / last frame of every shot),
   `cuts.png` (every cut and candidate as a frame-before | frame-after pair). Look at **all**
   of them and at every character image. **Read the video yourself first**: go through the
   timeline sheets frame by frame (0.1 s apart) and write down, before looking at the detected
   list, (a) the exact time and frame of every cut — the last frame of the old shot and the
   first frame of the new one — and (b) for every person the exact times (to 0.1 s) when they
   are on screen, in which position and at what angle. A smooth movement (a head turning, a hand
   sweeping through the frame) is not a cut; a jump of composition, person or background is.
   Then compare with `cuts` and `candidates`: every candidate is settled by looking at its
   before | after pair (and, if needed, single frames around it). Where your list and the
   detector disagree, go with what the frames show and rerun with `--cuts F1,F2,…` (frame
   numbers where a new shot starts: the accepted cuts). A missed cut between shots of different
   people is the costly mistake; a false cut inside one group is harmless. Also work out: what
   tells the people apart (viewer-side position, clothes, headgear), the style of each character
   image (photo / anime / cartoon / 3D / painting / object), and the type of every person and
   every character — exactly one of man / woman / boy / girl / character (the only nouns the
   prompts use).
4. **Shot plan** — for every shot write down its **subject** (the replaced person whose face is
   on screen, the largest if several) and **every other replaced person visible in any way**:
   from behind, in profile, at the frame edge, half hidden. Then group:
   - Group by subject, put every visible replaced person into that group's generation, treat
     camera moves between people as two-person wide shots, glue short shots to neighbours, keep
     each clip ≤ ~8 s and ≤ 3 runs: **read `references/shot_planning.md` and follow it.**
   - Write `WORK/plan.json` — `{"groups": {"A": [1, 3, 5], "B": [2, 4]}}` (shot numbers) —
     and build the clips:
     ```bash
     python scripts/build_groups.py WORK/driving.mp4 WORK/sp/shots.json WORK/plan.json WORK/grp --max-s 15 --audio [--mute A,B]
     ```
     **Sound goes into the clips by default (`--audio`)**: the model's
     subtitles and mouth movements follow the source better with it, and it changes nothing else. Groups whose people do not speak are built silent with
     `--mute A,B` (group ids). With no sound in the source the clips are silent anyway. Clips are `WORK/grp/g_<id>.mp4`: the group's shots, with 6 solid
     magenta frames between shots that were not neighbours (they keep near-identical shots apart
     and mark the exact cut for `assemble.py`), and, up to whole seconds, the source frames right before and after the group's shots (`head`/`tail` in groups.json; thrown away at assembly, billed).
     **Never fill a clip with copies of itself**, the model then just repeats the reference (the result comes back unchanged). A group under 4 s → exit 2: glue its shots
     to the group they touch in the video (contiguous shots become one run), or else to the
     group closest in length that has a person to replace. Short shots (pans, 0.5 s inserts)
     go with the neighbouring shots that show the same people; a pan shows both people, so
     put it with the shots on either side of it.
     `groups.json` lists per group the length (`media_length_ms` → `mediaLength`), the shots and
     their times **on the group's own clip** (use those for `{WHEN}`).
   - Per group: the people to replace (with what marks them in that group) and the people who
     stay. More than two replaced people in one group: say in the question that some may stay
     unchanged.
5. **Prices from Nim** — never from memory. Per group, then add up:
   `models_explore action=get model_id=advanced:seedance:v2fal:standard` with
   `referenceVideoCount=1`, `referenceImageCount=<that group's character images>`,
   `aspectRatio`, `resolution`, `minDurationMs=<group media_length_ms>` →
   `priceEstimate.credits`. The reference video adds a duration-based charge on top; the
   final charge can be well above the estimate — say "can be higher".

   | Option | Length | Resolution |
   |---|---|---|
   | A. Check | first 5 s (skip if the clip is ≤ 5 s) | 480p |
   | B. Full | whole prepared length | 480p |
   | C. Full | whole prepared length | 720p |

   Option A is planned again on its own 5 s (steps 3–4 on `driving_5s.mp4`).
6. **The one question** (host choice UI if there is one, else a numbered list): what was done
   to the video (one line), that it will be generated in N parts (one line: which people in
   which part, if N > 1), who becomes which character, options A / B / C with one total price
   each, and **D. Change something** (segment, resolution, mapping, wishes). Ask an
   unclear mapping in the same message. **When the video has speech and more than one person,
   ask in the same message, plainly, whether each character speaks in all scenes** («говорят ли
   персонажи во всех сценах, и где кто молчит — это улучшит результат»): the frames alone do
   not tell who owns the voice (a listener's mouth moves too). Groups of people the user says do not speak are built with `--mute` and get the
   silent `{PERFORMANCE}` line; groups of speakers keep the sound. The answer approves one
   generation per group and,
   after an intake refusal, one retry of that group without sound. After that run Stages 1–2
   without further questions. Anything else paid needs a new yes.
   - Option A: `prepare_video.py <video> WORK/driving_5s.mp4 --start 0 --end 5`, then steps 3–4
     on that file and use it from here on.

## Stage 1 — Generate

1. **Upload** every group clip and the character PNGs: `media_upload` → run its `curl_example`
   with the real path (one upload URL serves several files while valid) → keep each `file_url`.
2. **Prompt per group** from `references/video_prompt.md`: that
   group's people (subject and extras) and their images; `@Image` numbers follow that group's
   `fileInputs`. Fill `{PERFORMANCE}` per person (speaks / does not speak), `{MARKERS}` whenever
   the clip has separators (several runs), `{SETTING}` (keep the environment).
3. **Call `generate_video` once per group, all in one message** (they run in parallel), with
   the parameters of the Model table.
4. **Poll** `get_generation_status` for every group every 1–2 min until `finished | failed |
   cancelled | removed` (typically 4–8 min).
5. **On failure find the real cause** — `errorCause` is often null; do not guess:
   - `素材处理失败` / `Failed to register input media with the provider` — the clip is outside
     the pixel limits; check it went through `prepare_video.py`.
   - Error text names moderation / safety / sensitive / copyright content, or `failed` within
     ~20 s with `errorCause` null (the clip was refused at intake, e.g. film footage of
     recognizable actors, or the error `InputVideoSensitiveContentDetected`) → **one**
     retry of that group with the clip built without sound (`build_groups.py … --mute <id>`).
     **Never blur** anything to get past a refusal, neither the source nor the character images:
     a blurred source passes intake but the blur stays in the result and nothing is swapped.
     Refused again → try the shots without the recognizable person on their own and leave that
     person original (a clip without him was accepted), or tell the user the clip cannot be used
     and ask for another one (see the guide).
   - Anything else → tell the user that part of the video failed, with the `promptId`; no blind
     retry (a rerun of one group is a new paid step and needs a new yes). Keep the finished
     groups' results.
   Refused and failed generations are not charged.

## Stage 2 — Finish and deliver

1. Download every `mediaUrl` to `WORK/raw_<id>.mp4`. With several groups put the shots back:
   ```bash
   python scripts/assemble.py WORK/driving.mp4 WORK/grp/groups.json WORK/assembled.mp4 A=WORK/raw_A.mp4 B=WORK/raw_B.mp4
   ```
   Exit 0 = the output has exactly the original's frame count. (Exit 3 or an error: do not
   deliver; tell the user the video could not be assembled, with the `promptId`s.) This runs
   for a single group too: it cuts off the extra frames and matches the length.
2. Put the source audio back (`driving_5s.mp4` for option A):
   ```bash
   python scripts/finalize.py WORK/assembled.mp4 WORK/driving.mp4 WORK/result.mp4
   ```
3. Hand `WORK/result.mp4` to the user as a file in the chat (see "What the user sees").
4. Reply in 1–2 lines: that the video is ready, and the credits spent (all groups). Nothing else
   — no links, no assessment, no process details.
5. **After option A, ask whether to make the full video** — one question (host choice UI if
   there is one): full @480p / full @720p with their prices, or not now. Get the prices the
   same way as in Stage 0, step 5.

## Stage 3 — Full run after the check

When the user picks a full run after option A: the 5 s check covered only the start, so run
Stage 0 steps 3–4 again on the full `driving.mp4` (split, plan, `build_groups.py`), with the
same character images and mapping. The user's choice is the yes for one generation per group
(plus the moderation retry). Then Stage 1 and Stage 2.

## Failure handling

Limits and error meanings: `references/pipeline_limits.md`. Explain errors to the user with the
guide's "Частые причины отказа".
