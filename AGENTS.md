# AGENTS.md

Nim's public agent plugin: skills plus the Nim MCP server registration for Claude Code, Codex, and Cursor. Everything under `plugins/nim/` ships to users.

## Layout

- `plugins/nim/skills/<skill>/SKILL.md`: user-facing skills, with optional `references/` and `scripts/`.
- `plugins/nim/.mcp.json`: the Nim MCP server registration.
- The plugin version, identical in five manifests: `.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`, and `plugin.json` in `plugins/nim/.claude-plugin/`, `plugins/nim/.codex-plugin/`, and `plugins/nim/.cursor-plugin/`.
- `.agents/skills/`: skills for contributors to this repo. Codex reads them there; `.claude/skills/` is a generated mirror for Claude Code. They never ship.
- `scripts/`: repo tooling. Node 24+ runs it directly; there is nothing to install.

## Adding or changing a skill

1. **Name**: `nim-<kebab-case>`. The folder name and the frontmatter `name` are the same.
2. **Frontmatter**: `name` and `description`, at most 1024 characters. The description says what the skill does and when to use it. When it overlaps another skill, say what it is not for and which skill to use instead.
3. **Scope**: one skill per pull request: its folder, its README row, and the version bump.
4. **README**: add one row to the Skills table: `` | `nim-x` | `/nim:nim-x` | One user-facing sentence. | ``. Keep the blank line after the table. A use-case bullet is optional: one short line for users. Instructions for the agent belong in `SKILL.md`, not in the README.
5. **No per-skill `agents/openai.yaml`**: Codex metadata lives in `plugins/nim/.codex-plugin/plugin.json`.
6. **Version**: run `node scripts/bump-version.ts minor` for a new skill or `patch` for a change, once per pull request. Clients only pick up a change when the version goes up.
7. **Check**: run `node scripts/check-skills.ts --base origin/main` and fix everything it reports. CI runs the same check plus `claude plugin validate --strict`.
8. **Review**: before you open the pull request, run the `nim-skill-review` skill: `/nim-skill-review` in Claude Code, `$nim-skill-review` in Codex.

## Writing a skill

- When a skill calls Nim, name the Nim MCP tools (`models_explore`, `generate_image`, `generate_video`, `media_upload`, `get_generation_status`, and so on). Follow the model's live `generationContract` from `models_explore` instead of hard-coding model IDs or parameters.
- Skills also run in chat hosts such as Claude Desktop and Cowork, not only in coding agents.
- Keep `SKILL.md` focused. Move long examples and reference tables to `references/` and link them.
- Leave maintainer notes, such as how to edit the skill or how it was developed, out of `SKILL.md`: every line ships to users.

## Contributor skills

Edit `.agents/skills/` only, then run `node scripts/sync-agent-skills.ts` to refresh `.claude/skills/`. Each contributor skill sets `internal: true` under `metadata` in its frontmatter, so `npx skills add nim-video/skills` doesn't install it for users.
