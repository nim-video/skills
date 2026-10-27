# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "numpy", "opencv-python-headless"]
# ///
"""Typeset printed matter as paper pieces: quote cards and newspaper clippings with REAL text (outlet, date,
headline or quote verbatim). Output: PNG (transparent outside the torn paper) + JSON with the size and the boxes
of the highlighted phrases (source px), for a `highlight` marker parented to the card.

usage: uv run typeset.py spec.json OUT_DIR
spec.json = list of items:
  {"kind": "quote", "name": "chronicle", "outlet": "San Francisco Chronicle", "kicker": "EDITORIAL",
   "text": "San Franciscans must decide if they want the most relentless and effective legislator in California.",
   "highlight": ["most relentless and effective legislator in California"], "byline": "Chronicle Editorial Board",
   "date": "May 9, 2026", "width": 1000}
  {"kind": "clipping", "name": "sb35", "outlet": "Los Angeles Times", "date": "Sept. 29, 2017",
   "headline": "Gov. Brown signs housing bills", "width": 640, "body_lines": 5, "tint": "news"}
  {"kind": "label", "name": "src", "text": "Source: CA Senate, sd11.senate.ca.gov", "size": 26}
Fonts: masthead UnifrakturMaguntia (blackletter, like a newspaper nameplate; not a logo copy), headline and
quote Playfair Display, small text Inter / Libre Franklin. No invented text: body copy of clippings is drawn
as grey lines, never fake words."""
import json, os, random, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); FD = os.path.normpath(os.path.join(HERE, '..', 'assets', 'fonts'))
F = lambda n, s: ImageFont.truetype(os.path.join(FD, n), int(s))
PAPER = {'white': (246, 242, 232), 'news': (236, 229, 210), 'cream': (243, 238, 226)}

def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= width or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def torn_alpha(w, h, seed, sides='ltrb', amp=7):
    r = np.random.default_rng(seed); m = np.zeros((h, w), np.uint8); pts = []
    jag = lambda n: cv2.GaussianBlur(r.normal(0, 1, (1, n)).astype(np.float32), (0, 0), 1.5).ravel() * amp
    top, bot, lef, rig = jag(w), jag(w), jag(h), jag(h); pad = amp + 2
    # each side runs only between the corners (pad .. size-pad): running it across the full width makes the outline
    # jump at the corners and leaves a triangle wedge outside the sheet (the v6 bug)
    for x in range(pad, w - pad): pts.append((x, pad + (abs(top[x]) if 't' in sides else 0)))
    for y in range(pad, h - pad): pts.append((w - pad - (abs(rig[y]) if 'r' in sides else 0), y))
    for x in range(w - pad - 1, pad - 1, -1): pts.append((x, h - pad - (abs(bot[x]) if 'b' in sides else 0)))
    for y in range(h - pad - 1, pad - 1, -1): pts.append((pad + (abs(lef[y]) if 'l' in sides else 0), y))
    cv2.fillPoly(m, [np.array(pts, np.int32)], 255); return cv2.GaussianBlur(m, (3, 3), 0)

