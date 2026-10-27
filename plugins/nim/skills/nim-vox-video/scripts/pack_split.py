# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "numpy", "opencv-python-headless"]
# ///
"""Split a generated sheet into separate transparent PNG elements + a labelled index sheet.

usage: uv run pack_split.py sheet.png OUT_DIR --mode alpha|white|ink|engraving|green [--prefix item] [--names a,b,c]
  alpha      sheet that already has transparency (GPT Image Edit with background=transparent, or a
             BiRefNet cut of a whole sheet): items = connected alpha blobs, colours untouched
  white      photo objects on a flat light background
  ink        black ink on white -> pure-black RGBA, alpha = ink density (recolourable by the engine)
  engraving  ink drawing on white -> keeps white interior inside the silhouette (ready for paper rim)
  key        objects on a flat chroma background of any hue (magenta #FF00FF recommended: it is in almost no
             object): background hue read from the sheet border, removed by hue distance, edge spill pulled out
  green      objects on chroma-green background
Cleanup (v8): blobs smaller than --min-frac of the biggest item are dropped as crumbs; pieces that
nearly touch are joined (--join px); near-duplicates (same size and look) are dropped; items cut by
the sheet border are skipped. Writes OUT_DIR/<prefix>_index.json and OUT_DIR/_sheet.jpg.
--names "lamp,docs,cup" renames the items in reading order (left to right, top to bottom rows).
No ML needed."""
import argparse, json, os
import numpy as np, cv2
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(); ap.add_argument('sheet'); ap.add_argument('out'); ap.add_argument('--mode', default='alpha')
ap.add_argument('--prefix', default='item'); ap.add_argument('--min', type=int, default=1500); ap.add_argument('--join', type=int, default=0)
ap.add_argument('--min-frac', type=float, default=0.04); ap.add_argument('--names', default='')
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
src = Image.open(a.sheet); rgba = np.array(src.convert('RGBA')); im = rgba[..., :3].astype(np.float32); H, W = im.shape[:2]
join = a.join or max(9, min(H, W) // 90)
lum = im.mean(2); alpha_src = rgba[..., 3]
if a.mode == 'alpha':
    if alpha_src.min() > 250: raise SystemExit('sheet has no transparency: use --mode white (or cut the sheet with BiRefNet first)')
    mask = (alpha_src > 40).astype(np.uint8)
elif a.mode in ('ink', 'engraving'):
    ink = np.clip((235 - lum) / 180, 0, 1); mask = (ink > 0.15).astype(np.uint8)
elif a.mode == 'key':
    edge = np.concatenate([im[:12].reshape(-1, 3), im[-12:].reshape(-1, 3), im[:, :12].reshape(-1, 3), im[:, -12:].reshape(-1, 3)])
    bgc = np.median(edge, 0).astype(np.uint8); hsv = cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    bh = cv2.cvtColor(bgc.reshape(1, 1, 3), cv2.COLOR_RGB2HSV)[0, 0].astype(np.float32)
    dh = np.abs(hsv[..., 0] - bh[0]); dh = np.minimum(dh, 180 - dh)
    gkey = np.clip(1 - (dh - 10) / 12, 0, 1) * np.clip((hsv[..., 1] - 70) / 60, 0, 1) * np.clip((hsv[..., 2] - 60) / 60, 0, 1)
    mask = (gkey < .5).astype(np.uint8)
    spill = gkey[..., None]; im = np.clip(im - spill * (bgc.astype(np.float32) - im.mean(2, keepdims=True)) * .7, 0, 255); rgba[..., :3] = im.astype(np.uint8)
elif a.mode == 'white':
    edge = np.concatenate([im[:12].reshape(-1, 3), im[-12:].reshape(-1, 3), im[:, :12].reshape(-1, 3), im[:, -12:].reshape(-1, 3)])
    dist = np.abs(im - np.median(edge, 0)).max(2); mask = (dist > 30).astype(np.uint8)
else:
    r, g, b = im[..., 0], im[..., 1], im[..., 2]; gkey = np.clip(((g - np.maximum(r, b)) - 15) / 40, 0, 1); mask = (gkey < .5).astype(np.uint8)
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (join * 2 + 1, join * 2 + 1))
groups = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
n, lab, stats, _ = cv2.connectedComponentsWithStats(groups, 8)
cand = []
for i in range(1, n):
    x, y, w, h, area = stats[i]; real = int((mask[y:y + h, x:x + w] * (lab[y:y + h, x:x + w] == i)).sum())
    if real < a.min or w < 30 or h < 30: continue
    if x <= 2 or y <= 2 or x + w >= W - 2 or y + h >= H - 2: continue        # touches the border: probably cut
    cand.append((i, x, y, w, h, real))
