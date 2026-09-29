/**
 * Checks the plugin packaging conventions from AGENTS.md. CI runs it on every pull request; run it
 * before you push:
 *
 *   node scripts/check-skills.ts --base origin/main   # what CI runs
 *   node scripts/check-skills.ts                      # skips the checks that need a base branch
 *   node scripts/check-skills.ts --list               # every skill's description, to compare triggers
 *
 * With --base, the plugin version must be higher than on the base branch whenever anything under
 * plugins/nim/ changes, and a skill pull request that reaches beyond one skill gets warnings.
 */
import { parseArgs } from 'node:util';
import {
  AGENT_SKILLS_DIR,
  CLAUDE_SKILLS_DIR,
  PLUGIN_DIR,
  PLUGIN_NAME,
  PRIMARY_MANIFEST,
  README,
  SKILLS_BADGE,
  SKILLS_DIR,
  SKILL_PREFIX,
  VERSION_BADGE,
  VERSION_FILES,
  changedSince,
  compareSemver,
  exists,
  git,
  isSemver,
  listFiles,
  listSkills,
  readFrontmatter,
  readSkillsTable,
  readText,
  readVersionAt,
  readVersions,
} from './lib.ts';

type Problem = { level: 'error' | 'warning'; message: string; file?: string; line?: number };

