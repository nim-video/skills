/**
 * Shared helpers for the repo tooling in scripts/. Node 24+ runs these files directly with native
 * TypeScript type stripping, so they stay dependency-free and use erasable syntax only.
 */
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

export type Json = string | number | boolean | null | Json[] | { [key: string]: Json };
export type JsonObject = { [key: string]: Json };

export const ROOT = path.resolve(import.meta.dirname, '..');
export const PLUGIN_NAME = 'nim';
export const PLUGIN_DIR = 'plugins/nim';
export const SKILLS_DIR = `${PLUGIN_DIR}/skills`;
export const SKILL_PREFIX = `${PLUGIN_NAME}-`;
export const README = 'README.md';
export const PRIMARY_MANIFEST = `${PLUGIN_DIR}/.claude-plugin/plugin.json`;

/** Contributor-only skills: Codex reads `.agents/skills` (the copy you edit), Claude Code reads the `.claude/skills` mirror. */
export const AGENT_SKILLS_DIR = '.agents/skills';
export const CLAUDE_SKILLS_DIR = '.claude/skills';

export const VERSION_BADGE = /(img\.shields\.io\/badge\/version-)(\d+\.\d+\.\d+)(-)/;
export const SKILLS_BADGE = /(img\.shields\.io\/badge\/skills-)(\d+)(-)/;

/**
 * The update skill states the installed plugin version in its body, which every host shows the
 * agent, rather than relying on frontmatter it may not show. bump-version.ts keeps it in sync.
 */
export const UPDATE_SKILL = `${SKILLS_DIR}/nim-plugin-update/SKILL.md`;
export const UPDATE_SKILL_VERSION = /(Installed plugin version: `)(\d+\.\d+\.\d+)(`)/;

type VersionFile = {
  file: string;
  field: string;
  pick: (manifest: JsonObject) => Json | undefined;
};

/**
 * Every manifest that carries the plugin version. Clients cache the plugin by version and only
 * deliver a change when the version goes up, so all five move together. Claude Code's rule:
 * https://code.claude.com/docs/en/plugins/host-marketplace#release-a-new-version
 */
export const VERSION_FILES: VersionFile[] = [
  {
    file: '.claude-plugin/marketplace.json',
    field: `plugins[${PLUGIN_NAME}].version`,
    pick: (manifest) => {
      const entry = Array.isArray(manifest.plugins)
        ? manifest.plugins.find((plugin) => isObject(plugin) && plugin.name === PLUGIN_NAME)
        : undefined;
      return isObject(entry) ? entry.version : undefined;
    },
  },
  {
    file: '.cursor-plugin/marketplace.json',
    field: 'metadata.version',
    pick: (manifest) => (isObject(manifest.metadata) ? manifest.metadata.version : undefined),
  },
  { file: PRIMARY_MANIFEST, field: 'version', pick: (manifest) => manifest.version },
  { file: `${PLUGIN_DIR}/.codex-plugin/plugin.json`, field: 'version', pick: (manifest) => manifest.version },
  { file: `${PLUGIN_DIR}/.cursor-plugin/plugin.json`, field: 'version', pick: (manifest) => manifest.version },
];

