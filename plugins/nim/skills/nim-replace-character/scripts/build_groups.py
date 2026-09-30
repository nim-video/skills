#!/usr/bin/env python3
"""Stitch groups of shots into separate clips, one per generation.

Shots that are in no group are simply left out; assemble.py puts the original ones back.
Between two shots that were not neighbours in the video, the clip gets a short separator: solid
magenta frames. It makes the model treat them as separate shots (near-identical shots otherwise
melt into one take) and marks the exact place of the cut, so assemble.py finds every shot in the
result even when the model shifts the timing. The clip is then lengthened to a whole number of
seconds (the model's duration is set in whole seconds) with the source frames right before and
after its runs (`head`/`tail` in groups.json). A clip under 4 s is refused (exit 2): glue it to
another group, never repeat its own frames. The extra frames and separators are cut away at
assembly; they only cost credits.

Usage: build_groups.py DRIVING SHOTS.json PLAN.json OUT_DIR [--max-s 15] [--sep 6] [--audio] [--mute A,B]
  PLAN.json: {"groups": {"A": [1, 3, 5], "B": [2, 4, 6]}}   (shot numbers from split_shots.py)
  --max-s   longest clip the model takes: 15 for Seedance 2.0
  --sep     separator length in frames (default 6)
  --mute    groups (ids, comma-separated) whose clips stay silent even with --audio: the people in
            them do not speak
  --audio   keep the source sound in the clips (cut by the same frame ranges, silence on the
            separators and padding). Default: silent clips
Writes OUT_DIR/g_<id>.mp4 (silent, 24 fps, <= 20 MB) and OUT_DIR/groups.json; prints it.
Exit 0 ok, 2 bad plan (or a group over --max-s: split it), 3 a group does not fit the upload cap.
"""
import json, os, subprocess, sys

MAX_BYTES = int(20_000_000 * 0.97)
MAX_INPUTS = 120                 # one ffmpeg input per segment
CRFS = (17, 21, 25, 29)
MARKER = "0xFF00FF"


def die(code, **kw):
    print(json.dumps({"status": "error", **kw}, indent=1)); sys.exit(code)


def runs_of(shots, ids):
    """Consecutive shots merge into one contiguous run of source frames."""
    runs = []
    for i in sorted(ids):
        s = shots[i]
        if runs and runs[-1][1] == s["start_frame"]:
            runs[-1][1] = s["end_frame"]
        else:
            runs.append([s["start_frame"], s["end_frame"]])
    return runs


def encode(src, segs, dst, crf, w, h, fps, audio=False):
    """segs: ("clip", a, b) | ("sep", n) — frame-exact concat."""
    cmd, parts = ["ffmpeg", "-v", "error", "-y"], []
    for i, sg in enumerate(segs):
        if sg[0] == "clip":
            cmd += ["-i", src]
            parts.append(f"[{i}:v]trim=start_frame={sg[1]}:end_frame={sg[2]},setpts=PTS-STARTPTS[v{i}]")
            if audio:
                parts.append(f"[{i}:a]atrim=start={sg[1] / fps:.6f}:end={sg[2] / fps:.6f},asetpts=PTS-STARTPTS,"
                             f"aresample=44100,aformat=channel_layouts=stereo[a{i}]")
        else:
            cmd += ["-f", "lavfi", "-t", "2", "-i", f"color=c={MARKER}:s={w}x{h}:r={fps}"]
            parts.append(f"[{i}:v]trim=end_frame={sg[1]},setpts=PTS-STARTPTS,setsar=1[v{i}]")
            if audio:
                parts.append(f"anullsrc=r=44100:cl=stereo,atrim=end={sg[1] / fps:.6f},asetpts=PTS-STARTPTS[a{i}]")
    chain = "".join(f"[v{i}][a{i}]" if audio else f"[v{i}]" for i in range(len(segs)))
    fc = ";".join(parts + [f"{chain}concat=n={len(segs)}:v=1:a={1 if audio else 0}"
                           + ("[ov][oa]" if audio else "") + ("" if audio else ",format=yuv420p[o]")])
    if audio:
        fc += ";[ov]format=yuv420p[o]"
    out = ["-map", "[o]", "-r", str(fps)] + (["-map", "[oa]", "-c:a", "aac", "-b:a", "128k"] if audio else ["-an"])
    r = subprocess.run(cmd + ["-filter_complex", fc] + out
                       + ["-c:v", "libx264", "-preset", "fast", "-crf", str(crf),
                          "-movflags", "+faststart", dst], capture_output=True, text=True)
    if r.returncode:
        die(3, reason="ffmpeg failed", detail=r.stderr[-400:])