biggest = max([c[5] for c in cand] or [1]); kept = []
for c in cand:
    i, x, y, w, h, real = c
    if real < biggest * a.min_frac: continue                                   # crumbs, sparks, stray fragments
    if max(w, h) / max(1, min(w, h)) > 12 and real < biggest * .15: continue   # thin slivers
    kept.append(c)
items, thumbs = [], []
for i, x, y, w, h, real in sorted(kept, key=lambda c: (c[2] // max(1, H // 6), c[1])):
    sel = (lab[y:y + h, x:x + w] == i); crop = rgba[y:y + h, x:x + w].copy()
    if a.mode == 'alpha':
        al = (alpha_src[y:y + h, x:x + w] * sel).astype(np.uint8); rgb = crop[..., :3]
    elif a.mode == 'ink':
        al = (ink[y:y + h, x:x + w] * sel * 255).astype(np.uint8); rgb = np.zeros((h, w, 3), np.uint8)
    elif a.mode == 'engraving':
        sil = (mask[y:y + h, x:x + w] * sel).astype(np.uint8)
        sil = cv2.morphologyEx(sil, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        cs, _ = cv2.findContours(sil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); sil = np.zeros_like(sil); cv2.drawContours(sil, cs, -1, 1, -1)
        al = cv2.GaussianBlur(sil * 255, (3, 3), 0); rgb = crop[..., :3]
    else:  # keep holes (wire loops), soft alpha from colour distance, eat the pale halo
        dd = dist[y:y + h, x:x + w] if a.mode == 'white' else (1 - gkey[y:y + h, x:x + w]) * 255
        if a.mode == 'key': dd = dd * 1.6
        soft = np.clip((dd - 30) / 45, 0, 1) * sel
        al = (cv2.GaussianBlur(soft.astype(np.float32), (3, 3), 0) * 255).astype(np.uint8); rgb = crop[..., :3]
    # near-duplicate check: same size (+-8%) and similar 16x16 look
    th = cv2.resize(np.dstack([rgb, al]).astype(np.float32), (16, 16), interpolation=cv2.INTER_AREA)
    if any(abs(w - it['size'][0]) < .08 * w and abs(h - it['size'][1]) < .08 * h and np.abs(th - t2).mean() < 12 for it, t2 in zip(items, thumbs)):
        continue
    ys, xs = np.nonzero(al > 20)
    if len(xs) == 0: continue
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    out = np.dstack([rgb, al])[y0:y1, x0:x1]
    items.append({'file': None, 'size': [int(x1 - x0), int(y1 - y0)], 'src_bbox': [int(x + x0), int(y + y0), int(x1 - x0), int(y1 - y0)]}); thumbs.append(th)
    items[-1]['_px'] = out
names = [s.strip() for s in a.names.split(',') if s.strip()]
for j, it in enumerate(items):
    it['file'] = f'{names[j] if j < len(names) else a.prefix + "_%02d" % j}.png'
    Image.fromarray(it.pop('_px'), 'RGBA').save(os.path.join(a.out, it['file']))
json.dump({'mode': a.mode, 'sheet': os.path.abspath(a.sheet), 'items': items}, open(os.path.join(a.out, f'{a.prefix}_index.json'), 'w'), indent=1)
cols = 6; cell = 260; rows = (len(items) + cols - 1) // cols; sheet = Image.new('RGB', (cols * cell, max(1, rows) * cell), (64, 160, 100)); d = ImageDraw.Draw(sheet)
for j, it in enumerate(items):
    e = Image.open(os.path.join(a.out, it['file'])); e.thumbnail((cell - 20, cell - 40))
    sheet.paste(e, ((j % cols) * cell + 10, (j // cols) * cell + 10), e); d.text(((j % cols) * cell + 8, (j // cols) * cell + cell - 22), it['file'], fill=(255, 255, 255))
sheet.save(os.path.join(a.out, '_sheet.jpg'), quality=85)
print(len(items), 'items ->', a.out, f'(dropped {len(cand) - len(kept)} crumbs/slivers)' if len(cand) > len(kept) else '')
if len(names) and len(names) != len(items): print(f'WARNING: {len(names)} names for {len(items)} items: check _sheet.jpg and rename')
