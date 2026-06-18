---
name: nim-update-plugin
description: Update the installed Nim plugin and its bundled Nim skills from the GitHub repository using ordinary git and file-copy commands. Use when the user asks to update, refresh, pull, reinstall, or sync Nim skills or the Nim plugin from GitHub, especially after a new Nim skill was added and the current chat cannot see it yet.
---

# Nim Update Plugin

## Overview

Update the local Nim plugin by pulling the latest `nim-video/skills` repository, refreshing or reinstalling the host plugin when possible, copying `plugins/nim` as a portable fallback, verifying the expected skill files, and telling the user to open a new chat. Prefer the host's native plugin manager when plugin metadata, MCP config, or version changed; use plain git and file-copy commands when no plugin manager is available.

The current chat's skill list is loaded before this skill runs. Even after a successful update, newly added skills will usually be available only in a new chat.

## Workflow

1. Identify the installed Nim plugin directory.
2. Identify or create a local clone of `https://github.com/nim-video/skills`.
3. Update that clone with `git fetch` and a clean checkout of the desired branch or ref.
4. Read the latest plugin version from the updated repository manifest.
5. Decide whether a native reinstall/refresh is needed.
6. Prefer the host's native plugin reinstall/refresh command when available.
7. If no native plugin manager is available, choose the correct target directory for the latest version and copy `plugins/nim/` there.
8. Verify that expected skill folders now exist under the active or target plugin's `skills/` directory.
9. Finish by telling the user the update is done and that they must open a new chat.

## Find The Installed Plugin Directory

Prefer the path from the currently loaded Nim skill, if available. For example, if the invoked skill path is:

```text
/Users/name/.codex/plugins/cache/nim/nim/0.1.0/skills/nim-update-plugin/SKILL.md
```

then the installed plugin directory is:

```text
/Users/name/.codex/plugins/cache/nim/nim/0.1.0
```

Treat the version segment as an example only. Do not hardcode `0.1.0`.

If the current skill path is not available, search likely plugin roots:

```bash
find "$HOME/.codex" "$HOME/.claude" "$HOME/.cursor" -path '*/plugins/nim*' -type d 2>/dev/null
```

Choose the directory that contains the plugin manifest and `skills/`:

```bash
test -d "$INSTALLED_NIM_PLUGIN/skills"
test -f "$INSTALLED_NIM_PLUGIN/.codex-plugin/plugin.json" \
  -o -f "$INSTALLED_NIM_PLUGIN/.claude-plugin/plugin.json" \
  -o -f "$INSTALLED_NIM_PLUGIN/.cursor-plugin/plugin.json"
```

## Update The Source Repository

Use an agent-owned temporary or work directory. Reuse an existing clone when it is already present and clean enough to update:

```bash
REPO_DIR="${TMPDIR:-/tmp}/nim-skills-update"

if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" fetch --prune origin
else
  rm -rf "$REPO_DIR"
  git clone https://github.com/nim-video/skills "$REPO_DIR"
  git -C "$REPO_DIR" fetch --prune origin
fi

git -C "$REPO_DIR" checkout main
git -C "$REPO_DIR" reset --hard origin/main
```

If the user asked for a specific branch, tag, or commit, check out that ref instead of `origin/main`.

## Resolve The Target Version

After updating the source repository, read the latest plugin version from the repository manifest:

```bash
LATEST_VERSION=$(
  sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
    "$REPO_DIR/plugins/nim/.codex-plugin/plugin.json" | head -1
)
test -n "$LATEST_VERSION"
```

Read the currently installed version when the installed manifest exists:

```bash
INSTALLED_VERSION=$(
  sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
    "$INSTALLED_NIM_PLUGIN/.codex-plugin/plugin.json" 2>/dev/null | head -1
)
```

Compare the installed and latest plugin payloads:

```bash
cmp -s "$INSTALLED_NIM_PLUGIN/.codex-plugin/plugin.json" "$REPO_DIR/plugins/nim/.codex-plugin/plugin.json" || PLUGIN_METADATA_CHANGED=1
cmp -s "$INSTALLED_NIM_PLUGIN/.mcp.json" "$REPO_DIR/plugins/nim/.mcp.json" || PLUGIN_METADATA_CHANGED=1
test "$INSTALLED_VERSION" = "$LATEST_VERSION" || PLUGIN_VERSION_CHANGED=1
```

