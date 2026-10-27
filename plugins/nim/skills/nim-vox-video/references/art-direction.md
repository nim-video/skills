# Art direction (once per video or series)

Write `art.md` before any design frame: medium, palette, type, frame rules. Every design-frame prompt pastes the
STYLE BLOCK and CLOSER verbatim; the engine palette uses the same colours, so model pixels and code pixels match.

## Medium (default M12)

**M12 Dense Archival Editorial Collage, STYLE BLOCK:**
> Detailed documentary editorial collage, realistic full-color photographic cutouts with preserved natural
> colors, colored antique engraved objects, neutral warm-white folded newsprint and graph paper, saturated yellow
> paper accents, restrained green pencil annotations, ink-black details, natural off-white cut-paper rims, visible
> scissors and torn-fiber edges, varied print scales, tangible shallow layering and soft paper shadows. No
> monochrome or sepia treatment.

**CLOSER (M12):**
> Deliver detail at three scales: bold silhouette, readable narrative objects, and fine paper-and-print texture.
> Keep the background quieter than the hero. No flat vector simplification, random stickers, repeated decorative
> icons, muddy contrast, excessive grunge, glossy CGI, watermarks, or unintended readable text. No red accents,
> radial rays, sunburst backgrounds, or colored dotted silhouettes behind people.

Other media (swap the STYLE BLOCK, keep the layer structure): M1 Paper Cut (flat cardstock diorama, depth
shadows), M2 3D Paper Cut, M4 Mixed Media (photo cutouts, torn paper, tape, marker doodles), M7 Ink and Wash,
M10 Watercolor Storybook, M11 Retro Print (risograph, 2-3 spot colours). Pixel art, claymation, plush and flat
vector need their own CLOSER (drop the "no flat vector" clause).

**Colour default:** full colour. Photos keep their colours; no grayscale, sepia or duotone unless asked.
Archival photos that are black and white stay as they are (do not colourise).

## Palette (engine `palette` and prompt words)

| role | default | engine key | in prompts |
|---|---|---|---|
| paper | `#f3eee2` warm white | `paper` | neutral warm-white newsprint, graph paper |
| ink | `#16161a` | `ink` | ink-black details |
| accent | `#23824F` forest green | `accent` | restrained green pencil annotations |
| paper accent | `#F2C230` saturated yellow | `accent2` | saturated yellow paper accents |
| plate | brand dark (e.g. navy `#26245e`) | `navy` or any name | dark blue paper label |

Client brand colours override (packshot, plates), photo colours stay natural. No red accents unless the brand
requires red.

## Type (all drawn by code)

| element | font | look |
|---|---|---|
| scene title | Anton 110-150 px (9:16) | 2 colours: ink + accent, on a yellow torn strip |
| name plate | Special Elite 34-40 px | ink on cream strip, under the title |
| source strip | Inter 22-26 px | grey on white label, bottom corner, "Source: Outlet, date" |
| headline / quote | Playfair Display (typeset.py) | real wording only |
| masthead | UnifrakturMaguntia | newspaper nameplate feel, not a logo copy |
| packshot | Montserrat Black / ExtraBold, Noto Sans SC for CJK | as the client's end card |
| disclaimer | Inter 20 px per 1080 width | regular, no bar, bottom safe area |

## Frame rules (what the design frame must have)

1. Filled edge to edge; objects cropped by the frame edges are good, empty paper areas bigger than a palm are not.
2. 6-10 objects of different scale in 2-3 layers: background papers (plate), middle (1-2 large objects: a
   building, a map, a stack), foreground (3-6 hand-size props). One hero and one title read first.
3. Hero: a person (grey silhouette placeholder, real photo later) or one big object; 45-75% of the frame width.
4. Title space: one blank saturated-yellow torn strip (and an optional small cream label) where the title will be
   typeset; it may lie over the hero's chest. 9:16: lower third; 16:9: left or right third.
5. Every object is a noun of the scene's phrase or its setting (v2 recipes below); no generic desk filler
   repeated across scenes.

## Layout recipes (pick per scene by content; render in the chosen medium)

1 Cutout Collage (person + props) · 2 Archival Color Poster · 3 Mixed-Media Data Collage (money, charts) ·
4 Annotated Data Viz (one line chart + circle) · 5 Archival Timeline (dates) · 6/7 Evidence wall (connections;
never for real people in ads) · 8 Document Forensics (laws, letters: one passage highlighted) · 9 Paper-Craft
Desk Flat-Lay · 10 Hand-Drawn Route Map (journeys, transit) · 11 Map Graphic (places) · 12 Flat Illustration
(abstract) · 13 Color Halftone Portrait (introducing a person) · 14 Kinetic Typography (one-word stress) ·
15 Vintage Newsprint Chaos (era) · 16 Grid and Scale Repetition (magnitude) · 17 Screen-in-Screen (internet) ·
18 Exploded View (how things work). Pairings: data 3/4, documents 8, history 5/15, titles 14, people 13/1,
places 11/10, scale 16.
