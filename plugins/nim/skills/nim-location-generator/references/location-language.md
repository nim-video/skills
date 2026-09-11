# Brief, composition, and prompt

## What to extract from the user's wishes

Compile a working note without turning it into a mandatory questionnaire:

```text
Output: concept | prompt | image | edit | series
Location and purpose of the shot:
Confirmed facts / visible motifs / creative assumptions:
Format, count, resolution, and budget, if specified:
Direction / story density / lived-in feel:
People / foreground / subject area:
Camera, lighting, time, weather:
References: identifier → role → generation input (or analysis in concept/prompt-only mode)
Preserve / change:
Model: auto or an explicit choice
```

Common location types: living room (`living_room`), kitchen (`kitchen`), bedroom (`bedroom`), bathroom (`bathroom`), street (`street`), cafe (`cafe`), custom (`custom`). These are suggestions, not an exhaustive list. Also support a studio, workshop, office, shop, courtyard, park, natural setting, or fantastical environment if that is what the user requests.

A short, meaningful brief is acceptable; do not impose arbitrary character-count requirements. Treat work, interests, and habits as facts only when stated by the user. A reference may show a bicycle or vinyl records; do not declare that the owner is an athlete, musician, wealthy person, or follower of a religion. Label any unconfirmed backstory as a creative option.

## Translating everyday language into settings

| Request | Setting and result |
|---|---|
| Calm, natural, true to life, unobtrusive | `restrained`: a functional space, a limited palette, and subtle distinctive details |
| Unusual, with a twist, creative | `creative`: one strong spatial design move and one unusual accent; the location remains usable |
| Editorial, magazine style, art direction, set design | `editorial`: sculptural composition and a bold palette; preserve physical plausibility for a photographic scene |
| Few details, concise | `storyDensity=light`: 1–2 small narrative groups |
| Lived-in, with a story | `storyDensity=lived-in`: 2–3 connected groups of objects and signs of use |
| Lots of story, rich detail | `storyDensity=rich`: 3–4 clearly readable groups, without filling the subject area |
| Clean, minimalist | `clutter=minimal`: few individual objects and orderly surfaces |
| Naturally tidy | `clutter=natural`: plausible signs of activity, not a showroom display |
| Layered, creative mess | `clutter=layered`: more overlaps and signs of use around the subject area |
| No foreground, clean edges, nothing in front of the camera | `foregroundEnabled=false` |
| Framing, depth through objects near the camera | `foregroundEnabled=true` |
| No people, empty location | `people=empty` |
| A couple of passersby/visitors in the background | `people=background` for the requested public space |

Story density and clutter are independent: `rich + minimal` means several tidy groups, while `light + layered` means one layered group. "Depth" alone does not enable foreground: perspective, light, and background can create depth. "Architecture only/no props" overrides object groups.

## Layers and the clear area

- **Foreground is off by default.** The readable composition begins in the mid-ground; edges are open, with no nearby blurred objects or occlusions. Explicitly place each story cluster and movable prop in the middle or far distance, behind or beside the staging area, and describe the near floor as open. This includes plants, counter equipment, tabletop props, and hanging lights; an unlocated detail list can otherwise introduce foreground objects. "Cinematic" does not override this rule.
- **Foreground on:** 1–3 partially cropped objects near the edges. One may be softly blurred. The central region and subject area remain open.
- **Mid-ground:** the main focal point and a natural place for a standing or seated subject, approximately 30–45% of the frame width. Do not insert a silhouette, mannequin, frame, marker, or empty white rectangle to mark the area.
- **Background:** readable architecture, plausible depth, and object groups according to density. Each typical group has 3–6 related objects/signs of use; one main accent, with the others subordinate, and at most one unobtrusive Easter egg. For minimalism, reduce the objects; do not pack the frame to meet a quota.

If a background for a person is needed, align the camera height, clear floor space/seat, scale, and expected light direction. For an object background, leave a suitable supporting surface. For a panorama without a character, a close-up, or an isometric view, use an area suited to the purpose instead of mechanically applying 30–45%.

