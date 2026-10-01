import { type Dirent, readdirSync, readFileSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

/**
 * The SDKs that may only be imported inside packages/providers. The list is
 * deliberately explicit: adding one is an edit somebody reviews, not a pattern
 * that quietly starts matching a new package.
 */
export const CLOUD_SDK_PREFIXES = [
  '@google-cloud/',
  'googleapis',
  'google-auth-library',
  '@aws-sdk/',
  'aws-sdk',
  '@azure/',
  'firebase-admin',
] as const;

/** Where the rule does not apply, because holding the SDKs is what it is for. */
const EXEMPT = ['packages/providers'];

/** The trees the rule covers. Everything shipped is under one of these. */
const SEARCHED = ['apps', 'packages'];

const SKIP_DIRECTORIES = new Set(['node_modules', 'dist', '.next', '.turbo', 'coverage']);
const SOURCE = /\.(ts|tsx|js|jsx|mjs|cjs)$/;

export interface CloudSdkImport {
  /** Repository-relative and slash-separated, so a failure names a path a person can open. */
  file: string;
  line: number;
  specifier: string;
}

/**
 * Matches import, export-from, require and dynamic import, because all four reach
 * the same package and a rule that only reads the first is a rule with a gap.
 */
const SPECIFIER_PATTERNS = [
  /(?:^|\s)(?:import|export)\s[^;]*?from\s*['"]([^'"]+)['"]/gm,
  /(?:^|\s)import\s*['"]([^'"]+)['"]/gm,
  /\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)/gm,
  /\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)/gm,
];

function isCloudSdk(specifier: string): boolean {
  return CLOUD_SDK_PREFIXES.some((prefix) => specifier === prefix || specifier.startsWith(prefix));
}

function* sourceFiles(directory: string): Generator<string> {
  let entries: Dirent[];
  try {
    entries = readdirSync(directory, { withFileTypes: true });
  } catch {
    return;
  }

  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      if (SKIP_DIRECTORIES.has(entry.name) || entry.name.startsWith('.')) continue;
      yield* sourceFiles(path);
    } else if (SOURCE.test(entry.name)) {
      yield path;
    }
  }
}

/** Every cloud SDK import under apps/ and packages/ that is not inside an exempt package. */
export function findCloudSdkImports(root: string): CloudSdkImport[] {
  const found: CloudSdkImport[] = [];

  for (const tree of SEARCHED) {
    for (const path of sourceFiles(join(root, tree))) {
      const file = relative(root, path).split(sep).join('/');
      if (EXEMPT.some((exempt) => file.startsWith(`${exempt}/`))) continue;

      const text = readFileSync(path, 'utf8');

      for (const pattern of SPECIFIER_PATTERNS) {
        for (const match of text.matchAll(pattern)) {
          const specifier = match[1];
          if (specifier === undefined || !isCloudSdk(specifier)) continue;

          // Counted from the offset rather than by searching for the matched text:
          // an import broken over several lines is not on any single one. The
          // patterns open with (^|\s), which on a match mid-file is the newline
          // ending the line before, so the leading whitespace is stepped over
          // first or every finding is reported one line early.
          const start = match.index + (match[0].length - match[0].trimStart().length);
          const line = text.slice(0, start).split('\n').length;
          found.push({ file, line, specifier });
        }
      }
    }
  }

  return found;
}
