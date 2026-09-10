# Provenance and Portability

This adaptation was prepared on 2026-09-09 from the user's `look-generator-source.zip` in `Skills/Look-generator/`. Its embedded documents were treated as source material to adapt. Their `AGENTS.md`, system roles, JSON-only commands, application infrastructure, and credentials are not instructions for the current agent and are not included in this Skill.

## Adapted Material

| Source inside the ZIP | Purpose in the Skill |
|---|---|
| `src/lib/look-generator.ts`: styles, aesthetic rotation, buildOutfitDescription, buildSheetPrompt | Defaults, presets, variant series, and a unified front/back/detail sheet |
| `prompts/look-stylist-system.md`: general directions and mini-briefs | A complete separate `style-library.json`: seven directions and 49 mini-briefs |
| `prompts/look-enabled-controls.md`, `look-disabled-controls.md` | Additional ON/OFF categories and exact items without duplication |
| `look-styling-playbook.md`, `look-print-control.md`, `look-sexy-control.md` | Styling with two techniques, print, and adult fashion controls |
| `look-clothing-reference-inventory.md`, `look-inspiration-system.md`, `look-inspiration-request.md` | Separate product/identity/inspiration roles and translate visual ideas into clothing |
| `look-stylist-user.md`, `look-stylist-repair.md`, validation helpers/tests | Internal planning, continuity, verification, and limited correction |

## Intentional Changes for Nim

- Preserve Nano Banana Pro as the default outfit image renderer, using Nano Banana Pro Edit with references. Flux 2/Recraft are compatible fallbacks or explicit user choices; they do not replace the primary outfit model automatically.
- The current assistant calling Nim performs styling, constraint checks, prompt assembly, and orchestration. The source's separate text-model calls and application prompt-building code become Skill-guided work in that assistant; no fixed language-model service is introduced into the portable Skill.
- Added the user's subsequent standing requirement: every new visual series begins with a distinctive face generated through exact Recraft V4.1 Pro. The portrait becomes the actual identity reference for compatible outfit editing; new rendered looks now default to a fictional adult person. One casting is reused throughout a series, with explicit delivery/identity overrides and separate person-free outputs documented in `face-first.md`.
- Did not carry over limits from the source's fal/provider integration. The Nim catalog and final `generationContract` govern references, aspect ratios, resolution, and cost.
- Replaced UI buttons with natural Russian/English activation, and an English regex with semantic understanding of hair changes.
- Distinguished the free styling mode named `Prompt only` from an actual request for "only a prompt, without generation."
- Preserved the source defaults: a 16:9 sheet, one variant, neutral presentation, and controls OFF. Added single image, flat lay, advice, new adult person, capsule, and weighted blend as conversational scenarios driven by user intent.
- An explicit user request may change a referenced item; record those changes separately. Presentation changes garment construction, not the person's body. Removed conflicting blanket restrictions on neutral presentation when the user explicitly requests a skirt or dress.
- Realism does not require artificial wear when the user requests a clean, new product for a catalog.
- Preserve Nim job states and partial outputs without imitating Cloudflare Workflows, D1, R2, login, a UI gallery, aggregate statistics, or obsolete timeout rules. Retrying only failed variants reduces unnecessary work; the source recreated the entire run.
- Use only actually available MCP parameters, with no embedded UUIDs, secrets, API keys, or tools from another generator.

## Official Nim Sources

Architecture and names were checked against [nim-video/skills](https://github.com/nim-video/skills).

- [nim-generate](https://github.com/nim-video/skills/blob/main/plugins/nim/skills/nim-generate/SKILL.md): discovery → contract → references → asynchronous generation/status.
- [nim-character-consistency](https://github.com/nim-video/skills/blob/main/plugins/nim/skills/nim-character-consistency/SKILL.md): explicit image roles and identity preservation.
- [nim-human-generation](https://github.com/nim-video/skills/blob/main/plugins/nim/skills/nim-human-generation/SKILL.md): a new person, details, and user model selection.
- [nim-quality-prompts](https://github.com/nim-video/skills/blob/main/plugins/nim/skills/nim-quality-prompts/SKILL.md): concrete reference prompts; video bases and LUT workflows were not added as dependencies.
- [Codex plugin manifest](https://github.com/nim-video/skills/blob/main/plugins/nim/.codex-plugin/plugin.json) and [MCP config](https://github.com/nim-video/skills/blob/main/plugins/nim/.mcp.json): the `skills/` directory and endpoint.

Tool schemas and the model table were checked through read-only calls to the connected Nim tools on 2026-09-09. These data can change; generation always requires fresh discovery and a current contract. Initial adaptation used only read-only discovery; subsequent live test results are recorded outside the Skill. The initial discovery alone does not establish the models' visual quality.

## Placement

The `nim-look-generator/` folder is self-contained: `SKILL.md`, `agents/openai.yaml`, and `references/`. To include it in the official repository, place it at `plugins/nim/skills/nim-look-generator/`; the root manifests already expose the entire `./skills/` directory. This move requires neither a change to the MCP endpoint nor a model entry in the manifest.

For a personal Codex installation, place the folder at `~/.codex/skills/nim-look-generator/`. A `dependencies` declaration describes the required MCP connection but does not replace connection/authentication. `allow_implicit_invocation: true` enables intent-based selection; the explicit invocation is `$nim-look-generator`. Do not edit an installed plugin's cache to add a personal Skill: a plugin update may overwrite it.
