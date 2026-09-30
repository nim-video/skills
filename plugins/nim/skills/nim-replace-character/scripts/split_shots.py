#!/usr/bin/env python3
"""Split the prepared video into shots (frame-exact) and draw the review sheets.

Cuts come from three frame-to-frame signals on a 96x54 thumbnail: the gray difference d, the
colour-histogram distance h and the share f of pixels that changed by more than 20 grey levels.
Real cuts change the whole frame (f 0.21-0.73); a subtitle appearing, a gesture or fast motion
change only part of it (f <= 0.25 with small h). A ratio-to-local-median rule also finds a jump
between two near-identical shots, and a zoom / punch-in jump inside one shot counts as a cut too
(harmless when both parts go into the same group). Weaker jumps are `candidates` (shown as
before | after pairs) — the agent decides. `scores` gives d, h, f of every cut and candidate. Sheets:
  sheet_N.png      per shot: first / middle / last frame
  cuts.png         every cut and candidate as a before | after pair with frame and time
  timeline_N.png   one frame every 0.1 s (5 s per sheet) with its time — who is on screen when

Usage: split_shots.py VIDEO OUT_DIR [--cuts F1,F2,...] [--step 0.1]
  --cuts   replaces the detected cuts: frame numbers where a NEW shot starts (0 is implied);
           take them from `cuts` and, where the pair sheet shows a real cut, from `candidates`.
Prints JSON: fps, total_frames, cuts, candidates, shots [{index, start_frame, end_frame
(exclusive), start_s, end_s, frames}], sheets. Also writes OUT_DIR/shots.json (build_groups.py).
Needs a constant-frame-rate file (prepare_video.py output).
"""
import argparse, json, os, subprocess
import cv2, numpy as np
from PIL import Image, ImageDraw

SHOTS_PER_SHEET = 6
TW = 320
CUT_D, CUT_HD, CUT_H, CUT_F = 20.0, 8.0, 0.2, 0.2   # cut: f >= 0.2 and (d >= 20 or (h >= 0.2 and d >= 8))
CUT_ABS, CUT_RATIO, CUT_HMIN, CUT_FMIN = 6.0, 10.0, 0.08, 0.08  # between look-alike shots: d >= 6, 10x median, h >= 0.08, f >= 0.08
CAND_ABS, CAND_RATIO, CAND_H = 2.5, 5.0, 0.12


def probe(path):
    d = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate,nb_read_frames", "-of", "json", path],
        capture_output=True, text=True, check=True).stdout)["streams"][0]
    num, den = d["r_frame_rate"].split("/")
    return {"width": d["width"], "height": d["height"], "fps": float(num) / float(den),
            "frames": int(d["nb_read_frames"])}


def diff_series(path):
    """d, h, f per frame pair: gray difference, colour-histogram distance, share of pixels changed > 20."""
    cap, prev, d, h, f = cv2.VideoCapture(path), None, [], [], []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        t = cv2.resize(fr, (96, 54), interpolation=cv2.INTER_AREA)
        g = cv2.cvtColor(t, cv2.COLOR_BGR2GRAY).astype(np.float32)
        hist = cv2.normalize(cv2.calcHist([t], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3), None).flatten()
        if prev is not None:
            diff = np.abs(g - prev[0])
            d.append(float(diff.mean())); f.append(float((diff > 20).mean()))
            h.append(float(cv2.compareHist(hist, prev[1], cv2.HISTCMP_BHATTACHARYYA)))
        prev = (g, hist)
    return np.array(d), np.array(h), np.array(f)


def find_cuts(d, h, f, fps):
    """-> (cuts, candidates): frame numbers where a new shot would start."""
    w = max(int(fps), 2)
    cuts, cands = [], []
    for i in range(len(d)):
        med = max(float(np.median(d[max(0, i - w):i + w + 1])), 0.3)
        hard = f[i] >= CUT_F and (d[i] >= CUT_D or (h[i] >= CUT_H and d[i] >= CUT_HD))
        alike = d[i] >= CUT_ABS and d[i] >= CUT_RATIO * med and h[i] >= CUT_HMIN and f[i] >= CUT_FMIN
        if hard or alike:
            if cuts and i + 1 - cuts[-1] <= 2:            # neighbours: keep the stronger one
                if d[i] > d[cuts[-1] - 1]:
                    cuts[-1] = i + 1
            else:
                cuts.append(i + 1)
        elif (d[i] >= CAND_ABS and d[i] >= CAND_RATIO * med) or h[i] >= CAND_H:
            cands.append(i + 1)
    cands = [c for c in cands if all(abs(c - k) > 2 for k in cuts)]
    return cuts, [c for i, c in enumerate(cands) if i == 0 or c - cands[i - 1] > 1]   # one per run


def detect_cuts(path, fps):
    """Every cut and candidate of a video (assemble.py snaps to these)."""
    d, h, f = diff_series(path)
    cuts, cands = find_cuts(d, h, f, fps)
    return sorted(cuts + cands)


def grab(video, select, out_dir, width):
    """Decode the frames chosen by an ffmpeg select expression -> png paths in frame order."""
    for f in os.listdir(out_dir):
        if f.startswith("f_"):
            os.remove(os.path.join(out_dir, f))
    pat = os.path.join(out_dir, "f_%04d.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf",
                    f"select='{select}',scale={width}:-2", "-fps_mode", "passthrough", pat], check=True)
    return sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith("f_"))


