# Design frame → layers (per scene)

Cost per scene: ~24 credits (production GPT Image 2.5 Flare Medium: frame 6 + sheet 9 + plate 9; an edit is
5 cr + 1 per reference megapixel, a 2K frame is ~4 MP) . Wall time: ~1 min of generation (calls run in parallel) + ~1-2 min local work.

Find every model with `models_explore` and follow its live `generationContract`; call it with `generate_image`.

## 1. Design frame

`generate_image` with `model_id` of **GPT Image 2.5 Flare Medium** text-to-image (`models_explore` search "gpt
image 2.5 flare", pick the Medium text-to-image model, then `get` for its contract),
`requestedAspectRatio` = the video's (9:16, 16:9, 4:5, 1:1), `resolution: 2K` (9:16 comes back 1440x2560), 6 cr.
Download with `nim_fetch.py <promptId>=design.png` (no status polling in the chat). Keep the result's mediaUrl:
both edits use it as their reference. Medium looks as good as the High tier (22 cr). Alternative: Nano Banana Pro
(25 cr, softer cut-paper rims).

Prompt template (fill the brackets, keep the order):
```
A vertical 9:16 dense editorial paper-collage design frame seen straight from above, filling the whole frame
edge to edge. HERO PLACEHOLDER: a large plain flat mid-grey paper silhouette of [a man's / a woman's] head and
shoulders [in a suit jacket], no face, no features, solid grey, placed [lower-center], about [60]% of the frame
width, its bottom edge bleeding off the bottom of the frame.            <- or HERO: [the big object of the scene]
BACKGROUND LAYER: [warm-white folded newsprint desk with pale graph-paper sheets and a cropped (map / blueprint /
document) sheet], low contrast, large torn paper pieces overlapping the frame edges.
MIDDLE LAYER, [upper half]: a large full-color photographic cutout of [the big setting object], spanning most of
the frame width; [1-2 more large objects].
FOREGROUND LAYER: [3-6 props of this phrase, each with its position: at right, lower right ...], all large and
partly cropped by the frame edge.
TITLE SPACE: one wide blank saturated-yellow torn paper strip lying across the [lower third over the silhouette's
chest], completely empty, plus one smaller blank cream paper label below it, empty.
Objects are big, overlapping in 2-3 layers, cropped by the frame edges, no empty areas, no tiny stickers.
[One restrained green pencil curve.] No readable text anywhere, no letters, no numbers, no logos.
[STYLE BLOCK] [CLOSER]
```
Scene without a person: HERO is the scene's main object (a rocket, a newspaper stack, a train). A scene whose
hero is a code-made card (quote card, clippings, counter): ask for "a blank cream paper card [size, place]" as the
hero placeholder; typeset.py makes the real card and it goes where the blank card is.

## 2. Sheet of objects (chroma) and plate

Both are `generate_image` with **GPT Image 2.5 Flare Medium edit** (from `models_explore`),
`fileInputs: [design mediaUrl]`, ~9 cr each with a 2K reference (5 + 1 per reference megapixel).

Sheet, `requestedAspectRatio: "1:1"`:
```
Using this collage as the reference, lay out each of its story objects separately on one seamless flat pure
magenta chroma-key background (#FF00FF), in a loose 3x3 grid with wide empty gaps between items. Each object
complete and uncropped (restore any part hidden or cut by the frame), with exactly the same design, colours,
materials, lighting and top-down viewing angle as in the collage, flat even light, no cast shadows, no
reflections of the background, no paper rims, no outlines. Objects: 1 [..], 2 [..], ... Do not include the grey
silhouette, the yellow or cream paper strips, or the background papers. No text, no letters, no numbers.
```
Plate, `requestedAspectRatio` = the video's:
```
Edit this collage: remove every story object, the grey silhouette and the yellow and cream paper strips. Keep
only the background layer exactly as it is: the [desk, graph-paper and map sheets, torn paper pieces], in the
same positions. Fill the areas where objects were with the continuation of the same background papers.
No objects, no people, no text.
```
Why magenta: the edit has no transparent-background option. Magenta + `pack_split --mode key` keeps every
object whole (white cups, papers, clear glass lenses) for free; a grey sheet split by colour (`--mode white`) eats
every white part. If an object is magenta itself, ask for a green (#00B140) sheet and use `--mode key` too.

## 3. Split, name, place

```
uv run scripts/pack_split.py sheet.jpg items --mode key
```
Open `items/_sheet.jpg`, rename files to nouns (`lamp.png`, `cup.png`). Then:
```
uv run scripts/layerize.py design.png items lay.json --size 1080x1920 --plate plate.png \
   --hero ../../people/wiener_cut.png --scene scene_03.draft.json --id s03 --t0 @hard --t1 @Chronicle [--hints hints.json]
```
- SIFT places textured, big objects (building, lamp, stack). Items printed `UNMATCHED` or with `agree` < 0.35:
  look at the design frame and write `hints.json` `{"cup": [x, y, width, rot]}` (video px; width of the object as
  drawn). Hints override SIFT. One round is usually enough.
- Open `lay_check.jpg` (design | rebuilt | difference). Rebuilt should read like the design; small shifts are OK.
- `hero_slot` fits the person by head width and head top; if the photo ends at the chest and the slot bleeds off
  the bottom, the photo is scaled up so the body bleeds too. Low-res photos upscale soft: pick the biggest photo.
- `title_slots`: centre, size and angle of each blank yellow strip: put the title strip there, size the font so
  the text fills ~85% of the slot width.
- The draft has the plate, every item with a default entrance (back to front, landing with the plate), the hero
  and the title placeholder. Finish it with `scene_build.py row.json` (title, name plate, actions, extra layers;
  format in `worker.md`), then check the scene.

## 4. Gate

`uv run scripts/vox_engine.py timeline.json --gate` (the timeline lists the scene) writes
`timeline_gate/sNN_design_vs_final.jpg` and prints fill / empty / objects / match. Fail = rework the scene:
missing objects, wrong scale, empty area the design did not have, hero too small.