export function isObject(value: Json | undefined): value is JsonObject {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function readText(file: string): string {
  return readFileSync(path.join(ROOT, file), 'utf8');
}

export function writeText(file: string, text: string): void {
  writeFileSync(path.join(ROOT, file), text);
}

export function exists(file: string): boolean {
  return existsSync(path.join(ROOT, file));
}

export function parseJsonObject(text: string, file: string): JsonObject {
  const data: Json = JSON.parse(text);
  if (!isObject(data)) {
    throw new Error(`${file} must contain a JSON object`);
  }
  return data;
}

export function git(args: string[]): string {
  return execFileSync('git', args, { cwd: ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
}

function nulSeparated(output: string): string[] {
  return output.split('\0').filter((entry) => entry !== '');
}

/** Tracked files plus untracked ones git would add, so a new skill is checked before `git add`. */
export function listFiles(dir: string): string[] {
  const files = nulSeparated(git(['ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', dir]));
  return [...new Set(files)].filter((file) => exists(file));
}

/** Paths changed since `ref`, including uncommitted and untracked files. */
export function changedSince(ref: string): string[] {
  const files = [
    ...nulSeparated(git(['diff', '-z', '--name-only', ref])),
    ...nulSeparated(git(['ls-files', '-z', '--others', '--exclude-standard'])),
  ];
  return [...new Set(files)];
}

export type ManifestVersion = { file: string; field: string; version?: string; problem?: string };

export function readVersions(): ManifestVersion[] {
  return VERSION_FILES.map(({ file, field, pick }) => {
    try {
      const value = pick(parseJsonObject(readText(file), file));
      return typeof value === 'string' ? { file, field, version: value } : { file, field, problem: `${field} is missing` };
    } catch (error) {
      return { file, field, problem: error instanceof Error ? error.message : String(error) };
    }
  });
}

/** The plugin version at a git ref, or undefined when the ref or the manifest doesn't exist there. */
export function readVersionAt(ref: string): string | undefined {
  try {
    const { version } = parseJsonObject(git(['show', `${ref}:${PRIMARY_MANIFEST}`]), PRIMARY_MANIFEST);
    return typeof version === 'string' ? version : undefined;
  } catch {
    return undefined;
  }
}

const SEMVER = /^\d+\.\d+\.\d+$/;

export function isSemver(version: string | undefined): version is string {
  return version !== undefined && SEMVER.test(version);
}

/** Negative when a < b, zero when equal, positive when a > b. Both must be X.Y.Z. */
export function compareSemver(a: string, b: string): number {
  const left = a.split('.').map(Number);
  const right = b.split('.').map(Number);
  for (let i = 0; i < 3; i += 1) {
    const diff = (left[i] ?? 0) - (right[i] ?? 0);
    if (diff !== 0) {
      return diff;
    }
  }
  return 0;
}

export type BumpPart = 'major' | 'minor' | 'patch';

export function bumpSemver(version: string, part: BumpPart): string {
  const [major = 0, minor = 0, patch = 0] = version.split('.').map(Number);
  if (part === 'major') {
    return `${major + 1}.0.0`;
  }
  if (part === 'minor') {
    return `${major}.${minor + 1}.0`;
  }
  return `${major}.${minor}.${patch + 1}`;
}

/** Skill folder names under plugins/nim/skills, and any files sitting directly in that folder. */
export function listSkills(): { skills: string[]; looseFiles: string[] } {
  const skills = new Set<string>();
  const looseFiles: string[] = [];
  for (const file of listFiles(SKILLS_DIR)) {
    const rest = file.slice(SKILLS_DIR.length + 1);
    const slash = rest.indexOf('/');
    if (slash === -1) {
      looseFiles.push(file);
    } else {
      skills.add(rest.slice(0, slash));
    }
  }
  return { skills: [...skills].sort(), looseFiles };
}

/**
 * Minimal SKILL.md frontmatter reader: top-level `key: value` pairs, folded (`>`) and literal (`|`)
 * blocks, quoted strings, and plain multi-line scalars; a nested map comes back as its raw text.
 * Accepts CRLF files, which some existing skills use. Enough for the checks here without a YAML
 * dependency.
 */
export function readFrontmatter(markdown: string): Map<string, string> | undefined {
  const text = markdown.replace(/^﻿/, '').replace(/\r\n?/g, '\n');
  if (!text.startsWith('---\n')) {
    return undefined;
  }
  const end = text.indexOf('\n---', 3);
  if (end === -1) {
    return undefined;
  }
  const lines = text.slice(4, end).split('\n');
  const fields = new Map<string, string>();
  for (let i = 0; i < lines.length; i += 1) {
    const match = /^([\w-]+):[ \t]*(.*)$/.exec(lines[i] ?? '');
    if (!match) {
      continue;
    }
    const block: string[] = [];
    while (i + 1 < lines.length && /^(\s|$)/.test(lines[i + 1] ?? '')) {
      i += 1;
      block.push(lines[i] ?? '');
    }
    fields.set(match[1] ?? '', scalar((match[2] ?? '').trim(), block));
  }
  return fields;
}

function scalar(value: string, block: string[]): string {
  const indents = block.filter((line) => line.trim() !== '').map((line) => line.length - line.trimStart().length);
  const indent = indents.length > 0 ? Math.min(...indents) : 0;
  const lines = block.map((line) => line.slice(indent).trimEnd());
  if (/^[>|][+-]?$/.test(value)) {
    const body = lines.join('\n').trim();
    // Literal blocks keep line breaks; folded blocks join lines and keep blank lines as breaks.
    return value.startsWith('|')
      ? body
      : body
          .split(/\n{2,}/)
          .map((paragraph) => paragraph.replace(/\n/g, ' '))
          .join('\n');
  }
  const joined = [value, ...lines.map((line) => line.trim())].filter((part) => part !== '').join(' ');
  const quoted = /^(["'])([\s\S]*)\1$/.exec(joined);
  return quoted ? (quoted[2] ?? '') : joined;
}

export type SkillRow = { line: number; name: string; invoke: string; summary: string };
export type SkillsTable = { rows: SkillRow[]; lastLine: number; nextLine?: string };

/** Rows of the table under "## Skills" in README.md. Line numbers are 1-based. */
export function readSkillsTable(readme: string): SkillsTable | undefined {
  const lines = readme.replace(/\r\n?/g, '\n').split('\n');
  const heading = lines.findIndex((line) => /^##\s+Skills\s*$/.test(line));
  if (heading === -1) {
    return undefined;
  }
  let start = heading + 1;
  while (start < lines.length && !lines[start]?.startsWith('|') && !lines[start]?.startsWith('## ')) {
    start += 1;
  }
  if (!lines[start]?.startsWith('|')) {
    return undefined;
  }
  let end = start;
  while (end < lines.length && lines[end]?.startsWith('|')) {
    end += 1;
  }
  const rows: SkillRow[] = [];
  for (let i = start; i < end; i += 1) {
    const match = /^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|(.*)\|\s*$/.exec(lines[i] ?? '');
    if (match) {
      rows.push({ line: i + 1, name: match[1] ?? '', invoke: match[2] ?? '', summary: (match[3] ?? '').trim() });
    }
  }
  return { rows, lastLine: end, nextLine: lines[end] };
}
