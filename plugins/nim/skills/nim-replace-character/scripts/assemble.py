#!/usr/bin/env python3
"""Put the shots back in their original order, frame for frame.

Every shot of every group is cut out of that group's result and laid onto the original
timeline at exactly its original frame range; shots that were left out of every group are taken
from the original video. Where a shot sits in the result is found from the magenta separators
build_groups.py put between the shots (a separator the model dropped: the boundary is interpolated between
the separators that were found, or taken from a cut the result shows right there). Each shot is then resampled
by time to exactly its original number of frames, so every shot starts and ends on the original
frame. The output is silent — finalize.py adds the source audio.

Usage: assemble.py DRIVING GROUPS.json OUT.mp4 A=result_A.mp4 [B=result_B.mp4 ...]
Prints JSON: per group the result length vs group length and, per shot boundary, where it was
placed and how (marker | snap | interpolated); output frame count vs original.
Exit 0 ok, 3 frame count mismatch.
"""
import json, subprocess, sys
import cv2, numpy as np
from split_shots import detect_cuts, probe

SNAP_S = 0.6                     # search window for the fallbacks
MARK_S = 0.8                     # first pass: a separator counts for an expected one within 0.8 s
REFINE_S = 0.5                   # later passes: within 0.5 s of the position predicted from neighbouring anchors
MAX_INPUTS = 200


def marker_runs(path):
    """Runs of (mostly) solid magenta frames -> [(first, last_exclusive)]; frames next to a run
    that are still tinted (codec smear) belong to the separator, not to the shot."""
    cap, sc = cv2.VideoCapture(path), []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        t = cv2.resize(f, (64, 36), interpolation=cv2.INTER_AREA)
        b, g, r = t[..., 0], t[..., 1], t[..., 2]
        sc.append(float(((b > 170) & (r > 170) & (g < 90)).mean()))
    runs, i = [], 0
    while i < len(sc):
        if sc[i] > 0.5:
            j = i
            while j < len(sc) and sc[j] > 0.5:
                j += 1
            if j - i >= 1:
                a, b = i, j
                while a > 0 and sc[a - 1] > 0.12:
                    a -= 1
                while b < len(sc) and sc[b] > 0.12:
                    b += 1
                runs.append((a, b))
            i = j
        else:
            i += 1
    return runs


def trim_ranges(ranges, first, last):
    """Cut `first` frames off the start and `last` off the end of a list of frame ranges."""
    ranges = [list(r) for r in ranges]
    while first and ranges:
        n = min(first, ranges[0][1] - ranges[0][0]); ranges[0][0] += n; first -= n
        if ranges[0][0] >= ranges[0][1]: ranges.pop(0)
    while last and ranges:
        n = min(last, ranges[-1][1] - ranges[-1][0]); ranges[-1][1] -= n; last -= n
        if ranges[-1][0] >= ranges[-1][1]: ranges.pop()
    return [tuple(r) for r in ranges]


def group_pieces(g, res, fps, S):
    """Result frames of every run: [(ranges, length, src_start, src_len)] + report. `ranges` are the
    result frame ranges of the shot; a separator the model added inside a shot is cut out of it."""
    rf, R = res["fps"], res["frames"]
    k = (R / rf) / (g["frames"] / fps)                    # result length / group length
    scale = k * rf / fps                                  # result frames per group frame
    marks = marker_runs(g["result"])
    runs = g["runs"]
    # expected separators (group-frame centres): before every run but the first, and before the padding
    exp = [r["grp_start"] - S / 2 for r in runs[1:]]
    if g["pad_frames"]:
        exp.append(g["real_end"] + S / 2)
    tol = MARK_S * rf
    found = {}                                            # expected index -> (first, last_exclusive)
    for m in marks:                                       # each marker belongs to its nearest expected one
        c = (m[0] + m[1]) / 2
        d, i = min((abs(c - e * scale), i) for i, e in enumerate(exp))
        if d <= tol and (i not in found or d < abs(sum(found[i]) / 2 - exp[i] * scale)):
            found[i] = m
    cen = lambda m: (m[0] + m[1]) / 2
    for _ in range(3):                                    # unmatched separators: look near the position predicted from anchors
        free = [m for m in marks if m not in found.values()]
        moved = False
        for i, e in enumerate(exp):
            if i in found or not free:
                continue
            left = max((j for j in found if j < i), default=None)
            right = min((j for j in found if j > i), default=None)
            if left is not None and right is not None:
                x = cen(found[left]) + (e - exp[left]) * (cen(found[right]) - cen(found[left])) / (exp[right] - exp[left])
                lo, hi = cen(found[left]) + 1, cen(found[right]) - 1
            elif left is not None:
                x, lo, hi = cen(found[left]) + (e - exp[left]) * scale, cen(found[left]) + 1, 1e9
            elif right is not None:
                x, lo, hi = cen(found[right]) - (exp[right] - e) * scale, -1e9, cen(found[right]) - 1
            else:
                x, lo, hi = e * scale, -1e9, 1e9
            near = [m for m in free if lo < cen(m) < hi and abs(cen(m) - x) <= REFINE_S * rf]
            if near:
                found[i] = min(near, key=lambda m: abs(cen(m) - x)); free.remove(found[i]); moved = True
        if not moved:
            break
    pos, notes, cuts = {}, [], None
    for i, e in enumerate(exp):                           # place the boundaries
        if i in found:
            a, b = found[i]; pos[i] = ((a + b) / 2, "marker")
            continue
        left = max((j for j in found if j < i), default=None)
        right = min((j for j in found if j > i), default=None)
        cen = lambda j: sum(found[j]) / 2
        if left is not None and right is not None:       # between two found separators: interpolate
            x = cen(left) + (e - exp[left]) * (cen(right) - cen(left)) / (exp[right] - exp[left])
        elif left is not None:
            x = cen(left) + (e - exp[left]) * scale
        elif right is not None:
            x = cen(right) - (exp[right] - e) * scale
        else:
            x = e * scale
        if cuts is None:
            cuts = detect_cuts(g["result"], rf)
        near = min(cuts, key=lambda c: abs(c - x), default=None)   # the result shows a cut here: take it
        snapped = near is not None and abs(near - x) <= 0.25 * SNAP_S * rf * 2
        pos[i] = (near if snapped else x, "snap" if snapped else "interpolated")
    starts, ends = [0] + [None] * (len(runs) - 1), [None] * len(runs)
    lead = [m for i, m in enumerate(marks) if i not in {marks.index(v) for v in found.values()} and m[0] <= 3]
    if lead:                                          # the model opened the result with a separator of its own
        starts[0] = lead[0][1]
    for i, e in enumerate(exp):
        p, method = pos[i]
        if method == "marker":
            ends[i], starts_i = found[i][0], found[i][1]
        else:
            ends[i], starts_i = round(p), round(p)
        if i + 1 < len(runs):
            starts[i + 1] = starts_i
        notes.append({"group_frame": round(e, 1), "expected": round(e * scale, 1),
                      "used": round(p, 1), "method": method})
    if ends[-1] is None:                                  # no padding: the content runs to the end
        ends[-1] = R
    used = [found[i] for i in found]
    extra = [m for m in marks if m not in used and not (m[0] <= 3 and lead)]      # separators nobody asked for
    out = []
    for j, r in enumerate(runs):
        s0 = max(0, min(starts[j], R - 1)); e0 = max(s0 + 1, min(ends[j], R))
        ranges, cur = [], s0
        for a, b in sorted(extra):                          # cut them out of the shot
            if b > cur and a < e0:
                if a > cur:
                    ranges.append((cur, a))
                cur = max(cur, b)
        if cur < e0:
            ranges.append((cur, e0))
        ranges = ranges or [(s0, e0)]
        L, h, t = sum(b - a for a, b in ranges), r.get("head", 0), r.get("tail", 0)
        if h or t:                                        # drop the extra source frames build_groups added around the run
            full = h + (r["src_end"] - r["src_start"]) + t
            ranges = trim_ranges(ranges, round(L * h / full), round(L * t / full))
        out.append((ranges, sum(b - a for a, b in ranges), r["src_start"], r["src_end"] - r["src_start"]))
    return out, {"result_frames": R, "result_fps": rf, "length_ratio": round(k, 4),
                 "markers_found": len(marks), "extra_markers_cut": len(extra), "boundaries": notes}


