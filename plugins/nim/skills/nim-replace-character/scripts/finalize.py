#!/usr/bin/env python3
"""Put the source audio back on the Seedance result.

Seedance cannot keep the input sound, so the result is generated silent and the prepared
video's audio track is muxed onto it (video stream copied whole, audio cut or left short to the video's length).

Usage: finalize.py RESULT.mp4 SOURCE.mp4 OUT.mp4
Prints JSON: output path, output probe, whether source audio was added.
"""
import argparse, json, subprocess


def info(path):
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", path],
        capture_output=True, text=True, check=True).stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    return {"width": v["width"], "height": v["height"], "fps": v["r_frame_rate"],
            "duration_s": round(float(d["format"]["duration"]), 3),
            "has_audio": any(s["codec_type"] == "audio" for s in d["streams"])}


def main():
    a = argparse.ArgumentParser(); a.add_argument("result"); a.add_argument("source"); a.add_argument("out")
    args = a.parse_args()
    has_audio = info(args.source)["has_audio"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", args.result]
    if has_audio:
        cmd += ["-i", args.source, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                "-t", str(info(args.result)["duration_s"])]
    else:
        cmd += ["-c", "copy"]
    subprocess.run(cmd + ["-movflags", "+faststart", args.out], check=True, capture_output=True)
    print(json.dumps({"output": args.out, "probe": info(args.out),
                      "audio": "source" if has_audio else "none"}, indent=2))


if __name__ == "__main__":
    main()
