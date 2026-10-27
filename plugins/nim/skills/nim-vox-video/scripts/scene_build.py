# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10"]
# ///
"""Storyboard row + layerize draft -> finished scene fragment (scene_NN.json). Replaces the per-worker build.py.

usage: uv run scene_build.py scenes/s03/row.json
  row.json (paths relative to the row file):
  {
   "draft": "scene_03.draft.json",        layerize --scene output (plate, items, hero, title1)
   "lay": "lay.json",                     layerize output (title slots)
   "out": "scene_03.json",
   "plate_from": "left",                  bottom | left | right | top (alternate scene to scene)
   "title": ["THE HARD", "WORK"],         ink part, accent part ([] or null: no title strip)
   "title_at": "@hard",
   "name": {"text": "Scott Wiener, State Senator", "x": 540, "y": 1735, "rot": -2, "at": "@hard+0.1"},
   "hero_at": "@And#1", "hero": {"size": 820},          optional overrides of the hero layer
   "enter": {"pen": "@do", "glasses": ["@do-0.1", "pop"]},   entrance time [and fx] per item (default: layerize's)
   "actions": {"lamp": {"glow": "@work"}, "watch": {"swing": "@hard", "until": "@writing"},
               "rocket": {"rise": "@moon-0.25"}, "cablecar": {"roll": "@San-0.25"}, "stamp": {"slam": "@signed"}},
   "drop": ["mug"],                       items to leave out
   "add": [ ...extra engine layers (counter, source strip, typeset cards, markers)... ],
   "hide_after": "@writing+0.45"          optional: remove the scene's pieces once the next plate covers them
  }
Prints the finished layer list in one line per layer. Then run the scene's test timeline through --check / --gate."""
import json, os, sys
from PIL import Image, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.join(HERE, '..', 'assets', 'fonts', 'Anton-Regular.ttf')
row_path = sys.argv[1]; base = os.path.dirname(os.path.abspath(row_path)); R = json.load(open(row_path, encoding='utf-8'))
P = lambda f: os.path.join(base, f)
F = json.load(open(P(R.get('draft', 'scene.draft.json')), encoding='utf-8'))
lay = json.load(open(P(R['lay']), encoding='utf-8')) if R.get('lay') else {}
W, H = lay.get('size', [1080, 1920])
F['layers'] = [L for L in F['layers'] if L['id'] not in R.get('drop', [])]
by = {L['id']: L for L in F['layers']}

def fit(parts, slot_w, frac=.9, cap=172):
    """largest Anton size whose text fits the slot width"""
    for s in range(200, 40, -2):
        f = ImageFont.truetype(FONT, s)
        if sum(f.getlength(p) for p in parts) + 60 <= slot_w * frac and s <= cap: return s
    return 40

def at(t, d): return f'{t}+{d}' if isinstance(t, str) else round(t + d, 2)

# plate: slides over the previous scene from the given side, lands just before the first word
if 'plate' in by and R.get('plate_from'):
    side = R['plate_from']; by['plate']['in'].update({'from': side, 'dist': H if side in ('bottom', 'top') else W})

for n, v in R.get('enter', {}).items():
    t, fx = (v, None) if isinstance(v, (str, int, float)) else (v[0], v[1])
    L = by[n]; L['in']['t'] = t
    if fx: L['in'] = {'t': t, 'fx': fx} | ({'dist': 500} if fx == 'drop' else {})

for n, act in R.get('actions', {}).items():
    L = by[n]
    if 'glow' in act:   # lamp switches on: a glow at the top of the lamp, flickering on its word
        F['layers'].append({'id': f'{n}_glow', 'type': 'glow', 'x': L['x'] + act.get('dx', 0), 'y': L['y'] - L['size'] * act.get('up', .3),
                            'r': act.get('r', 280), 'color': act.get('color', '#ffd98a'), 'strength': .55, 'z': L['z'] + .5,
                            'in': {'t': act['glow'], 'fx': 'flicker'}})
    if 'swing' in act:   # watch on a chain, sign on a nail: swings around its top
        w, h = Image.open(P(L['src'])).size if os.path.exists(P(L['src'])) else (L['size'], L['size'])
        L['wiggle'] = {'t': act['swing'], 'rot': act.get('rot', 9), 'freq': 1.1, 'decay': .8, 'pivot': act.get('pivot', [0, round(-.45 * h)])} | ({'until': act['until']} if 'until' in act else {})
    if 'rise' in act:   # rocket / balloon: flies up and out along a path
        L['keys'] = L.get('keys', []) + [{'t': act['rise'], 'path': [[L['x'] - 10, L['y'] - 500], [L['x'] - 60, -1300]], 'dur': act.get('dur', 1.5),
                                          'ease': 'in', 'orient': False, 'sfx': 'whoosh'}]
    if 'roll' in act:   # vehicle rolls in from the side
        L['in'] = {'t': act['roll'], 'fx': 'roll', 'from': act.get('from', 'right'), 'dist': 1200, 'dur': act.get('dur', 1.2)}
    if 'slam' in act: L['in'] = {'t': act['slam'], 'fx': 'slam'}
    if 'drop' in act: L['in'] = {'t': act['drop'], 'fx': 'drop', 'dist': 500}

if 'hero' in by:
    if R.get('hero_at') is not None: by['hero']['in'] = {'t': R['hero_at'], 'fx': 'slide', 'from': 'bottom', 'dist': 1100}
    by['hero'].update(R.get('hero', {}))

T = by.get('title1')
if T and R.get('title'):
    a, b = R['title']; slot = (lay.get('title_slots') or [{'w': W * .8}])[0]
    T['parts'] = [{'text': a + ' ', 'fg': 'ink'}, {'text': b, 'fg': 'accent'}]; T['size'] = fit([a + ' ', b], slot['w'])
    T['in'] = {'t': R.get('title_at', F['t0']), 'fx': 'wipe'}
elif T: F['layers'].remove(T)
F['layers'] = [L for L in F['layers'] if not (L['id'].startswith('title') and L['id'] != 'title1')]

if R.get('name'):
    N = R['name']; ztop = max(L.get('z', 0) for L in F['layers'])
    F['layers'].append({'id': 'name', 'type': 'strip', 'text': N['text'], 'font': 'SpecialElite.ttf', 'size': N.get('size', 36), 'bg': 'cream', 'fg': 'ink',
                        'x': N['x'], 'y': N['y'], 'rot': N.get('rot', -2), 'z': ztop + 1, 'overlay': True, 'in': {'t': N['at'], 'fx': 'wipe'}})
F['layers'] += R.get('add', [])
if R.get('hide_after'):
    for L in F['layers']: L['out'] = {'t': R['hide_after'], 'fx': 'fade', 'dur': .05}
for L in F['layers']: L.pop('_note', None)
json.dump(F, open(P(R.get('out', 'scene.json')), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for L in sorted(F['layers'], key=lambda L: L.get('z', 0)):
    print(f"{L['id']:14s} {L['type']:7s} z {L.get('z', 0):<5} in {L.get('in', {}).get('t', '-')} {L.get('in', {}).get('fx', '')}"
          + (' +action' if any(k in L for k in ('keys', 'wiggle')) or L['id'].endswith('_glow') else ''))
print('scene ->', P(R.get('out', 'scene.json')))
