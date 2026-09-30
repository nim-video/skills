/**
 * Sets the plugin version in all five manifests and refreshes the README badges.
 *
 *   node scripts/bump-version.ts minor     # a new skill
 *   node scripts/bump-version.ts patch     # a change to an existing skill
 *   node scripts/bump-version.ts 0.6.0     # an explicit version; also re-syncs manifests and badges
 *
 * Bump once per pull request: minor and patch refuse to bump again when this branch is already
 * ahead of origin/main, unless you pass --force.
 */
import { parseArgs } from 'node:util';
import {
  PRIMARY_MANIFEST,
  README,
  SKILLS_BADGE,
  UPDATE_SKILL,
  UPDATE_SKILL_VERSION,
  VERSION_BADGE,
  VERSION_FILES,
  bumpSemver,
  compareSemver,
  isSemver,
  listSkills,
  readText,
  readVersionAt,
  readVersions,
  writeText,
} from './lib.ts';

const USAGE = 'usage: node scripts/bump-version.ts <major|minor|patch|X.Y.Z> [--force]';
const VERSION_FIELD = /("version"\s*:\s*")[^"]*(")/g;

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: { force: { type: 'boolean', default: false } },
});
const [target] = positionals;
if (target === undefined || positionals.length > 1) {
  fail(USAGE);
}

const previous = readVersions().find(({ file }) => file === PRIMARY_MANIFEST)?.version;
const next = nextVersion(target);

// Prepare every file before writing any, so a failure leaves the tree untouched.
const updates = VERSION_FILES.map(({ file }) => {
  const text = readText(file);
  const count = text.match(VERSION_FIELD)?.length ?? 0;
  if (count !== 1) {
    fail(`${file}: expected exactly one "version" field, found ${count}`);
  }
  return { file, text: text.replace(VERSION_FIELD, `$1${next}$2`) };
});

const { skills } = listSkills();
let readme = readText(README);
if (VERSION_BADGE.test(readme)) {
  readme = readme.replace(VERSION_BADGE, `$1${next}$3`);
} else {
  console.warn(`! ${README}: version badge not found`);
}
if (SKILLS_BADGE.test(readme)) {
  readme = readme.replace(SKILLS_BADGE, `$1${skills.length}$3`);
} else {
  console.warn(`! ${README}: skills badge not found`);
}

const updateSkill = readText(UPDATE_SKILL);
if (!UPDATE_SKILL_VERSION.test(updateSkill)) {
  fail(`${UPDATE_SKILL}: the "Installed plugin version" line is missing`);
}

for (const { file, text } of updates) {
  writeText(file, text);
}
writeText(README, readme);
writeText(UPDATE_SKILL, updateSkill.replace(UPDATE_SKILL_VERSION, `$1${next}$3`));

console.log(`${previous ?? 'unknown'} → ${next}`);
for (const { file } of updates) {
  console.log(`  ${file}`);
}
console.log(`  ${README} (version badge ${next}, skills badge ${skills.length})`);
console.log(`  ${UPDATE_SKILL} (installed plugin version ${next})`);

function nextVersion(requested: string): string {
  if (isSemver(requested)) {
    return requested;
  }
  if (requested !== 'major' && requested !== 'minor' && requested !== 'patch') {
    fail(USAGE);
  }
  const versions = readVersions();
  const current = versions.find(({ file }) => file === PRIMARY_MANIFEST)?.version;
  if (!isSemver(current) || versions.some(({ version }) => version !== current)) {
    const found = versions.map(({ file, version, problem }) => `${file}: ${version ?? problem}`).join('; ');
    fail(`the manifests disagree on the version (${found}); pass an explicit X.Y.Z`);
  }
  const onMain = readVersionAt('origin/main');
  if (!values.force && isSemver(onMain) && compareSemver(current, onMain) > 0) {
    fail(`this branch already bumped the version (${onMain} on origin/main, ${current} here); bump once per pull request, or pass --force`);
  }
  return bumpSemver(current, requested);
}

function fail(message: string): never {
  console.error(message);
  process.exit(1);
}