def frames_at(video, frames, out_dir, width):
    fr = sorted(set(frames))
    png = grab(video, "+".join(f"eq(n\\,{n})" for n in fr), out_dir, width)
    return dict(zip(fr, png))


def main():
    a = argparse.ArgumentParser(); a.add_argument("video"); a.add_argument("out_dir")
    a.add_argument("--cuts", help="comma-separated frame numbers replacing the detected cuts")
    a.add_argument("--step", type=float, default=0.1)
    args = a.parse_args(); os.makedirs(args.out_dir, exist_ok=True)
    p = probe(args.video); fps, total = p["fps"], p["frames"]
    d_, h_, f_ = diff_series(args.video)
    auto, cands = find_cuts(d_, h_, f_, fps)
    cuts = [int(x) for x in args.cuts.split(",") if x.strip()] if args.cuts is not None else auto
    bounds = [0] + [c for c in sorted(set(cuts)) if 0 < c < total] + [total]
    shots = [{"index": i + 1, "start_frame": bounds[i], "end_frame": bounds[i + 1],
              "start_s": round(bounds[i] / fps, 3), "end_s": round(bounds[i + 1] / fps, 3),
              "frames": bounds[i + 1] - bounds[i]} for i in range(len(bounds) - 1)]
    th = round(TW * p["height"] / p["width"])
    sheets = []
    # 1) per shot: first / middle / last
    want = {s["index"]: [s["start_frame"], (s["start_frame"] + s["end_frame"] - 1) // 2,
                         s["end_frame"] - 1] for s in shots}
    png = frames_at(args.video, [n for v in want.values() for n in v], args.out_dir, TW)
    for k in range(0, len(shots), SHOTS_PER_SHEET):
        chunk = shots[k:k + SHOTS_PER_SHEET]
        sheet = Image.new("RGB", (3 * TW, len(chunk) * (th + 22)), "white"); d = ImageDraw.Draw(sheet)
        for r, s in enumerate(chunk):
            y = r * (th + 22)
            d.text((6, y + 5), f"shot {s['index']}  frames {s['start_frame']}-{s['end_frame'] - 1}"
                   f"  ({s['start_s']:.2f}-{s['end_s']:.2f} s)   first | middle | last", fill="black")
            for c, n in enumerate(want[s["index"]]):
                sheet.paste(Image.open(png[n]).convert("RGB").resize((TW, th)), (c * TW, y + 22))
        out = os.path.join(args.out_dir, f"sheet_{k // SHOTS_PER_SHEET + 1}.png"); sheet.save(out)
        sheets.append(out)
    # 2) every cut and candidate: frame before | frame after
    marks = sorted([(c, "cut") for c in auto] + [(c, "candidate") for c in cands])
    if marks:
        png = frames_at(args.video, [n for c, _ in marks for n in (c - 1, c)], args.out_dir, TW)
        per_row, pw = 2, 2 * TW
        rows = -(-len(marks) // per_row)
        sheet = Image.new("RGB", (per_row * pw, rows * (th + 22)), "white"); d = ImageDraw.Draw(sheet)
        for i, (c, kind) in enumerate(marks):
            x, y = (i % per_row) * pw, (i // per_row) * (th + 22)
            d.text((x + 6, y + 5), f"{kind} at frame {c} ({c / fps:.2f} s): {c - 1} | {c}", fill="black")
            for j, n in enumerate((c - 1, c)):
                sheet.paste(Image.open(png[n]).convert("RGB").resize((TW, th)), (x + j * TW, y + 22))
        out = os.path.join(args.out_dir, "cuts.png"); sheet.save(out); sheets.append(out)
    # 3) timeline: a frame every `step` seconds, 5 s per sheet
    every = max(1, round(args.step * fps))
    files = grab(args.video, f"not(mod(n\\,{every}))", args.out_dir, 192)
    tw, tth, per = 192, round(192 * p["height"] / p["width"]), int(round(5 / (every / fps)))
    for k in range(0, len(files), per):
        chunk = files[k:k + per]; cols = 10; rows = -(-len(chunk) // cols)
        sheet = Image.new("RGB", (cols * tw, rows * (tth + 14)), "white"); d = ImageDraw.Draw(sheet)
        for i, f in enumerate(chunk):
            x, y = (i % cols) * tw, (i // cols) * (tth + 14)
            d.text((x + 3, y + 1), f"{(k + i) * every / fps:.1f}s  f{(k + i) * every}", fill="black")
            sheet.paste(Image.open(f).convert("RGB").resize((tw, tth)), (x, y + 14))
        out = os.path.join(args.out_dir, f"timeline_{k // per + 1}.png"); sheet.save(out); sheets.append(out)
    for f in os.listdir(args.out_dir):
        if f.startswith("f_"):
            os.remove(os.path.join(args.out_dir, f))
    res = {"fps": fps, "total_frames": total, "width": p["width"], "height": p["height"],
           "cuts": auto, "candidates": cands, "shots": shots, "sheets": sheets,
           "scores": {str(c): {"d": round(float(d_[c - 1]), 1), "h": round(float(h_[c - 1]), 2),
                               "f": round(float(f_[c - 1]), 2)} for c in auto + cands}}
    json.dump(res, open(os.path.join(args.out_dir, "shots.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