const NAME = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const MAX_NAME = 64;
const MAX_DESCRIPTION = 1024;
const STRAY_FILES = [/(^|\/)\.DS_Store$/, /(^|\/)Thumbs\.db$/, /(^|\/)\.env$/, /(^|\/)__pycache__\//, /\.pyc$/, /(^|\/)node_modules\//];

const { values } = parseArgs({
  options: {
    base: { type: 'string' },
    list: { type: 'boolean', default: false },
  },
});

const problems: Problem[] = [];
const { skills, looseFiles } = listSkills();

if (values.list) {
  for (const skill of skills) {
    const file = `${SKILLS_DIR}/${skill}/SKILL.md`;
    const description = exists(file) ? readFrontmatter(readText(file))?.get('description') : undefined;
    console.log(`${skill}\n  ${description ?? '(no description)'}\n`);
  }
} else {
  const version = checkVersions();
  checkSkills();
  checkReadme(version);
  checkShippedFiles();
  checkContributorSkills();
  if (values.base) {
    checkAgainstBase(values.base, version);
  }
  report(version);
}

function error(message: string, file?: string, line?: number): void {
  problems.push({ level: 'error', message, file, line });
}

function warning(message: string, file?: string, line?: number): void {
  problems.push({ level: 'warning', message, file, line });
}

/** All five manifests carry the same X.Y.Z version. Returns it. */
function checkVersions(): string | undefined {
  const versions = readVersions();
  for (const { file, field, version, problem } of versions) {
    if (problem) {
      error(problem, file);
    } else if (!isSemver(version)) {
      error(`${field} must be an X.Y.Z version, found "${version}"`, file);
    }
  }
  const primary = versions.find(({ file }) => file === PRIMARY_MANIFEST)?.version;
  if (!isSemver(primary)) {
    return undefined;
  }
  const differing = versions.filter(({ version }) => isSemver(version) && version !== primary);
  if (differing.length > 0) {
    const list = differing.map(({ file, version }) => `${file} (${version})`).join(', ');
    error(`every manifest must carry the version from ${PRIMARY_MANIFEST} (${primary}); differs in ${list}. Run: node scripts/bump-version.ts ${primary}`);
  }
  return primary;
}

function checkSkills(): void {
  for (const file of looseFiles) {
    error(`files belong inside a skill folder: ${SKILLS_DIR}/<skill>/`, file);
  }
  for (const skill of skills) {
    const file = `${SKILLS_DIR}/${skill}/SKILL.md`;
    if (!exists(file)) {
      error('each skill folder needs a SKILL.md', `${SKILLS_DIR}/${skill}`);
      continue;
    }
    const frontmatter = readFrontmatter(readText(file));
    if (!frontmatter) {
      error('SKILL.md must start with YAML frontmatter (between --- lines) with name and description', file, 1);
      continue;
    }
    const name = frontmatter.get('name') ?? '';
    if (name === '') {
      error('frontmatter needs a name', file);
    } else {
      if (name !== skill) {
        error(`name "${name}" must match the folder name "${skill}"`, file);
      }
      if (!name.startsWith(SKILL_PREFIX)) {
        error(`name "${name}" must start with "${SKILL_PREFIX}"; rename the folder too`, file);
      }
      if (!NAME.test(name) || name.length > MAX_NAME) {
        error(`name "${name}" must be lowercase kebab-case, at most ${MAX_NAME} characters`, file);
      }
    }
    const description = frontmatter.get('description') ?? '';
    if (description === '') {
      error('frontmatter needs a description: what the skill does and when to use it', file);
    } else if (description.length > MAX_DESCRIPTION) {
      error(`description is ${description.length} characters; keep it within ${MAX_DESCRIPTION}`, file);
    }
  }
}

function checkReadme(version: string | undefined): void {
  const readme = readText(README);
  const versionBadge = VERSION_BADGE.exec(readme)?.[2];
  if (versionBadge === undefined) {
    warning('version badge not found', README);
  } else if (version && versionBadge !== version) {
    error(`version badge says ${versionBadge}, the manifests say ${version}. Run: node scripts/bump-version.ts ${version}`, README, lineOf(readme, VERSION_BADGE));
  }
  const skillsBadge = SKILLS_BADGE.exec(readme)?.[2];
  if (skillsBadge === undefined) {
    warning('skills badge not found', README);
  } else if (Number(skillsBadge) !== skills.length) {
    error(
      `skills badge says ${skillsBadge}, but there are ${skills.length} skills. node scripts/bump-version.ts minor (or patch) updates it; if this branch already bumped, pass the current version (${version ?? 'X.Y.Z'}) instead`,
      README,
      lineOf(readme, SKILLS_BADGE),
    );
  }

  const table = readSkillsTable(readme);
  if (!table) {
    error('README.md needs a "## Skills" section with the skills table', README);
    return;
  }
  const listed = new Set<string>();
  for (const row of table.rows) {
    if (listed.has(row.name)) {
      error(`${row.name} has two rows`, README, row.line);
    }
    listed.add(row.name);
    if (!skills.includes(row.name)) {
      error(`row for ${row.name}, but ${SKILLS_DIR}/${row.name}/ doesn't exist`, README, row.line);
    }
    if (row.invoke !== `/${PLUGIN_NAME}:${row.name}`) {
      error(`the Invoke column for ${row.name} must be \`/${PLUGIN_NAME}:${row.name}\``, README, row.line);
    }
    if (row.summary === '') {
      error(`add a one-sentence, user-facing summary for ${row.name}`, README, row.line);
    }
  }
  for (const skill of skills.filter((name) => !listed.has(name))) {
    error(`add ${skill} to the Skills table: | \`${skill}\` | \`/${PLUGIN_NAME}:${skill}\` | One user-facing sentence. |`, README, table.lastLine);
  }
  if (table.nextLine !== undefined && table.nextLine.trim() !== '') {
    error('leave a blank line after the Skills table, or GitHub renders the next line as a table row', README, table.lastLine + 1);
  }
}

/** Everything under plugins/nim/ ships to users: no per-skill Codex metadata, no stray files. */
function checkShippedFiles(): void {
  for (const file of listFiles(PLUGIN_DIR)) {
    const inSkill = file.startsWith(`${SKILLS_DIR}/`) ? file.slice(SKILLS_DIR.length + 1) : undefined;
    if (inSkill !== undefined && /^[^/]+\/agents\/openai\.yaml$/.test(inSkill)) {
      error(`per-skill agents/openai.yaml isn't used here; Codex metadata lives in ${PLUGIN_DIR}/.codex-plugin/plugin.json`, file);
    } else if (STRAY_FILES.some((pattern) => pattern.test(file))) {
      error(`remove this stray file; everything under ${PLUGIN_DIR}/ ships to users`, file);
    }
  }
}

/** .claude/skills mirrors .agents/skills exactly, and contributor skills stay hidden from `npx skills add`. */
function checkContributorSkills(): void {
  const canonical = relativeFiles(AGENT_SKILLS_DIR);
  const mirror = relativeFiles(CLAUDE_SKILLS_DIR);
  const drifted = [...new Set([...canonical.keys(), ...mirror.keys()])].filter((key) => {
    const source = canonical.get(key);
    const copy = mirror.get(key);
    return source === undefined || copy === undefined || readText(source) !== readText(copy);
  });
  if (drifted.length > 0) {
    error(`${CLAUDE_SKILLS_DIR} must mirror ${AGENT_SKILLS_DIR}; out of sync: ${drifted.sort().join(', ')}. Edit ${AGENT_SKILLS_DIR}, then run: node scripts/sync-agent-skills.ts`);
  }
  for (const [key, file] of canonical) {
    const metadata = /^[^/]+\/SKILL\.md$/.test(key) ? (readFrontmatter(readText(file))?.get('metadata') ?? '') : undefined;
    if (metadata !== undefined && !/\binternal:\s*true\b/.test(metadata)) {
      error('contributor skills need `internal: true` under `metadata` in the frontmatter, so `npx skills add` skips them', file);
    }
  }
}

function checkAgainstBase(base: string, version: string | undefined): void {
  let mergeBase: string;
  try {
    mergeBase = git(['merge-base', base, 'HEAD']).trim();
  } catch {
    error(`can't find ${base}; fetch it first: git fetch origin main`);
    return;
  }
  const changed = changedSince(mergeBase);

  // Compare with the base tip, not the merge base: two pull requests that both bump 0.4.0 to 0.5.0
  // merge cleanly, and the second one would reach nobody.
  if (version && changed.some((file) => file.startsWith(`${PLUGIN_DIR}/`))) {
    const baseVersion = readVersionAt(base);
    if (isSemver(baseVersion) && compareSemver(version, baseVersion) <= 0) {
      error(
        `${PLUGIN_DIR}/ changed, so the version must go above ${baseVersion} (the version on ${base}); clients only update when it does. Run: node scripts/bump-version.ts minor for a new skill, or patch for a change`,
        PRIMARY_MANIFEST,
      );
    }
  }

  const touched = new Set(
    changed.filter((file) => file.startsWith(`${SKILLS_DIR}/`)).map((file) => file.slice(SKILLS_DIR.length + 1).split('/')[0] ?? ''),
  );
  if (touched.size === 0) {
    return;
  }
  if (touched.size > 1) {
    warning(`this change touches ${touched.size} skills (${[...touched].sort().join(', ')}); keep one skill per pull request`);
  }
  const packaging = new Set([README, ...VERSION_FILES.map(({ file }) => file)]);
  const beyond = changed.filter((file) => !file.startsWith(`${SKILLS_DIR}/`) && !packaging.has(file));
  if (beyond.length > 0) {
    warning(`a skill pull request usually changes only its skill folder, README.md, and the version manifests; this one also changes ${beyond.sort().join(', ')}`);
  }
}

function relativeFiles(dir: string): Map<string, string> {
  return new Map(listFiles(dir).map((file) => [file.slice(dir.length + 1), file]));
}

function lineOf(text: string, pattern: RegExp): number | undefined {
  const index = text.search(pattern);
  return index === -1 ? undefined : text.slice(0, index).split('\n').length;
}

function report(version: string | undefined): void {
  const annotate = process.env.GITHUB_ACTIONS === 'true';
  for (const { level, message, file, line } of problems) {
    if (annotate) {
      const location = [file ? `file=${file}` : '', line ? `line=${line}` : ''].filter((part) => part !== '').join(',');
      console.log(`::${level}${location ? ` ${location}` : ''}::${escapeAnnotation(message)}`);
    } else {
      const where = file ? `${file}${line ? `:${line}` : ''}: ` : '';
      console.log(`${level === 'error' ? '✗' : '!'} ${where}${message}`);
    }
  }
  const errors = problems.filter(({ level }) => level === 'error').length;
  const warnings = problems.length - errors;
  const warningNote = warnings > 0 ? `, ${warnings} warning${warnings === 1 ? '' : 's'}` : '';
  if (errors > 0) {
    console.log(`\n${errors} error${errors === 1 ? '' : 's'}${warningNote}. Conventions: AGENTS.md`);
    process.exitCode = 1;
  } else {
    console.log(`✓ ${skills.length} skills, version ${version ?? 'unknown'}${warningNote}`);
  }
}

/** GitHub Actions workflow commands need %, CR, and LF escaped. */
function escapeAnnotation(message: string): string {
  return message.replaceAll('%', '%25').replaceAll('\r', '%0D').replaceAll('\n', '%0A');
}
