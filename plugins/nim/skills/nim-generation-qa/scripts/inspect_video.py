#!/usr/bin/env python3
"""Download a finished Nim video and prepare it for visual QA.

Cross-platform (Linux / macOS / Windows). Needs only Python 3.8+.
No system ffmpeg required: dependencies are pip packages that ship their own binaries.

Usage:
  python inspect_video.py <mediaUrl>                    # 2 fps contact sheets for the whole clip
  python inspect_video.py <mediaUrl> --fps 8 --start 4 --end 6   # dense look at a suspicious moment

Prints one JSON object: metadata, audio levels, and paths of contact-sheet images to view.
Exit code 2 = download failed (JSON includes the blocked domain if a proxy denied it).
"""
import argparse, importlib.util, json, pathlib, re, subprocess, sys, tempfile, urllib.error, urllib.parse, urllib.request

DEPS = [("cv2", "opencv-python-headless"), ("PIL", "pillow"), ("imageio_ffmpeg", "imageio-ffmpeg")]


def ensure_deps():
    missing = [pkg for mod, pkg in DEPS if importlib.util.find_spec(mod) is None]
    if not missing:
        return
    base = [sys.executable, "-m", "pip", "install", "-q", *missing]
    if subprocess.call(base) != 0:  # externally-managed Python (e.g. Debian/Ubuntu)
        subprocess.check_call(base + ["--break-system-packages"])


def download(url, dest):
    try:
        urllib.request.urlretrieve(url, dest)  # honors HTTPS_PROXY env vars
    except Exception as e:
        info = {"error": "download_failed", "detail": str(e), "host": urllib.parse.urlparse(url).hostname}
        if isinstance(e, urllib.error.HTTPError):
            info["status"] = e.code
            info["deny_reason"] = e.headers.get("x-deny-reason")
        print(json.dumps(info, indent=1))
        sys.exit(2)


def audio_report(clip):
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    r = subprocess.run([exe, "-hide_banner", "-i", str(clip), "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    err = r.stderr
    has_audio = bool(re.search(r"Stream #\S+.*Audio:", err))
    mean = re.search(r"mean_volume:\s*(-?[\d.]+) dB", err)
    peak = re.search(r"max_volume:\s*(-?[\d.]+) dB", err)
    return {"has_audio": has_audio,
            "mean_db": float(mean.group(1)) if mean else None,
            "peak_db": float(peak.group(1)) if peak else None,
            "note": "levels only; naturalness and sync are unverified"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--fps", type=float, default=2.0, help="frames sampled per second")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--width", type=int, default=512, help="max frame edge in px")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--rows", type=int, default=3)
    ap.add_argument("--out", default=str(pathlib.Path(tempfile.gettempdir()) / "nim_qa"))
    a = ap.parse_args()

    ensure_deps()
    import cv2
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.load_default(size=max(14, a.width // 22))  # Pillow >= 10.1
    except TypeError:
        font = ImageFont.load_default()

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    import hashlib
    clip = out / f"clip_{hashlib.sha1(a.url.encode()).hexdigest()[:10]}.mp4"
    if not clip.exists():  # dense re-runs on the same URL reuse the download
        download(a.url, clip)

    cap = cv2.VideoCapture(str(clip))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    step = max(1, round(src_fps / a.fps))

    frames, i = [], 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        t = i / src_fps
        if t >= a.start and (a.end is None or t <= a.end) and i % step == 0:
            img = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
            img.thumbnail((a.width, a.width))
            d, label = ImageDraw.Draw(img), f"{t:05.2f}s"
            box = d.textbbox((6, 6), label, font=font)
            d.rectangle((box[0] - 4, box[1] - 3, box[2] + 4, box[3] + 3), fill=(0, 0, 0))  # legible on any frame
            d.text((6, 6), label, font=font, fill=(255, 255, 0))
            frames.append(img)
        i += 1
    cap.release()

    per, tag, sheets = a.cols * a.rows, f"{a.start:g}-{a.end if a.end is not None else 'end'}", []
    for s in range(0, len(frames), per):
        chunk = frames[s:s + per]
        tw, th = chunk[0].size
        sheet = Image.new("RGB", (a.cols * tw, a.rows * th))
        for k, img in enumerate(chunk):
            sheet.paste(img, ((k % a.cols) * tw, (k // a.cols) * th))
        p = out / f"sheet_{tag}_{s // per + 1:02d}.jpg"
        sheet.save(p, quality=85)
        sheets.append(str(p))

    print(json.dumps({
        "video": {"width": w, "height": h, "fps": round(src_fps, 3), "frames": i,
                  "duration_s": round(i / src_fps, 2), "aspect": f"{w}:{h}"},
        "audio": audio_report(clip),
        "sampled": {"fps": a.fps, "count": len(frames), "range_s": [a.start, a.end]},
        "contact_sheets": sheets,
        "next": "Open every contact sheet with your image-viewing tool; re-run with --fps 8 --start/--end on suspicious moments.",
    }, indent=1))


if __name__ == "__main__":
    main()
