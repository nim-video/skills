# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "imageio-ffmpeg"]
# ///
"""Long VO from several generate_voice_sample calls (each call = 3 takes, each takes may be a new voice):
pick one take per part so that all parts sound like the SAME voice, then join them.

usage: uv run vo_pick.py OUT.wav --parts p1a.mp3,p1b.mp3,p1c.mp3 p2a.mp3,p2b.mp3,p2c.mp3 ... [--gap 0.28] [--max-len 20]
--max-len: only combinations whose joined length fits (seconds) are considered; if none fits, the shortest wins.
Voice similarity = distance of mean log-mel spectrum (timbre) + median pitch; the combination with the
smallest total distance between consecutive parts wins (ties: shorter total length). Prints the choice.
"""
import argparse, itertools, subprocess
import numpy as np, imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 22050
def load(p):
    b = subprocess.run([FF, '-loglevel', 'error', '-i', p, '-ar', str(SR), '-ac', '1', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(b, np.float32); e = np.abs(a) > 0.01; idx = np.nonzero(e)[0]
    return a[max(0, idx[0] - 800): idx[-1] + 2000] if len(idx) else a
def voiceprint(a):
    n = 1024; hop = 256; win = np.hanning(n); frames = np.lib.stride_tricks.sliding_window_view(a, n)[::hop] * win
    spec = np.abs(np.fft.rfft(frames, axis=1)) ** 2; f = np.fft.rfftfreq(n, 1 / SR)
    mel = lambda x: 2595 * np.log10(1 + x / 700); edges = np.interp(np.linspace(mel(80), mel(7600), 42), mel(f), f)
    fb = np.array([np.clip(np.minimum((f - edges[i]) / (edges[i + 1] - edges[i] + 1e-9), (edges[i + 2] - f) / (edges[i + 2] - edges[i + 1] + 1e-9)), 0, None) for i in range(40)])
    lm = np.log(spec @ fb.T + 1e-9); voiced = lm.mean(1) > np.percentile(lm.mean(1), 40); lm = lm[voiced]
    ac = [np.argmax(np.correlate(fr, fr, 'full')[n - 1 + 40:n - 1 + 300]) + 40 for fr in frames[voiced][::8]]   # crude pitch period
    return lm.mean(0) - lm.mean(), np.median(SR / np.array(ac)) if ac else 0
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--parts', nargs='+', required=True); ap.add_argument('--gap', type=float, default=.28); ap.add_argument('--max-len', type=float, default=0)
a = ap.parse_args(); groups = [p.split(',') for p in a.parts]
audio = [[load(p) for p in g] for g in groups]; vp = [[voiceprint(x) for x in g] for g in audio]
def dist(u, v): return np.linalg.norm(u[0] - v[0]) + abs(np.log((u[1] + 1) / (v[1] + 1))) * 8
combos = list(itertools.product(*[range(len(g)) for g in groups]))
length = lambda c: (sum(len(audio[i][c[i]]) for i in range(len(c))) / SR + a.gap * len(c))
if a.max_len:
    fit = [c for c in combos if length(c) <= a.max_len]
    if not fit: print(f'WARNING: no combination fits {a.max_len}s (shortest {min(map(length, combos)):.1f}s): shortest used, consider a shorter script'); fit = [min(combos, key=length)]
    combos = fit
best = min(combos, key=lambda c: (sum(dist(vp[i][c[i]], vp[i + 1][c[i + 1]]) for i in range(len(c) - 1)), length(c)))
gap = np.zeros(int(a.gap * SR), np.float32); out = np.concatenate([np.concatenate([audio[i][k], gap]) for i, k in enumerate(best)])
subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-ar', '48000', a.out], input=out.tobytes(), check=True)
print('picked', [groups[i][k] for i, k in enumerate(best)], f'-> {a.out} ({len(out) / SR:.1f}s)')
