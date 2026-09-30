#!/usr/bin/env python3
"""Depth-map motion reference via fal.ai.

Usage:
    depth_map.py --smoke                     # built-in public test clip
    depth_map.py <source> [out.mp4]          # source: URL or a local video file
    depth_map.py <source> --no-audio         # silent depth (default)
    depth_map.py <source> --attach-audio     # explicit audio-reference alternative
    depth_map.py <source> --audio-out a.m4a  # also write the audio as its own asset
    depth_map.py --selftest

`out` defaults to <name>-depth.mp4. Local files are sent inline as a base64 data
URI, so the reference clip is never published to a CDN.

By default the depth reference is silent. Original source audio is copied into the
FINAL generated video separately using restore_source_audio.py. --attach-audio is
an explicit alternative for tasks that need source sound inside the motion reference.
Do not use it for the normal final-audio workflow.

Reads FAL_KEY from the environment. The key is never printed, never logged,
never passed as an argument. See ../references/depth-provider.md for the swap
to a Nim-native `depth_map` tool.
"""
import base64
import hashlib
import json
import mimetypes
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://fal.run/fal-ai/depth-anything-video"

# Inline base64 costs ~1.33x the file size in the request body. Reference clips
# are meant to be 3-8s, so this ceiling is generous; past it the answer is a
# shorter clip, not a bigger POST.
MAX_LOCAL_BYTES = 25 * 1024 * 1024

# Known-good public clip from the fal docs. Used by --smoke so the smoke test
# never depends on a second argument surviving a shell paste.
SMOKE_URL = "https://v3b.fal.media/files/b/0a8fb1c1/xNTrr7wtczzLBkJdyE5_f_7JTYCmQe.mp4"

# VDA-Small is the Apache-2.0 variant. VDA-Base/Large are CC-BY-NC-4.0
# (non-commercial). The API default is VDA-Large, so this field must never be
# dropped - omit it and the call silently runs on a non-commercial model.
INPUT = {
    "model": "VDA-Small",
    "colormap": "grayscale",
    "resolution": "auto",  # never 360p: 640x360 = 230400 px, under the 409600 px
                           # floor Seedance enforces on reference video.
}


def call(url, payload, key, timeout=2700):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        # Print status and body only. Never echo request headers.
        sys.exit(f"fal returned HTTP {err.code}: {err.read()[:400].decode(errors='replace')}")


def cache_key(identity, config=None):
    payload = identity + json.dumps(INPUT, sort_keys=True) + json.dumps(config or {}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


# --- audio ---------------------------------------------------------------
# The depth model returns a silent visualization. Its schema exposes no audio field,
# so the track can only be carried across by copying it from the source afterwards.


def have(cmd):
    return shutil.which(cmd) is not None


def has_audio(src):
    """True when the source carries at least one audio stream. Never raises."""
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
             "stream=index", "-of", "csv=p=0", src],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(probe.stdout.strip())


def extract_audio(src, audio_out):
    """Write the source audio to a standalone asset for a separate audio reference."""
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", src, "-vn",
         "-map", "0:a:0", "-c:a", "copy", audio_out],
        check=True, timeout=1800,
    )


def mux_audio(depth_path, src, out):
    """Attach the source's audio to the depth clip, replacing `out` atomically."""
    tmp = out + ".muxing.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", depth_path, "-i", src,
         "-c", "copy", "-map", "0:v:0", "-map", "1:a:0", tmp],
        check=True, timeout=1800,
    )
    os.replace(tmp, out)


def is_url(src):
    return src.startswith(("http://", "https://"))


def default_out(src):
    if is_url(src):
        stem = pathlib.PurePosixPath(urllib.parse.urlparse(src).path).stem
    else:
        stem = pathlib.Path(src).stem
    return f"{stem or 'source'}-depth.mp4"


