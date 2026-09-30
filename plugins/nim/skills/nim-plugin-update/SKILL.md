---
name: nim-plugin-update
description: >-
  Keeps the Nim plugin up to date and installs it on request. Use once at the
  start of any conversation that works with Nim (image or video generation,
  editing, templates, upscaling, credits, or any other Nim skill or Nim MCP
  tool), before the first other Nim tool call, and whenever the user asks to
  install, update, reinstall, or check the version of the Nim plugin or Nim
  skills. Calls check_plugin_update and, when a newer version exists, offers a
  one-click update without blocking the user's task.
---

# Nim plugin update

Installed plugin version: `0.6.0`

## When to run

- Once per conversation, before your first other Nim tool call. Skip it if you already checked in this conversation.
- Whenever the user asks to install, update, or check the version of the Nim plugin or skills.

## Check

Call `check_plugin_update` with `installed_version` set to the installed plugin version above. Then act on `status`:

- `up_to_date` or `unavailable`: don't mention it; continue with the user's request.
- `update_available`: tell the user in one sentence that Nim plugin `latest_version` is available (they have `installed_version`) and that updating takes one click. Continue with their request; install the update when they agree, now or later in the conversation. If they decline, don't offer it again in this conversation.
- `not_installed`: only returned without `installed_version`; install when the user asked for it.

## Install or update in a Claude chat

In Claude Desktop or claude.ai, the plugin is a `.plugin` file the user saves from the chat.

1. Download `download_url` with your code tool, for example `curl -fsSL -o nim.plugin "<download_url>"`.
2. Compare the file's SHA-256 (`sha256sum nim.plugin` or `shasum -a 256 nim.plugin`) with `sha256` from the tool. If they differ, delete the file, tell the user the download failed, and stop.
3. Share `nim.plugin` with the user exactly as downloaded: don't unpack, rename, or rebuild it. The chat shows it as a plugin card with a Save button.
4. Tell the user to click Save: it replaces the installed version, and new chats use the updated skills.

If you can't download files, give the user `download_url`, ask them to download the file and attach it here, and share that file back unchanged.

## Update in Claude Code, Codex, or Cursor

Don't download the `.plugin` file here: the plugin updates from its marketplace.

- Claude Code: `claude plugin marketplace update nim`, then `claude plugin update nim@nim`, then restart Claude Code.
- Codex and Cursor: update the Nim plugin from the plugin marketplace.
