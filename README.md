# Nim Skills

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Version](https://img.shields.io/badge/version-0.7.0-blue.svg)](./plugins/nim/.claude-plugin/plugin.json)
[![Skills](https://img.shields.io/badge/skills-19-orange.svg)](#skills)
[![MCP](https://img.shields.io/badge/MCP-mcp.nim.video-purple.svg)](https://nim.video)

**Turn your coding agent into a creative studio.** Nim is the AI engine for visual
generation and ideation — discover the right model, generate images and video, edit
from references, and run templated creative workflows, all from your agent through the
[Nim MCP](https://nim.video).

Works with **Claude Code**, **Codex**, and **Cursor** today; the same `SKILL.md` skills
are designed to extend to more agents.

## Install

### Claude Code

```sh
claude plugin marketplace add nim-video/skills
claude plugin install nim@nim
```

The plugin bundles the Nim MCP server automatically — on first generation you'll be
prompted to authenticate with Nim.

### Codex

```sh
codex plugin marketplace add nim-video/skills
```

Then enable the `nim` plugin from the `/plugins` picker. The bundled MCP server is
registered on install; you'll complete Nim authentication on first use.

> Prefer to wire the MCP server yourself (no plugin)? Add it directly:
>
> ```toml
> # ~/.codex/config.toml
> [mcp_servers.nim]
> url = "https://mcp.nim.video/mcp"
> ```

### Cursor

Install **Nim** from the Cursor plugin marketplace (Settings → Plugins). The bundled
Nim MCP server is registered with the plugin; you'll authenticate with Nim on first use.

> Prefer to wire the MCP server yourself (no plugin)? Add it directly in
> Cursor's MCP settings:
>
> ```json
> {
>   "mcpServers": {
>     "Nim": { "url": "https://mcp.nim.video/mcp" }
>   }
> }
> ```

## Skills

| Skill              | Invoke                  | What it does                                                                                                                                                                                           |
| ------------------ | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `nim-generate`     | `/nim:nim-generate`     | Generate and edit images **and** video — text-to-image, image editing, text-to-video, and image-to-video. Discovers the right model, follows its contract, handles references, and returns the result. |
| `nim-character-consistency` | `/nim:nim-character-consistency` | Create new images of an existing character, person, product, or object while preserving visual identity across scenes, poses, lighting, and styles. |
| `nim-location-generator` | `/nim:nim-location-generator` | Create location concepts, interiors, exteriors, and UGC backgrounds; preserve a place across edits and alternate views using references and approved Nim image models. |
| `nim-b-roll-seedance` | `/nim:nim-b-roll-seedance` | Create staged product/lifestyle b-roll videos from a brief and references. Builds concise creative direction, handles reference roles internally, and generates with Seedance 2 through Nim.            |
| `nim-hookgen-seedance` | `/nim:nim-hookgen-seedance` | Write and generate talking-head "hook" UGC ad clips for short-form (TikTok / Reels / Shorts). Proposes spoken hook options, maps character/product/location references, and generates with Seedance 2 through Nim. |
| `nim-long-video-chain` | `/nim:nim-long-video-chain` | Chain multiple 15s Seedance clips into one continuous longer video (roughly 15s–5 min). Plans segments, writes shared-world prompts, generates in batches of up to 3, and hands off ffmpeg stitching to the user. |
| `nim-human-generation` | `/nim:nim-human-generation` | Generate believable editorial young-adult human portraits and fashion/UGC character images. Intakes age, gender presentation, and look; defaults to Nano Banana Pro in 9:16 and supports user-specified models. |
| `nim-look-generator` | `/nim:nim-look-generator` | Create fashion looks, capsules, and lookbooks from wishes or exact clothing references. The agent plans and writes prompts; Recraft V4.1 Pro casts the face, then Nano Banana Pro renders the outfits. |
| `nim-ugc-prompts` | `/nim:nim-ugc-prompts` | Build copy-ready UGC video prompts for creator ads, selfie hooks, mirror try-ons, street interviews, iPhone footage, VO, lip sync, and reference-driven Nim generation. |
| `nim-quality-prompts` | `/nim:nim-quality-prompts` | Improve image reference prompts and video prompts with Nim MCP rules, reference-frame planning, LUTs, camera quality, cinematic grammar, and multi-bank prompt retrieval. |
| `nim-template-runner` | `/nim:nim-template-runner` | Browse, inspect, and run Nim templates. Collects template inputs, uploads references, calls `run_template`, and polls for final media. |
| `nim-credits` | `/nim:nim-credits` | Check Nim credit balance, explain insufficient-credit failures, and help users buy packs or upgrade through Nim MCP. |
| `nim-product-creative` | `/nim:nim-product-creative` | Easy way to create a creative imagery with your product. |
| `nim-upscale` | `/nim:nim-upscale` | Upscale your video or image with state of the art upscale models. |
| `nim-generation-qa` | `/nim:nim-generation-qa` | Review finished Nim images and videos against the brief, report defects, and propose a revised prompt. |
| `nim-seedance-prompt-recovery` | `/nim:nim-seedance-prompt-recovery` | Write and revise Seedance 2.0/2.5 prompts, diagnose failed generations, and suggest targeted wording, reference, or audio corrections. |
| `nim-plugin-update` | `/nim:nim-plugin-update` | Checks for a newer Nim plugin at the start of a chat and installs the update in one click. |
| `nim-multi-angle-reshoot` | `/nim:nim-multi-angle-reshoot` | Reshoot an existing video from new camera angles as a multi-camera edit, keeping the original action. |
| `nim-replace-character` | `/nim:nim-replace-character` | Replace the people in your video with characters from your images and get back the finished video with the original sound. |

The skill drives model discovery (`models_explore`), generation (`generate_image` /
`generate_video`), templates (`explore_templates`, `get_template`, `run_template`),
reference uploads (`media_upload`), credits, and status polling
(`get_generation_status`) through the Nim MCP.

## What you can do

- **Generate** — images and videos from a prompt, in any aspect ratio the model supports.
- **Animate** — bring a still image to motion with image-to-video models.
- **Long-form video** — chain multiple 15s Seedance clips into one continuous story (up to ~5 minutes), then stitch locally with ffmpeg.
- **Edit & restyle** — feed reference media and let Nim edit or restyle it.
- **Keep identity consistent** — generate the same character, person, product, or
  object in new scenes from references.
- **Run templates** — browse Nim templates, collect their required inputs, and run
  repeatable creative workflows.
- **Manage credits** — check your Nim balance and resolve insufficient-credit states.
- **Ideate** — ask for several variations of a concept in one go and compare directions.
- **Upscale** — upscale your media to the best quality 
- **Reshoot from new angles** — turn a source video into a multi-angle edit of the same action.
- **Reiterate** — review each finished result and get a better prompt for the next run.
- **Draft and recover Seedance prompts** — use `nim-seedance-prompt-recovery` before
  writing a prompt, when editing it, and after a failed generation. Preserve
  character reference roles and requested speech; default to natural sounds with
  no music unless music was requested. Prompt-only work needs no MCP connection
  and does not start a generation; retries stay within the user's authorization.

## Contributing

Skills live in `plugins/nim/skills/<skill>/SKILL.md`, and the conventions are in
[AGENTS.md](./AGENTS.md). Before you open a pull request, run the check (Node 24+):

```sh
node scripts/check-skills.ts --base origin/main
```

CI runs the same check plus `claude plugin validate --strict`.

## License

MIT — see [LICENSE](./LICENSE).
