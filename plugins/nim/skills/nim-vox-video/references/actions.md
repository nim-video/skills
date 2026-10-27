# Meaningful actions

**Rule:** every movement must be explained by a word of its phrase. Read the phrase, underline the verbs and
the nouns that can act (rocket, lamp, train, counter, quote, newspapers). Those objects get an action timed to
their word; every other object is simply laid on the desk during the assembly (back to front, in the order the
phrase names things). If you cannot say which word motivates a movement, do not add it.

## Assembly (the default for every object)

- Plate slides in (new sheet over the previous scene) 0.3 s before the scene's first word.
- Objects: back to front, 0.12-0.18 s apart, entrance by where they sit: near an edge → `slide` from that edge;
  large → `drop`; small → `pop`. Hero on its word (0.3 s before). Title `wipe` on its key word. Marks after.
- After landing: living paper (automatic, `"live": 1`; 0 disables). Nothing else moves unless it has a reason.

## Library

| phrase gives | object | timeline |
|---|---|---|
| "to the moon", "launch", "takes off" | rocket | `keys: [{"t": "@moon-0.4", "path": [[x, y-400], [x+40, y-1400]], "dur": 1.6, "ease": "in", "orient": false, "sfx": "whoosh"}]` + marker arrow along the route drawn just before |
| "lights", "switches on", "bright idea", "work late" | lamp | a `glow` layer at the bulb: `{"type": "glow", "x":..,"y":..,"r": 260, "in": {"t": "@work", "fx": "flicker"}}` |
| "calls him", "quote", "says" | quote card | `typeset.py` card + `marker` `shape: highlight`, `parent: card`, `pts` = a highlight box, `in.fx: draw` on the quoted words |
| numbers, "100+", "laws passed" | counter | `{"type": "counter", "from": 25, "to": 100, "fmt": "{}+", "in": {"t": "@laws", "fx": "count", "dur": 1.1}}` |
| "headlines", "the papers", "writes" | clippings | `drop` one by one onto a pile (0.25 s apart), small rotation each, thud on each landing |
| "train", "BART", "ride", "commute" | train | `in.fx: roll` from the side along the rails (`dist` 1200, `dur` 1.4), or `keys.path` along a drawn route map |
| "time", "years", "every day" | pocket watch | `wiggle: {"t": "@time", "rot": 9, "freq": 1.1, "decay": .8, "pivot": [0, -h/2]}` (swings on its chain) |
| "signed", "passed", "approved" | stamp / pen | `stamp` with `slam` on the word; pen `keys` across the paper with a marker underline drawn behind it |
| "build", "homes" | houses | `drop` in a row left to right on the word, each 0.12 s later (a street being built) |
| "vote", "choose" | check mark | `poly` tick or marker path drawn in 0.3 s on the word |
| "grows", "rises", "more" | chart line | marker `path` drawn left to right; dot `pop` at the end |
| "nation", "city", "map" | map piece | camera push-in (`camera` key `zoom` 1 → 1.06 over 2 s) instead of moving the map |
| "fight", "push" | arrow | marker arrow (brush) from the person to the target, drawn on the verb |

Transitions between scenes: the next plate slides over on the next scene's first word (alternate from
bottom / right / left), or the camera pans to the next scene placed beside it (`origin` in the scene entry,
camera key with `"sfx": "whoosh"`). Never fade whole frames.

## Do not

- Loop or wiggle objects that have no reason (no bobbing cups, no spinning clocks).
- Move every object every scene; most objects only land.
- Let an action fight the title: the title and the hero stay still while the action plays.
- Animate a whole design frame with Seedance; Seedance is only for real motion inside a screen or window.
