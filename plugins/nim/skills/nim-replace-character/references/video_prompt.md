# Video prompt (Seedance 2.0, reference-video mode)

The group clip goes in as `referenceVideos` (`@Video1`); the model generates a new video that
follows it. One generation = one clip (a group of shots) + the character images of every
replaced person visible in that clip + this text. `@Image1…@ImageN` follow the `fileInputs`
order, numbered **per generation** (all images of character 1 first, then character 2, …).
Name every image in the text — an image the prompt never mentions can be ignored. Fill only the
placeholders; copy everything else verbatim. Empty placeholders leave no blank line behind.

Times in the prompt (`{WHEN}`, `{ORDER}`) are on the **group clip's own timeline**
(`groups.json` → `times`), not on the source video.

## Template

```
{TOP}
Recreate the video @Video1 shot for shot — same camera, framing, cuts, timing, motion, expressions and gestures — with {CHANGE}:
{REPLACE}
{ORDER}{KEEP}
{IMG_ROLE}
Each new person takes over the original person's exact position, scale, pose, movement, expression and timing; nothing of the original person's {GONE} remains.
{PERFORMANCE}
{MARKERS}{SETTING}
{REQUIRED}Do not add cuts or invent new movement or scene elements.
{STYLE}{USER_WISHES}
```

- `{TOP}` — always the first line, verbatim, one of two (`characters` / `new characters` when two or more are replaced):
  `Only the character in @Video1 is replaced, by the new character from the images; the location, lighting and all movements stay exactly as in @Video1.`
  `Only the characters in @Video1 are replaced, by the new characters from the images; the location, lighting and all movements stay exactly as in @Video1.`
- `{CHANGE}` — `one change` / `two changes` / `three changes` (number of replaced people).
- `{REPLACE}` — **every** replaced person visible in the clip's shots, one line each, in order
  of first appearance, including people seen from behind, in profile or at the frame edge
  (`{WHERE}` says so: "seen from behind in the LEFT foreground"; add `; only his hair and
  clothes show`):
  `{WHEN}Person A — the {WHERE} {WHOM} in {MARKER} — becomes the {WHO} from {IMGS}{OUTFIT_PART}{REMOVED}.`
  With one replaced person drop the label: `{WHEN}The {WHERE} {WHOM} in {MARKER} becomes the {WHO} from {IMGS}…`
  - `{WHO}` (the character in the image) and `{WHOM}` (the person in the video) — exactly one
    of: `man`, `woman`, `boy`, `girl`, `character`. `character` = anything that is not clearly
    one of the other four (robot, mannequin, creature, plush toy…). Anime/cartoon people still
    get man/woman/boy/girl — `{STYLE}` keeps them drawn. Never write `performer`, `person`,
    `actor`, `singer`, `agent`, `anime girl` or any other noun.
  - `{WHEN}` — the time range(s) where this person is on screen, when people appear in
    different shots or could be confused: `0.0–2.5 s: ` or `at 0.0–2.0 s and 6.0–8.0 s: `.
    Skip it when the person is in the whole clip.
  - `{WHERE}` — how to find that person **in the video**: one person → drop it; side by side →
    viewer's side in caps (`viewer's FAR RIGHT`, `viewer's LEFT`, `MIDDLE`); different shots →
    `{WHEN}` and `{MARKER}`.
  - `{MARKER}` — what marks the person in the video: clothes, headgear, prop, guitar colour
    (`bearded man in a red hoodie and headphones`). One person in several outfits → list them.
  - `{IMGS}` — `@Image1`; several images of one character: `@Image1–@Image3`.
  - `{OUTFIT_PART}` — the clothes: from the character's images (`, wearing a dark jacket`, 3–8
    words; several outfits in the images → pick one that suits the scene) or, when the video's
    clothes stay (the user asks, or the outfits do not fit the scene): `, keeping the clothes
    (and the headphones…) from @Video1`.
  - `{REMOVED}` — what the original wears that the character does not (mask, hood, cap,
    glasses…): `; the cap and glasses are removed`, and if the hair differs, `and his hair
    follows @Image1`. A cap or beanie left in the prompt stays on the new person — always
    remove it here when the character has none.
- `{ORDER}` — only for a clip with camera moves between people (pans, slides, wipes; SKILL.md
  step 4). **One short sentence per part**, times from `groups.json` → `times`, who is on
  screen first and who second, each with `@Image`, then a newline:
  `0.0–1.5 s: the camera pans from the man in the blue jacket (@Image2) to the bearded man in the red hoodie (@Image1).`
  No "never show…" line and no long lists (a long version can lose the swap).
- `{KEEP}` — people who stay as they are (same nouns), or empty: `Keep the LEFT man and the MIDDLE woman the same.`
- `{IMG_ROLE}` — what the images are for; `{IMGS}` here lists all character images
  (`@Image1 and @Image2`):
  - clothes from the video (when `{OUTFIT_PART}` keeps them): `{IMGS} define only the new people's face, hair, skin, facial hair and body build; do not use their backgrounds, poses or clothes.`
  - clothes from the images: `{IMGS} define only the new people's face, hair, skin, body build and clothing; do not use their backgrounds or poses.`
  - one person: `the new person's`, `@Image1 defines`.
- `{GONE}` — `face` when the video's clothes stay; `face, hair, body or clothes` when the
  images' clothes are used (add `, mask` etc. for worn gear).
