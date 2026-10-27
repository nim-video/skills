# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "numpy", "opencv-python-headless"]
# ///
"""Design frame -> layers. Finds where every cut-out item sits on the design frame and writes engine layers
that rebuild the frame: position, size, rotation and draw order (z) of each item, plus the hero slot (the grey
placeholder silhouette) and title slots (blank yellow paper strips).

usage: uv run layerize.py design.png ITEMS_DIR OUT.json [--size 1080x1920] [--plate plate.png] [--prefix scenes/s03/]
  ITEMS_DIR  transparent PNGs of the frame's objects (pack_split --mode alpha output of the GPT Edit sheet)
  OUT.json   {"size", "design", "plate", "items": [...], "layers": [...], "hero_slot", "title_slots", "unmatched"}
             "layers" are ready for timeline.json (type image, src, x, y, size, rot, z); add "in"/"keys" yourself.
Also writes OUT_check.jpg: design | rebuilt (plate + items + slots) | difference, to look at before animating.
Method: SIFT keypoints of each item (inside its alpha) matched to the design frame, similarity transform by
RANSAC (scale, rotation, shift). Small or redrawn items (few keypoints) are reported UNMATCHED: look at the design frame and
pass --hints {"cup": [x, y, width, rot]} (video px, width of the item as drawn): hints override SIFT. Draw order: where two placed items
overlap, the one whose pixels agree with the design frame there is on top."""
import argparse, glob, json, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(); ap.add_argument('design'); ap.add_argument('items'); ap.add_argument('out')
ap.add_argument('--size', default=''); ap.add_argument('--plate', default=''); ap.add_argument('--prefix', default='')
ap.add_argument('--hints', default='', help='json {item_name: [x, y, width, rot]} in video px for items to search near')
ap.add_argument('--z0', type=int, default=20); ap.add_argument('--min-inliers', type=int, default=10)
ap.add_argument('--scene', default='', help='also write a draft scene fragment here (scene_NN.json) with a default assembly')
ap.add_argument('--id', default='s01'); ap.add_argument('--t0', default='0'); ap.add_argument('--t1', default='4')
ap.add_argument('--hero', default='', help='person cutout PNG to place in the hero slot (real photo, never generated)')
a = ap.parse_args()
D = cv2.cvtColor(np.array(Image.open(a.design).convert('RGB')), cv2.COLOR_RGB2BGR); DH, DW = D.shape[:2]
VW, VH = (int(v) for v in a.size.split('x')) if a.size else (DW, DH); k = VW / DW   # design px -> video px
if abs(VH / DH - k) > .02: print(f'WARNING: design aspect {DW}x{DH} differs from video {VW}x{VH}: x scale used')
sift = cv2.SIFT_create(nfeatures=12000); gD = cv2.cvtColor(D, cv2.COLOR_BGR2GRAY)
kD, dD = sift.detectAndCompute(gD, None); bf = cv2.BFMatcher(cv2.NORM_L2)
name_of = lambda f: os.path.splitext(os.path.basename(f))[0]
hints = json.load(open(a.hints, encoding='utf-8')) if a.hints else {}
files = sorted(glob.glob(os.path.join(a.items, '*.png'))) if os.path.isdir(a.items) else a.items.split(',')

def place(path):
    I = np.array(Image.open(path).convert('RGBA')); rgb = cv2.cvtColor(I[..., :3], cv2.COLOR_RGB2BGR); al = I[..., 3]
    m = cv2.erode((al > 128).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
    kI, dI = sift.detectAndCompute(cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY), m)
    res = {'file': path, 'w': I.shape[1], 'h': I.shape[0], 'method': None}
    if dI is not None and len(kI) >= 6:
        good = [p[0] for p in bf.knnMatch(dI, dD, k=2) if len(p) == 2 and p[0].distance < .78 * p[1].distance]
        if len(good) >= 6:
            src = np.float32([kI[g.queryIdx].pt for g in good]); dst = np.float32([kD[g.trainIdx].pt for g in good])
            M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=6, maxIters=5000, confidence=.995)
            if M is not None and inl.sum() >= a.min_inliers and .1 < math.hypot(M[0, 0], M[1, 0]) < 5:
                res.update(M=M, inliers=int(inl.sum()), method='sift')
    hint = hints.get(name_of(path))
    if hint:   # the agent's placement [x, y, width, rot] in video px wins over SIFT: build the transform from it
        sc = hint[2] / k / I.shape[1]; th = math.radians(hint[3] if len(hint) > 3 else 0); c, sn = sc * math.cos(th), sc * math.sin(th)
        M = np.float32([[c, -sn, 0], [sn, c, 0]]); M[:, 2] = [hint[0] / k, hint[1] / k] - M[:, :2] @ np.array([I.shape[1] / 2, I.shape[0] / 2])
        res.update(M=M, inliers=0, method='hint')
    return res, I