def resolve_source(src):
    """(video_url, identity). Accepts an http(s) URL or a local video file."""
    if is_url(src):
        return src, src

    path = pathlib.Path(src)
    if not path.is_file():
        sys.exit(f"not a URL and not a readable file: {src}")

    size = path.stat().st_size
    if size > MAX_LOCAL_BYTES:
        sys.exit(
            f"{path.name} is {size / 1e6:.1f} MB, over the {MAX_LOCAL_BYTES / 1e6:.0f} MB inline "
            f"limit. Trim the reference to the 3-8s window you actually need, re-encode it "
            f"smaller, or host it and pass a URL."
        )

    ctype = mimetypes.guess_type(path.name)[0] or ""
    if not ctype.startswith("video/"):
        sys.exit(f"{path.name}: unsupported type ({ctype or 'unknown'}). Use mp4, mov, or webm.")

    raw = path.read_bytes()
    # One code path, and the clip stays off a public CDN. If clips ever
    # routinely exceed MAX_LOCAL_BYTES, add fal CDN upload
    # (POST https://rest.alpha.fal.ai/storage/upload/initiate, then PUT) rather
    # than raising the ceiling.
    return f"data:{ctype};base64,{base64.b64encode(raw).decode()}", hashlib.sha256(raw).hexdigest()


def parse_args(argv):
    """(mode, opts) where mode is 'selftest' | 'usage' | 'run'."""
    if argv == ["--selftest"]:
        return "selftest", {}
    if argv == ["--smoke"]:
        argv = [SMOKE_URL]

    audio, audio_out, positional = False, None, []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--no-audio":
            audio = False
        elif arg == "--attach-audio":
            audio = True
        elif arg == "--audio-out":
            i += 1
            if i >= len(argv):
                return "usage", {}
            audio_out = argv[i]
        elif arg.startswith("--"):
            return "usage", {}
        else:
            positional.append(arg)
        i += 1

    if not 1 <= len(positional) <= 2:
        return "usage", {}
    return "run", {
        "src": positional[0],
        "out": positional[1] if len(positional) == 2 else default_out(positional[0]),
        "audio": audio,
        "audio_out": audio_out,
    }


def _expect_exit(fn, needle):
    try:
        fn()
    except SystemExit as err:
        assert needle in str(err), f"expected {needle!r} in {err!r}"
    else:
        raise AssertionError(f"expected SystemExit containing {needle!r}")


def selftest():
    a = cache_key("https://example.test/v.mp4")
    assert a == cache_key("https://example.test/v.mp4"), "cache key must be stable"
    assert a != cache_key("https://example.test/other.mp4"), "cache key must vary by source"
    assert cache_key("x", {"audio": True}) != cache_key("x", {"audio": False}), (
        "legacy audio cache variants must remain distinguishable for migration"
    )
    assert INPUT["model"] == "VDA-Small", "must not run on a non-commercial model"
    assert INPUT["resolution"] != "360p", "360p is below the Seedance pixel floor"
    assert default_out(SMOKE_URL) == "xNTrr7wtczzLBkJdyE5_f_7JTYCmQe-depth.mp4"
    assert default_out("https://h.test/a%20b.mp4?token=x") == "a%20b-depth.mp4", (
        "stem stays percent-encoded on purpose: decoding could collide two distinct URLs"
    )

    assert parse_args(["--selftest"])[0] == "selftest"
    assert parse_args([])[0] == "usage"
    assert parse_args(["a", "b", "c"])[0] == "usage"
    assert parse_args(["--audio-out"])[0] == "usage", "a flag without its value is usage"
    assert parse_args(["--bogus", "x.mp4"])[0] == "usage", "an unknown flag is usage"
    assert parse_args(["--smoke"])[1]["src"] == SMOKE_URL
    assert parse_args(["--smoke"])[1]["out"] == "xNTrr7wtczzLBkJdyE5_f_7JTYCmQe-depth.mp4"
    assert parse_args(["https://h.test/x.mp4"])[1] == {
        "src": "https://h.test/x.mp4", "out": "x-depth.mp4", "audio": False, "audio_out": None,
    }, "depth is silent by default; original audio belongs on the final generated video"
    assert parse_args(["--attach-audio", "x.mp4"])[1]["audio"] is True
    assert parse_args(["--no-audio", "x.mp4"])[1]["audio"] is False
    assert parse_args(["--no-audio", "x.mp4"])[1]["out"] == "x-depth.mp4"
    assert parse_args(["--audio-out", "a.m4a", "x.mp4"])[1]["audio_out"] == "a.m4a"
    assert parse_args(["--audio-out", "a.m4a", "--no-audio", "x.mp4"])[1]["audio_out"] == "a.m4a"

    with tempfile.TemporaryDirectory() as tmp:
        clip = pathlib.Path(tmp, "clip.mp4")
        payload = b"\x00\x01\x02fake-mp4"
        clip.write_bytes(payload)

        video_url, identity = resolve_source(str(clip))
        assert video_url.startswith("data:video/mp4;base64,"), video_url[:40]
        assert base64.b64decode(video_url.split(",", 1)[1]) == payload, "payload must round-trip"
        assert identity == hashlib.sha256(payload).hexdigest(), "identity tracks file content"
        assert default_out(str(clip)) == "clip-depth.mp4"

        touched = pathlib.Path(tmp, "clip2.mp4")
        touched.write_bytes(payload + b"!")
        assert resolve_source(str(touched))[1] != identity, "edited file must get a new identity"

        notes = pathlib.Path(tmp, "notes.txt")
        notes.write_bytes(b"hi")
        _expect_exit(lambda: resolve_source(str(notes)), "unsupported type")
        _expect_exit(lambda: resolve_source(str(pathlib.Path(tmp, "gone.mp4"))), "not a URL")

        # a file that is not a video must read as "no audio" rather than raising
        assert has_audio(str(notes)) is False, "a non-audio file must not raise"
        assert has_audio(str(pathlib.Path(tmp, "absent.mp4"))) is False, "a missing file must not raise"

        global MAX_LOCAL_BYTES
        original, MAX_LOCAL_BYTES = MAX_LOCAL_BYTES, 4
        try:
            _expect_exit(lambda: resolve_source(str(clip)), "inline limit")
        finally:
            MAX_LOCAL_BYTES = original

    print("selftest ok")