- `{PERFORMANCE}` — always, one of two lines (the user says who speaks, SKILL.md step 6):
  - person who **speaks** (clip built with sound): `Each new person copies the original person's facial performance exactly, frame by frame: every expression, the direction of the eyes and gaze, and every mouth and lip movement, in sync with the original speech. @Video1 carries that speech: the new person's lips follow it word by word.`
  - person who **does not speak** (clip built with `--mute`, or a musician / listener):
    `Each new person copies the original person's facial performance exactly: every expression, the direction of the eyes and gaze, and every mouth movement. The new person does not speak.` (several people: `Neither new person speaks.` / `The new people do not speak.`)
  Several people in one clip: name each (`Person A speaks…`); a mix of speakers and
  non-speakers is avoided by the grouping (the groups follow the person).
- `{MARKERS}` — whenever the clip has separators (several runs): `@Video1 has short solid
  magenta frames between some of its parts: keep every magenta frame exactly where it is, with
  nothing else in it.` plus a newline. It keeps the shots apart and marks each cut.
- `{SETTING}` — never empty. Default: `Keep the environment exactly as in @Video1: the
  {the scene's main items, e.g. studio, couch, microphones, wall poster}, the lighting and
  colours stay the same.` plus a newline. Only when the user asked for another place:
  `Move the scene to {place}; keep the camera angles, shot sizes and depth of field.`
- `{REQUIRED}` — two or more replaced people: `Both replacements are required: no shot may keep an original replaced person. ` (`All replacements are required: …` for three). One person: empty.
- `{STYLE}` — empty when every character image is a photo. For a drawn / rendered / object
  character one line + newline (without it the model can turn a drawn character photoreal):

  | Image looks like | Line (for the character from @Image2) |
  |---|---|
  | 2D anime / manga | `The character from @Image2 stays a 2D anime drawing (line art, cel shading), not photoreal.` |
  | 2D cartoon / comic | `The character from @Image2 stays a 2D cartoon drawing with its outlines and flat colours, not photoreal.` |
  | 3D CGI / game render | `The character from @Image2 keeps its 3D CGI render look, not photoreal.` |
  | painting / illustration | `The character from @Image2 keeps its painted look, not photoreal.` |
  | plush / figurine / object | `The character from @Image2 stays a {plush toy / figurine / …} with its material, not a person.` |
- `{USER_WISHES}` — the user's own extra wishes, as they said them, or empty.

## Example — two people, a camera pan between them, clothes stay

```
Only the characters in @Video1 are replaced, by the new characters from the images; the location, lighting and all movements stay exactly as in @Video1.
Recreate the video @Video1 shot for shot — same camera, framing, cuts, timing, motion, expressions and gestures — with two changes:
Person A — the bearded man in a red hoodie and headphones, with the silver guitar — becomes the man from @Image1, keeping the clothes and the headphones from @Video1; the cap is removed and his hair follows @Image1.
Person B — the man in a blue jacket and glasses, with the green guitar — becomes the man from @Image2, keeping the clothes from @Video1; the glasses are removed and his hair follows @Image2.
4.0–4.5 s: the camera pans from the man with the silver guitar (@Image1) to the man with the green guitar (@Image2).
6.67–7.21 s: the camera pans from the man with the green guitar (@Image2) to the man with the silver guitar (@Image1).
@Image1 and @Image2 define only the new people's face, hair, skin, facial hair and body build; do not use their backgrounds, poses or clothes.
Each new person takes over the original person's exact position, scale, pose, movement, expression and timing; nothing of the original person's face remains.
Each new person copies the original person's facial performance exactly: every expression, the direction of the eyes and gaze, and every mouth movement. Neither new person speaks.
@Video1 has short solid magenta frames between some of its parts: keep every magenta frame exactly where it is, with nothing else in it.
Keep the environment exactly as in @Video1: the studio, the couch, the microphones, the guitars, the wall poster, the lighting and colours stay the same.
Both replacements are required: no shot may keep an original replaced person. Do not add cuts or invent new movement or scene elements.
```

## Example — one person who speaks, one person behind him, clothes from the images

```
Only the characters in @Video1 are replaced, by the new characters from the images; the location, lighting and all movements stay exactly as in @Video1.
Recreate the video @Video1 shot for shot — same camera, framing, cuts, timing, motion, expressions and gestures — with two changes:
Person A — the man in the olive jacket, facing the camera — becomes the man from @Image1, wearing a dark gray top.
Person B — the dark-haired man in the dark jacket, seen from behind in the LEFT foreground — becomes the man from @Image2, wearing a black jacket; only his hair and clothes show.
@Image1 and @Image2 define only the new people's face, hair, skin, body build and clothing; do not use their backgrounds or poses.
Each new person takes over the original person's exact position, scale, pose, movement, expression and timing; nothing of the original person's face, hair, body or clothes remains.
Each new person copies the original person's facial performance exactly, frame by frame: every expression, the direction of the eyes and gaze, and every mouth and lip movement, in sync with the original speech. @Video1 carries that speech: the new person's lips follow it word by word.
@Video1 has short solid magenta frames between some of its parts: keep every magenta frame exactly where it is, with nothing else in it.
Keep the environment exactly as in @Video1: the office, the desk, the lighting and colours stay the same.
Both replacements are required: no shot may keep an original replaced person. Do not add cuts or invent new movement or scene elements.
```
