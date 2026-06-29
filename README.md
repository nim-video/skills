# Nim Skills

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](./.claude-plugin/plugin.json)
[![Skills](https://img.shields.io/badge/skills-6-orange.svg)](#skills)
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
| `nim-b-roll-seedance` | `/nim:nim-b-roll-seedance` | Create staged product/lifestyle b-roll videos from a brief and references. Builds concise creative direction, handles reference roles internally, and generates with Seedance 2 through Nim.            |
| `nim-hookgen-seedance` | `/nim:nim-hookgen-seedance` | Write and generate talking-head "hook" UGC ad clips for short-form (TikTok / Reels / Shorts). Proposes spoken hook options, maps character/product/location references, and generates with Seedance 2 through Nim. |
| `nim-human-generation` | `/nim:nim-human-generation` | Generate believable editorial young-adult human portraits and fashion/UGC character images. Intakes age, gender presentation, and look; defaults to Nano Banana Pro in 9:16 and supports user-specified models. |
| `nim-template-runner` | `/nim:nim-template-runner` | Browse, inspect, and run Nim templates. Collects template inputs, uploads references, calls `run_template`, and polls for final media. |
| `nim-credits` | `/nim:nim-credits` | Check Nim credit balance, explain insufficient-credit failures, and help users buy packs or upgrade through Nim MCP. |

The skill drives model discovery (`models_explore`), generation (`generate_image` /
`generate_video`), templates (`explore_templates`, `get_template`, `run_template`),
reference uploads (`media_upload`), credits, and status polling
(`get_generation_status`) through the Nim MCP.

## What you can do

- **Generate** — images and videos from a prompt, in any aspect ratio the model supports.
- **Animate** — bring a still image to motion with image-to-video models.
- **Edit & restyle** — feed reference media and let Nim edit or restyle it.
- **Run templates** — browse Nim templates, collect their required inputs, and run
  repeatable creative workflows.
- **Manage credits** — check your Nim balance and resolve insufficient-credit states.
- **Ideate** — ask for several variations of a concept in one go and compare directions.

## License

MIT — see [LICENSE](./LICENSE).
