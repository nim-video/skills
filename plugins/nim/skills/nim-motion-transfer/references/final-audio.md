# Compatible MP4 delivery with the source soundtrack

For final MP4 delivery, encode the source soundtrack as **AAC-LC at 192 kb/s, 48 kHz, stereo**
(`-c:a aac -profile:a aac_low -b:a 192k -ar 48000 -ac 2`) and use `-movflags +faststart`.
Encode the final picture as H.264 Baseline (`-c:v libx264 -profile:v baseline
-pix_fmt yuv420p -crf 20 -tag:v avc1 -maxrate 4M -bufsize 8M`). Preserve source
frame rate and requested aspect ratio; normalize dimensions as below. For 720p/24fps delivery,
`-level:v 3.1` may be specified. Do not force that level on larger/faster output.
Use this compatible export even for silent deliverables, omitting audio settings.
This is the most widely compatible combination. Output encoded as High-profile H.264 or
HE-AAC has failed to play or upload in some players; the exact cause was not isolated.
Do not claim that either codec is universally unsupported. Preserve the source performance and timing, but describe the
sound as transcoded, not bit-exact. If the user explicitly requires bit-exact
encoded audio, explain the conflict with AAC-LC conversion before proceeding.

1. Keep the source and the agreed interval, starting at zero; trim other intervals first.
2. Reuse silent depth or create it with `--no-audio`. Do not send the source sound
   to the generation model; disable generated sound with `generateAudio: false`
   when supported. Otherwise discard its soundtrack during assembly.
3. Download the generated picture for audio assembly. Inspect input durations and
   start timestamps. Report short output rather than looping, stretching or freezing it.
4. Run `scripts/restore_source_audio.py generated.mp4 source.mp4 final.mp4
   --duration 15 --resolution 720p --aspect-ratio 9:16 --ffmpeg <executable>`
   with the actual agreed duration, resolution tier and aspect ratio.
   The helper first encodes source audio to AAC-LC, then muxes that track into
   the trimmed H.264 Baseline/yuv420p video with faststart. It refuses to overwrite originals.
   It neither loops nor pads short audio and does not use `-shortest`.
5. Verify actual output dimensions against the table, H.264 Baseline, yuv420p, AAC profile LC at 48 kHz stereo, audio presence, final duration, start alignment and playback
   around cuts and the ending. The helper verifies packet hashes against the encoded
   AAC-LC intermediate, NOT the original compressed source. Hash equality confirms
   mux integrity; it does not prove synchronization or playback compatibility.

Missing source audio is an error for source-soundtrack requests. Do not substitute
model-generated audio. For split workflows, assemble picture fragments first and
attach one continuous source soundtrack. Deliver the local final file explicitly;
the raw Nim generation URL does not include this audio assembly.

## Normalize final dimensions for compatibility

Inspect the downloaded file's actual dimensions. A Nim resolution label does not
guarantee a standard pixel size. For final 16:9 and 9:16 delivery, use this local
compatibility convention, unless the user explicitly requests original dimensions:

| Requested tier | Landscape 16:9 (width x height) | Portrait 9:16 (width x height) |
|---|---|---|
| 480p | 854 x 480 | 480 x 854 |
| 720p | 1280 x 720 | 720 x 1280 |
| 1080p | 1920 x 1080 | 1080 x 1920 |

480p uses the even-pixel approximation of 16:9. Fit the picture within the target
canvas without stretching or cropping, pad as needed, and set square pixels (SAR=1).
The helper applies this during the existing final video encode, together with audio
assembly. Use the same filter for silent final exports. Keep the downloaded original.
Use the selected generation tier, not an inferred tier from dimensions such as
676 x 1200. Do not upscale to a higher tier unless requested.

Other aspect ratios and explicit original-size requests use `--aspect-ratio preserve`;
this keeps source dimensions and SAR, instead of forcing the picture into 16:9.
For tiers outside this table, preserve the requested format and handle export separately.

This is a compatibility preset, not a claim that nonstandard dimensions are invalid.
Nonstandard sizes such as 676 x 1200 have failed to play in some players where
720 x 1280 worked after a full re-encode; resolution was not isolated as the cause.
