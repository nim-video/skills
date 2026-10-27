# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "numpy", "opencv-python-headless", "rembg[cpu]"]
# ///
"""Cut an object out of its background -> trimmed RGBA PNG (original colours kept) + quality report.

usage: uv run cutout.py in.jpg out.png [--mode rembg|key|auto]
  rembg  DEFAULT for objects and photos: ML matting (isnet), keeps white parts, glass and handles,
         drops cast shadows. Model (~170 MB) downloads once per machine and is cached.
  key    no ML. Works best when the asset was generated on a flat CHROMA background that does not
         occur in the object (green #00B140 by default, magenta #FF00FF for green objects): the
         background and its cast shadow are removed by hue, so white or light objects stay whole.
         On white/grey backgrounds it builds a solid silhouette from colour distance + edges and
         fills enclosed holes (laptop palm rests, glass cups), then drops the cast shadow.
  rembg  ML matting for real photos with busy backgrounds: `uv run --with "rembg[cpu]" cutout.py ...`
  auto   key if the corners are uniform, otherwise rembg
Prints `solidity` and `holes`; a WARNING means look at the result and regenerate on chroma.
"""
import argparse, sys
import numpy as np, cv2
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('--mode', default='rembg'); ap.add_argument('--model', default='isnet-general-use')
a = ap.parse_args(); im = Image.open(a.src).convert('RGB'); rgb = np.array(im); arr = rgb.astype(np.float32); H, W = arr.shape[:2]
c = max(8, min(H, W) // 40)
corners = np.concatenate([arr[:c, :c].reshape(-1, 3), arr[:c, -c:].reshape(-1, 3), arr[-c:, :c].reshape(-1, 3), arr[-c:, -c:].reshape(-1, 3)])
uniform = corners.std(0).max() < 14; mode = a.mode if a.mode != 'auto' else ('key' if uniform else 'rembg')

def fill_holes(m):
    ff = m.copy(); mask = np.zeros((H + 2, W + 2), np.uint8); cv2.floodFill(ff, mask, (0, 0), 1)
    return m | (1 - ff)

if mode == 'key':
    bg = np.median(corners, 0); hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    bh = cv2.cvtColor(bg.reshape(1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2HSV)[0, 0].astype(np.float32)
    chroma = bh[1] > 120                                                     # saturated key colour
    if chroma:  # distance in hue (shadows of the key colour keep its hue -> removed too)
        dh = np.abs(hsv[..., 0] - bh[0]); dh = np.minimum(dh, 180 - dh)
        keyness = np.clip(1 - (dh - 8) / 14, 0, 1) * np.clip((hsv[..., 1] - 60) / 60, 0, 1)
        alpha = 1 - keyness; solid = (alpha > .5).astype(np.uint8)
        # despill: pull the key hue out of semi-transparent edge pixels
        spill = keyness[..., None]; arr = arr - spill * (bg - arr.mean(2, keepdims=True)) * .6; rgb = np.clip(arr, 0, 255).astype(np.uint8)
    else:       # white / grey background: colour distance + edges, solid silhouette, holes filled
        d = np.abs(arr - bg).max(2); edges = cv2.Canny(cv2.GaussianBlur(rgb, (3, 3), 0), 20, 60)
        m = ((d > 18) | (cv2.dilate(edges, np.ones((3, 3), np.uint8)) > 0)).astype(np.uint8)
        k = max(5, min(H, W) // 60); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        m = fill_holes(m)
        # cast shadow: darker than bg but almost colourless and soft -> drop pixels that are only "darker bg"
        lum, bl = arr.mean(2), bg.mean(); sat = hsv[..., 1]
        shadowish = (lum < bl - 3) & (lum > bl - 70) & (sat < 25) & (d < 70) & (cv2.Laplacian(lum, cv2.CV_32F, ksize=3).__abs__() < 6)
        m = m & ~(cv2.morphologyEx(shadowish.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)).astype(bool)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)); m = fill_holes(m); solid = m
        alpha = cv2.GaussianBlur(cv2.erode(solid * 255, np.ones((3, 3), np.uint8)).astype(np.float32) / 255, (3, 3), 0)
    n, lab, st, _ = cv2.connectedComponentsWithStats(solid, 8); keep = np.zeros_like(solid)
    big = st[1:, cv2.CC_STAT_AREA].max() if n > 1 else 0
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] > big * 0.02: keep[lab == i] = 1
    alpha = alpha * cv2.dilate(keep, np.ones((5, 5), np.uint8))
    out = Image.fromarray(np.dstack([rgb, (np.clip(alpha, 0, 1) * 255).astype(np.uint8)]), 'RGBA')
else:
    try:
        from rembg import remove, new_session
    except ImportError:
        sys.exit('rembg not installed: run with  uv run --with "rembg[cpu]" cutout.py ...  or regenerate the asset on chroma and use --mode key')
    out = remove(im, session=new_session(a.model), alpha_matting=True, alpha_matting_foreground_threshold=240,
                 alpha_matting_background_threshold=15, alpha_matting_erode_size=6)
bb = out.getchannel('A').point(lambda v: 255 if v > 30 else 0).getbbox(); out = out.crop(bb); out.save(a.dst)
# quality report
m = (np.array(out.getchannel('A')) > 128).astype(np.uint8); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
hull = cv2.contourArea(cv2.convexHull(np.vstack(cs))) if cs else 1; solidity = m.sum() / max(hull, 1)
hh, ww = m.shape; mask = np.zeros((hh + 2, ww + 2), np.uint8); ff = m.copy(); cv2.floodFill(ff, mask, (0, 0), 1); holes = int((1 - ff).sum())
warn = holes > m.sum() * 0.01
print(a.dst, out.size, 'mode', mode, f'solidity {solidity:.2f} holes {holes}px', 'WARNING: check holes / ragged edge, regenerate on chroma' if warn else 'ok')