placed, imgs = [], {}
for f in files:
    r, I = place(f); imgs[f] = I
    if r['method'] is None: print('UNMATCHED', os.path.basename(f)); continue
    M = r['M']; s = math.hypot(M[0, 0], M[1, 0]); rot = math.degrees(math.atan2(M[1, 0], M[0, 0]))
    cx, cy = M @ np.array([r['w'] / 2, r['h'] / 2, 1])
    r.update(scale=s, rot=rot, cx=cx, cy=cy); placed.append(r)

# warp every item into design space once (for z order, slots and the check image)
warped = {}
for r in placed:
    I = imgs[r['file']]; W = cv2.warpAffine(I, r['M'], (DW, DH), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)); warped[r['file']] = W
    al = W[..., 3] > 128; vis = al.sum()
    if vis:
        err = np.abs(W[..., :3].astype(np.int16) - cv2.cvtColor(D, cv2.COLOR_BGR2RGB).astype(np.int16)).mean(2)[al]
        r['agree'] = round(float((err < 40).mean()), 2)
# draw order from pairwise overlaps
Drgb = cv2.cvtColor(D, cv2.COLOR_BGR2RGB).astype(np.int16); wins = {r['file']: 0 for r in placed}
for i in range(len(placed)):
    for j in range(i + 1, len(placed)):
        A, B = warped[placed[i]['file']], warped[placed[j]['file']]; ov = (A[..., 3] > 128) & (B[..., 3] > 128)
        if ov.sum() < 400: continue
        ea = np.abs(A[..., :3].astype(np.int16) - Drgb).mean(2)[ov].mean(); eb = np.abs(B[..., :3].astype(np.int16) - Drgb).mean(2)[ov].mean()
        wins[placed[i]['file'] if ea < eb else placed[j]['file']] += 1
        wins[placed[j]['file'] if ea < eb else placed[i]['file']] -= 1
order = sorted(placed, key=lambda r: (wins[r['file']], -r['scale'] * r['w'] * r['h']))
for z, r in enumerate(order): r['z'] = a.z0 + z

# hero slot: large flat low-saturation mid-grey area (the placeholder silhouette)
hsv = cv2.cvtColor(D, cv2.COLOR_BGR2HSV); grey = ((hsv[..., 1] < 22) & (hsv[..., 2] > 85) & (hsv[..., 2] < 175)).astype(np.uint8)
flat = cv2.Laplacian(cv2.GaussianBlur(gD, (0, 0), 3), cv2.CV_32F, ksize=3).__abs__() < 10; grey = (grey & flat).astype(np.uint8)
grey = cv2.morphologyEx(grey, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8)); grey = cv2.morphologyEx(grey, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
def head_metrics(m):
    """top row, head centre x and head width of a person mask (rows wider than 4% of the mask width count)"""
    rows = m.sum(1); W0 = m.shape[1]; top = int(np.argmax(rows > W0 * .04)); bot = int(np.nonzero(rows)[0].max())
    hh = max(4, int((bot - top) * .12)); band = m[top + hh // 2: top + hh * 2]
    xs = np.nonzero(band)[1]; wid = np.median((band > 0).sum(1)) if len(xs) else 0
    return top, float(xs.mean()) if len(xs) else W0 / 2, float(wid)
n, lab, st, _ = cv2.connectedComponentsWithStats(grey, 8); hero = None
if n > 1:
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    if st[i, cv2.CC_STAT_AREA] > DW * DH * .04:
        sil = cv2.morphologyEx((lab == i).astype(np.uint8), cv2.MORPH_OPEN, np.ones((21, 21), np.uint8))   # drop thin spurs
        x, y, w, h = cv2.boundingRect(sil); top, hcx, hw = head_metrics(sil)
        hero = {'bbox': [round(x * k), round(y * k), round(w * k), round(h * k)], 'head_top': [round(hcx * k), round(top * k)], 'head_w': round(hw * k),
                'area': round(float(sil.sum()) / (DW * DH), 3)}
        if a.hero:   # fit the real cutout: same head width, same head top, same head centre
            P = np.array(Image.open(a.hero).convert('RGBA'))[..., 3] > 128; ptop, pcx, pw = head_metrics(P.astype(np.uint8))
            sc = hero['head_w'] / max(1, pw)
            if (y + h) * k >= VH - 4 and hero['head_top'][1] + (P.shape[0] - ptop) * sc < VH + 10:   # slot bleeds off the bottom: so must the photo
                sc = (VH + 10 - hero['head_top'][1]) / max(1, P.shape[0] - ptop); hero['note'] = 'photo scaled up so the body bleeds off the bottom like the slot'
            size = P.shape[1] * sc
            hero['place'] = {'size': round(size), 'x': round(hero['head_top'][0] + (P.shape[1] / 2 - pcx) * sc), 'y': round(hero['head_top'][1] + (P.shape[0] / 2 - ptop) * sc)}
            if size > P.shape[1] * 1.6: hero['warning'] = f'person photo upscaled x{size / P.shape[1]:.1f}: use a bigger photo if there is one'
# title slots: blank saturated yellow paper strips
yel = ((hsv[..., 0] > 15) & (hsv[..., 0] < 34) & (hsv[..., 1] > 110) & (hsv[..., 2] > 150)).astype(np.uint8)
yel = cv2.morphologyEx(yel, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)); n, lab, st, _ = cv2.connectedComponentsWithStats(yel, 8); slots = []
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] < DW * DH * .012: continue
    cs, _ = cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); (cx, cy), (w, h), ang = cv2.minAreaRect(cs[0])
    if w < h: w, h, ang = h, w, ang + 90
    if ang > 45: ang -= 90
    if ang < -45: ang += 90
    slots.append({'center': [round(cx * k), round(cy * k)], 'w': round(w * k), 'h': round(h * k), 'rot': round(ang, 1)})
