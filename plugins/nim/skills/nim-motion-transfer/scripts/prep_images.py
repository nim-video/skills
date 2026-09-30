#!/usr/bin/env python3
"""Make character images acceptable to Seedance: aspect ratio within 2:5..5:2.

Out-of-range images are padded (never cropped) with their own edge colour up to the limit.
Usage: prep_images.py OUT_DIR IMG [IMG ...]   → OUT_DIR/<name>.png per image; prints JSON.
"""
import json, os, sys
from PIL import Image

LO, HI = 2 / 5, 5 / 2


def main():
    out_dir, paths = sys.argv[1], sys.argv[2:]
    os.makedirs(out_dir, exist_ok=True)
    report = []
    for p in paths:
        im = Image.open(p).convert("RGB"); w, h = im.size; r = w / h
        nw, nh = (w, round(w / HI) + 1) if r > HI else (round(h * LO) + 1, h) if r < LO else (w, h)
        if (nw, nh) != (w, h):
            bg = Image.new("RGB", (nw, nh), im.getpixel((0, 0)))
            bg.paste(im, ((nw - w) // 2, (nh - h) // 2)); im = bg
        dst = os.path.join(out_dir, os.path.splitext(os.path.basename(p))[0] + ".png"); im.save(dst)
        report.append({"src": p, "size": [w, h], "out": dst, "out_size": list(im.size), "padded": (nw, nh) != (w, h)})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
