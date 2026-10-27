# Example: GrowUSA ad 2 "transit" (9:16, 6 s VO + packshot)

Format reference only (images, VO and cutouts are not bundled, so it does not render as is):
- `timeline.json`: palette, desk, captions off with a reason, `scenes` list (two designed scenes + the shared packshot fragment with `at`).
- `scenes/s1/scene_01.json`, `scenes/s2/scene_02.json`: fragments written by layerize.py and finished by hand: plate, items placed from the design frame, hero, title strip with two colours, fact label, source strip, actions (train `roll` on "BART", plan unrolling, brush arrow on "fight").
- `scenes/s1/hints.json`: placement hints for small items SIFT could not match.
- `packshot.json`: the campaign end card rebuilt in code (rect, poly, text, photo cutout), reused by all ads of the series.

