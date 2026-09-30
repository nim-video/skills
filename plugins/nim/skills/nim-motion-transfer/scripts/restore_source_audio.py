#!/usr/bin/env python3
"""Replace generated audio with source audio after generation (no network calls).

Usage: restore_source_audio.py generated.mp4 source.mp4 final.mp4 --duration 14.733333 --resolution 720p --aspect-ratio 9:16
Use --ffmpeg with an absolute executable path when FFmpeg is not on PATH.
Duration is the agreed usable source interval starting at zero. Trim a different
source interval first. Encodes source sound as AAC-LC at 192 kb/s for MP4 playback.
This helper never retimes or loops either input. Audio is not a bit-exact source copy.
"""
import argparse
import math
import pathlib
import subprocess
import tempfile


def run(ffmpeg, args):
    return subprocess.run([ffmpeg, '-nostdin', '-v', 'error', *args],
                          capture_output=True, text=True, check=True)


def audio_hash(ffmpeg, path, duration):
    return run(ffmpeg, ['-i', str(path), '-map', '0:a:0', '-t', str(duration),
                       '-c:a', 'copy', '-f', 'hash', '-hash', 'sha256', '-']).stdout.strip()


def video_filter(resolution, aspect_ratio):
    sizes = {'480p': (854, 480), '720p': (1280, 720), '1080p': (1920, 1080)}
    if resolution not in sizes or aspect_ratio not in ('16:9', '9:16', 'preserve'):
        raise ValueError('Choose 480p/720p/1080p and 16:9/9:16/preserve')
    if aspect_ratio == 'preserve':
        return None
    width, height = sizes[resolution]
    if aspect_ratio == '9:16':
        width, height = height, width
    # Fit the displayed aspect ratio (including non-square source pixels).
    # Explicit expressions also work on FFmpeg versions without reset_sar.
    return (f"scale=w='trunc(min({width},{height}*dar)/2)*2':"
            f"h='trunc(min({height},{width}/dar)/2)*2',setsar=1,"
            f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2')


def restore(generated, source, output, duration, ffmpeg='ffmpeg', *, resolution, aspect_ratio):
    vf = video_filter(resolution, aspect_ratio)
    generated, source, output = map(pathlib.Path, (generated, source, output))
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Duration must be positive')
    if output.exists() or output.resolve() in (generated.resolve(), source.resolve()):
        raise ValueError('Choose a new output file; originals are never overwritten')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='restore-audio-', dir=output.parent) as tmp:
        audio = pathlib.Path(tmp) / 'source-aac-lc.m4a'
        # Missing audio fails here, before video rendering. Encode once, then mux.
        run(ffmpeg, ['-i', str(source), '-map', '0:a:0', '-t', str(duration),
                     '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k',
                     '-ar', '48000', '-ac', '2',
                     str(audio)])
        expected = audio_hash(ffmpeg, audio, duration)
        staged = pathlib.Path(tmp) / 'final.mp4'
        run(ffmpeg, ['-i', str(generated), '-i', str(audio),
                     '-map', '0:v:0', '-map', '1:a:0', '-t', str(duration),
                     *(['-vf', vf] if vf else []),
                     '-c:v', 'libx264', '-profile:v', 'baseline', '-crf', '20',
                     '-pix_fmt', 'yuv420p', '-tag:v', 'avc1',
                     '-maxrate', '4M', '-bufsize', '8M',
                     '-c:a', 'copy', '-movflags', '+faststart', str(staged)])
        actual = audio_hash(ffmpeg, staged, duration)
        if actual != expected:
            raise RuntimeError('Encoded AAC-LC packet hash does not match; output not delivered')
        staged.rename(output)
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('generated')
    parser.add_argument('source')
    parser.add_argument('output')
    parser.add_argument('--duration', required=True, type=float)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--resolution', required=True, choices=('480p', '720p', '1080p'))
    parser.add_argument('--aspect-ratio', required=True, choices=('16:9', '9:16', 'preserve'),
                        help='Use preserve for other aspect ratios or explicit source-size requests')
    args = parser.parse_args()
    digest = restore(args.generated, args.source, args.output, args.duration, args.ffmpeg,
                     resolution=args.resolution, aspect_ratio=args.aspect_ratio)
    print(f'Final video: {args.output}\nAAC-LC mux verified (not source-bit-exact): {digest}')


if __name__ == '__main__':
    main()
