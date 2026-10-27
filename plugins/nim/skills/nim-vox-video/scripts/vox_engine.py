# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10", "numpy", "opencv-python-headless", "imageio-ffmpeg"]
# ///
"""Vox collage engine v8.1: declarative timeline.json -> layered paper-collage animation -> MP4.

v8: scenes built from design frames ("scenes": scene_NN.json fragments with their own layers, z band and
origin); plate layers; meaningful actions (path moves: rise / fly along a route, wiggle: swing / sway / shake,
glow: a lamp switching on, highlight: marker over text, roll: a vehicle passing); living paper (slow breathing
of landed pieces); design gate (--gate: design frame vs final still + fill / empty-zone / layer metrics);
stills at start, middle and end of every scene; checks for wedge corners on sheets, arrow stubs, objects hidden
under the hero, ambiguous word references and a packshot title before the packshot; parallel render (--jobs).

Every frame is a pure function of time. Layers live in WORLD pixels on one paper desk; a keyframed
camera looks at it. Generated / real images are only ingredients. Motion, text, marks, numbers, UI,
timing, shadows and sound are produced here, so nothing drifts, misspells or ignores the voice-over.

v4: smooth camera every frame while layers move on twos; animation principles (anticipation, arcs,
spring settle, squash on impact, height-based dynamic shadows); design pack (pack:...); paper panels
with torn edges; print treatments; screens composited into their device (no drift); layout check.

usage (uv resolves dependencies automatically on any OS):
  uv run vox_engine.py timeline.json --check            # layout / overlap / frame-edge report
  uv run vox_engine.py timeline.json --stills 0.5,2,4   # contact sheet (half res)
  uv run vox_engine.py timeline.json --draft            # 540p, layers 12 fps, fast
  uv run vox_engine.py timeline.json --out final.mp4    # final
"""
import json, math, os, random, re, subprocess, argparse
import numpy as np, cv2, imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, '..', 'assets'))
FF = imageio_ffmpeg.get_ffmpeg_exe()

# ================================================================ easing
def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def spring(p, z=0.68, w=12.0):
    """critically-ish damped spring step: tiny overshoot (~5%), settles by p=1"""
    if p <= 0: return 0.0
    if p >= 1: return 1.0
    wd = w * math.sqrt(1 - z * z); e = math.exp(-z * w * p)
    return 1 - e * (math.cos(wd * p) + z * w / wd * math.sin(wd * p))
EASE = {'linear': lambda p: p, 'out': lambda p: 1 - (1 - p) ** 3, 'in': lambda p: p ** 3,
        'inOut': lambda p: 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2, 'spring': spring,
        'soft': lambda p: spring(p, .85, 9)}
def bump(p, at, width): return math.exp(-((p - at) / width) ** 2)
def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

_fonts = {}
def font(name, size):
    k = (name, int(size))
    if k not in _fonts:
        p = name if os.path.isfile(name) else os.path.join(ASSETS, 'fonts', name)
        _fonts[k] = ImageFont.truetype(p, max(1, int(size)))
    return _fonts[k]

# ================================================================ materials (shared print look)
def grain(im, amt=6, seed=0):
    rng = np.random.default_rng(seed); a = np.array(im).astype(np.int16)
    a[..., :3] = np.clip(a[..., :3] + rng.normal(0, amt, a.shape[:2] + (1,)), 0, 255)
    return Image.fromarray(a.astype(np.uint8), im.mode)

def paper_fiber(w, h, seed=0, strength=0.10):
    """procedural paper: multi-scale mottling + fibres, values ~[1-strength, 1]"""
    rng = np.random.default_rng(seed); f = np.zeros((h, w), np.float32)
    for s, amp in ((60, .5), (14, .3), (3, .2)):
        f += cv2.resize(rng.random((max(2, h // s), max(2, w // s))).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC) * amp
    for _ in range(int(w * h / 9000)):
        x, y = rng.integers(0, w), rng.integers(0, h); a = rng.uniform(0, math.pi); L = rng.integers(6, 30)
        cv2.line(f, (int(x), int(y)), (int(x + L * math.cos(a)), int(y + L * math.sin(a))), float(f.mean() - .25), 1)
    f = (f - f.min()) / (np.ptp(f) + 1e-6); return 1 - strength * f

def unify(im, sat=0.92, contrast=1.04, warm=(1.02, 1.0, 0.965)):
    a = np.array(im).astype(np.float32); rgb = a[..., :3] / 255
    g = rgb.mean(2, keepdims=True); rgb = g + (rgb - g) * sat; rgb = (rgb - .5) * contrast + .5
    rgb *= np.array(warm, np.float32); a[..., :3] = np.clip(rgb * 255, 0, 255); return Image.fromarray(a.astype(np.uint8), 'RGBA')

def halftone(im, cell=6, mode='color', seed=0):
    """'color': colour dots on paper; 'news': dark ink dots on yellowed newsprint"""
    a = np.array(im).astype(np.float32); h, w = a.shape[:2]; rgb = a[..., :3] / 255
    d = 1 - cv2.GaussianBlur(rgb.mean(2), (0, 0), cell * .4)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); u, v = (xx + yy) / 1.4142, (xx - yy) / 1.4142
    fu, fv = (u % cell) / cell - .5, (v % cell) / cell - .5; dist = np.sqrt(fu * fu + fv * fv)
    r = np.sqrt(np.clip(d, 0, 1)) * .62; dots = np.clip((r - dist) * cell * 1.2 + .5, 0, 1)[..., None]
    if mode == 'news':
        paper = np.array([0.93, 0.89, 0.78], np.float32); ink = rgb * .35 + np.array([.12, .11, .1]) * .65
    else:
        paper = np.array([0.98, 0.96, 0.92], np.float32); ink = np.clip(rgb * 0.85, 0, 1)
    out = paper * (1 - dots) + ink * dots; out *= paper_fiber(w, h, seed, .08)[..., None]
    a[..., :3] = np.clip(out * 255, 0, 255); return Image.fromarray(a.astype(np.uint8), 'RGBA')

def print_look(im, kind, seed=0):
    if kind in (None, 'photo'): return unify(im)
    if kind == 'paper':
        im = unify(im); a = np.array(im).astype(np.float32); a[..., :3] *= paper_fiber(im.width, im.height, seed, .12)[..., None]
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    if kind == 'halftone': return halftone(im, 6, 'color', seed)
    if kind == 'newsprint': return halftone(im, 5, 'news', seed)
    return im

def wobble_mask(hard, border, amp=2.2, seed=0):
    rng = np.random.default_rng(seed)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (border * 2 + 1, border * 2 + 1)); d = cv2.dilate(hard, k)
    n = cv2.GaussianBlur(rng.random(d.shape).astype(np.float32), (0, 0), 5); n = (n - n.mean()) / (n.std() + 1e-6)
    dist = cv2.distanceTransform(d, cv2.DIST_L2, 3)
    return cv2.GaussianBlur(((dist > 1.5 + amp * n) & (d > 0)).astype(np.uint8) * 255, (3, 3), 0)

def paper_rim(im, rim=12, paper=(250, 247, 238), seed=0):
    """cutout -> irregular off-white cut-paper rim, cut 'with scissors': the outline is simplified first
    (thin gaps and loops bridged, small notches filled) and the tear noise scales with the rim width, so a
    small asset never gets a busy high-frequency edge. returns (image, offset of source inside it)"""
    if rim <= 0: return im, (0, 0)
    rim = max(3, int(round(rim))); pad = rim * 4 + 10
    big = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0)); big.alpha_composite(im, (pad, pad))
    hard = (np.array(big.getchannel('A')) > 90).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (rim * 3 + 1, rim * 3 + 1)); hard = cv2.morphologyEx(hard, cv2.MORPH_CLOSE, k)
    ff = hard.copy(); mk = np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8); cv2.floodFill(ff, mk, (0, 0), 255)
    holes = cv2.bitwise_not(ff); n, lab, st, _ = cv2.connectedComponentsWithStats(holes, 8)
    for i in range(1, n):  # scissors do not cut tiny windows: fill holes smaller than ~(6 rims)^2
        if st[i, cv2.CC_STAT_AREA] < (rim * 6) ** 2: hard[lab == i] = 255
    rng = np.random.default_rng(seed); kk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (rim * 2 + 1, rim * 2 + 1)); d = cv2.dilate(hard, kk)
    nz = cv2.GaussianBlur(rng.random(d.shape).astype(np.float32), (0, 0), max(4, rim * 1.6)); nz = (nz - nz.mean()) / (nz.std() + 1e-6)
    dist = cv2.distanceTransform(d, cv2.DIST_L2, 3); wm = cv2.GaussianBlur(((dist > 1.5 + rim * .22 * nz) & (d > 0)).astype(np.uint8) * 255, (3, 3), 0)
    p = Image.new('RGBA', big.size, paper + (0,)); p.putalpha(Image.fromarray(wm))
    p = grain(p, 5, seed); p.alpha_composite(big); return p, (pad, pad)

