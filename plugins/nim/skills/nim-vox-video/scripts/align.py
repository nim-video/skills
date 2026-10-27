# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "imageio-ffmpeg"]
# ///
"""Word timings for the VO -> words.json [{"w","s","e"}].

usage: uv run align.py vo.mp3 words.json --text "the exact script"
  1) faster-whisper word timestamps if available (`uv run --with faster-whisper align.py ...`,
     downloads a ~140 MB model once); the script text is then used to fix the spelling.
  2) fallback, no ML: ffmpeg silence detection splits speech into phrases, words are spread over
     each phrase by syllable weight. Accurate to ~0.1-0.2 s, enough for event sync.
"""
import argparse, json, re, subprocess
import numpy as np, imageio_ffmpeg

ap = argparse.ArgumentParser(); ap.add_argument('audio'); ap.add_argument('out'); ap.add_argument('--text', default=''); ap.add_argument('--engine', default='auto')
a = ap.parse_args(); FF = imageio_ffmpeg.get_ffmpeg_exe()
pcm = subprocess.run([FF, '-loglevel', 'error', '-i', a.audio, '-ar', '16000', '-ac', '1', '-f', 'f32le', '-'], capture_output=True).stdout
audio = np.frombuffer(pcm, np.float32); dur = len(audio) / 16000
words = None
if a.engine in ('auto', 'whisper'):
    try:
        from faster_whisper import WhisperModel
        segs, _ = WhisperModel('base.en', device='cpu', compute_type='int8').transcribe(audio, word_timestamps=True)
        words = [{'w': x.word.strip(), 's': round(x.start, 2), 'e': round(x.end, 2)} for s in segs for x in s.words]
        if a.text:   # spelling from the script (names, numbers, punctuation): align token lists, copy script words over
            import difflib
            toks = a.text.split(); nz = lambda w: ''.join(c for c in w.lower() if c.isalnum())
            sm = difflib.SequenceMatcher(None, [nz(w['w']) for w in words], [nz(t) for t in toks], autojunk=False)
            fixed = []
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag in ('equal', 'replace') and i2 - i1 == j2 - j1:
                    fixed += [dict(words[i1 + k], w=toks[j1 + k]) for k in range(i2 - i1)]
                elif tag == 'replace' and i2 > i1 and j2 > j1:   # "8 at 235" -> "8,235", "Heat waves" -> "Heatwaves": spread the span over the script words
                    s0, e0, n = words[i1]['s'], words[i2 - 1]['e'], j2 - j1
                    fixed += [{'w': toks[j1 + k], 's': round(s0 + (e0 - s0) * k / n, 2), 'e': round(s0 + (e0 - s0) * (k + 1) / n, 2)} for k in range(n)]
                elif tag == 'delete': fixed += words[i1:i2]
                elif tag == 'insert' and fixed:                   # script word the recogniser skipped: give it a sliver after the previous word
                    for k in range(j1, j2): fixed.append({'w': toks[k], 's': fixed[-1]['e'], 'e': round(fixed[-1]['e'] + .05, 2)})
            words = fixed
            if len(words) != len(toks): print(f'WARNING: {len(words)} recognised words vs {len(toks)} in the script: check words.json')
    except ImportError:
        if a.engine == 'whisper': raise
if words is None:
    if not a.text: raise SystemExit('fallback alignment needs --text "script"')
    toks = a.text.split()
    # speech envelope -> phrases separated by >=0.18 s of silence
    hop = 160; env = np.sqrt(np.convolve(audio ** 2, np.ones(hop) / hop, 'same'))[::hop]; thr = max(0.012, np.percentile(env, 30) * 2.5)
    voiced = env > thr; segs = []; i = 0; n = len(voiced)
    while i < n:
        if voiced[i]:
            j = i
            while j < n and (voiced[j] or (j + 18 < n and voiced[j:j + 18].any())): j += 1
            segs.append([i * hop / 16000, j * hop / 16000]); i = j
        else: i += 1
    syl = lambda w: max(1, len(re.findall(r'[aeiouy]+', w.lower())) + (2 if any(ch.isdigit() for ch in w) else 0))
    # phrases end at punctuation; map phrases to speech segments greedily by length
    phrases, cur = [], []
    for t in toks:
        cur.append(t)
        if t[-1] in '.,;:!?': phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    while len(segs) > len(phrases): k = int(np.argmin([segs[i + 1][0] - segs[i][1] for i in range(len(segs) - 1)])); segs[k][1] = segs[k + 1][1]; del segs[k + 1]
    while len(segs) < len(phrases): k = int(np.argmax([s[1] - s[0] for s in segs])); s0, s1 = segs[k]; segs[k:k + 1] = [[s0, (s0 + s1) / 2], [(s0 + s1) / 2, s1]]
    words = []
    for ph, (s0, s1) in zip(phrases, segs):
        wts = [syl(w) for w in ph]; tot = sum(wts); t = s0
        for w, wt in zip(ph, wts):
            d = (s1 - s0) * wt / tot; words.append({'w': w, 's': round(t, 2), 'e': round(t + d, 2)}); t += d
json.dump(words, open(a.out, 'w'), indent=0); print(f'{dur:.1f}s', ' '.join(f"{x['w']}@{x['s']}" for x in words))