slots.sort(key=lambda s: -s['w'] * s['h'])

layers = []
for r in placed:
    name = os.path.splitext(os.path.basename(r['file']))[0]
    L = {'id': name, 'type': 'image', 'src': a.prefix + os.path.basename(r['file']), 'x': round(r['cx'] * k), 'y': round(r['cy'] * k),
         'size': round(r['w'] * r['scale'] * k), 'rot': round(r['rot'], 1), 'z': r['z']}
    if r.get('agree', 1) < .35: L['_check'] = 'weak match: verify in the check image or pass --hints'
    layers.append(L)
layers.sort(key=lambda L: L['z'])
out = {'size': [VW, VH], 'design': os.path.abspath(a.design), 'plate': os.path.abspath(a.plate) if a.plate else None,
       'items': [{'file': os.path.basename(r['file']), 'method': r['method'], 'inliers': r.get('inliers'), 'agree': r.get('agree'), 'z': r['z']} for r in placed],
       'unmatched': [os.path.basename(f) for f in files if f not in [r['file'] for r in placed]],
       'layers': layers, 'hero_slot': hero, 'title_slots': slots}
json.dump(out, open(a.out, 'w', encoding='utf-8'), indent=1)

# check image: design | rebuilt | difference
base = np.array(Image.open(a.plate).convert('RGB').resize((DW, DH))) if a.plate else np.full((DH, DW, 3), 236, np.uint8)
reb = Image.fromarray(base).convert('RGBA')
for r in sorted(placed, key=lambda r: r['z']): reb.alpha_composite(Image.fromarray(warped[r['file']], 'RGBA'))
dr = ImageDraw.Draw(reb)
if hero: x, y, w, h = [v / k for v in hero['bbox']]; dr.rectangle((x, y, x + w, y + h), outline=(255, 0, 255, 255), width=6)
for s in slots:
    cx, cy = s['center'][0] / k, s['center'][1] / k; dr.rectangle((cx - s['w'] / k / 2, cy - s['h'] / k / 2, cx + s['w'] / k / 2, cy + s['h'] / k / 2), outline=(0, 120, 255, 255), width=6)