If the version changed, the plugin manifest changed, or `.mcp.json` changed, treat this as a plugin update, not only a skills update. Refresh/reinstall through the host's plugin manager when one is available.

## Refresh Or Reinstall The Plugin

Use the host's native plugin manager when available, because the host may keep separate plugin registry state outside the plugin files.

For Codex, refresh the Git marketplace snapshot and reinstall the plugin cache:

```bash
codex plugin marketplace upgrade nim
codex plugin add nim@nim
```

After that, rediscover the installed Nim plugin directory if possible, because a version bump may create a new cache path.

For other hosts, use their equivalent "update", "refresh", "reinstall", or "remove then install" plugin action for the Nim plugin. Preserve user authentication and settings; do not delete user config unless the host's documented reinstall flow requires it.

If a native plugin manager succeeds, skip manual copying unless verification still shows stale files. If no native plugin manager exists or the host is just a folder-based plugin loader, continue with the file-copy fallback below.

## File-Copy Fallback

Use this fallback for hosts without a plugin manager, for local development fixtures, or when the installed plugin is plainly a folder that the host loads directly.

If the installed plugin lives in a versioned cache directory, such as:

```text
.../plugins/cache/nim/nim/0.1.0
```

then sync into the sibling directory for the latest version:

```bash
case "$INSTALLED_NIM_PLUGIN" in
  */plugins/cache/nim/nim/*)
    NIM_VERSION_PARENT=$(dirname "$INSTALLED_NIM_PLUGIN")
    TARGET_NIM_PLUGIN="$NIM_VERSION_PARENT/$LATEST_VERSION"
    ;;
  *)
    TARGET_NIM_PLUGIN="$INSTALLED_NIM_PLUGIN"
    ;;
esac
```

Use `TARGET_NIM_PLUGIN` for the copy and verification steps below. This prevents broken or misleading versioned paths when the plugin version changes. If the host has an obvious `latest` symlink next to versioned directories, update it to point at `TARGET_NIM_PLUGIN`; otherwise do not invent platform-specific state.

## Copy The Plugin

Use `rsync` when available so removed files disappear too:

```bash
rsync -a --delete \
  --exclude '.git' \
  "$REPO_DIR/plugins/nim/" \
  "$TARGET_NIM_PLUGIN/"
```

If `rsync` is unavailable, replace the target directory with a backup-and-copy sequence:

```bash
BACKUP="${TARGET_NIM_PLUGIN}.backup.$(date +%Y%m%d%H%M%S)"
if [ -d "$TARGET_NIM_PLUGIN" ]; then
  cp -R "$TARGET_NIM_PLUGIN" "$BACKUP"
  rm -rf "$TARGET_NIM_PLUGIN"
fi
mkdir -p "$TARGET_NIM_PLUGIN"
cp -R "$REPO_DIR/plugins/nim/." "$TARGET_NIM_PLUGIN/"
```

If copying fails after deleting the target, restore the backup before reporting failure.

## Verify

Always verify that the plugin still has manifests and skills:

```bash
test -d "$TARGET_NIM_PLUGIN/skills"
test -f "$TARGET_NIM_PLUGIN/skills/nim-generate/SKILL.md"
```

When the user expects a newly added skill, verify that exact folder too:

```bash
test -f "$TARGET_NIM_PLUGIN/skills/<expected-skill>/SKILL.md"
```

For the human generator update, the expected folder is:

```bash
test -f "$TARGET_NIM_PLUGIN/skills/nim-person-generator/SKILL.md"
```

If verification fails, report the missing file and do not claim the update succeeded.

## Final Message

On success, answer in the user's language and keep it short:

```text
Готово, я обновил Nim-плагин и его скиллы. Открой новый чат, потому что текущий чат уже загрузил старый список скиллов и не увидит обновление.
```

Mention the installed path only when the user is debugging the update.

## Test Fixture

To test this skill without touching a live installation:

1. Clone `https://github.com/nim-video/skills`.
2. Check out the commit before the target skill was added, for example `4b23fd8` before `f15438e Add human generator SKILL`.
3. Copy that old `plugins/nim` directory to a temporary installed-plugin target.
4. Run the same update steps with `INSTALLED_NIM_PLUGIN` pointed at that temporary target.
5. Verify that `skills/nim-person-generator/SKILL.md` appears after the copy.
