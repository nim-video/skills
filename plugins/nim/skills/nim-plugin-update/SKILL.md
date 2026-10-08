---
name: nim-plugin-update
description: >-
  Keeps the Nim plugin connected and up to date. Use once at the start of any
  conversation that works with Nim (image or video generation, editing,
  templates, upscaling, credits, or any other Nim skill or Nim MCP tool),
  before the first other Nim tool call, including when the Nim tools are not
  available yet, and whenever the user asks to install, connect, update, or
  check the version of the Nim plugin or Nim skills. Shows a Connect button
  when the Nim connector isn't connected, calls check_plugin_update, and offers
  a one-click update without blocking the user's task.
---

# Nim plugin update

Installed plugin version: `0.7.5`

## Connect Nim first

The Nim tools come from the Nim connector that the Nim plugin adds. If `check_plugin_update` and the other Nim tools aren't available in this conversation, the connector isn't connected yet or is off in this chat. Don't tell the user Nim is unavailable and don't switch to another provider. Instead:

1. Call `search_mcp_registry` with `keywords: ["nim"]`.
2. If a result has `url` `https://mcp.nim.video/mcp`, call `suggest_connectors` with its `directoryUuid` and `keywords: ["videos"]`. The user gets a Connect button. Tell them in one sentence to click Connect and sign in to Nim.
3. If no result has that URL, the Nim connector hasn't been connected yet: until then it lives only inside the Nim plugin, where search can't find it. Give the user these steps:
   - Claude Desktop or claude.ai: open **Customize → Plugins → Nim → Connectors**, click **Connect** next to Nim, and sign in to Nim.
   - Claude Code: run `/mcp`, select the Nim server, and choose **Authenticate**.
   - ChatGPT, Codex, or Cursor: sign in to Nim when the app asks on the first Nim tool call, or from its plugin or MCP settings.

Continue the user's request once the Nim tools are available. After the first connection, the connector is found by search, so later reconnects get the Connect button.

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

## Install or update in ChatGPT or the Codex app

The ChatGPT desktop app and the Codex app install the Nim plugin from an archive the user uploads; you can't add it for them. ChatGPT marks the plugin **Desktop only** because it bundles the Nim MCP server, so it doesn't run in ChatGPT on the web.

1. Give the user `https://github.com/nim-video/skills/releases/latest/download/nim-chatgpt.zip` to download. If you can download files, download it and hand it to them unchanged instead.
2. Tell them to open **Plugins**, choose **New Plugin**, select `nim-chatgpt.zip`, and click **Add plugin**. When updating, if the old Nim plugin stays next to the new one, remove the old one.
3. Tell them to start a new chat and sign in to Nim when asked.

Don't add the archive when the Nim plugin is already installed from a marketplace (its skills are named `nim:…`): the skills would load twice. Update that install from its marketplace instead.

## Update a marketplace install (Claude Code, Codex, Cursor)

When the plugin came from a marketplace, don't download files here: it updates from its marketplace.

- Claude Code: `claude plugin marketplace update nim`, then `claude plugin update nim@nim`, then restart Claude Code.
- Codex: `codex plugin marketplace upgrade nim`, then `codex plugin add nim@nim`, then restart Codex.
- Cursor: update the Nim plugin from the plugin marketplace.
