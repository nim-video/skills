# Replacing Character Pipeline — limits and errors

Internal reference for the model; user-facing wording lives in `user_guide.md`. Re-check `generationContract` with `models_explore get` before each run.

## Video: Seedance 2.0 Advanced Mode, reference mode (default, `advanced:seedance:v2fal:standard`)
| Field | Rule |
|---|---|
| `referenceVideos` | 1–3 URLs (the skill sends one: the group clip). A new video that follows the clip — there is **no edit mode** |
| `mediaLength` | required, 4000–15000 ms in whole seconds; `build_groups.py` makes every clip a whole number of seconds long so the two match |
| `requestedAspectRatio` | `16:9 9:16 1:1 4:3 3:4 21:9` (no `auto`) — the nearest to the clip; `assemble.py` restores the original aspect |
| `fileInputs` | character images, max 9, aspect ratio 2:5…5:2 (`prep_images.py` pads) |
| `resolution` | 480p, 720p, 1080p, 4k |
| `generateAudio` | `false`; `finalize.py` puts the source audio back |
| `prompt` | up to 10 000 characters — `video_prompt.md` |
| forbidden | `sourceVideo`, `fps`, `keepSound` |

Price: 15 credits/s at 480p for the video, plus a duration-based charge for the reference
video (the estimate says "minimum price"; `generate_video` reports the exact charge). Typical
time ~4–5 min. Output: silent (generateAudio false), its length can differ a little from
`mediaLength` — `assemble.py` stretches every shot back to its original frames.

## Every clip sent 
Width × height 409 600 – 8 295 044 px, at least 854×480 and ≤ 20 MB — `prepare_video.py`
guarantees it for the source and `build_groups.py` re-encodes group clips under the cap.

## Shot groups
`split_shots.py` finds cuts from three per-frame signals on a 96x54 thumbnail: gray difference d,
colour-histogram distance h and the share f of changed pixels. Real cuts: d ≥ 20, or h ≥ 0.2
with d ≥ 8 (and f ≥ 0.2); between look-alike shots d ≥ 6 with ≥ 10× the local median and
h ≥ 0.08. Fast motion, gestures and subtitles stay below that. Weaker jumps are `candidates`
the agent checks on `cuts.png`. `timeline_N.png` gives one frame per 0.1 s.

`build_groups.py` puts 6 solid magenta frames between non-neighbouring shots: without them the
model melts near-identical shots into one take and the start of the result no longer matches
the original shot. `assemble.py` finds the separators in the result (magenta score > 0.5 on a
64x36 thumbnail, tinted neighbours count as separator) and cuts the shots out between them;
missing separator → nearest cut within 0.6 s → proportional position. Each shot is resampled by
time to its original frame count. A clip is never lengthened with copies of itself or filler:
short shots are glued to a neighbouring group, and the seconds still missing come from the
source frames right before and after the runs (`head`/`tail`), which assembly cuts off again.

## Error → action
| Symptom | Action |
|---|---|
| `素材处理失败` / `Failed to register input media with the provider` | video outside the pixel limits — rerun `prepare_video.py`; no blur |
| image aspect-ratio error (`… between 2:5 and 5:2`) | rerun `prep_images.py` |
| error text names moderation / safety / content / copyright | one retry of the group without sound (`--mute`); never blur the source or the character images |
| `failed` ~17 s after the start, `errorCause` null, source shows recognizable real faces (film / TV) | source refused at intake; blurring it passes intake but the blur stays in the result — tell the user the clip cannot be used, ask for another |
| `failed`, `errorCause` null, anything else | tell the user with the `promptId`; no blind retry |
| `insufficient_credits` | show `purchaseOptions`; `nim-credits` skill |
| contract rejects a parameter | re-read `generationContract`, fix the call |

