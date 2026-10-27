# Cutouts

- Objects of a design frame: no ML cutout. The sheet is generated on a magenta chroma background and split by
  colour (`pack_split.py --mode key`, free).
- Real people and real products from photos: `cutout.py` (local rembg isnet, free; the model, ~170 MB, downloads
  once). Look at every cutout on a coloured background before use: holes and see-through areas show there.
- Engravings, ink drawings, line art on white: no ML: `pack_split.py --mode engraving` / `--mode ink`.
- White matte paper items (napkins, receipts) and thin wire frames cut well with rembg; clear glass may keep a grey
  box of background: put it on the sheet instead and split it with `--mode key`.
- The engine's paper rim covers 10-12 px of edge, so small hair differences vanish; holes do not.
- Pick the biggest photo of a person: low-res photos upscale soft in the hero slot.