def main():
    mode, opts = parse_args(sys.argv[1:])
    if mode == "selftest":
        return selftest()
    if mode == "usage":
        sys.exit(__doc__)

    src, out = opts["src"], opts["out"]
    video_url, identity = resolve_source(src)

    # Fail on a missing tool before spending anything, not after the paid call.
    if opts["audio"] or opts["audio_out"]:
        missing = [c for c in ("ffmpeg", "ffprobe") if not have(c)]
        if missing:
            sys.exit(
                f"{' and '.join(missing)} not found on PATH. Install ffmpeg, or pass "
                f"--no-audio to run without the audio track."
            )

    # Paid depth identity is independent of local audio delivery options.
    stamp = cache_key(identity)
    marker = pathlib.Path(out + ".cachekey")
    legacy = {cache_key(identity, {"audio": a, "audio_out": b})
              for a in (True, False) for b in (True, False)}
    legacy.add(hashlib.sha256((identity + json.dumps(INPUT, sort_keys=True)).encode()).hexdigest())
    cached = (pathlib.Path(out).exists() and marker.exists()
              and marker.read_text().strip() in legacy | {stamp})
    if cached:
        print(f"cached depth -> {out}")
    else:
        key = os.environ.get("FAL_KEY")
        if not key:
            sys.exit("FAL_KEY is not set. Export it in your shell - never commit it into a skill.")
        result = call(ENDPOINT, {"video_url": video_url, **INPUT}, key)
        url = (result.get("video") or {}).get("url")
        if not url:
            sys.exit(f"no video in response: {json.dumps(result)[:400]}")
        pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=600) as resp, open(out, "wb") as fh:
            shutil.copyfileobj(resp, fh)
    # Cache paid work before local postprocessing, so audio errors do not cause rebilling.
    marker.write_text(stamp)

    notes = []
    source_has_audio = has_audio(src) if opts["audio"] or opts["audio_out"] else False

    if opts["audio_out"]:
        if not source_has_audio:
            sys.exit(
                f"{src} carries no audio stream, so there is nothing to write to "
                f"{opts['audio_out']}. The depth clip was written to {out}."
            )
        extract_audio(src, opts["audio_out"])
        notes.append(f"audio -> {opts['audio_out']}")

    if opts["audio"]:
        if source_has_audio:
            mux_audio(out, src, out)
            notes.append("source audio attached")
        else:
            notes.append("source has no audio, depth clip written silent")

    if not opts["audio"] and cached:
        if not have("ffmpeg"):
            sys.exit("Cached video may contain audio. Install ffmpeg to produce a silent reference; depth was not recalculated.")
        tmp = out + ".silent.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", out, "-map", "0:v:0", "-c:v", "copy", "-an", tmp], check=True)
        os.replace(tmp, out)
    print("\n".join([out, *notes, f"depth cache key: {stamp[:12]}"]))


if __name__ == "__main__":
    main()
