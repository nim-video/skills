# Full-script voice-over with public Nim MCP

Read at pipeline stage 3. Use the live `search_voices`, `text_to_speech` and
`get_generation_status` tools. Tool namespace prefixes vary by host; the names below
are the MCP tool names. No ElevenLabs API key or direct ElevenLabs request is needed.

## Select one voice

If the user supplies a usable ElevenLabs voice ID, use it. Otherwise call
`search_voices` with the spoken language and requested voice character, for example:

```json
{"source":"library","language":"en","query":"documentary narrator","limit":5}
```

Use a returned `voiceId` as `voice_id` and its `name` as `voice_name`. Match language
and delivery to the approved brief; offer preview links when the user wants to choose.
`source: "library"` works for public users. Team voices require creator access.
A `generatedVoiceId` from `generate_voice_sample` is a temporary preview and cannot
be passed as `voice_id`. Do not use voice samples to produce the full narration.

## Generate the approved script

Call `text_to_speech` with these arguments (replace the example ID and name with
values returned by voice search):

```json
{
  "text": "[curious] What if everything you knew was wrong?",
  "voice_id": "VOICE_ID_FROM_SEARCH",
  "voice_name": "VOICE_NAME_FROM_SEARCH",
  "model": "eleven_v3",
  "stability": 0.5,
  "speed": 1
}
```

- `text` and `voice_id` are required. `voice_name` should be included when known.
- `eleven_v3` is the default. Delivery tags such as `[curious]`, `[excited]` or
  `[whispers]` belong before the words they affect. Use them only where the brief
  calls for that delivery. Other models may not support tags.
- Maximum 5000 characters per Eleven v3 call, including tags. Prefer one call for
  a script within the limit. For longer narration, split at sentence or paragraph
  boundaries and keep the same `voice_id`, model and settings across every part.
- Optional controls: `stability` 0–1 (default 0.5), `similarity_boost` 0–1
  (default 0.75), `speed` 0.7–1.2 (default 1), `style` 0–1 (default 0, ignored
  by models without style support). Omit controls the brief does not need.
- Pass `project_id` only when the user names a project; resolve it with
  `list_projects`. Otherwise omit it and use Nim's default project.
- Before the paid batch, estimate Eleven v3 VO as
  `sum(max(1, ceil(len(part_text) * 16 / 1000)))` credits. This is the rate from
  GitLab MR !5556; follow newer live pricing if provided. Do not apply this rate
  to other models. Log actual `creditsCharged` from each accepted job.

## Wait, download and align

Save `promptId`, `workflowId`, voice settings and `creditsCharged` as soon as the
queued result arrives. Poll `get_generation_status` with the returned ID:

```json
{"promptId":"PROMPT_ID_FROM_TEXT_TO_SPEECH"}
```

Use the suggested polling interval. `queued` and `running` mean continue waiting;
`finished` means download `mediaUrl` as the MP3. `failed`, `cancelled` and `removed`
are terminal: report the result and stop that job. Avoid narrating unchanged polls.
This status step applies to TTS even though image batches use `nim_fetch.py`.

For one call, keep the downloaded `vo.mp3` as the final narration. For several
parts, concatenate them in script order with ffmpeg (decode and re-encode to one
48 kHz WAV) and save `vo.wav`. Do not use `vo_pick.py` to select or reorder TTS
parts; all parts already use the selected voice.

Measure the final audio duration with ffprobe or ffmpeg. It must fit the target
length before storyboard timing is locked; if it overruns, shorten the script or
adjust delivery within the approved brief and budget. Do not silently truncate speech.

Run the existing aligner on the final audio:

```sh
uv run scripts/align.py vo.mp3 words.json --text "The exact spoken script without delivery tags."
```

For joined audio, substitute `vo.wav`. Supply the approved spoken words, not audio
tags or production directions, to `--text`. Point `timeline.json`'s `audio.vo` to
the actual final audio file and `audio.words` to `words.json`.

## Failure and retry handling

- `status: "insufficient_credits"` means no job was created. Show the returned
  message, stop paid work and do not automatically retry.
- If the submission response is lost or times out, do not blindly repeat
  `text_to_speech`: another job and charge may be created. Recover an existing
  job through a known `promptId` or `workflowId` with `get_generation_status`.
  If neither ID is known, report the uncertain submission before any new paid call.
- A failed download or local alignment does not require new synthesis: reuse
  the existing finished generation and audio.

Contract sources: [GitLab MR !5556](https://gitlab.com/nim.video/common/alpha-service/-/merge_requests/5556)
and the live Nim MCP tool schemas. Do not treat a successful merge as proof that
every deployment has the tools; if unavailable, report that prerequisite rather
than substituting voice-sample generation.