def finish(im, seed, sides, tint):
    a = np.array(im).astype(np.float32); h, w = a.shape[:2]; rng = np.random.default_rng(seed)
    f = cv2.resize(rng.random((max(2, h // 40), max(2, w // 40))).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    a[..., :3] *= (1 - .05 * f)[..., None]; a[..., :3] += rng.normal(0, 3, (h, w, 1))
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGB').convert('RGBA'); out.putalpha(Image.fromarray(torn_alpha(w, h, seed, sides))); return out

def quote(s, seed):
    W = s.get('width', 1000); pad = int(W * .075); d0 = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    fq = F('PlayfairDisplay-Bold.ttf', W * .052); lines = wrap(d0, '“' + s['text'] + '”', fq, W - 2 * pad); lh = int(fq.size * 1.28)
    mh = int(W * .16); H = mh + pad + int(W * .04) + len(lines) * lh + int(W * .17)
    im = Image.new('RGB', (W, H), PAPER['cream']); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, mh), fill=(18, 18, 20)); fm = F('UnifrakturMaguntia.ttf', mh * .52)
    d.text((W / 2, mh / 2), s['outlet'], font=fm, fill=(246, 242, 232), anchor='mm')
    y = mh + int(pad * .55)
    if s.get('kicker'): d.text((pad, y), s['kicker'], font=F('Montserrat-ExtraBold.ttf', W * .022), fill=(35, 130, 79)); y += int(W * .05)
    boxes = []
    for i, ln in enumerate(lines):
        d.text((pad, y), ln, font=fq, fill=(22, 22, 26)); y += lh
    # highlight boxes: the phrase's words located line by line (a phrase may wrap onto the next line)
    y_end = y; y = mh + int(pad * .55) + (int(W * .05) if s.get('kicker') else 0)
    for hl in s.get('highlight', []):
        target = hl.split(); ti = 0; yy = y
        for ln in lines:
            ws = ln.split(); x = pad; run = None
            for w in ws:
                ww = d.textlength(w, font=fq); sp = d.textlength(' ', font=fq); clean = w.strip('“”.,"')
                if ti < len(target) and clean == target[ti].strip('.,"'):
                    run = (run[0] if run else x, x + ww); ti += 1
                elif run: boxes.append([int(run[0] - 6), int(yy + lh * .12), int(run[1] + 6), int(yy + lh * .98)]); run = None
                x += ww + sp
            if run: boxes.append([int(run[0] - 6), int(yy + lh * .12), int(run[1] + 6), int(yy + lh * .98)])
            yy += lh
    y = y_end + int(W * .03); d.line((pad, y, W - pad, y), fill=(200, 194, 180), width=2); y += int(W * .03)
    if s.get('byline'): d.text((pad, y), s['byline'], font=F('LibreFranklin-Medium.ttf', W * .028), fill=(30, 30, 30)); y += int(W * .04)
    if s.get('date'): d.text((pad, y), s['date'], font=F('Inter.ttf', W * .025), fill=(110, 110, 110))
    return finish(im, seed, s.get('torn', 'b'), 'cream'), boxes

def clipping(s, seed):
    W = s.get('width', 640); pad = int(W * .07); d0 = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    fh = F('PlayfairDisplay-Black.ttf', W * s.get('headline_scale', .085)); lines = wrap(d0, s['headline'], fh, W - 2 * pad); lh = int(fh.size * 1.15)
    nb = s.get('body_lines', 5); H = int(W * .13) + int(W * .06) + len(lines) * lh + int(W * .05) + nb * int(W * .045) + pad
    im = Image.new('RGB', (W, H), PAPER.get(s.get('tint', 'news'), PAPER['news'])); d = ImageDraw.Draw(im); y = int(pad * .6)
    fm = F('UnifrakturMaguntia.ttf', W * .062) if s.get('masthead', 'blackletter') == 'blackletter' else F('PlayfairDisplay-Bold.ttf', W * .05)
    d.text((W / 2, y), s['outlet'], font=fm, fill=(20, 20, 20), anchor='mt'); y += int(W * .085)
    d.line((pad, y, W - pad, y), fill=(40, 40, 40), width=2)
    d.text((W / 2, y + int(W * .012)), s.get('date', ''), font=F('Inter.ttf', W * .026), fill=(60, 60, 60), anchor='mt'); y += int(W * .05)
    d.line((pad, y, W - pad, y), fill=(40, 40, 40), width=1); y += int(W * .03)
    for ln in lines: d.text((pad, y), ln, font=fh, fill=(18, 18, 18)); y += lh
    y += int(W * .03); rr = random.Random(seed)
    for i in range(nb):   # body copy as grey type lines (no invented words)
        x1 = W - pad - (rr.randint(20, 120) if i == nb - 1 else rr.randint(0, 12))
        for x in range(pad, x1, 14): d.line((x, y + 6, min(x1, x + rr.randint(5, 11)), y + 6), fill=(120, 116, 108), width=int(W * .012))
        y += int(W * .045)
    return finish(im, seed, s.get('torn', 'ltrb'), 'news'), []

def label(s, seed):
    f = F(s.get('font', 'Inter.ttf'), s.get('size', 26)); d0 = ImageDraw.Draw(Image.new('RGB', (10, 10))); w = int(d0.textlength(s['text'], font=f)) + 36; h = int(f.size * 1.9)
    im = Image.new('RGB', (w, h), PAPER['white']); ImageDraw.Draw(im).text((18, h / 2), s['text'], font=f, fill=(40, 40, 40), anchor='lm'); return finish(im, seed, 'lr', 'white'), []

if __name__ == '__main__':
    spec = json.load(open(sys.argv[1], encoding='utf-8')); out = sys.argv[2]; os.makedirs(out, exist_ok=True); meta = {}
    for i, s in enumerate(spec):
        im, boxes = {'quote': quote, 'clipping': clipping, 'label': label}[s['kind']](s, 1000 + i * 7)
        p = os.path.join(out, s['name'] + '.png'); im.save(p); meta[s['name']] = {'file': s['name'] + '.png', 'size': list(im.size), 'highlights': boxes}
        print(p, im.size, f'{len(boxes)} highlight box(es)' if boxes else '')
    json.dump(meta, open(os.path.join(out, 'typeset.json'), 'w'), indent=1)
