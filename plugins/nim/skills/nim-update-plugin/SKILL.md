---
name: nim-update-plugin
description: Update the installed Nim plugin and bundled Nim skills from the GitHub repository with the same behavior across Codex, Claude Code, Cursor, and generic file-based agents. Use when the user asks to update, refresh, pull, reinstall, or sync Nim skills or the Nim plugin from GitHub, especially after a new Nim skill or plugin version was released and the current chat cannot see it yet.
---

# Nim Update Plugin

## Contract

Provide the same user-visible behavior on every host:

1. Refresh the Nim marketplace/source repository from `https://github.com/nim-video/skills`.
2. Refresh or reinstall the installed Nim plugin through the host's native plugin manager when available.
3. Fall back to a plain git + file-copy update only when the host has no plugin manager or is folder-based.
4. Verify the active installed plugin path and expected skill files.
5. Tell the user to open a new chat or restart the agent because the current chat loaded the old skill list.

Do not treat `git pull` alone as a complete update. A plugin update usually has two layers: the marketplace/source clone and the installed plugin cache or registry entry.

## Source Refresh

When the host has a marketplace command, use it. Otherwise refresh a local clone:

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

If the user requested a branch, tag, or commit, check out that ref instead of `origin/main`.

## Native Adapters

Prefer a native adapter whenever it exists. Native adapters know how to update plugin registry state, versioned cache directories, MCP/tool metadata, and any host-specific bookkeeping.

### Codex

Use Codex's plugin manager:

```bash
codex plugin marketplace upgrade nim
codex plugin add nim@nim --json
```

Read `installedPath` from the JSON output of `codex plugin add nim@nim --json`. Use that path for verification. Do not guess a versioned cache directory such as `0.1.0`.

If the normal refresh fails and the user approves a stronger reinstall, use:

```bash
codex plugin remove nim@nim
codex plugin add nim@nim --json
```

Treat remove/add as a last resort because it may affect enable/auth state.

### Claude Code

Use Claude Code's plugin manager:

```bash
claude plugin marketplace update nim
claude plugin update nim@nim
```

If the command name differs in the user's Claude Code version, use the equivalent UI or slash-command flow:

```text
/plugin install nim@nim
```

after updating the marketplace. For older third-party marketplace behavior, the manual fallback is:

```bash
cd "$HOME/.claude/plugins/marketplaces/nim" && git pull --ff-only
```

then reinstall/update `nim@nim` through Claude Code. Restart Claude Code after a successful update.

### Other Hosts

Use the host's equivalent "marketplace update" plus "plugin update/reinstall" command. Preserve user authentication and settings. Do not delete user config unless the host's documented reinstall flow requires it.

If no native plugin manager exists, use the file-copy fallback.

## File-Copy Fallback

Use this only for folder-based plugin loaders, local development fixtures, or hosts with no plugin manager.

First identify the installed Nim plugin directory. Prefer the current skill path when available. For example:

```text
/Users/name/.codex/plugins/cache/nim/nim/0.1.0/skills/nim-update-plugin/SKILL.md
```

means:

```text
/Users/name/.codex/plugins/cache/nim/nim/0.1.0
```

Treat the version segment as an example only. Do not hardcode it.

If the current skill path is unavailable, search likely roots:

```bash
find "$HOME/.codex" "$HOME/.claude" "$HOME/.cursor" -path '*/plugins/nim*' -type d 2>/dev/null
```

Choose a directory containing `skills/` and a plugin manifest:

```bash
test -d "$INSTALLED_NIM_PLUGIN/skills"
test -f "$INSTALLED_NIM_PLUGIN/.codex-plugin/plugin.json" \
  -o -f "$INSTALLED_NIM_PLUGIN/.claude-plugin/plugin.json" \
  -o -f "$INSTALLED_NIM_PLUGIN/.cursor-plugin/plugin.json"
```

Read the latest version from the refreshed repository:

```bash
LATEST_VERSION=$(
  sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
    "$REPO_DIR/plugins/nim/.codex-plugin/plugin.json" | head -1
)
test -n "$LATEST_VERSION"
```

If the installed plugin lives in a versioned cache directory, sync into the sibling for the latest version:

```bash
case "$INSTALLED_NIM_PLUGIN" in
  */plugins/cache/nim/nim/*)
    TARGET_NIM_PLUGIN="$(dirname "$INSTALLED_NIM_PLUGIN")/$LATEST_VERSION"
    ;;
  *)
    TARGET_NIM_PLUGIN="$INSTALLED_NIM_PLUGIN"
    ;;
esac
```

Copy with `rsync` when available:

```bash
rsync -a --delete \
  --exclude '.git' \
  "$REPO_DIR/plugins/nim/" \
  "$TARGET_NIM_PLUGIN/"
```

If `rsync` is unavailable:

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

## Verification

After any adapter or fallback, verify the active installed plugin path. For native adapters, rediscover the path from the command output or host state instead of reusing an old path.

Always verify:

```bash
test -d "$TARGET_NIM_PLUGIN/skills"
test -f "$TARGET_NIM_PLUGIN/skills/nim-generate/SKILL.md"
```

When the user expects a newly added skill, verify that exact folder:

```bash
test -f "$TARGET_NIM_PLUGIN/skills/<expected-skill>/SKILL.md"
```

For the human generator update:

```bash
test -f "$TARGET_NIM_PLUGIN/skills/nim-person-generator/SKILL.md"
```

When possible, also compare the installed plugin version with the repository manifest version. If verification fails, report the missing file or stale version and do not claim success.

## Optional Diagnostics

If the host exposes installed commit or version metadata, compare it against the refreshed marketplace remote and show a short changelog before making risky changes:

```bash
git -C "$REPO_DIR" log --oneline <installed-sha>..origin/main -- plugins/nim
```

Ask before destructive remove/reinstall flows. A normal marketplace update plus plugin update does not need extra confirmation when the user explicitly asked to update Nim.

## Final Message

On success, answer in the user's language and keep it short:

```text
Готово, я обновил Nim-плагин и его скиллы. Открой новый чат, потому что текущий чат уже загрузил старый список скиллов и не увидит обновление.
```

Mention paths and versions only when the user is debugging the update.

## Test Fixture

To test without touching a live installation:

1. Clone `https://github.com/nim-video/skills`.
2. Check out the commit before the target skill was added, for example `4b23fd8` before `f15438e Add human generator SKILL`.
3. Copy that old `plugins/nim` directory to a temporary installed-plugin target.
4. Run the file-copy fallback with `INSTALLED_NIM_PLUGIN` pointed at that temporary target.
5. Verify that `skills/nim-person-generator/SKILL.md` or another expected new skill appears after the update.
