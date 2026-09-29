/**
 * Mirrors contributor skills from .agents/skills (read by Codex; the copy you edit) into
 * .claude/skills (read by Claude Code). check-skills.ts fails when the two drift.
 *
 *   node scripts/sync-agent-skills.ts
 */
import { cpSync, existsSync, readdirSync, rmSync } from 'node:fs';
import path from 'node:path';
import { AGENT_SKILLS_DIR, CLAUDE_SKILLS_DIR, ROOT, git } from './lib.ts';

const source = path.join(ROOT, AGENT_SKILLS_DIR);
const skills = existsSync(source)
  ? readdirSync(source, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name)
  : [];

for (const skill of skills) {
  const target = path.join(ROOT, CLAUDE_SKILLS_DIR, skill);
  rmSync(target, { recursive: true, force: true });
  cpSync(path.join(source, skill), target, { recursive: true });
  console.log(`synced ${CLAUDE_SKILLS_DIR}/${skill}`);
}

// Drop mirrored skills whose source is gone. Only folders git tracks, so nothing unrecoverable is deleted.
const mirrored = git(['ls-files', '-z', '--', CLAUDE_SKILLS_DIR])
  .split('\0')
  .filter((file) => file !== '')
  .map((file) => file.slice(CLAUDE_SKILLS_DIR.length + 1).split('/')[0] ?? '');
for (const skill of new Set(mirrored)) {
  if (skill !== '' && !skills.includes(skill)) {
    rmSync(path.join(ROOT, CLAUDE_SKILLS_DIR, skill), { recursive: true, force: true });
    console.log(`removed ${CLAUDE_SKILLS_DIR}/${skill}`);
  }
}
