#!/usr/bin/env python3
"""Prepare the driving video so it passes every limit before upload.

Checks duration (4-30 s), trims only when asked (the full length is kept, fractional seconds
included), makes width/height even, upscales videos under 409 600 px (width x height, the provider's
minimum for the provider) to a 720 px short side, converts to constant 24 fps (the
generation's output rate), and re-encodes step by step until the file fits the upload cap, verifying the real size after
every step.

Usage:
  prepare_video.py IN OUT.mp4 [--start S] [--end E] [--max-bytes N] [--min-short-side 480]

Duration: < 4 s is rejected (exit 2) — slowing or looping would change the motion.
> 30 s is rejected (exit 2) unless --start/--end select a 4-30 s segment; the agent asks the
user which part to keep (default suggestion: the first 30 s). result.media_length_ms is the
exact clip length; for the price, round it up to whole seconds.

Exit codes: 0 ready (OUT written), 2 duration/input problem, 3 could not fit the size cap.
Prints JSON: source probe, every attempt with its resulting size, final probe.
"""
import argparse
import json
import os
import subprocess
import sys

DEFAULT_MAX_BYTES = 20_000_000          # Nim upload cap "20 MB"; decimal MB is the stricter reading
SAFETY = 0.97                            # stay a little under the cap
MIN_S, MAX_S = 4.0, 30.0
TARGET_FPS = 24                          # Seedance output rate; the source video is always sent at it
MIN_PIXELS, MAX_PIXELS = 409_600, 8_295_044  # provider limit on the video (width x height)
MIN_SHORT = 720                          # upscale target when under MIN_PIXELS (safe margin)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries",
               "stream=codec_type,codec_name,width,height,r_frame_rate:"
               "stream_side_data=rotation:format=duration,size,format_name",
               "-of", "json", path])
    if out.returncode:
        raise SystemExit(json.dumps({"status": "error", "reason": "unreadable video",
                                     "detail": out.stderr.strip()[:300]}))
    d = json.loads(out.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    if v is None:
        raise SystemExit(json.dumps({"status": "error", "reason": "no video stream"}))
    w, h = v["width"], v["height"]
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if abs(rot) in (90, 270):            # displayed geometry is what the frame will have
        w, h = h, w
    num, den = (v.get("r_frame_rate") or "0/1").split("/")
    return {"width": w, "height": h, "rotation": rot, "codec": v.get("codec_name"),
            "container": d["format"].get("format_name"),
            "fps": round(float(num) / float(den or 1), 3),
            "duration_s": round(float(d["format"]["duration"]), 3),
            "size_bytes": int(d["format"].get("size") or os.path.getsize(path)),
            "has_audio": any(s["codec_type"] == "audio" for s in d["streams"])}


def scale_filter(p, long_side):
    w, h = p["width"], p["height"]
    f = []
    if w * h < MIN_PIXELS:                          # too small for the provider: upscale
        f.append(f"scale=-2:{MIN_SHORT}:flags=lanczos" if w >= h else f"scale={MIN_SHORT}:-2:flags=lanczos")
    elif long_side and max(w, h) > long_side:
        f.append(f"scale={long_side}:-2" if w >= h else f"scale=-2:{long_side}")
    else:
        f.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")
    f.append(f"fps={TARGET_FPS}")                   # always: constant 24 fps, also fixes VFR
    f.append("format=yuv420p")
    return ",".join(f)


def encode(src, dst, p, trim, long_side, crf=None, kbps=None, audio_k=128):
    base = ["ffmpeg", "-v", "error", "-y"]
    if trim["start"] is not None:
        base += ["-ss", f"{trim['start']:.3f}"]
    base += ["-i", src]
    if trim["duration"] is not None:
        base += ["-t", f"{trim['duration']:.3f}"]
    vf = ["-vf", scale_filter(p, long_side)]
    vcodec = ["-c:v", "libx264", "-preset", "fast", "-profile:v", "high"]
    audio = (["-c:a", "aac", "-b:a", f"{audio_k}k", "-ac", "2"] if p["has_audio"] and audio_k
             else ["-an"])
    tail = ["-movflags", "+faststart", "-map_metadata", "-1", dst]
    if crf is not None:
        r = run(base + vf + vcodec + ["-crf", str(crf)] + audio + tail)
        return r.returncode == 0, r.stderr.strip()[:300]
    # two-pass average bitrate for a predictable size
    log = dst + ".2pass"
    r1 = run(base + vf + vcodec + ["-b:v", f"{kbps}k", "-pass", "1", "-passlogfile", log,
                                   "-an", "-f", "mp4", os.devnull])
    if r1.returncode:
        return False, r1.stderr.strip()[:300]
    r2 = run(base + vf + vcodec + ["-b:v", f"{kbps}k", "-maxrate", f"{int(kbps*1.3)}k",
                                   "-bufsize", f"{kbps*2}k", "-pass", "2", "-passlogfile", log]
             + audio + tail)
    for ext in ("-0.log", "-0.log.mbtree"):
        try:
            os.remove(log + ext)
        except OSError:
            pass
    return r2.returncode == 0, r2.stderr.strip()[:300]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("src"); a.add_argument("dst")
    a.add_argument("--start", type=float); a.add_argument("--end", type=float)
    a.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    a.add_argument("--min-short-side", type=int, default=576)
    args = a.parse_args()

    p = probe(args.src)
    start = args.start or 0.0
    end = args.end if args.end is not None else p["duration_s"]
    seg = round(end - start, 3)
    trim = {"start": args.start,
            "duration": seg if (args.start is not None or args.end is not None) else None}
    report = {"source": p, "segment": {"start": start, "end": end, "duration_s": seg}}

    if seg < MIN_S:
        report.update(status="rejected", reason=f"duration {seg}s is under 4 s; a longer video is needed")
        print(json.dumps(report, indent=2)); sys.exit(2)
    if seg > MAX_S:
        report.update(status="needs_trim",
                      reason=f"duration {seg}s is over 30 s; choose a 4-30 s segment with --start/--end",
                      suggestion={"start": 0.0, "end": 30.0})
        print(json.dumps(report, indent=2)); sys.exit(2)

    limit = int(args.max_bytes * SAFETY)
    w, h = p["width"], p["height"]
    even = w % 2 == 0 and h % 2 == 0
    mp4_h264 = p["codec"] == "h264" and "mp4" in (p["container"] or "")

    # Step 0: no re-encode when nothing needs fixing (keeps original quality).
    if (trim["duration"] is None and even and mp4_h264 and MIN_PIXELS <= w * h <= MAX_PIXELS and p["size_bytes"] <= limit
            and not p["rotation"] and abs(p["fps"] - TARGET_FPS) < 0.01):
        r = run(["ffmpeg", "-v", "error", "-y", "-i", args.src, "-c", "copy",
                 "-movflags", "+faststart", args.dst])
        if r.returncode == 0 and os.path.getsize(args.dst) <= limit:
            res = probe(args.dst); res["media_length_ms"] = round(res["duration_s"] * 1000)
            report.update(status="ready", attempts=[{"step": "copy", "size_bytes": os.path.getsize(args.dst)}],
                          result=res, max_bytes=args.max_bytes)
            print(json.dumps(report, indent=2)); sys.exit(0)

    # Ladder: cheap losses first. Seedance renders at 480p-1080p, so capping the long
    # side at 1920/1280 costs nothing visible; CRF and bitrate go down only after that.
    short = min(w, h)
    # never upscale: the floor is at most the source long side
    floor_long = min(max(w, h), max(args.min_short_side * max(w, h) // max(short, 1), 64))

    def kbps_for(audio_k):
        return max(150, int((limit * 8 * 0.95 / seg - audio_k * 1000) / 1000))

    ladder = [
        {"long": 1920, "crf": 23},
        {"long": 1280, "crf": 23},
        {"long": 1280, "crf": 27},
        {"long": 1280, "kbps": kbps_for(128), "audio": 128},
        {"long": 960, "kbps": kbps_for(96), "audio": 96},
        {"long": floor_long, "kbps": kbps_for(64), "audio": 64},
    ]
    attempts = []
    tmp = args.dst + ".tmp.mp4"
    seen = set()
    for i, st in enumerate(ladder, 1):
        long_side = max(min(st["long"], max(w, h)), floor_long) if st["long"] else None
        key = (long_side, st.get("crf"), st.get("kbps"))
        if key in seen:                                   # same params as an earlier step
            continue
        seen.add(key)
        # CRF steps are only worth it when the last result was near the cap; far above it,
        # go straight to the bitrate-targeted steps.
        last = next((x["size_bytes"] for x in reversed(attempts) if x.get("size_bytes")), None)
        if st.get("crf") is not None and last and last > 1.5 * limit:
            attempts.append({"step": i, "skipped": "previous result >1.5x cap"})
            continue
        ok, err = encode(args.src, tmp, p, trim, long_side, crf=st.get("crf"),
                         kbps=st.get("kbps"), audio_k=st.get("audio", 128))
        size = os.path.getsize(tmp) if ok and os.path.exists(tmp) else None
        attempts.append({"step": i, "long_side": long_side, "fps": TARGET_FPS,
                         "crf": st.get("crf"), "video_kbps": st.get("kbps"),
                         "size_bytes": size, "fits": bool(size and size <= limit),
                         **({"error": err} if not ok else {})})
        if size and size <= limit:
            os.replace(tmp, args.dst)
            res = probe(args.dst)
            res["media_length_ms"] = round(res["duration_s"] * 1000)
            fine = (MIN_S - 0.1 <= res["duration_s"] <= MAX_S + 0.1 and res["width"] % 2 == 0
                    and res["height"] % 2 == 0 and abs(res["fps"] - TARGET_FPS) < 0.01)
            report.update(status="ready" if fine else "error", attempts=attempts, result=res,
                          max_bytes=args.max_bytes)
            print(json.dumps(report, indent=2)); sys.exit(0 if fine else 3)

    if os.path.exists(tmp):
        os.remove(tmp)
    report.update(status="too_large", attempts=attempts, max_bytes=args.max_bytes,
                  reason="could not fit the cap at the minimum quality floor; use a shorter segment")
    print(json.dumps(report, indent=2)); sys.exit(3)


if __name__ == "__main__":
    main()
