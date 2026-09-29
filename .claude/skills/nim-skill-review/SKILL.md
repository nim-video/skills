---
name: nim-skill-review
description: >-
  Review a new or changed skill in the nim-video/skills repository before it
  is merged: run the repo checks, fix packaging (name prefix, README row,
  version bump, stray files), and flag trigger overlaps with existing skills.
  Use when adding or editing anything under plugins/nim/, before opening a
  pull request, or when asked to review a skill pull request in this
  repository.
metadata:
  internal: true
---

# Nim skill review

Checks a skill change against this repository's conventions in `AGENTS.md`, so the author catches packaging problems before a maintainer does. A skill the team has already tested is accepted as it is: fix the packaging, but report problems with its logic, prompts, or scripts instead of rewriting them.

## 1. Find the change

```sh
git fetch origin main
git diff --stat origin/main...HEAD
git status --short
```

Identify the skill folder under `plugins/nim/skills/`. If the change spans several skills, or reaches beyond that folder, `README.md`, and the version manifests, ask the author to split it unless a maintainer asked for it.

## 2. Run the checks

```sh
node scripts/check-skills.ts --base origin/main
```

Fix every error; each message says how. For the version, run `node scripts/bump-version.ts minor` for a new skill or `patch` for a change. Bump once per pull request; the script refuses a second bump. Rerun the check until it passes.

When you review someone else's pull request, list the errors instead of pushing fixes, unless you're asked to push.

## 3. Review what the script can't

Read the changed `SKILL.md` and README lines, and sort each finding into blocking or a suggestion.

Blocking:

- **README row**: one sentence that tells a user what they get, not instructions for the agent.

Suggestions, for the author to decide:

- **Trigger overlap**: run `node scripts/check-skills.ts --list` and compare the descriptions. If this skill and another would both fire on the same request (several skills already write Seedance prompts), suggest narrowing the description or adding "Not for …; use `nim-…`".
- **Nim tools**: the skill should name the Nim MCP tools and follow the model's `generationContract` from `models_explore`, rather than hard-coding model IDs or telling the agent to find "an equivalent tool".
- **Maintainer notes**: instructions about editing the skill itself, or how it was developed, ship to every user.
- **Paid calls**: generations, upscales, templates, and credit purchases spend the user's credits. Flag flows that start or retry them without the user's go-ahead.
- **Size**: long examples and reference tables belong in `references/`, linked from `SKILL.md`.
- **README bullets**: optional; one short line for users.

## 4. Report

Reply in three short parts: the check result, blocking issues (fixed or still open), and suggestions. Skip empty parts.