reb = np.array(reb.convert('RGB')); diff = (np.abs(reb.astype(np.int16) - Drgb).mean(2) > 45).astype(np.uint8) * 255
sh = 960 / DH; tile = lambda x: cv2.resize(x, (int(DW * sh), 960))
strip = np.hstack([tile(Drgb.astype(np.uint8)), tile(reb), tile(cv2.cvtColor(diff, cv2.COLOR_GRAY2RGB))])
Image.fromarray(strip).save(os.path.splitext(a.out)[0] + '_check.jpg', quality=85)
if a.scene:   # draft fragment: plate, items assembled back to front, hero in its slot, title slot(s) as strips
    sdir = os.path.dirname(os.path.abspath(a.scene)); rel = lambda f: os.path.relpath(os.path.abspath(f), sdir).replace(os.sep, '/')
    tm = lambda v: float(v) if str(v).replace('.', '', 1).lstrip('-').isdigit() else v
    F = {'id': a.id, 't0': tm(a.t0), 't1': tm(a.t1), 'design': rel(a.design), 'layers': []}
    if a.plate: F['plate'] = rel(a.plate); F['layers'].append({'id': 'plate', 'type': 'plate', 'src': rel(a.plate), 'z': 0, 'in': {'t': f'{a.t0}-0.45' if isinstance(tm(a.t0), str) else max(0, tm(a.t0) - .45), 'fx': 'slide', 'from': 'bottom', 'dist': VH, 'spin': 0, 'arc': 0, 'dur': .4, 'sfx': 'slide'}})
    order = sorted(layers, key=lambda L: L['z']); n_it = len(order)
    for i, L in enumerate(order):
        x, y, wdt = L['x'], L['y'], L['size']; edge = min((x, 'left'), (VW - x, 'right'), (y, 'top'), (VH - y, 'bottom'))
        fx = 'drop' if wdt > VW * .45 else ('slide' if edge[0] < VW * .28 else 'pop')
        L2 = {k2: v for k2, v in L.items() if not k2.startswith('_')}; L2['src'] = rel(os.path.join(a.items, os.path.basename(L['src'])))
        off = round(-.5 + i * .12, 2)   # v8.1: the plate lands at t0-0.05 and the first objects land with it (no empty plate)
        t0s = (f'{a.t0}+{off}' if off >= 0 else f'{a.t0}{off}') if isinstance(tm(a.t0), str) else max(0, round(tm(a.t0) + off, 2))
        L2['in'] = {'t': t0s, 'fx': fx} | ({'from': edge[1], 'dist': 900} if fx == 'slide' else {}) | ({'dist': 500} if fx == 'drop' else {})
        L2['_note'] = 'default entrance: give it a meaningful action if its phrase has one (see references/actions.md), else keep it'
        F['layers'].append(L2)
    if hero:
        hx, hy = hero['head_top']; bx, by, bw, bh = hero['bbox']
        pl = hero.get('place', {'size': int(bw * .78), 'x': hx, 'y': by + int(bh * .55)})
        H = {'id': 'hero', 'type': 'image', 'hero': True, 'z': a.z0 + n_it + 5, 'size': pl['size'], 'x': pl['x'], 'y': pl['y'], 'rim': 12,
             'in': {'t': f'{a.t0}+0.3' if isinstance(tm(a.t0), str) else tm(a.t0) + .3, 'fx': 'slide', 'from': 'bottom', 'dist': 900},
             '_note': 'set size so the shoulders span the slot; the head top should sit near head_top ' + str(hero['head_top'])}
        H['src'] = rel(a.hero) if a.hero else 'PUT_PERSON_CUTOUT.png'; F['layers'].append(H)
    for j, sl in enumerate(slots[:2]):
        F['layers'].append({'id': f'title{j + 1}', 'type': 'strip', 'z': a.z0 + n_it + 10 + j, 'x': sl['center'][0], 'y': sl['center'][1], 'rot': sl['rot'],
                            'parts': [{'text': 'TITLE ', 'fg': 'ink'}, {'text': 'WORDS', 'fg': 'accent'}], 'size': int(sl['h'] * .62), 'bg': 'accent2',
                            'overlay': True, 'in': {'t': a.t0, 'fx': 'wipe'}, '_note': f'slot {sl["w"]}x{sl["h"]}: write the title, keep it inside the slot'})
    json.dump(F, open(a.scene, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('draft scene ->', a.scene)
for r in placed: print(f"{os.path.basename(r['file']):24s} {r['method']:8s} inliers {r.get('inliers', 0):4d} agree {r.get('agree', 0):.2f} z {r['z']} scale {r['scale']:.2f} rot {r['rot']:+.1f}")
print('hero slot:', hero and hero['bbox'], '| title slots:', len(slots), '| unmatched:', out['unmatched'] or 'none', '->', a.out)