def main():
    args = sys.argv[1:]
    audio = "--audio" in args
    if audio:
        args.remove("--audio")
    mute = set()
    if "--mute" in args:
        i = args.index("--mute"); mute = set(args[i + 1].split(",")); del args[i:i + 2]
    opt = {"--max-s": 15, "--sep": 6}
    for k in opt:
        if k in args:
            i = args.index(k); opt[k] = int(args[i + 1]); del args[i:i + 2]
    max_s, S = opt["--max-s"], opt["--sep"]
    has_audio = "audio" in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", args[0]],
                                         capture_output=True, text=True).stdout
    audio = audio and has_audio                            # no sound in the source: silent clips
    if len(args) != 4:
        die(2, reason=__doc__)
    driving, shots_path, plan_path, out_dir = args
    meta = json.load(open(shots_path)); fps = round(meta["fps"])
    shots = {s["index"]: s for s in meta["shots"]}
    groups = json.load(open(plan_path))["groups"]
    used = [i for ids in groups.values() for i in ids]
    if len(used) != len(set(used)) or any(i not in shots for i in used):
        die(2, reason="a shot is in two groups or does not exist", shots=sorted(shots))
    os.makedirs(out_dir, exist_ok=True)
    out = {"status": "ok", "fps": meta["fps"], "total_frames": meta["total_frames"],
           "width": meta["width"], "height": meta["height"], "marker": MARKER, "sep": S, "groups": {}}
    for gid, ids in groups.items():
        runs = runs_of(shots, ids)
        real = sum(b - a for a, b in runs)
        base = real + S * (len(runs) - 1)                    # with the separators
        if base < 4 * fps:                                   # never stretch a short clip with copies of itself
            die(2, reason=f"group {gid} is {base / fps:.1f} s, under 4 s: glue it to the group whose shots are next to it or closest in length")
        want = -(-base // fps) * fps                         # whole seconds: the missing frames come from the video
        if want > max_s * fps:
            die(2, reason=f"group {gid} is {base / fps:.1f} s, over {max_s} s: split it into parts")
        head, tail = [0] * len(runs), [0] * len(runs)        # extra source frames before / after each run
        gap = [runs[0][0]] + [runs[j][0] - runs[j - 1][1] for j in range(1, len(runs))] + [meta["total_frames"] - runs[-1][1]]
        need, j = want - base, 0
        while need and any(gap):                             # one frame at a time, after and before the runs in turn
            k = j % (2 * len(runs)); r = k // 2
            gi = r + 1 if k % 2 == 0 else r                  # gap after run r / before run r
            if gap[gi]:
                gap[gi] -= 1; need -= 1
                if k % 2 == 0: tail[r] += 1
                else: head[r] += 1
            j += 1
        if need:
            die(2, reason=f"group {gid}: the video has no frames left to fill {want / fps:.0f} s")
        segs, pos, grp_start = [], 0, []
        for j, (a, b) in enumerate(runs):
            if j:
                segs.append(("sep", S)); pos += S
            grp_start.append(pos); segs.append(("clip", a - head[j], b + tail[j])); pos += b - a + head[j] + tail[j]
        real_end = pos
        if len(segs) > MAX_INPUTS:
            die(2, reason=f"group {gid} needs {len(segs)} segments; merge or drop tiny shots")
        dst = os.path.join(out_dir, f"g_{gid}.mp4")
        for crf in CRFS:
            encode(driving, segs, dst, crf, meta["width"], meta["height"], fps, audio and gid not in mute)
            if os.path.getsize(dst) <= MAX_BYTES:
                break
        else:
            die(3, reason=f"group {gid} does not fit 20 MB", group=gid)
        times = []
        for j, (a, b) in enumerate(runs):                    # per-shot times on the group timeline
            for i in sorted(ids):
                s = shots[i]
                if a <= s["start_frame"] and s["end_frame"] <= b:
                    t0 = grp_start[j] + head[j] + s["start_frame"] - a
                    times.append({"shot": i, "start_s": round(t0 / fps, 2),
                                  "end_s": round((t0 + s["frames"]) / fps, 2)})
        out["groups"][gid] = {
            "file": dst, "shots": sorted(ids),
            "runs": [{"src_start": a, "src_end": b, "grp_start": grp_start[k], "head": head[k], "tail": tail[k]}
                     for k, (a, b) in enumerate(runs)],
            "real_frames": real, "real_end": real_end, "frames": pos, "pad_frames": pos - real_end,
            "duration_s": round(pos / fps, 3), "media_length_ms": round(pos / fps * 1000),
            "size_bytes": os.path.getsize(dst), "times": times}
    out["excluded_shots"] = sorted(set(shots) - set(used))
    json.dump(out, open(os.path.join(out_dir, "groups.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