Private interiors are empty by default. In `auto`, public places may contain a few small background figures going about their activities; no one becomes the main subject or looks at the camera. An explicit request for people takes precedence over the default. If the main task is to place a recognizable person or an exact product in the scene, use an appropriate Nim workflow that preserves the subject, with this location as the environment. Its image-generation stages must still obey [model-routing.md](model-routing.md), including the closed model set, all supplied references, and fixed Nano/GPT 2K settings.

## Optics, materials, and light

For a photographic scene, specify the camera position and height, a moderately wide-angle or normal lens, natural perspective, material/construction, a few signs of use, contact shadows, and appropriate reflections. Use one main physically motivated light source: a window, the sun, or a lamp; specify its direction, softness, and the time of day. Additional sources must be consistent with it.

Do not turn the word set `8K, masterpiece, HDR, luxury` into a quality description. "Luxury" is acceptable as a user request and is expressed through materials and design choices. For an illustration, describe the graphic technique, palette, and hierarchy of forms without requiring a photographic camera. For fantasy, preserve the world's internal logic instead of forcing everyday realism.

Unless signage is requested, use unlettered surfaces. For exact text, preserve the capitalization, language, quotation marks, and the sign's placement and material; check the result separately. Do not promise flawless typography.

## Assembling the prompt

Write the finished prompt as ordinary, connected prose. By default, English may be used for generation and the user's language for explanations; an explicit request for another language takes precedence. Do not translate literal sign text. Preserve key constraints and avoid contradictory style tags.

Order: **location and task → preserve/change for edit → composition and area → object groups → materials → camera → light → people/lettering/frame cleanliness**. Length depends on the task; approximately 150–250 English words are enough for a typical location, and a simple edit should be shorter.

For Flux, phrase the desired state positively: `unoccupied room`, `open unobstructed frame edges`, `clear mid-ground staging area`, `plain unlettered surfaces`. Do not create a separate `negative_prompt`: Nim has no such field, and FLUX.2 does not support negative prompts. [BFL guidelines](https://docs.bfl.ai/guides/prompting_guide_flux2).

Example for "a warm living room belonging to a sound designer in Lisbon, UGC background, no foreground," when the user has stated the profession:

> A vertical photographic background plate of a modest Lisbon living room used by a sound designer. An unoccupied, human-scale mid-ground leaves about one third of the frame width clear beside a simple linen sofa, suitable for a standing presenter. The frame edges remain open and unobstructed; the readable composition begins in the mid-ground. At the back, one coherent work area contains compact speakers, headphones and a neatly coiled cable on an oak desk. A secondary group pairs a small stack of records with a turntable and a worn wooden shelf. Warm limewashed walls, aged timber joinery and matte ceramic surfaces show restrained everyday wear. View from chest height with a natural 35 mm lens perspective, straight verticals and readable architectural depth. Soft late-afternoon light enters through the window on camera left, producing gentle contact shadows and believable reflections. The room feels quietly lived-in, with a limited warm palette, plain unlettered surfaces and an open staging area.

When JSON is requested, it may contain: `normalized_brief`, `visible_design_cues`, `creative_hypotheses`, `compiled_prompt`. JSON is optional in ordinary conversation; do not send this entire object in `prompt` instead of the `compiled_prompt` itself.

## Location bible for a series

Record the chosen master frame/reference, the layout of walls and openings, relative positions of large furniture, 2–4 recognizable details, material and palette, scale, base lighting, and the clear area. Separately list the variables for each shot: angle, time, weather, or specific props. If the user asks to save it, add prompts, links, and workflow IDs to a local Markdown/JSON file, excluding temporary upload tokens.

The same seed does not guarantee the same room. For views of one location, use the verified master as an image-reference. Do not claim that the hidden side of a room is known from one photo: a new view is a consistent reconstruction, with accuracy checked against visible reference details.
