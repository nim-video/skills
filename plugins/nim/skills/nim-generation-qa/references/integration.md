# Nim MCP integration

This package contains agent instructions, not a running MCP service or analysis endpoint. A description makes the skill discoverable; it cannot guarantee execution after every generation.

## Deployment

Ship nim-generation-qa alongside Nim's existing skills and register it through the host's supported discovery mechanism. agents/openai.yaml is optional Codex metadata; other hosts may ignore it.

Add the block below to each generation skill's successful-completion path, or once in shared agent instructions covering all Nim creative workflows. Prefer one maintained common path. Cover direct image/video generation, templates, edits, upscale and lipsync where available. Do not assume a new MCP API.

## Completion instruction to integrate

> After each successful Nim creative image/video output becomes available, show the result and ask the user whether they want a quality analysis. Invoke nim-generation-qa only if they say yes, or if they already asked for a review. Supply the latest approved brief, exact submitted prompt/settings, reference-role map, generation identifier and every actual output. Review every batch variant and approved retry. Show results with an evidence-based review; uninspectable properties remain unverified. If defects exist, prepare complete prompt changes and a bounded rerun proposal, then obtain approval unless that concrete retry is already authorized. Do not automatically spend credits on another generation based solely on review findings. Do not trigger QA for uploads, catalog calls, failed jobs without media, or describe_video's echoed source video.

A widget does not perform this QA. Where the host can resume the agent with the finished media, use that. Where it cannot (Claude app, Claude Desktop and other chat hosts), the agent must poll to completion in the same reply and ask about the review before ending it, as described in SKILL.md "Same-turn completion". Do not narrate polling or re-embed media the widget already shows.

## Conceptual orchestration, not an existing API

```text
creative output finished
  → recover brief + request + references
  → show results, ask whether the user wants an analysis
  → no? stop here
  → for each output revision:
        reuse existing review, or invoke nim-generation-qa
  → show aggregate review
  → findings? prepare prompt + scope + estimate
  → wait for approval unless already authorized
  → perform authorized retry once
  → review new output, including regressions
```

Use workflow/output identity plus revision/fingerprint to avoid duplicate reviews and repeated analysis charges on each status poll. Explicit re-review with new criteria/evidence may create a review revision.

A failed review must not discard the output or hide successful batch siblings. Failed/cancelled generation is a workflow error, not a scored media defect.

Preserve submitted requests before generation: status responses may not retain the brief/references. If a template exposes no prompt, compare brief and inputs and mark the prompt comparison unavailable.

Use scripts/inspect_video.py plus native image viewing first; otherwise available local tools or an authorized analysis service. Do not invent get_video_analysis or assume describe_video accepts audit questions. Discover live contracts and retain evaluator limitations.

This package does not authorize uploads to another provider, credit purchases, account changes or recurring monitoring. It does authorize running the bundled scripts/inspect_video.py, including the pip dependencies it installs for itself (opencv-python-headless, pillow, imageio-ffmpeg).