def torn_sheet(tex, w, h, sides='ltrb', fiber=(250, 247, 240), seed=0):
    """a sheet of `tex` (w x h) with torn edges on `sides` showing white paper core along the tear"""
    r = np.random.default_rng(seed); ts = max(w / tex.width, h / tex.height) * 1.05
    t = tex.resize((math.ceil(tex.width * ts), math.ceil(tex.height * ts)), Image.LANCZOS)
    ox, oy = int(r.integers(0, max(1, t.width - w))), int(r.integers(0, max(1, t.height - h))); t = t.crop((ox, oy, ox + w, oy + h)).convert('RGBA')
    pad = 30; W, H = w + pad * 2, h + pad * 2

    def edge(n, amp):  # jagged 1-D profile
        e = np.cumsum(r.normal(0, 1, n)); e = cv2.GaussianBlur(e.reshape(1, -1).astype(np.float32), (0, 0), 3).ravel()
        e -= np.linspace(e[0], e[-1], n); e = e / (np.abs(e).max() + 1e-6) * amp
        e = e + r.normal(0, amp * .12, n); ramp = max(8, n // 12)
        win = np.clip(np.minimum(np.arange(n), np.arange(n)[::-1]) / ramp, 0, 1); return e * win * win   # no spikes at corners
    outer = np.zeros((H, W), np.uint8); inner = np.zeros((H, W), np.uint8)
    pts_o, pts_i = [], []
    def run(side, n):
        amp = 14 if side in sides else 0
        return edge(n, amp), edge(n, amp * .6)
    lo, li = run('l', H); to, ti = run('t', W); ro, ri = run('r', H); bo, bi = run('b', W)
    core = lambda side: 7 if side in sides else 0
    # v8 fix: each side runs only along the sheet itself (pad .. W-pad). v6 ran every side across the whole
    # padded canvas, so the outline jumped from (W-1, pad) to (W-pad, 0) at each corner and filled a white
    # triangle (wedge) outside the sheet at all four corners.
    for x in range(pad, W - pad): pts_o.append((x, pad + to[x])); pts_i.append((x, pad + ti[x] + core('t')))
    for y in range(pad, H - pad): pts_o.append((W - pad + ro[y], y)); pts_i.append((W - pad + ri[y] - core('r'), y))
    for x in range(W - pad - 1, pad - 1, -1): pts_o.append((x, H - pad + bo[x])); pts_i.append((x, H - pad + bi[x] - core('b')))
    for y in range(H - pad - 1, pad - 1, -1): pts_o.append((pad + lo[y], y)); pts_i.append((pad + li[y] + core('l'), y))
    cv2.fillPoly(outer, [np.array(pts_o, np.int32)], 255); cv2.fillPoly(inner, [np.array(pts_i, np.int32)], 255)
    rect = np.zeros((H, W), np.uint8); rect[pad:pad + h, pad:pad + w] = 255; inner = cv2.bitwise_and(inner, rect)
    outer = cv2.erode(outer, np.ones((3, 3), np.uint8)); inner = cv2.erode(inner, np.ones((3, 3), np.uint8))
    sheet = Image.new('RGBA', (W, H), fiber + (0,)); sheet.putalpha(Image.fromarray(cv2.GaussianBlur(outer, (3, 3), 0)))
    body = Image.new('RGBA', (W, H), (0, 0, 0, 0)); body.paste(t, (pad, pad)); body.putalpha(Image.fromarray(cv2.GaussianBlur(inner, (3, 3), 0)))
    sheet = grain(sheet, 4, seed); sheet.alpha_composite(body); return sheet

def torn_strip(text, fnt, fg, bg, padx=30, pady=16, tape=False, seed=0):
    """torn paper label; `text` may be a list of (text, font, colour) segments drawn on one baseline"""
    segs = text if isinstance(text, list) else [(text, fnt, fg)]
    if len(segs) > 1 or isinstance(text, list):
        asc = max(f.getmetrics()[0] for _, f, _ in segs); top = min(asc - f.getmetrics()[0] + f.getbbox(s)[1] for s, f, _ in segs if s.strip())
        bot = max(asc - f.getmetrics()[0] + f.getbbox(s)[3] for s, f, _ in segs if s.strip()); tw = sum(f.getlength(s) for s, f, _ in segs)
        rr = random.Random(seed); w = int(tw) + padx * 2; h = bot - top + pady * 2
        im = Image.new('RGBA', (w + 24, h + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im); pts = []
        for x in range(12, w + 13, 9): pts.append((x, 12 + rr.uniform(-2, 2)))
        for y in range(12, h + 13, 6): pts.append((w + 12 + rr.uniform(-5, 5), y))
        for x in range(w + 12, 11, -9): pts.append((x, h + 12 + rr.uniform(-2, 2)))
        for y in range(h + 12, 11, -6): pts.append((12 + rr.uniform(-5, 5), y))
        d.polygon(pts, fill=bg + (255,)); x = 12 + padx
        for s, f, c in segs: d.text((x, 12 + pady - top + asc - f.getmetrics()[0]), s, font=f, fill=c); x += f.getlength(s)
        im = grain(im, 5, seed)
        if tape:
            tp = Image.new('RGBA', (90, 34), (238, 228, 196, 175)).rotate(rr.uniform(-30, -18), expand=True)
            big = Image.new('RGBA', (im.width + 40, im.height + 40), (0, 0, 0, 0)); big.alpha_composite(im, (20, 20)); big.alpha_composite(tp, (0, 0)); im = big
        return im
    rr = random.Random(seed); tb = fnt.getbbox(text); w = tb[2] - tb[0] + padx * 2; h = tb[3] - tb[1] + pady * 2
    im = Image.new('RGBA', (w + 24, h + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im); pts = []
    for x in range(12, w + 13, 9): pts.append((x, 12 + rr.uniform(-2, 2)))
    for y in range(12, h + 13, 6): pts.append((w + 12 + rr.uniform(-5, 5), y))
    for x in range(w + 12, 11, -9): pts.append((x, h + 12 + rr.uniform(-2, 2)))
    for y in range(h + 12, 11, -6): pts.append((12 + rr.uniform(-5, 5), y))
    d.polygon(pts, fill=bg + (255,)); d.text((12 + padx - tb[0], 12 + pady - tb[1]), text, font=fnt, fill=fg)
    im = grain(im, 5, seed)
    if tape:
        tp = Image.new('RGBA', (90, 34), (238, 228, 196, 175)).rotate(rr.uniform(-30, -18), expand=True)
        big = Image.new('RGBA', (im.width + 40, im.height + 40), (0, 0, 0, 0)); big.alpha_composite(im, (20, 20)); big.alpha_composite(tp, (0, 0)); im = big
    return im

def stamp(text, fnt, color, seed=0):
    rng = np.random.default_rng(seed); tb = fnt.getbbox(text); pw, ph = 36, 20; w, h = tb[2] - tb[0] + pw * 2, tb[3] - tb[1] + ph * 2
    m = Image.new('L', (w + 24, h + 24), 0); d = ImageDraw.Draw(m)
    d.rounded_rectangle((12, 12, w + 12, h + 12), 12, outline=255, width=max(6, fnt.size // 12))
    d.text((12 + pw - tb[0], 12 + ph - tb[1]), text, font=fnt, fill=255)
    n = cv2.GaussianBlur(rng.random((m.height, m.width)).astype(np.float32), (0, 0), 1.5)
    n2 = cv2.GaussianBlur(rng.random((m.height, m.width)).astype(np.float32), (0, 0), 12)
    ink = np.array(m).astype(np.float32) / 255 * np.clip(0.6 + (n - .5) * 2.2 + (n2 - .5) * 1.5, 0, 1) ** .6
    im = Image.new('RGBA', m.size, color + (0,)); im.putalpha(Image.fromarray((np.clip(ink, 0, 1) * 235).astype(np.uint8))); return im

def text_img(text, fnt, fill, stroke=0, sfill=None):
    tb = fnt.getbbox(text, stroke_width=stroke)
    im = Image.new('RGBA', (tb[2] - tb[0] + 8, tb[3] - tb[1] + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - tb[0], 4 - tb[1]), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=sfill); return im

def shadow_of(im, blur, op, color=(40, 28, 16)):
    """soft shadow from an RGBA image's alpha (computed at 1/4 res: cheap enough per frame)"""
    a = np.array(im.getchannel('A')); h, w = a.shape; q = 4
    small = cv2.resize(a, (max(1, w // q), max(1, h // q)), interpolation=cv2.INTER_AREA).astype(np.float32)
    pad = int(blur / q * 3) + 2; small = np.pad(small, pad); small = cv2.GaussianBlur(small, (0, 0), max(.5, blur / q))
    big = cv2.resize(small, ((w // q + pad * 2) * q, (h // q + pad * 2) * q), interpolation=cv2.INTER_LINEAR) * op
    sh = Image.new('RGBA', (big.shape[1], big.shape[0]), color + (0,)); sh.putalpha(Image.fromarray(np.clip(big, 0, 255).astype(np.uint8)))
    return sh, pad * q

# ================================================================ marker geometry
def ellipse_pts(cx, cy, rx, ry, turns=1.1, rot=-0.15, n=80, seed=3):
    r = random.Random(seed); pts = []
    for i in range(n):
        a = -2.3 + 2 * math.pi * turns * i / (n - 1); j = 1 + 0.04 * math.sin(i * .33) + r.uniform(-.006, .006)
        x, y = rx * math.cos(a) * j, ry * math.sin(a) * j
        pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
    return pts
def arrow_pts(x0, y0, x1, y1, bend=0.18, n=30):
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2; nx, ny = -(y1 - y0) * bend, (x1 - x0) * bend
    pts = [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * (mx + nx) + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * (my + ny) + t * t * y1) for t in np.linspace(0, 1, n)]
    a = math.atan2(pts[-1][1] - pts[-3][1], pts[-1][0] - pts[-3][0]); L = 0.07 * math.hypot(x1 - x0, y1 - y0) + 18
    return pts, [(x1 - L * math.cos(a - .5), y1 - L * math.sin(a - .5)), (x1, y1), (x1 - L * math.cos(a + .5), y1 - L * math.sin(a + .5))]
def partial(pts, frac):
    pts = np.array(pts, np.float32); seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); L = seg.sum() * clamp(frac)
    out, acc = [tuple(pts[0])], 0
    for i, s in enumerate(seg):
        if acc + s >= L: out.append(tuple(pts[i] + (pts[i + 1] - pts[i]) * ((L - acc) / max(s, 1e-6)))); break
        acc += s; out.append(tuple(pts[i + 1]))
    return out

def path_at(pts, u):
    """point and heading (deg) at fraction u of a smoothed polyline (Catmull-Rom through the points)"""
    P = np.array(pts, np.float32)
    if len(P) > 2:
        Q = [P[0]]
        for i in range(len(P) - 1):
            p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(len(P) - 1, i + 2)]
            for tt in np.linspace(0, 1, 12)[1:]:
                Q.append(.5 * (2 * p1 + (-p0 + p2) * tt + (2 * p0 - 5 * p1 + 4 * p2 - p3) * tt ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * tt ** 3))
        P = np.array(Q, np.float32)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)]); L = cum[-1] * clamp(u)
    i = int(min(len(seg) - 1, np.searchsorted(cum, L, 'right') - 1)); f = (L - cum[i]) / max(seg[i], 1e-6); pt = P[i] + (P[i + 1] - P[i]) * f
    d = P[i + 1] - P[i]; return (float(pt[0]), float(pt[1])), math.degrees(math.atan2(d[1], d[0]))

# ================================================================ screen content helpers
def sprite_img(rows, palette, cell):
    h, w = len(rows), max(len(r) for r in rows); im = Image.new('RGBA', (w * cell, h * cell), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c in palette: d.rectangle((x * cell, y * cell, x * cell + cell - 1, y * cell + cell - 1), fill=hexrgb(palette[c]))
    return im
class Video:
    def __init__(self, path, size, fps):
        w, h = size; p = subprocess.run([FF, '-loglevel', 'error', '-i', path, '-vf', f'fps={fps},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}',
                                         '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
        self.frames = np.frombuffer(p, np.uint8).reshape(-1, h, w, 3); self.fps = fps
    def at(self, t):
        return Image.fromarray(self.frames[int(max(0, t) * self.fps) % len(self.frames)]).convert('RGBA')

SFX_FOR = {'flicker': 'click', 'roll': 'roll', 'burst': 'tick', 'pop': 'tick', 'slam': 'thud', 'slide': 'slide', 'drop': 'thud', 'fade': 'none', 'draw': 'scribble', 'wipe': 'tape', 'count': 'tick', 'tear': 'tear'}
DUR = {'flicker': .5, 'roll': 1.4, 'burst': .7, 'pop': .32, 'slam': .32, 'slide': .55, 'drop': .5, 'fade': .3, 'draw': .5, 'wipe': .35, 'count': .9}
TEXTY = ('strip', 'stamp', 'counter', 'text')

def wedge_score(im):
    """number of triangular pieces sticking out at the corners of a sheet sprite (the v6 torn_sheet bug): thin
    opaque wedges are removed by a morphological opening; what is removed near a corner of the sheet's
    rotated bounding box and is bigger than tear noise counts as a wedge"""
    if im is None: return 0
    a = (np.array(im.getchannel('A')) > 128).astype(np.uint8); h, w = a.shape
    if a.sum() < 400: return 0
    r = int(min(9, max(4, min(h, w) * .02))); op = cv2.morphologyEx(a, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    spikes = (a & (1 - op)).astype(np.uint8); n, lab, st, cen = cv2.connectedComponentsWithStats(spikes, 8)
    cs, _ = cv2.findContours(op, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cs: return 0
    box = cv2.boxPoints(cv2.minAreaRect(max(cs, key=cv2.contourArea))); cnt = 0
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < r * r * 1.2: continue
        if min(np.hypot(*(cen[i] - c)) for c in box) < r * 5: cnt += 1
    return cnt

# ================================================================ engine
class Engine:
    def __init__(self, tl_path, draft=False):
        self.dir = os.path.dirname(os.path.abspath(tl_path)); T = json.load(open(tl_path, encoding='utf-8')); self.T = T
        self.W, self.H = T.get('size', [1920, 1080]); self.fps = T.get('fps', 24); self.afps = T.get('anim_fps', 12)
        self.scale_out = 0.5 if draft else 1.0; self.draft = draft; self.warnings = []; self._refs = set()
        self.OW, self.OH = (round(self.W * self.scale_out / 2) * 2, round(self.H * self.scale_out / 2) * 2)   # even for x264
        if draft: self.fps = self.afps
        self.dur = T['duration']; self.pal = {k: hexrgb(v) for k, v in T.get('palette', {}).items()}
        self.words = json.load(open(self.p(T['audio']['words']), encoding='utf-8')) if T.get('audio', {}).get('words') else []
        self.vo_end = self.words[-1]['e'] if self.words else 0
        if self.dur == 'auto': self.dur = round(self.vo_end + T.get('end_hold', 1.2), 2)   # packshot hold after the last word
        if self.words and T.get('captions', True) is True: T['captions'] = {'on': True}       # karaoke captions are on by default
        if T.get('captions') is False: T['captions'] = None
        self.boil = T.get('boil', {'amp': 0.6, 'rot': 0.2, 'rate': 4}); self.light = T.get('light', [0.55, 1.0])
        self.events = []; self.cache = {}; self.tcache = {}
        self.bg = Image.open(self.p(T['background']['image'])).convert('RGB')
        bw = T['background'].get('world', [self.W, self.H]); self.bg_world = (bw[0], bw[1], T['background'].get('origin', [0, 0]))
        self.camera = T.get('camera', [{'t': 0, 'x': self.W / 2, 'y': self.H / 2, 'zoom': 1}])
        for c in self.camera: c['t'] = self.time(c['t'])
        self.camera.sort(key=lambda c: c['t'])
        self.shakes = [(self.time(e['t']), e.get('amp', 10)) for e in T.get('shake', [])]
        self.packshot_t = self.time(T['packshot']) if T.get('packshot') is not None else None
        self.scenes = []; self.layers = []; [self.add_layer(L) for L in T.get('layers', [])]
        for i, S in enumerate(T.get('scenes', [])): self.add_scene(S, i)
        self.layers.sort(key=lambda L: L.get('z', 0)); self.byid = {L['id']: L for L in self.layers}
        for L in self.layers:
            if L['type'] == 'screen': self.byid[L['parent']].setdefault('_attached', []).append(L)
        self.noise = [grain(Image.new('RGB', (64, 64), (128, 128, 128)), 1, s) for s in range(3)]

    def p(self, f):
        if f.startswith('pack:'): return os.path.join(ASSETS, 'pack', f[5:] + ('' if os.path.splitext(f)[1] else '.png'))
        return f if os.path.isabs(f) else os.path.join(self.dir, f)

    def add_scene(self, S, i):
        """a scene fragment (scene_NN.json made by one sub-agent): its layers get the scene's z band, the scene's
        origin (world offset) and paths relative to the fragment file. The fragment may carry its own
        "design" (design frame), "plate", "t0"/"t1" (scene span) used by --stills scenes and --gate."""
        path = self.p(S['src']); F = json.load(open(path, encoding='utf-8')); base = os.path.dirname(path)
        ox, oy = S.get('origin', F.get('origin', [0, 0])); zb = S.get('z', 1000 * (i + 1)); sid = S.get('id', F.get('id', f's{i + 1:02d}'))
        rel = lambda f: f if (f.startswith('pack:') or os.path.isabs(f)) else os.path.join(base, f)
        shift = self.time(S['at']) if 'at' in S else 0.0   # reusable fragment (packshot): its numeric times count from "at"
        sh = lambda v: v + shift if isinstance(v, (int, float)) else v
        for L in F['layers']:
            L = json.loads(json.dumps(L)); L['id'] = f"{sid}.{L.get('id', len(self.layers))}"; L['z'] = zb + L.get('z', 0); L['_scene'] = sid
            if shift:
                for kk in ('in', 'out'):
                    if kk in L: L[kk]['t'] = sh(L[kk]['t'])
                for kk in L.get('keys', []) + (L['wiggle'] if isinstance(L.get('wiggle'), list) else [L['wiggle']] if 'wiggle' in L else []): kk['t'] = sh(kk['t'])
            for k in ('src', 'texture'):
                if k in L: L[k] = rel(L[k])
            for C in L.get('content', []):   # screen content files are relative to the fragment too
                if 'src' in C: C['src'] = rel(C['src'])
            if 'parent' in L: L['parent'] = f"{sid}.{L['parent']}"
            if 'parent' not in L: L['x'] = L.get('x', self.W / 2) + ox; L['y'] = L.get('y', self.H / 2) + oy
            if L.get('type') == 'marker' and 'pts' in L:
                q = L['pts']
                if L['shape'] in ('circle',): L['pts'] = [q[0] + ox, q[1] + oy] + q[2:]
                elif L['shape'] in ('arrow', 'highlight'): L['pts'] = [q[0] + ox, q[1] + oy, q[2] + ox, q[3] + oy]
                else: L['pts'] = [[x + ox, y + oy] for x, y in q]
            for kk in L.get('keys', []):
                if 'x' in kk and 'parent' not in L: kk['x'] += ox
                if 'y' in kk and 'parent' not in L: kk['y'] += oy
                if 'path' in kk: kk['path'] = [[x + ox, y + oy] for x, y in kk['path']]
            if 'in' in L and 'origin' in L['in']: L['in']['origin'] = [L['in']['origin'][0] + ox, L['in']['origin'][1] + oy]
            self.add_layer(L)
        t0 = self.time(S.get('t0', sh(F.get('t0', 0)))); t1 = self.time(S.get('t1', sh(F.get('t1', self.dur)) if 't1' in F else self.dur))
        self.scenes.append({'id': sid, 't0': t0, 't1': t1, 'origin': (ox, oy), 'design': rel(F['design']) if F.get('design') else None})

    def time(self, v):
        if isinstance(v, (int, float)): return float(v)
        s = str(v); off = 0.0
        m = re.search(r'([+-]{1,2})(\d*\.?\d+)$', s)   # only a trailing number is an offset ("@eight-oh-eight" is a word; "+-0.15" works)
        if m and not (s.startswith('@') and m.start() == 0): off = float(m.group(2)) * (-1 if m.group(1).count('-') % 2 else 1); s = s[:m.start()]
        if s.startswith('@'):
            key = s[1:]; use_end = key.endswith('.end'); key = key[:-4] if use_end else key; occ = 1; explicit = '#' in key
            if explicit: key, o = key.split('#'); occ = int(o)
            norm = lambda w: ''.join(ch for ch in w.lower() if ch.isalnum() or ch == '$')
            hits = [w for w in self.words if norm(w['w']) == norm(key)]
            exact = [w for w in hits if w['w'].strip('.,!?;:"\'') == key]
            if any(ch.isupper() for ch in key) and exact and len(exact) < len(hits): hits = exact   # "@Tea" prefers the capitalised word
            if len(hits) < occ: raise ValueError(f'word {key}#{occ} not in VO (words: {" ".join(w["w"] for w in self.words)})')
            if len(hits) > 1 and not explicit and key not in self._refs:
                self._refs.add(key); at = ', '.join('%.2fs' % w['s'] for w in hits)
                self.warnings.append(f'AMBIGUOUS @{key}: the word occurs {len(hits)} times ({at}); first one used: write @{key}#N')
            return (hits[occ - 1]['e'] if use_end else hits[occ - 1]['s']) + off
        return float(s) + off

    def col(self, v, default):
        if v is None: return self.pal.get(default, (0, 0, 0))
        return hexrgb(v) if v.startswith('#') else self.pal.get(v, (0, 0, 0))

    # ---------------------------------------------------------- layers
    def add_layer(self, L):
        L = dict(L)
        if L['type'] == 'grid': return self.expand_grid(L)
        L.setdefault('id', f"L{len(self.layers)}")
        for k in ('in', 'out'):
            if k in L: L[k] = dict(L[k]); L[k]['t'] = self.time(L[k]['t'])
        L['keys'] = [dict(k, t=self.time(k['t'])) for k in L.get('keys', [])]
        if 'wiggle' in L: L['wiggle'] = [dict(w, t=self.time(w['t']), until=self.time(w['until']) if 'until' in w else 1e9) for w in (L['wiggle'] if isinstance(L['wiggle'], list) else [L['wiggle']])]
        if L['type'] == 'plate':   # full-frame background made from the design frame (no rim, no shadow, no grade)
            L.setdefault('x', self.W / 2); L.setdefault('y', self.H / 2); L.setdefault('size', self.W); L.setdefault('rim', 0); L.setdefault('print', 'none'); L.setdefault('shadow', False); L.setdefault('boil', False)
        for f, d in (('x', 0), ('y', 0), ('scale', 1), ('rot', 0), ('alpha', 1), ('elev', 0)): L.setdefault(f, d)
        if L.get('packshot') and self.packshot_t is not None and 'in' in L and L['in']['t'] < self.packshot_t - .35:
            self.warnings.append(f'PACKSHOT EARLY {L["id"]}: enters at {L["in"]["t"]:.2f}s, before the packshot ({self.packshot_t:.2f}s): check its word reference')
        L['_seed'] = sum(map(ord, L['id'])) * 7919 % 65536
        L['_img'], L['_off'] = self.build(L)
        if L['_img'] is not None: L['_src_size'] = L.get('_src_size', L['_img'].size)
        if 'in' in L:
            fx = L['in'].get('fx', 'pop'); s = L['in'].get('sfx', SFX_FOR.get(fx, 'tick')); d = L['in'].get('dur', DUR.get(fx, .3))
            hit = {'slam': .5, 'drop': .55, 'slide': .25}.get(fx, 0) * d
            self.events.append((L['in']['t'] + hit, s, L['in'].get('vol', 1)))
            if fx in ('slam', 'drop') and L['in'].get('shake', True): self.shakes.append((L['in']['t'] + hit, L['in'].get('shake_amp', 7 if fx == 'slam' else 9)))
        for k in L['keys']:
            if any(f in k for f in ('x', 'y', 'path')): self.events.append((k['t'], k.get('sfx', 'whoosh' if 'path' in k else 'slide'), .6))
        if 'out' in L and L['out'].get('fx') in ('fly', 'scatter'): self.events.append((L['out']['t'] + .05, 'slide', .5))
        self.layers.append(L)

    def expand_grid(self, G):
        n, cols, rows = G['count'], G['cols'], G['rows']; cw, ch = G['cell']; x0, y0 = G['x'], G['y']; skip = G.get('skip', [])
        t0 = self.time(G['in']['t']); span = G['in'].get('span', 1.0); ox, oy = G['in'].get('origin', [x0, y0])
        cells = [(x0 + (c - (cols - 1) / 2) * cw, y0 + (r - (rows - 1) / 2) * ch) for r in range(rows) for c in range(cols)]
        cells = [(x, y) for x, y in cells if not any(a <= x <= b and cc <= y <= d for a, cc, b, d in skip)]
        cells = sorted(cells, key=lambda q: math.hypot(q[0] - ox, q[1] - oy))[:n]
        dmax = max(math.hypot(x - ox, y - oy) for x, y in cells) or 1; rng = random.Random(7); colors = G.get('colors', ['#3fa7d6'])
        for i, (x, y) in enumerate(cells):
            d = math.hypot(x - ox, y - oy) / dmax
            L = {'id': f"{G['id']}_{i}", 'type': 'card', 'src': G['src'], 'screen': G.get('screen'), 'color': colors[i % len(colors)],
                 'x': x + rng.uniform(-8, 8), 'y': y + rng.uniform(-8, 8), 'rot': rng.uniform(-5, 5), 'scale': G.get('scale', 1), 'z': G.get('z', 0),
                 'in': {'t': t0 + d * span, 'fx': G['in'].get('fx', 'pop'), 'sfx': 'tick' if i % 5 == 0 else 'none', 'vol': .6}}
            if 'out' in G: L['out'] = dict(G['out'], t=self.time(G['out']['t']) + d * G['out'].get('span', 0.2))
            self.add_layer(L)

    def build(self, L):
        """static RGBA (no shadow: shadows are dynamic) + offset of the source image inside it"""
        t = L['type']; seed = L['_seed']
        if t == 'plate': t = 'image'
        if t == 'rect':      # plain coloured box (packshot plates, check boxes, bars); "radius" rounds the corners
            w, h = L['w'], L['h']; im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), L.get('radius', 0), fill=self.col(L.get('color'), 'ink') + (255,))
            return (grain(im, 3, seed) if L.get('grain', True) else im), (0, 0)
        if t == 'poly':      # filled polygon, points in its own box (rainbow stripes, ticks, flags)
            pts = L['pts']; xs, ys = [p[0] for p in pts], [p[1] for p in pts]; w, h = int(max(xs)) + 2, int(max(ys)) + 2
            im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=self.col(L.get('color'), 'ink') + (255,)); return im, (0, 0)
        if t == 'glow':      # warm light pool (a lamp switching on): radial gradient, drawn additively
            r = L.get('r', 300); yy, xx = np.mgrid[-r:r, -r:r]; d = np.clip(1 - np.sqrt(xx ** 2 + yy ** 2) / r, 0, 1) ** 2
            c = self.col(L.get('color'), 'accent2'); a = (d * 255 * L.get('strength', .55)).astype(np.uint8)
            im = Image.new('RGBA', (2 * r, 2 * r), c + (0,)); im.putalpha(Image.fromarray(a)); return im, (0, 0)
        if t in ('image', 'decor'):
            im = Image.open(self.p(L['src'])).convert('RGBA')
            if 'crop' in L: im = im.crop(L['crop'])
            if L.get('flip'): im = im.transpose(Image.FLIP_LEFT_RIGHT)
            L['_orig_size'] = im.size
            if 'size' in L: im = im.resize((L['size'], round(im.height * L['size'] / im.width)), Image.LANCZOS)
            L['_src_size'] = im.size
            if t == 'decor' and 'doodles/' in L['src']:  # ink: recolour, no rim
                c = self.col(L.get('color'), 'ink'); rgb = Image.new('RGBA', im.size, c + (0,)); rgb.putalpha(im.getchannel('A')); return rgb, (0, 0)
            im = print_look(im, L.get('print', 'photo' if t == 'image' else None), seed)
            hw = 'themes/' in L['src'] or L.get('photo_decor')
            if hw:  # photo bits keyed from white: harden the soft halo so the paper rim hugs the object
                al = np.array(im.getchannel('A')).astype(np.float32); al = np.clip((al - 90) * 2.2, 0, 255); im.putalpha(Image.fromarray(al.astype(np.uint8)))
            rim = L.get('rim', 10 if t == 'image' or 'engravings/' in L['src'] or hw else 0)   # screen px at zoom 1
            return paper_rim(im, rim / max(L.get('scale', 1), .05), seed=seed)
        if t == 'panel':
            tex = Image.open(self.p(L['texture']))
            if tex.mode in ('RGBA', 'LA', 'P'):  # a scrap with its own torn alpha: keep only its solid inner rectangle
                tex = tex.convert('RGBA'); al = np.array(tex.getchannel('A')) > 250
                al = cv2.erode(al.astype(np.uint8), np.ones((max(3, tex.width // 6),) * 2, np.uint8)); ys, xs = np.nonzero(al)
                if len(xs): tex = tex.crop((xs.min(), ys.min(), xs.max(), ys.max()))
            tex = tex.convert('RGB'); L['_src_size'] = (L['w'], L['h']); sh = torn_sheet(tex, L['w'], L['h'], L.get('torn', 'ltrb'), seed=seed)
            return sh, (30, 30)
        if t == 'card':
            k = ('card', L['src'], L['color'])
            if k not in self.cache:
                im = Image.open(self.p(L['src'])).convert('RGBA')
                if L.get('screen'):
                    x0, y0, x1, y1 = L['screen']; d = ImageDraw.Draw(im); c = hexrgb(L['color'])
                    d.rectangle((x0, y0, x1, y1), fill=c); [d.rectangle((x0 + 18, y0 + 30 + j * 46, x1 - 18 - (j % 2) * 60, y0 + 52 + j * 46), fill=tuple(min(255, v + 70) for v in c)) for j in range(4)]
                im = unify(im.resize((260, round(im.height * 260 / im.width)), Image.LANCZOS))
                card = Image.new('RGBA', (im.width + 36, im.height + 36), (250, 247, 238, 255)); card.alpha_composite(im, (18, 18))
                self.cache[k] = grain(card, 5, seed)
            return self.cache[k], (18, 18)
        if t == 'strip':   # "text" or "parts": [{"text", "fg", "font", "size"}] for two-colour titles
            parts = L.get('parts') or [{'text': L['text']}]
            segs = [(q['text'], font(q.get('font', L.get('font', 'Anton-Regular.ttf')), q.get('size', L.get('size', 64))), self.col(q.get('fg', L.get('fg')), 'ink')) for q in parts]
            return torn_strip(segs, None, None, self.col(L.get('bg'), 'paper'), padx=L.get('padx', 30), pady=L.get('pady', 16), tape=L.get('tape', False), seed=seed), (0, 0)
        if t == 'stamp': return stamp(L['text'], font(L.get('font', 'Anton-Regular.ttf'), L.get('size', 90)), self.col(L.get('color'), 'accent'), seed=seed), (0, 0)
        if t == 'text': return text_img(L['text'], font(L.get('font', 'Anton-Regular.ttf'), L.get('size', 120)), self.col(L.get('color'), 'ink')), (0, 0)
        if t == 'counter':
            f = font(L.get('font', 'Anton-Regular.ttf'), L.get('size', 300)); im = text_img(L.get('fmt', '{}').format(L['to']), f, (0, 0, 0)); L['_src_size'] = im.size
            return None, (0, 0)
        return None, (0, 0)

    # ---------------------------------------------------------- animation state (principles live here)
    def state(self, L, t):
        S = {'x': L['x'], 'y': L['y'], 's': L['scale'], 'r': L['rot'], 'a': L['alpha'], 'h': L['elev'], 'sx': 1.0, 'sy': 1.0, 'rev': 1.0}
        for k in L['keys']:
            if t < k['t']: continue
            dur = k.get('dur', .45); p = clamp((t - k['t']) / dur); moved = False
            ease = EASE[k['ease']] if 'ease' in k else None; ant = k.get('anticip', .07 if ease is None else 0)
            pre = .2 if ant else 0
            if p < pre: e = -ant * math.sin(math.pi * p / pre)                    # anticipation: lean back first
            else: e = (ease or spring)((p - pre) / (1 - pre) if pre else p)
            if 'path' in k:   # move along a route (rocket rises along the arrow, a train runs along the rails)
                pe = EASE[k.get('ease', 'inOut')](p) if k.get('ease') != 'spring' else spring(p)
                pts = [(S['x'], S['y'])] + [tuple(q) for q in k['path']] if k.get('from_here', True) else [tuple(q) for q in k['path']]
                (S['x'], S['y']), ang = path_at(pts, pe)
                if k.get('orient'): S['r'] += ang - path_at(pts, 0)[1]
                moved = True
            for f, sf in (('x', 'x'), ('y', 'y'), ('scale', 's'), ('rot', 'r'), ('alpha', 'a'), ('elev', 'h')):
                if f in k:
                    base = S[sf]; S[sf] = base + (k[f] - base) * (e if f != 'alpha' else clamp(e)); moved |= f in ('x', 'y', 'scale')
            if moved and 'elev' not in k: S['h'] += k.get('lift', .45) * math.sin(math.pi * p)   # lifted while moving -> shadow grows
        if 'in' in L:
            I = L['in']; fx = I.get('fx', 'pop'); dur = I.get('dur', DUR.get(fx, .3)); p = (t - I['t']) / dur
            if p < 0: return None
            p = clamp(p); dist = I.get('dist', 700)
            dx, dy = {'left': (-1, 0), 'right': (1, 0), 'top': (0, -1), 'bottom': (0, 1)}[I.get('from', 'top' if fx == 'drop' else 'left')]
            if fx == 'pop':
                S['s'] *= spring(p, .55, 13); S['a'] *= clamp(p * 5); S['h'] += .3 * (1 - p)
            elif fx == 'slam':  # falls toward the desk (ease in), squash on impact, settle
                if p < .5: q = (p / .5) ** 2; S['s'] *= 1.5 - .5 * q; S['h'] += 1.2 * (1 - q); S['a'] *= clamp(.25 + q)
                else: q = (p - .5) / .5; S['s'] *= 1 - .05 * math.sin(math.pi * q) * (1 - q)
            elif fx == 'slide':  # arc path, spring arrival, small rotation follow-through, squash on landing
                e = spring(p, .7, 11); u = clamp(p * 1.3)
                S['x'] += dx * dist * (1 - e) + dy * dist * I.get('arc', .12) * 4 * u * (1 - u)
                S['y'] += dy * dist * (1 - e) - abs(dx) * dist * I.get('arc', .12) * 4 * u * (1 - u)
                S['r'] += I.get('spin', 8) * (1 - spring(p, .5, 10)) * (1 if dx + dy > 0 else -1)
                S['h'] += .7 * (1 - clamp(p * 1.6)); k = bump(p, .3, .07)
                S['sx'] *= 1 + .035 * k * (abs(dx) - abs(dy)); S['sy'] *= 1 - .035 * k * (abs(dx) - abs(dy))
            elif fx == 'drop':  # gravity fall, squash, tiny bounce
                if p < .55: q = (p / .55) ** 2; S['y'] -= dist * (1 - q); S['h'] += 1 - q; S['r'] += I.get('spin', 4) * (1 - q)
                else: q = (p - .55) / .45; S['y'] -= dist * .03 * math.sin(math.pi * q) * (1 - q)
                k = bump(p, .56, .05); S['sx'] *= 1 + .07 * k; S['sy'] *= 1 - .07 * k
            elif fx == 'burst':  # flies out of a point along an arc with spin (screws from an opened device)
                ox, oy = I['origin']; e = spring(p, .62, 10); u = clamp(p * 1.25)
                S['x'] = ox + (S['x'] - ox) * e; S['y'] = oy + (S['y'] - oy) * e - I.get('arc', 220) * 4 * u * (1 - u)
                S['r'] += I.get('spin', 300) * (1 - e); S['h'] += 1.3 * (1 - clamp(p * 1.4)); S['s'] *= .7 + .3 * clamp(p * 3)
            elif fx == 'fade': S['a'] *= p
            elif fx == 'flicker':  # a lamp catching: two quick flashes, then steady
                S['a'] *= 1.0 if p >= .7 else (.85 if (.12 < p < .2 or .38 < p < .5) else .08 + .3 * p)
            elif fx == 'roll':     # a vehicle rolling in at constant speed and braking softly (no bounce, no spin)
                e = 1 - (1 - p) ** 2.2; S['x'] += dx * dist * (1 - e); S['y'] += dy * dist * (1 - e); S['r'] += math.sin(t * 40) * .25 * (1 - p)
            elif fx in ('draw', 'count', 'wipe'): S['rev'] = EASE['inOut'](p) if fx != 'count' else EASE['out'](p)
        if 'out' in L:
            O = L['out']; fx = O.get('fx', 'fade'); dur = O.get('dur', .4); p = (t - O['t']) / dur
            if p >= 1: return None
            if p > 0:
                if fx == 'fade': S['a'] *= 1 - p
                elif fx in ('fly', 'scatter'):
                    if fx == 'fly': ux, uy = {'left': (-1, 0), 'right': (1, 0), 'top': (0, -1), 'bottom': (0, 1)}[O.get('to', 'left')]
                    else:
                        cx, cy = O.get('from', [960, 540]); vx, vy = S['x'] - cx, S['y'] - cy; nn = math.hypot(vx, vy) or 1; ux, uy = vx / nn, vy / nn
                    pre = .22; e = -.05 * math.sin(math.pi * p / pre) if p < pre else ((p - pre) / (1 - pre)) ** 2.2   # anticipation, then accelerate away
                    D = O.get('dist', 1800); S['x'] += ux * D * e; S['y'] += uy * D * e; S['r'] += 14 * max(0, e) * (1 if ux + uy > 0 else -1); S['h'] += .6 * clamp(p * 2)
                elif fx == 'pop': S['s'] *= 1 - EASE['in'](p); S['h'] += .2
                elif fx == 'lift': S['h'] += 1.5 * p; S['a'] *= 1 - EASE['in'](p); S['s'] *= 1 + .08 * p
        for w in L.get('wiggle', []):   # swing / sway / tremble around a pivot, decaying (a watch on its chain, a flag, a nervous needle)
            if w['t'] <= t < w['until']:
                ph = t - w['t']; dec = math.exp(-w.get('decay', 0) * ph); f = w.get('freq', 1.0); sn = math.sin(2 * math.pi * f * ph)
                dr = w.get('rot', 0) * sn * dec; S['x'] += w.get('x', 0) * sn * dec; S['y'] += w.get('y', 0) * math.sin(2 * math.pi * f * ph + 1.3) * dec
                if dr and 'pivot' in w:   # pivot in source px from the image centre (e.g. the watch ring at the top)
                    px, py = w['pivot']; th = math.radians(S['r']); qx, qy = px * math.cos(th) - py * math.sin(th), px * math.sin(th) + py * math.cos(th)
                    th2 = math.radians(dr); S['x'] += (-qx * math.cos(th2) + qy * math.sin(th2) + qx) * S['s']; S['y'] += (-qx * math.sin(th2) - qy * math.cos(th2) + qy) * S['s']
                S['r'] += dr
        live = self.T.get('live', 1.0) * L.get('live', 1.0)
        if live and L['type'] not in ('plate', 'panel', 'marker', 'glow', 'screen') and t > L.get('in', {}).get('t', -9) + .8:   # living paper
            ph = L['_seed'] % 628 / 100; S['h'] += live * .05 * (1 + math.sin(2 * math.pi * t / 3.1 + ph)); S['r'] += live * .12 * math.sin(2 * math.pi * t / 4.3 + ph)
        b = L.get('boil', L['type'] in ('decor', 'strip', 'stamp', 'card', 'counter', 'text'))
        if b and self.boil.get('amp', 0):
            amt = b if isinstance(b, (int, float)) and not isinstance(b, bool) else 1.0
            rr = random.Random(L['_seed'] * 1009 + int(t * self.boil.get('rate', 4)))
            S['x'] += rr.uniform(-1, 1) * self.boil['amp'] * amt; S['y'] += rr.uniform(-1, 1) * self.boil['amp'] * amt; S['r'] += rr.uniform(-1, 1) * self.boil.get('rot', .2) * amt
        if 'parent' in L and L['type'] != 'screen':
            P = self.byid[L['parent']]; ps = self.state(P, t)
            if ps is None: return None
            pw, ph = P['_src_size']; lx, ly = S['x'] - pw / 2, S['y'] - ph / 2; c, sn = math.cos(math.radians(ps['r'])), math.sin(math.radians(ps['r']))
            S['x'], S['y'] = ps['x'] + (lx * c - ly * sn) * ps['s'], ps['y'] + (lx * sn + ly * c) * ps['s']; S['s'] *= ps['s']; S['r'] += ps['r']; S['a'] *= ps['a']; S['h'] += ps['h']
        return S

    def cam(self, t):
        ks = self.camera; c = {'x': ks[0]['x'], 'y': ks[0]['y'], 'zoom': ks[0].get('zoom', 1), 'rot': ks[0].get('rot', 0)}
        for k in ks[1:]:
            if t >= k['t']:
                dur = k.get('dur', .6); p = clamp((t - k['t']) / dur); e = EASE[k.get('ease', 'inOut')](p) if k.get('ease') != 'spring' else spring(p, .8, 9)
                for f in ('x', 'y', 'zoom', 'rot'):
                    if f in k: c[f] = c[f] + (k[f] - c[f]) * e
        sx = sy = 0
        for st, amp in self.shakes:
            if 0 <= t - st < .28:
                d = amp * (1 - (t - st) / .28) ** 2; rr = random.Random(int(t * 60)); sx += rr.uniform(-d, d); sy += rr.uniform(-d, d)
        return c['x'] + sx, c['y'] + sy, c['zoom'], c['rot']

    # ---------------------------------------------------------- frame
    def layer_image(self, L, tq):
        if L['type'] == 'counter':
            v = round(L['from'] + (L['to'] - L['from']) * self._rev); txt = (L.get('fmt', '{}') if v == L['to'] else L.get('fmt_roll', L.get('fmt', '{}'))).format(v); k = ('cnt', L['id'], txt)   # fmt_roll: '{}' while rolling, '{}+' at the end
            if k not in self.cache:
                self.cache[k] = text_img(txt, font(L.get('font', 'Anton-Regular.ttf'), L.get('size', 300)), self.col(L.get('color'), 'ink'))
            return self.cache[k]
        im = L['_img']
        if L.get('_attached'):
            im = im.copy(); ox, oy = L['_off']
            for C in L['_attached']:
                cst = self.state(C, tq)
                if cst is None or cst['a'] <= 0: continue
                c = self.screen_img(C, tq); b = C.get('bleed', 3); w, h = C['w'] + 2 * b, C['h'] + 2 * b
                c = c.resize((w, h), Image.BILINEAR); m = Image.new('L', (w, h), 0)
                ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), C.get('radius', 6), fill=int(255 * cst['a'])); c.putalpha(m)
                im.alpha_composite(c, (round(ox + C['x'] - w / 2), round(oy + C['y'] - h / 2)))
        return im

    def frame(self, t, cover=None):
        """render one frame; with cover=[] it also appends the union alpha of content layers (everything except the desk,
        plates, panels and glows) and per-layer visible boxes, for the design gate"""
        tq = math.floor(t * self.afps + 1e-6) / self.afps; tc = tq if self.T.get('camera_on_twos') else t
        W, H = self.OW, self.OH; cx, cy, z, _ = self.cam(tc); k = z * self.scale_out
        cov = np.zeros((H, W), np.uint8) if cover is not None else None; seen = []
        to_screen = lambda x, y: ((x - cx) * k + W / 2, (y - cy) * k + H / 2)
        bw, bh, (ox, oy) = self.bg_world; sx = min(self.bg.width / bw, self.bg.height / bh)   # texture px per world px: the texture covers the whole world in both axes
        x0, y0 = (cx - W / 2 / k - ox) * sx, (cy - H / 2 / k - oy) * sx
        frame = self.bg.transform((W, H), Image.EXTENT, (x0, y0, x0 + W / k * sx, y0 + H / k * sx), Image.BILINEAR).convert('RGBA')
        lx, ly = self.light
        for L in self.layers:
            if L['type'] == 'screen': continue
            self._tq = tq   # a parented marker keeps its own timing; its points are mapped through the parent in draw_marker
            st = self.state({k2: v for k2, v in L.items() if k2 != 'parent'} if L['type'] == 'marker' else L, tq)
            if st is None or st['a'] <= 0.01 or st['s'] <= 0.005: continue
            X, Y = to_screen(st['x'], st['y']); S = st['s'] * k
            if L['type'] == 'marker':
                self.draw_marker(frame, L, st, to_screen, k)
                if cov is not None and L['shape'] != 'highlight':
                    q = [to_screen(*pp) for pp in (([L['pts'][:2], L['pts'][2:]]) if L['shape'] == 'arrow' else ([[L['pts'][0] - L['pts'][2], L['pts'][1] - L['pts'][3]], [L['pts'][0] + L['pts'][2], L['pts'][1] + L['pts'][3]]] if L['shape'] == 'circle' else L['pts']))]
                    cv2.polylines(cov, [np.int32(q)], L['shape'] != 'arrow', 255, max(2, int(L.get('width', 12) * k)))
                continue
            self._rev = st['rev']; im = self.layer_image(L, tq)
            if im is None: continue
            big = im.width * im.height > 1.5e6
            if big: S = round(S, 2) or .01                      # big sheets: 1% scale steps -> transform cache hits during camera moves
            w, h = max(1, round(im.width * S * st['sx'])), max(1, round(im.height * S * st['sy']))
            if w * h > 40e6: continue
            if L['type'] in TEXTY and L.get('in', {}).get('fx') == 'wipe' and st['rev'] < 1:
                im = im.crop((0, 0, max(1, round(im.width * st['rev'])), im.height)); w = max(1, round(w * st['rev']))
            hgt = min(2.0, max(0.0, st['h'])); want_sh = L.get('shadow', L['type'] not in ('decor', 'glow') or 'engravings/' in L.get('src', '') or 'scraps/' in L.get('src', ''))
            dyn = bool(L.get('_attached')) or L['type'] == 'counter' or st['rev'] < 1
            tk = ('T', L['id'], w, h, round(st['r'] * 10), round(st['a'] * 40), round(hgt * 20), round(k, 3))
            if not dyn and tk in self.tcache: im, sh, spad = self.tcache[tk]
            else:
                im = im.resize((w, h), Image.BILINEAR if (w < im.width) else Image.BICUBIC)
                if abs(st['r']) > .05: im = im.rotate(-st['r'], expand=True, resample=Image.BICUBIC)
                if st['a'] < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * st['a'])))
                sh, spad = (None, 0)
                if want_sh:
                    base = L.get('shadow_px', 7) * k; sh, spad = shadow_of(im, base * (1.2 + 3 * hgt), L.get('shadow_op', .34) * st['a'] * (1 - .35 * min(1, hgt)))
                if not dyn:
                    if len(self.tcache) > 500: self.tcache.pop(next(iter(self.tcache)))
                    self.tcache[tk] = (im, sh, spad)
            px, py = round(X - im.width / 2), round(Y - im.height / 2)
            if px > W or py > H or px + im.width < 0 or py + im.height < 0: continue
            if sh is not None:
                base = L.get('shadow_px', 7) * k
                frame.alpha_composite(sh, (round(px - spad + lx * base * (1 + 5 * hgt)), round(py - spad + ly * base * (1 + 5 * hgt))))
            frame.alpha_composite(im, (px, py))
            if cov is not None and L['type'] in ('plate', 'panel') and im.width * im.height > W * H * .25:   # a sheet over the previous scene hides what is under it
                a0 = np.array(im.getchannel('A')); xa, ya = max(0, px), max(0, py); xb, yb = min(W, px + im.width), min(H, py + im.height)
                if xb > xa and yb > ya:
                    cov[ya:yb, xa:xb] = np.where(a0[ya - py:yb - py, xa - px:xb - px] > 128, 0, cov[ya:yb, xa:xb])
                    seen[:] = [q for q in seen if not (q[4][0] >= xa and q[4][1] >= ya and q[4][2] <= xb and q[4][3] <= yb)]
            if cov is not None and L['type'] not in ('plate', 'panel', 'glow') and not L.get('backdrop'):
                a0 = np.array(im.getchannel('A')); xa, ya = max(0, px), max(0, py); xb, yb = min(W, px + im.width), min(H, py + im.height)
                if xb > xa and yb > ya:
                    sub = a0[ya - py:yb - py, xa - px:xb - px]; cov[ya:yb, xa:xb] = np.maximum(cov[ya:yb, xa:xb], sub)
                    vis = (sub > 128).sum()
                    if vis > 0: seen.append((L['id'], L.get('z', 0), L['type'], int(vis), (xa, ya, xb, yb), bool(L.get('hero')), L.get('_scene')))
        if cover is not None: cover.extend([cov, seen])
        if self.T.get('captions'): self.draw_captions(frame, t, W, H)
        out = frame.convert('RGB')
        if self.T.get('grain', True):
            n = self.noise[int(tq * self.afps) % 3].resize((W, H), Image.NEAREST); out = ImageChops.overlay(out, n)
        if self.T.get('vignette', True):
            if ('vig', W) not in self.cache:
                yy, xx = np.mgrid[0:H, 0:W]; d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
                self.cache[('vig', W)] = (1 - .16 * np.clip(d - .55, 0, 1) ** 1.5)[..., None].astype(np.float32)
            out = Image.fromarray((np.array(out).astype(np.float32) * self.cache[('vig', W)]).astype(np.uint8))
        if len(self.cache) > 600: self.cache = {k: v for k, v in self.cache.items() if not (isinstance(k, tuple) and len(k) == 3 and isinstance(k[0], int))}
        return out

    def draw_marker(self, frame, L, st, to_screen, k):
        rev = st['rev']
        if rev <= 0: return
        if L.get('parent'):   # marker points are pixels of the parent's original image (e.g. typeset.py highlight boxes)
            P = self.byid[L['parent']]; ps = self.state(P, self._tq)
            if ps is None: return
            ow, oh = P.get('_orig_size', P['_src_size']); f = P['_src_size'][0] / ow; c, sn = math.cos(math.radians(ps['r'])), math.sin(math.radians(ps['r']))
            def wp(x, y):
                lx, ly = (x - ow / 2) * f * ps['s'], (y - oh / 2) * f * ps['s']; return ps['x'] + lx * c - ly * sn, ps['y'] + lx * sn + ly * c
            base = to_screen; to_screen = lambda x, y: base(*wp(x, y)); k = k * f * ps['s']
        col = self.col(L.get('color'), 'accent'); wdt = max(2, round(L.get('width', 12) * k)); a = int(230 * st['a'])
        if L['shape'] == 'highlight':   # marker swipe over printed words: grows left to right, multiplied into the paper
            x0, y0, x1, y1 = L['pts']; (sx0, sy0), (sx1, sy1) = to_screen(x0, y0), to_screen(x0 + (x1 - x0) * rev, y1)
            if sx1 - sx0 < 2: return
            col = self.col(L.get('color'), 'accent2'); rr = random.Random(L['_seed']); box = (int(sx0) - 4, int(sy0) - 4, int(sx1) + 4, int(sy1) + 4)
            m = Image.new('L', (box[2] - box[0], box[3] - box[1]), 0); dm = ImageDraw.Draw(m); h = sy1 - sy0
            pts = [(4 + i * 6, 4 + rr.uniform(-.06, .06) * h) for i in range(int((sx1 - sx0) / 6) + 1)]
            pts += [(4 + i * 6, 4 + h + rr.uniform(-.06, .06) * h) for i in range(int((sx1 - sx0) / 6), -1, -1)]
            dm.polygon(pts, fill=int(255 * L.get('opacity', .85) * st['a']))
            reg = frame.crop(box); tint = Image.new('RGBA', reg.size, col + (255,)); mul = ImageChops.multiply(reg.convert('RGB'), tint.convert('RGB')).convert('RGBA')
            reg.paste(mul, (0, 0), m); frame.paste(reg, box[:2]); return
        lay = Image.new('RGBA', frame.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        if L['shape'] == 'circle': pts, head = ellipse_pts(*L['pts'], seed=L['_seed']), None
        elif L['shape'] == 'arrow': pts, head = arrow_pts(*L['pts'], bend=L.get('bend', .18))
        else: pts, head = [tuple(q) for q in L['pts']], None
        sp = [to_screen(*q) for q in partial(pts, rev)]
        if L.get('style') == 'brush':  # hand-painted stroke: tapered ends, varying pressure
            pp = np.array([to_screen(*q) for q in partial(pts, 1.0)]); dense = [tuple(pp[0])]
            for i in range(1, len(pp)):
                seg = max(1, int(np.linalg.norm(pp[i] - pp[i - 1]) / 2)); dense += [tuple(pp[i - 1] + (pp[i] - pp[i - 1]) * j / seg) for j in range(1, seg + 1)]
            m = max(1, int(len(dense) * rev))
            for i, q in enumerate(dense[:m]):
                u = i / max(1, len(dense) - 1); rad = wdt * .55 * (.35 + .65 * math.sin(math.pi * min(1, u * 1.1)) ** .5) * (.9 + .2 * math.sin(i * .07))
                d.ellipse((q[0] - rad, q[1] - rad, q[0] + rad, q[1] + rad), fill=col + (a,))
        else: d.line(sp, fill=col + (a,), width=wdt, joint='curve')
        for q in (sp[0], sp[-1]): d.ellipse((q[0] - wdt / 2, q[1] - wdt / 2, q[0] + wdt / 2, q[1] + wdt / 2), fill=col + (a,))
        if head and rev >= .98: d.line([to_screen(*q) for q in head], fill=col + (a,), width=wdt, joint='curve')
        frame.alpha_composite(lay)

    def screen_img(self, L, t):
        w, h = L['w'], L['h']; im = Image.new('RGBA', (w, h), self.col(L.get('bg'), 'screen') + (255,))
        for C in L['content']:
            c0 = self.time(C.get('t', 0)); c1 = self.time(C['until']) if 'until' in C else 1e9
            if not (c0 <= t < c1): continue
            lt = t - c0; kind = C['kind']
            if kind == 'video':
                if '_v' not in C: C['_v'] = Video(self.p(C['src']), (w, h), self.afps)
                im = C['_v'].at(lt * C.get('speed', 1))
            elif kind == 'image':
                if '_i' not in C: C['_i'] = Image.open(self.p(C['src'])).convert('RGBA').resize((w, h), Image.LANCZOS)
                im = C['_i'].copy()
            elif kind == 'fill': im = Image.new('RGBA', (w, h), hexrgb(C['color']) + (255,))
            elif kind == 'code':
                d = ImageDraw.Draw(im); sz = C.get('size', 18); f = font('JetBrainsMono.ttf', sz); chars = int(lt * C.get('cps', 40)); y = 10; n = 0; seg = ''
                for line in C['lines']:
                    seg = line[:max(0, chars - n)]; n += len(line)
                    if seg: d.text((12, y), seg, font=f, fill=(120, 130, 140) if line.lstrip().startswith(('//', '#')) else hexrgb(C.get('color', '#9fe2a0')))
                    y += int(sz * 1.4)
                    if n >= chars: break
                if int(lt * 4) % 2 == 0: cx = 12 + f.getlength(seg); d.rectangle((cx, y - int(sz * 1.4) + 2, cx + sz * .5, y - 6), fill=(220, 230, 220))
            elif kind == 'steps':
                d = ImageDraw.Draw(im); rows, cols = C.get('rows', 4), 16; step = int(lt * C.get('bpm', 120) / 15) % cols
                pat = C.get('pattern', ['x...x...x...x...', '....x.......x...', '..x...x...x...xx', 'x..x..x.x..x..x.'])
                cw, ch = (w - 20) / cols, (h - 30) / rows; cc = [hexrgb(c) for c in C.get('colors', ['#ff7a1a', '#ffd23f', '#3fa7d6', '#e84855'])]
                for rI in range(rows):
                    for cI in range(cols):
                        fill = cc[rI] if pat[rI][cI] == 'x' else (40, 44, 52)
                        if cI == step: fill = tuple(min(255, v + 90) for v in fill)
                        d.rectangle((10 + cI * cw + 1, 20 + rI * ch + 2, 10 + (cI + 1) * cw - 2, 20 + (rI + 1) * ch - 3), fill=fill)
            elif kind == 'sprite':
                fr = C['frames'][int(lt * C.get('fps', 4)) % len(C['frames'])]; sp = sprite_img(fr, C['palette'], C.get('cell', 10))
                bob = int(abs(math.sin(lt * 6)) * C.get('bob', 6)); im.alpha_composite(sp, ((w - sp.width) // 2, (h - sp.height) // 2 - bob + C.get('dy', 0)))
        if L.get('scanlines', True):
            a = np.array(im); a[::3, :, :3] = (a[::3, :, :3] * .85).astype(np.uint8); im = Image.fromarray(a)
        return im

    def draw_captions(self, frame, t, W, H):
        C = self.T['captions']; k = self.scale_out; f = font(C.get('font', 'Anton-Regular.ttf'), C.get('size', 64) * k)
        if t > self.time(C.get('until', 1e9)): return
        if not hasattr(self, '_chunks'):
            self._chunks, cur = [], []
            for w in self.words:
                cur.append(w)
                if len(cur) >= C.get('max_words', 3) or w['w'][-1] in '.,!?': self._chunks.append(cur); cur = []
            if cur: self._chunks.append(cur)
        rep = C.get('replace', {})
        for ch in self._chunks:
            if ch[0]['s'] - .05 <= t < ch[-1]['e'] + .12:
                parts = [rep.get(w['w'].strip('.,!?'), w['w'].strip('.,!?')).upper() for w in ch]
                act = max([j for j, w in enumerate(ch) if w['s'] <= t] or [0]); keep = [j for j, q in enumerate(parts) if q]
                act = max([j for j in keep if j <= act] or [keep[0] if keep else 0]); parts = [parts[j] for j in keep]; act = keep.index(act) if act in keep else 0
                gap = 22 * k; tw = sum(f.getlength(q) for q in parts) + gap * (len(parts) - 1); x = (W - tw) / 2; y = H * C.get('y', .88); d = ImageDraw.Draw(frame)
                for j, q in enumerate(parts):
                    d.text((x, y), q, font=f, fill=self.pal.get('accent') if j == act else self.pal.get('ink', (20, 20, 20)), stroke_width=max(2, round(9 * k)), stroke_fill=self.pal.get('paper', (250, 247, 238)))
                    x += f.getlength(q) + gap
                return

    # ---------------------------------------------------------- layout check
    def check(self, quiet=False):
        """Layout report -> list of (kind, t, id_a, id_b, info). Errors block the render; warnings are printed.
        kinds: overlap, cut, arrow (aimless doodle arrow), stub (marker arrow too short), wedge (triangle corner on a
        sheet), tail, captions; warnings: hidden (object mostly under the hero), ambiguous word refs, packshot early."""
        found = []; step = 1 / self.afps; seen = set()
        def bbox(L, st):
            w, h = L.get('_src_size', (0, 0))
            if L['type'] in ('strip', 'stamp', 'text') and L['_img'] is not None: w, h = L['_img'].size
            s = st['s']; r = math.radians(st['r']); cw = abs(w * s * math.cos(r)) + abs(h * s * math.sin(r)); chh = abs(w * s * math.sin(r)) + abs(h * s * math.cos(r))
            return (st['x'] - cw / 2, st['y'] - chh / 2, st['x'] + cw / 2, st['y'] + chh / 2)
        def moving(L, t):
            return any(0 <= t - x < .7 for x in [L.get('in', {}).get('t', -9), L.get('out', {}).get('t', -9)] + [k['t'] for k in L['keys']])
        watch = [L for L in self.layers if L['type'] in TEXTY or L.get('hero')]
        objs = [L for L in self.layers if L['type'] in ('image', 'decor') and not L.get('hero') and not L.get('backdrop')]
        heroes = [L for L in self.layers if L.get('hero')]
        t = 0.0
        while t < self.dur:
            cur = []
            for L in watch:
                st = self.state(L, t)
                if st is not None and st['a'] > .3: cur.append((L, bbox(L, st)))
            for i in range(len(cur)):
                for j in range(i + 1, len(cur)):
                    (A, a), (B, b) = cur[i], cur[j]
                    if (A.get('hero') and B.get('hero')) or A.get('overlay') or B.get('overlay'): continue
                    if not (A['type'] in TEXTY or B['type'] in TEXTY): continue
                    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
                    small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1])) or 1
                    lim = .35 if (A.get('hero') or B.get('hero')) else .04
                    if ix / small > lim and (A['id'], B['id']) not in seen:
                        seen.add((A['id'], B['id'])); found.append(('overlap', round(t, 2), A['id'], B['id'], {'frac': ix / small, 'moving': moving(A, t) or moving(B, t), 'a': a, 'b': b}))
            cx, cy, z, _ = self.cam(t); vx0, vy0, vx1, vy1 = cx - self.W / 2 / z, cy - self.H / 2 / z, cx + self.W / 2 / z, cy + self.H / 2 / z
            for L, b in cur:
                if not moving(L, t) and L['type'] in TEXTY and (b[0] < vx0 - 4 or b[1] < vy0 - 4 or b[2] > vx1 + 4 or b[3] > vy1 + 4) and (L['id'], 'edge') not in seen:
                    seen.add((L['id'], 'edge')); found.append(('cut', round(t, 2), L['id'], None, {'box': b, 'view': (vx0, vy0, vx1, vy1)}))
            for H in heroes:   # an object resting mostly under the hero is invisible: move it or drop it
                hs = self.state(H, t)
                if hs is None or hs['a'] < .5 or moving(H, t): continue
                hb = bbox(H, hs)
                for O in objs:
                    if O.get('z', 0) >= H.get('z', 0) or (O['id'], 'hid') in seen or O.get('_scene') != H.get('_scene'): continue
                    os_ = self.state(O, t)
                    if os_ is None or os_['a'] < .5 or moving(O, t): continue
                    ob = bbox(O, os_); ar = max(1, (ob[2] - ob[0]) * (ob[3] - ob[1]))
                    ix = max(0, min(ob[2], hb[2] - (hb[2] - hb[0]) * .12) - max(ob[0], hb[0] + (hb[2] - hb[0]) * .12)) * max(0, min(ob[3], hb[3]) - max(ob[1], hb[1] + (hb[3] - hb[1]) * .1))
                    if ix / ar > .7: seen.add((O['id'], 'hid')); found.append(('hidden', round(t, 2), O['id'], H['id'], {'frac': ix / ar}))
            t += step * (2 if heroes else 1)
        stub = max(110, .07 * min(self.W, self.H))
        for L in self.layers:
            if L['type'] == 'decor' and 'arrow' in L.get('src', '') and not L.get('points_to'): found.append(('arrow', 0, L['id'], None, {}))
            if L['type'] == 'marker' and L['shape'] == 'arrow':
                x0, y0, x1, y1 = L['pts']; ln = math.hypot(x1 - x0, y1 - y0)
                if ln < stub: found.append(('stub', L.get('in', {}).get('t', 0), L['id'], None, {'len': ln, 'min': stub}))
            if L['type'] == 'panel' or (L['type'] in ('decor', 'image') and 'scraps/' in L.get('src', '')):
                wq = wedge_score(L['_img'])
                if wq: found.append(('wedge', 0, L['id'], None, {'n': wq}))
        if self.vo_end and self.dur - self.vo_end > 1.8: found.append(('tail', self.dur, None, None, {'tail': self.dur - self.vo_end}))
        if not self.T.get('captions') and not self.T.get('captions_reason'): found.append(('captions', 0, None, None, {}))
        warn_kinds = ('hidden',)
        errs = [f for f in found if f[0] not in warn_kinds]
        if not quiet:
            msg = {'overlap': lambda f: f'{f[1]:5.2f}s OVERLAP {f[2]} x {f[3]} ({f[4]["frac"]:.0%}{", while moving" if f[4]["moving"] else ""})',
                   'cut': lambda f: f'{f[1]:5.2f}s CUT BY FRAME {f[2]}',
                   'arrow': lambda f: f'DECOR ARROW {f[2]}: an arrow must point at something: use a marker arrow from -> to',
                   'stub': lambda f: f'ARROW STUB {f[2]}: {f[4]["len"]:.0f}px long (min {f[4]["min"]:.0f}): move the ends apart or circle the target instead',
                   'wedge': lambda f: f'WEDGE {f[2]}: {f[4]["n"]} triangular corner piece(s) stick out of the sheet',
                   'hidden': lambda f: f'{f[1]:5.2f}s WARNING HIDDEN {f[2]}: {f[4]["frac"]:.0%} of it rests under hero {f[3]}: move it out or drop it',
                   'tail': lambda f: f'TAIL {f[4]["tail"]:.1f}s after the last word: use "duration": "auto"',
                   'captions': lambda f: 'CAPTIONS off: karaoke captions stay on unless the user asked for none'}
            for w in self.warnings + self.plate_gaps(): print('WARNING', w)
            for f in found: print(msg[f[0]](f))
            print('layout OK: no text overlaps, nothing cut by the frame, no stubs, no wedges' if not errs else f'{len(errs)} layout issue(s)')
        return errs

    def plate_gaps(self, max_gap=.15):
        """v8.1: an empty plate on a scene change: time between a scene's plate landing and its first object landing"""
        out = []
        for S in self.scenes:
            mine = [L for L in self.layers if L.get('_scene') == S['id'] and 'in' in L]
            land = lambda L: L['in']['t'] + L['in'].get('dur', DUR.get(L['in'].get('fx', 'pop'), .3))
            pl = [land(L) for L in mine if L['type'] == 'plate']; ob = [land(L) for L in mine if L['type'] != 'plate']
            if pl and ob and min(ob) - min(pl) > max_gap:
                out.append(f'EMPTY PLATE {S["id"]}: plate alone for {min(ob) - min(pl):.2f}s at {min(pl):.2f}s: start the first objects earlier (with the plate)')
        return out

    # ---------------------------------------------------------- audio
    def sfx(self, path):
        SR = 48000; N = int((self.dur + 1) * SR); mix = np.zeros(N, np.float32); rng = np.random.default_rng(3)
        def bp(x, lo, hi):
            X = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / SR); X[(fr < lo) | (fr > hi)] = 0; return np.fft.irfft(X, len(x)).astype(np.float32)
        def add(t, x):
            i = int(max(0, t) * SR); j = min(N, i + len(x)); mix[i:j] += x[:j - i]
        def noise(d, lo, hi): return bp(rng.normal(0, 1, int(d * SR)), lo, hi)
        for t, kind, vol in self.events:
            if kind == 'slide': n = int(.26 * SR); add(t - .08, noise(.26, 900, 6000) * np.sin(np.linspace(0, np.pi, n)) ** 1.5 * .13 * vol)
            elif kind == 'thud':
                n = int(.3 * SR); tt = np.arange(n) / SR
                add(t, (np.sin(2 * np.pi * (90 - 40 * tt / .3) * tt) * np.exp(-tt * 16) + noise(.3, 200, 3000) * np.exp(-tt * 50) * .6) * .2 * vol)   # v8.1: was .42, louder than the voice
            elif kind == 'tick': n = int(.05 * SR); tt = np.arange(n) / SR; add(t, noise(.05, 2000, 9000) * np.exp(-tt * 110) * .14 * vol)
            elif kind == 'scribble': n = int(.35 * SR); tt = np.arange(n) / SR; add(t, noise(.35, 2500, 7000) * (.6 + .4 * np.sin(tt * 2 * np.pi * 11)) * np.sin(np.linspace(0, np.pi, n)) * .06 * vol)
            elif kind == 'tape': n = int(.3 * SR); tt = np.arange(n) / SR; add(t, noise(.3, 1500, 8000) * (rng.random(n) > .7) * np.exp(-tt * 6) * .1 * vol)
            elif kind == 'whoosh': n = int(.6 * SR); add(t - .05, noise(.6, 250, 2200) * np.sin(np.linspace(0, np.pi, n)) ** 2 * .14 * vol)
            elif kind == 'click': n = int(.06 * SR); tt = np.arange(n) / SR; add(t, (noise(.06, 1500, 6000) * np.exp(-tt * 140) + np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 200) * .3) * .22 * vol)
            elif kind == 'roll': n = int(1.2 * SR); tt = np.arange(n) / SR; add(t, noise(1.2, 60, 900) * (1 + .5 * np.sin(2 * np.pi * 9 * tt)) * np.sin(np.linspace(0, np.pi, n)) * .09 * vol)
        for c in self.camera[1:]:
            if c.get('sfx') == 'whoosh': n = int(.45 * SR); add(c['t'] - .1, noise(.45, 300, 2500) * np.sin(np.linspace(0, np.pi, n)) ** 2 * .11)
        mix += noise(self.dur + 1, 80, 1200) * .004; np.clip(mix, -1, 1, out=mix)
        subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', path], input=mix.tobytes(), check=True)

    def mix_audio(self, path):
        """SFX + VO (+ optional music), two-pass loudnorm to -14 LUFS / -1.5 dBTP"""
        sfx = path + '.sfx.wav'; self.sfx(sfx)
        vo = self.p(self.T['audio']['vo']) if self.T.get('audio', {}).get('vo') else None
        mus = self.p(self.T['audio']['music']) if self.T.get('audio', {}).get('music') else None
        ins = ['-i', sfx] + (['-i', vo] if vo else []) + (['-i', mus] if mus else [])
        parts = [f'[0:a]volume={self.T.get("audio", {}).get("sfx_vol", 0.64)}[s]']; tags = '[s]'; k = 1
        if vo: parts.append(f'[{k}:a]aresample=48000[v]'); tags += '[v]'; k += 1
        if mus: parts.append(f'[{k}:a]aresample=48000,volume={self.T["audio"].get("music_vol", 0.18)}[m]'); tags += '[m]'
        pre = ';'.join(parts) + f';{tags}amix=inputs={tags.count("[")}:normalize=0,atrim=0:{self.dur}'
        r = subprocess.run([FF, '-hide_banner', '-nostats', *ins, '-filter_complex', pre + ',loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
        js = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
        # v8: exact gain to -14 LUFS + true-peak limiter. loudnorm's linear mode silently falls back to a smaller gain
        # when the peaks would clip, which left short clips at -15 .. -16.5 LUFS in the v7 / v8 tests.
        gain = -14.0 - float(js['input_i'])
        lim = 'alimiter=limit=0.79:level=false:attack=2:release=60'   # 0.79 = -2 dBFS sample peak, true peak about -1.5
        subprocess.run([FF, '-y', '-loglevel', 'error', *ins, '-filter_complex', pre + f',volume={gain:.2f}dB,{lim}', '-ar', '48000', path], check=True)
        def lufs(f):   # integrated loudness as ebur128 reports it (what QA measures)
            t = subprocess.run([FF, '-hide_banner', '-nostats', '-i', f, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
            return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', t)[-1])
        for _ in range(4):   # the limiter eats part of every boost: trim again (overshooting a little) until within 0.2 LU
            got = lufs(path)
            if abs(got + 14) <= .2: break
            tmp = path + '.t.wav'; os.replace(path, tmp)
            subprocess.run([FF, '-y', '-loglevel', 'error', '-i', tmp, '-af', f'volume={(-14 - got) * 1.6:.2f}dB,{lim}', '-ar', '48000', path], check=True); os.remove(tmp)
        os.remove(sfx)

    def render(self, out, tl_path, jobs=0):
        """frames rendered in parallel chunks (one process each), concatenated without re-encoding"""
        import tempfile, shutil, concurrent.futures as cf
        n = int(math.ceil(self.dur * self.fps)); jobs = jobs or max(1, min(8, (os.cpu_count() or 2) - 1, n // 24 or 1))
        tmp = tempfile.mkdtemp(prefix='vox_'); bounds = [round(n * i / jobs) for i in range(jobs + 1)]
        segs = [os.path.join(tmp, f'seg{i:02d}.mp4') for i in range(jobs)]
        with cf.ProcessPoolExecutor(jobs) as ex:
            futs = [ex.submit(_render_chunk, tl_path, self.draft, bounds[i], bounds[i + 1], segs[i]) for i in range(jobs)]
            for f in cf.as_completed(futs): f.result()
        lst = os.path.join(tmp, 'list.txt'); open(lst, 'w').write(''.join(f"file '{q.replace(os.sep, '/')}'\n" for q in segs))
        audio = os.path.join(tmp, 'mix.wav'); self.mix_audio(audio)
        subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                        '-c:a', 'aac', '-b:a', '192k', '-t', str(self.dur), '-movflags', '+faststart', out], check=True)
        shutil.rmtree(tmp, ignore_errors=True); print('->', out, f'({jobs} processes)')

    # ---------------------------------------------------------- stills and the design gate
    def still_times(self, spec):
        """'scenes': start (+0.15 s after the scene's first entrance), middle and end (-0.35 s) of every scene;
        'beats': the same for every panel / plate entrance; or a list of seconds"""
        if spec in ('scenes', 'beats'):
            spans = [(S['id'], S['t0'], S['t1']) for S in self.scenes] if (spec == 'scenes' and self.scenes) else []
            if not spans:
                ts = sorted({L['in']['t'] for L in self.layers if L['type'] in ('panel', 'plate') and 'in' in L} | {0.0}); ts.append(self.dur)
                spans = [(f'b{i + 1}', a, b) for i, (a, b) in enumerate(zip(ts, ts[1:])) if b - a > .3]
            out = []
            for sid, a, b in spans:
                out += [(f'{sid} start', a + min(.6, (b - a) * .2)), (f'{sid} mid', (a + b) / 2), (f'{sid} end', max(a, b - .35))]
            return out
        return [(f'{float(x):.2f}s', float(x)) for x in spec.split(',')]

    def stills(self, spec, path):
        items = self.still_times(spec); ims = [self.frame(t) for _, t in items]; w, h = ims[0].size; cols = 3 if spec in ('scenes', 'beats') else min(4, len(ims))
        rows = math.ceil(len(ims) / cols); sheet = Image.new('RGB', (w * cols, h * rows), 'white'); d = ImageDraw.Draw(sheet)
        for i, ((lab, t), im) in enumerate(zip(items, ims)):
            sheet.paste(im, ((i % cols) * w, (i // cols) * h)); d.text(((i % cols) * w + 8, (i // cols) * h + 6), f'{lab} {t:.2f}s', fill=(255, 0, 0), font=font('Inter.ttf', 22))
        sheet.save(path, quality=88); print('->', path)

    def gate(self, outdir, fill_min=.55, empty_max=.07, match_min=.45):
        """Design gate: for every scene with a design frame, the final still (scene end - 0.35 s) is put next to the
        design ("design | final") and measured. fill = share of the content zone covered by content layers (all
        objects, hero, text, grids, inserts; not desk / plates / panels / glows); empty = biggest empty square as a
        share of the frame; layers by depth band; match = similarity of the design and the final at 1/20 size
        (structure + colour). A scene fails when fill < fill_min, empty > empty_max or match < match_min."""
        os.makedirs(outdir, exist_ok=True); report = []; ok_all = True
        for S in self.scenes:
            t = max(S['t0'], S['t1'] - .35); cov = []; im = self.frame(t, cover=cov); mask, seen = cov
            W, H = im.size; m = int(min(W, H) * .04); zone = np.zeros((H, W), bool); zone[m:H - m, m:W - m] = True
            if self.T.get('captions'): cy = int(H * self.T['captions'].get('y', .88) if isinstance(self.T['captions'], dict) else H * .88); zone[max(0, cy - int(H * .02)):min(H, cy + int(H * .07))] = False
            filled = (mask > 100) & zone; fill = filled.sum() / zone.sum()
            empty = (~(mask > 100) & zone).astype(np.uint8); dist = cv2.distanceTransform(empty, cv2.DIST_C, 3); side = 2 * dist.max(); emp = side * side / (W * H)
            seen = [q for q in seen if q[6] in (None, S['id'])]   # v8.1: pieces of earlier scenes peeking out under the plate do not count
            zs = sorted({q[1] for q in seen}); bands = {}
            for lid, z, typ, vis, box, hero, _ in seen:
                if typ in ('strip', 'stamp', 'text', 'counter', 'rect', 'poly'): band = 'text'
                elif hero: band = 'hero'
                else: band = ['back', 'mid', 'front'][min(2, int(3 * zs.index(z) / max(1, len(zs))))]
                bands[band] = bands.get(band, 0) + 1
            objs = sum(v for k, v in bands.items() if k in ('back', 'mid', 'front'))
            match = None; panel = im
            if S['design'] and os.path.exists(S['design']):
                D = Image.open(S['design']).convert('RGB').resize((W, H), Image.LANCZOS)
                a1 = cv2.resize(np.array(D), (W // 20, H // 20), interpolation=cv2.INTER_AREA).astype(np.float32); a2 = cv2.resize(np.array(im), (W // 20, H // 20), interpolation=cv2.INTER_AREA).astype(np.float32)
                g1, g2 = a1.mean(2), a2.mean(2); g1 = (g1 - g1.mean()) / (g1.std() + 1e-6); g2 = (g2 - g2.mean()) / (g2.std() + 1e-6)
                struct = float((g1 * g2).mean()); col = 1 - float(np.abs(a1 - a2).mean() / 80); match = round(max(0, .6 * struct + .4 * max(0, col)), 2)
                panel = Image.new('RGB', (W * 2 + 20, H + 60), (255, 255, 255)); panel.paste(D, (0, 60)); panel.paste(im, (W + 20, 60))
                dd = ImageDraw.Draw(panel); fz = font('Inter.ttf', 30); dd.text((10, 14), f'{S["id"]}  design', fill=(0, 0, 0), font=fz); dd.text((W + 30, 14), f'final {t:.2f}s', fill=(0, 0, 0), font=fz)
            fails = [x for x, bad in (('fill', fill < fill_min), ('empty', emp > empty_max), ('match', match is not None and match < match_min)) if bad]
            ok_all &= not fails
            row = {'scene': S['id'], 't': round(t, 2), 'fill': round(float(fill), 2), 'empty': round(float(emp), 3), 'objects': objs, 'bands': bands, 'match': match, 'pass': not fails, 'fails': fails}
            report.append(row); panel.save(os.path.join(outdir, f'{S["id"]}_design_vs_final.jpg'), quality=85)
            print(f"{S['id']:6s} t {t:5.2f}  fill {fill:.2f}  empty {emp:.3f}  objects {objs:2d} {bands}  match {match}  {'PASS' if not fails else 'FAIL: ' + ', '.join(fails)}")
        json.dump(report, open(os.path.join(outdir, 'gate.json'), 'w'), indent=1)
        print('design gate', 'PASSED' if ok_all else 'FAILED: fix the failing scenes (fill the gaps the design has, follow its composition)', '->', outdir)
        return ok_all

def _render_chunk(tl_path, draft, a, b, seg):
    E = Engine(tl_path, draft=draft); W, H = E.OW, E.OH
    enc = subprocess.Popen([FF, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(E.fps), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23' if draft else '17', '-pix_fmt', 'yuv420p', seg], stdin=subprocess.PIPE)
    for i in range(a, b): enc.stdin.write(E.frame(i / E.fps).tobytes())
    enc.stdin.close(); enc.wait()

def autofix(tl_path, rounds=6):
    """Fix what the check finds, in the timeline file itself: exits that cross a label become short fades
    and leave earlier, entrances that cross a label are delayed a little, labels overlapping at rest are pushed
    apart, labels cut by the frame are pulled inside. Re-checks after each round. (Top-level layers only.)"""
    tries = {}
    for rnd in range(rounds):
        E = Engine(tl_path, draft=True); found = E.check(quiet=True)
        T = json.load(open(tl_path, encoding='utf-8')); raw = {L.get('id'): L for L in T.get('layers', [])}; changed = False
        for kind, t, a, b, info in found:
            if kind == 'tail': T['duration'] = 'auto'; changed = True
            elif kind == 'captions' and T.get('captions') is None: T.pop('captions', None); changed = True
            elif kind == 'arrow' and a in raw: T['layers'].remove(raw[a]); changed = True
            elif kind == 'cut' and a in raw:
                L = raw[a]; (x0, y0, x1, y1), (v0, w0, v1, w1) = info['box'], info['view']; m = 30
                L['x'] = L.get('x', 0) + (max(0, v0 + m - x0) - max(0, x1 - (v1 - m))); L['y'] = L.get('y', 0) + (max(0, w0 + m - y0) - max(0, y1 - (w1 - m))); changed = True
            elif kind == 'overlap':
                A, B = E.byid[a], E.byid[b]
                for X in (A, B):
                    if 'out' in X and 0 <= t - X['out']['t'] < .7 and X['id'] in raw:
                        o = raw[X['id']]['out']; o['fx'] = 'fade'; o['dur'] = .15; o['t'] = round(E.time(o['t']) - .15, 2); changed = True; break
                else:
                    later = max((A, B), key=lambda X: X.get('in', {}).get('t', -1)); key = (a, b); tries[key] = tries.get(key, 0) + 1
                    if later['type'] not in TEXTY and (A if later is B else B)['type'] in TEXTY: later = A if later is B else B
                    if info['moving'] and tries[key] == 1 and 'in' in later and later['id'] in raw and 0 <= t - later['in']['t'] < .7:
                        i = raw[later['id']]['in']; i['t'] = round(E.time(i['t']) + .2, 2); i['fx'] = 'pop' if i.get('fx') in ('slide', 'drop') else i.get('fx', 'pop'); changed = True
                    elif later['id'] in raw and later['type'] in TEXTY:
                        oa, ob = (info['b'], info['a']) if later is B else (info['a'], info['b'])
                        dy = (ob[3] - oa[1] + 40) if (oa[1] + oa[3]) / 2 > (ob[1] + ob[3]) / 2 else -(oa[3] - ob[1] + 40)
                        raw[later['id']]['y'] = raw[later['id']].get('y', 0) + dy; changed = True
        if not changed: break
        json.dump(T, open(tl_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    return Engine(tl_path, draft=True).check()

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('timeline'); ap.add_argument('--draft', action='store_true'); ap.add_argument('--stills'); ap.add_argument('--out')
    ap.add_argument('--check', action='store_true'); ap.add_argument('--fix', action='store_true'); ap.add_argument('--force', action='store_true'); ap.add_argument('--jobs', type=int, default=0)
    ap.add_argument('--gate', action='store_true', help='design gate: design | final per scene + fill / empty / match metrics'); ap.add_argument('--full', action='store_true', help='stills / gate at full resolution')
    a = ap.parse_args(); base = os.path.splitext(a.timeline)[0]
    if a.check:
        autofix(a.timeline) if a.fix else Engine(a.timeline, draft=True).check()
    elif a.gate:
        ok = Engine(a.timeline, draft=not a.full).gate(base + '_gate')
        if not ok: raise SystemExit(1)
    elif a.stills:
        E = Engine(a.timeline, draft=not a.full); os.makedirs(base + '_stills', exist_ok=True)
        E.stills(a.stills, base + '_stills/' + (a.stills if a.stills in ('scenes', 'beats') else 'sheet') + '.jpg')
    else:
        E = Engine(a.timeline, draft=a.draft); problems = E.check()
        if problems and not a.force:
            raise SystemExit('fix the issues above (try --check --fix) or pass --force for a throwaway preview; final videos must pass --check')
        E.render(a.out or base + ('_draft.mp4' if a.draft else '.mp4'), a.timeline, a.jobs)