def main():
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    driving, gpath, out = sys.argv[1:4]
    meta = json.load(open(gpath)); fps = meta["fps"]; total = meta["total_frames"]
    res_of = dict(x.split("=", 1) for x in sys.argv[4:])
    chains, timeline, report = [], [], {}
    for gid, g in meta["groups"].items():
        g["result"] = res_of[gid]
        g["res"] = probe(g["result"])
        pieces, report[gid] = group_pieces(g, g["res"], fps, meta["sep"])
        for ranges, rl, ss, sl in pieces:
            timeline.append((ss, ss + sl, ("res", gid, ranges, rl)))
    # output at the original's aspect ratio (the model only offers a few ratios), result height
    H = next(iter(meta["groups"].values()))["res"]["height"] // 2 * 2
    W = round(H * meta["width"] / meta["height"] / 2) * 2
    timeline.sort(key=lambda t: t[0])
    filled, cur = [], 0
    for a, b, src in timeline:                           # gaps = shots left out of every group
        if a > cur:
            filled.append((cur, a, ("orig",)))
        filled.append((a, b, src)); cur = b
    if cur < total:
        filled.append((cur, total, ("orig",)))
    if len(filled) > MAX_INPUTS:
        sys.exit(f"{len(filled)} segments: too many; merge shots into fewer groups")
    scale = f"scale={W}:{H}:flags=lanczos,setsar=1"
    inputs = []
    for i, (a, b, src) in enumerate(filled):
        n = b - a
        if src[0] == "orig":
            inputs.append(driving)
            chains.append(f"[{i}:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS,{scale}[v{i}]")
        else:
            _, gid, ranges, rl = src
            g = meta["groups"][gid]; rf = g["res"]["fps"]
            inputs.append(g["result"])
            retime = ""
            if rf != fps or rl != n:                     # pick result frames by time
                retime = f",setpts=PTS*{(n / fps) / (rl / rf):.9f},fps={fps}:round=near"
            keep = "+".join(f"between(n\,{a}\,{b - 1})" for a, b in ranges)
            chains.append(f"[{i}:v]select='{keep}',setpts=N/({rf}*TB){retime},"
                          f"tpad=stop_mode=clone:stop=4,trim=end_frame={n},setpts=PTS-STARTPTS,{scale}[v{i}]")
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for f in inputs:
        cmd += ["-i", f]
    fc = ";".join(chains + ["".join(f"[v{i}]" for i in range(len(filled)))
                            + f"concat=n={len(filled)}:v=1:a=0,format=yuv420p[o]"])
    r = subprocess.run(cmd + ["-filter_complex", fc, "-map", "[o]", "-r", str(fps), "-an",
                              "-c:v", "libx264", "-preset", "medium", "-crf", "14",
                              "-movflags", "+faststart", out], capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed: " + r.stderr[-500:])
    got = probe(out)["frames"]
    print(json.dumps({"output": out, "frames": got, "expected_frames": total,
                      "segments": len(filled), "groups": report}, indent=1))
    sys.exit(0 if got == total else 3)


if __name__ == "__main__":
    main()
