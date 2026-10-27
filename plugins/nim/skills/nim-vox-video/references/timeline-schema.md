# timeline.json schema

World pixels: the video frame at camera zoom 1 (e.g. 1080x1920); the desk extends beyond it. Paths: relative to
the file that names them (a scene fragment's paths are relative to the fragment), or `pack:textures/<name>.jpg` (desk textures: newsprint, kraft, graph, blueprint).

## Time references
`1.25` · `"@fifty"` (first matching word, case/punctuation-insensitive, `$` kept) · `"@one#3"` (3rd occurrence;
the engine warns AMBIGUOUS when a word repeats and no `#N` is given) · `"@Tea"` (capitalised key prefers the
capitalised word) · `"@doom.end"` · offsets only as a trailing number: `"@cracked+0.15"`, `"@gets-0.1"`
(`"@eight-oh-eight"` is a word, not an offset).

## Top level
```json
{
  "size": [1080, 1920], "fps": 24, "anim_fps": 12, "duration": "auto", "end_hold": 1.2,
  "palette": {"paper": "#f3eee2", "ink": "#16161a", "accent": "#23824F", "accent2": "#F2C230", "navy": "#26245e"},
  "audio": {"vo": "vo.mp3", "words": "words.json", "sfx_vol": 0.64, "music": null},
  "background": {"image": "pack:textures/newsprint.jpg", "world": [3240, 5760], "origin": [-1080, -1920]},
  "captions": {"font": "Anton-Regular.ttf", "size": 58, "y": 0.9, "max_words": 3},
  "captions_reason": "only when captions are false: why (e.g. every scene carries its words as a title strip)",
  "packshot": "@Make",
  "live": 1.0,
  "camera": [{"t": 0, "x": 540, "y": 960, "zoom": 1}],
  "scenes": [
    {"src": "scenes/s1/scene_01.json"},
    {"src": "scenes/s2/scene_02.json", "origin": [0, 0]},
    {"src": "../shared/packshot.json", "at": "@Make", "z": 9000}
  ],
  "layers": []
}
```
- `scenes`: fragments in order; each gets z band 1000 x (index+1) unless `z` is given, `origin` shifts all its
  x/y (scenes laid side by side on the desk for camera pans), `at` makes the fragment's numeric times relative
  (reusable packshot). Fragment file: `{"id", "t0", "t1", "design", "plate", "layers": [...]}`; layer ids become
  `sid.id`; `parent` refers to ids inside the same fragment.
- `packshot`: time of the end card; layers flagged `"packshot": true` that enter >0.35 s earlier are reported.
- `live`: living paper (slow breathing of landed pieces); per layer `"live": 0` to keep something still.
- Captions are on by default; `"captions": false` needs `"captions_reason"`.

## Common layer fields
`id`, `type`, `x`, `y` (centre), `scale`, `rot`, `alpha`, `z`, `elev`, `boil` (true/false/multiplier), `live`,
`shadow`, `shadow_px`, `shadow_op`, `parent`, `hero` (checked against labels and objects hidden under it),
`overlay` (label intentionally on the hero), `backdrop` (not counted as content by the gate), `packshot`,
`in`, `out`, `keys`, `wiggle`.

### in (entrance)
`{"t": "@word", "fx": "...", "dur": s, "from": "left|right|top|bottom", "dist": px, "spin": deg, "arc": 0.12, "sfx": "...", "vol": 1}`

| fx | motion | default sfx |
|---|---|---|
| `slide` | arc path, spring arrival, rotation follow-through, squash on landing | slide |
| `drop` | gravity fall, squash, tiny bounce, auto shake | thud |
| `slam` | falls toward the desk from 1.5x, impact squash | thud |
| `pop` | spring scale from 0 | tick |
| `burst` | flies out of `origin: [x, y]` along an arc with `spin` | tick |
| `roll` | vehicle rolling in at constant speed, soft braking, slight rumble (train, cable car) | roll |
| `flicker` | a light catching: two quick flashes then steady (use on `glow`) | click |
| `fade` | opacity | none |
| `draw` | markers draw themselves | scribble |
| `wipe` | labels reveal left to right like tape | tape |
| `count` | counters roll | tick |

### out (exit; rarely needed in v8: the next plate covers the scene)
`{"t": ..., "fx": "fly|scatter|fade|pop|lift", "to": "left", "dist": 1800, "dur": 0.4}`

### keys (moves of a placed layer)
`[{"t": "@moon", "x": 600, "y": 300, "rot": -4, "scale": 0.84, "dur": 0.45, "lift": 0.9}]` · default motion
anticipation + spring settle + lift; `"ease": "out|inOut|in|linear|soft"` disables anticipation.
**Path move:** `{"t": "@moon-0.3", "path": [[x1, y1], [x2, y2], ...], "dur": 1.6, "ease": "in", "orient": false,
"sfx": "whoosh"}`: the layer travels from where it is through the points (smoothed); `orient: true` turns it along
the route.

### wiggle (decaying swing / sway / tremble)
`{"t": "@hard", "until": "@writing", "rot": 9, "x": 0, "y": 0, "freq": 1.1, "decay": 0.8, "pivot": [0, -180]}`
`pivot` = source px from the image centre (a watch ring at the top swings the watch below it).

## Layer types
| type | fields | notes |
|---|---|---|
| `plate` | `src`, `size` (default frame width), `x`, `y` (default frame centre) | the design frame's background; no rim, no shadow, no grade |
| `image` | `src`, `size` (px width), `crop`, `flip`, `rim` (default 10, 0 = none), `print` (`photo`, `paper`, `newsprint`, `halftone`, `none`) | objects and people |
| `panel` | `texture`, `w`, `h`, `torn` | torn paper sheet |
| `strip` | `text` or `parts` [{`text`, `fg`, `font`, `size`}], `font`, `size`, `fg`, `bg`, `tape`, `padx`, `pady` | torn paper label; parts = two-colour titles |
| `stamp` | `text`, `font`, `size`, `color` | rubber stamp; use `slam` |
| `text` | `text`, `font`, `size`, `color` | plain type (packshot, disclaimer) |
| `rect` | `w`, `h`, `color`, `radius`, `grain` | colour box (packshot bands, check boxes) |
| `poly` | `pts` (own box px), `color` | filled polygon (flag stripes, ticks) |
| `glow` | `r`, `color`, `strength` | warm light pool; `in.fx: flicker` |
| `marker` | `shape`: `circle [cx,cy,rx,ry]`, `arrow [x0,y0,x1,y1]` + `bend`, `path [[x,y],...]`, `highlight [x0,y0,x1,y1]`; `width`, `color`, `style` (`brush`), `opacity`, `parent` | `in.fx: draw`; with `parent`, points are px of the parent's original image (typeset.py boxes) |
| `counter` | `from`, `to`, `fmt` (`"{}+"`), `fmt_roll` (format while rolling, e.g. `"{}"`), `size`, `color`, `font` | `in.fx: count` |
| `grid` | `src`, `count`, `cols`, `rows`, `cell`, `skip`, `screen`, `colors`, `in.span`, `in.origin` | N cards in a pop wave |
| `screen` | `parent`, `x`, `y`, `w`, `h`, `radius`, `content [...]` | drawn into the parent image (video, image, fill, code, steps, sprite); x/y/w/h are pixels of the parent as rendered (after its `size`), content `src` relative to its file |

## Commands
```
uv run vox_engine.py timeline.json --check [--fix]     # overlaps, cuts, wedge corners, arrow stubs, hidden objects, word refs
uv run vox_engine.py timeline.json --stills scenes [--full]   # start / mid / end of every scene (or beats, or 1.2,3.4)
uv run vox_engine.py timeline.json --gate [--full]     # design | final per scene + fill / empty / objects / match
uv run vox_engine.py timeline.json --draft             # 540p 12 fps
uv run vox_engine.py timeline.json --out final.mp4 [--jobs N]   # parallel render, -14 LUFS two-pass
```
Gate thresholds: fill ≥ 0.55 (content layers over the frame minus margins and caption band), biggest empty
square ≤ 7% of the frame, match ≥ 0.45. `--out` and `--draft` refuse when `--check` finds errors.
