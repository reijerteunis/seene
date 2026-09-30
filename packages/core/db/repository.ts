/**
 * The one place this package opens a file it does not own, and the one place it
 * starts a process.
 *
 * The tests here read the repository as an authority and compare the database
 * against it: the routing table of `docs/architecture.md`, the acceptance criteria
 * of the tickets a column classification rests on, the `schemas` line of
 * `supabase/config.toml`, and every migration. The cache key of `@seen/core#test`
 * is this package's own contents plus whatever `turbo.json` names, so an authority
 * that turbo does not hash can be edited with nothing turbo hashes changing, and a
 * recorded pass is replayed over a version of it that no test ever read.
 *
 * That went wrong three times in SEEN-008, once per authority the suite acquired:
 * CODEX-03 on the architecture document, F34 on the tickets, F40 on the Data API
 * configuration. Each was repaired by naming the newcomer in `turbo.json` and in
 * an assertion, which is a repair that works until somebody reads something new
 * and does not think of the cache. The connection between what is read and what is
 * hashed was in nobody's way.
 *
 * So it is in the way here. A read goes through `readRepositoryFile`, which asks
 * turbo what the task hashes and refuses a path that is not in the answer before
 * it opens it, and `authorities.test.ts` asserts that no other module in this
 * package imports anything that can open a file at all. An authority added later
 * is hashed or it is unreadable, and neither of those is a green suite over a
 * document nobody read. What it cannot see is stated at each function.
 */
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

/** The repository root, from this module's own location: `packages/core/db`. */
export const REPOSITORY_ROOT = fileURLToPath(new URL('../../..', import.meta.url));

/** This package, relative to that root. turbo reports a task's inputs relative to
 * the package they belong to, and everything read here is named relative to the
 * repository, so one of the two has to be converted into the other. */
export const PACKAGE_DIRECTORY = relative(
  REPOSITORY_ROOT,
  fileURLToPath(new URL('..', import.meta.url)),
).replace(/\\/g, '/');

/** This module, relative to that root, so that a refusal can say where the rule it
 * is enforcing is written down. */
export const READER_MODULE = `${PACKAGE_DIRECTORY}/db/repository.ts`;

/**
 * The modules that can open a file or start a process, by the specifier an import
 * of one is written with.
 *
 * The list is short because the standard library's reading surface is: anything
 * else in this package can hold a path and can do nothing with it. `node:https`
 * and the like are absent on purpose. A test that fetched an authority over the
 * network would be reading something the repository does not hold, which is a
 * different objection and not this one.
 */
export const READING_MODULES = ['node:child_process', 'node:fs', 'node:fs/promises'];

/** The answer turbo gave this process, kept so that a suite reading many
 * migrations asks once. It is a measurement of files on disk and the files do not
 * change while the suite runs. */
let hashedInputs: Set<string> | undefined;

/**
 * The files turbo hashes to decide whether `@seen/core#test` may be replayed from
 * the cache, named relative to the repository root.
 *
 * `--dry=json` computes the hash and its input list without running the task, so
 * this is the same question the cache asks, asked from inside the suite the cache
 * would be replaying. Reading `turbo.json` instead would assert what somebody
 * wrote and not what turbo resolved: a glob turbo silently ignored would read as a
 * fix and hash nothing.
 */
export function testTaskInputs(): string[] {
  if (hashedInputs) return [...hashedInputs];
  const turbo = join(REPOSITORY_ROOT, 'node_modules', '.bin', 'turbo');
  if (!existsSync(turbo)) {
    throw new Error(
      `No turbo binary at ${turbo}, so this suite cannot measure what the test task hashes and `
      + 'cannot tell an authority it may read from one it may not. Install the workspace with '
      + '`pnpm install`.',
    );
  }
  let output: string;
  try {
    output = execFileSync(
      turbo,
      ['run', 'test', '--filter=@seen/core', '--dry=json'],
      { cwd: REPOSITORY_ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 },
    );
  } catch (cause) {
    throw new Error(
      'turbo could not report what the test task hashes, so nothing here can prove a file it '
      + `reads is in the cache key. turbo said: ${(cause as Error).message}`,
      { cause },
    );
  }
  const plan = JSON.parse(output.slice(output.indexOf('{'))) as {
    tasks?: { taskId?: string; inputs?: Record<string, string> }[];
  };
  const task = (plan.tasks ?? []).find((entry) => entry.taskId === '@seen/core#test');
  if (!task) {
    throw new Error(
      'turbo reported no @seen/core#test task at all, so nothing here can prove a file it reads '
      + `is in the cache key. It reported: ${(plan.tasks ?? []).map((entry) => entry.taskId).join(', ')}`,
    );
  }
  hashedInputs = new Set(Object.keys(task.inputs ?? {}).map(
    (input) => relative(REPOSITORY_ROOT, join(REPOSITORY_ROOT, PACKAGE_DIRECTORY, input))
      .replace(/\\/g, '/'),
  ));
  return [...hashedInputs];
}

/** The reason a path may not be read, as the reader would say it. */
function refusal(path: string, inputs: string[]): string {
  return `${path} is read by this package as an authority and is not among the ${inputs.length} `
    + 'inputs turbo hashes into @seen/core#test, so an edit to it would change nothing the cache '
    + 'key covers and a recorded pass would be replayed over a version of it that no test read. '
    + 'Name it in the test task\'s inputs in turbo.json, under $TURBO_ROOT$, and say there why it '
    + 'is an authority. SEEN-008 met this three times before the reader refused it: the '
    + 'architecture document (CODEX-03), the constrained tickets (F34) and the Data API '
    + `configuration (F40). turbo hashes: ${inputs.sort().join(', ')}`;
}

/**
 * A file of this repository, read as text, refused unless the test task hashes it.
 *
 * The hashing is asked first and the file is opened second, so a path that is not
 * hashed is refused whether or not it exists: the failure a reader needs to see is
 * the one about the cache, and a missing file is reported by the same sentence
 * because a file this task hashes is a file that was there when turbo looked.
 *
 * What this cannot see: a read from another package's tests, which run under their
 * own task and their own cache key; a file taken from somewhere other than disk,
 * such as a fixture fetched over the network or a value inlined into a source; and
 * a conclusion drawn from a directory's contents rather than a file's, which
 * `listRepositoryDirectory` covers only as far as it can.
 */
export function readRepositoryFile(path: string): string {
  const inputs = testTaskInputs();
  if (!inputs.includes(path)) throw new Error(refusal(path, inputs));
  return readFileSync(join(REPOSITORY_ROOT, path), 'utf8');
}

/** Whether a path exists in this repository. No hashing question is asked, because
 * the answer carries no content: a test that decides something from a file's
 * contents has to read it, and the read is where the refusal lives. */
export function repositoryPathExists(path: string): boolean {
  return existsSync(join(REPOSITORY_ROOT, path));
}

/**
 * The names in a directory of this repository, refused unless the test task hashes
 * something inside it.
 *
 * Weaker than the rule for a file, and deliberately so. turbo hashes files, not
 * directories, so the strongest thing that can be asked of a listing is that the
 * directory is in the cache key at all: `supabase/migrations` is there through a
 * glob that covers every member, `docs/tickets` through the tickets whose
 * criteria are read. What this leaves open is a test that concludes something
 * from the names alone, such as a count of the tickets, where a newcomer the glob
 * does not match changes the answer and not the hash. Every caller here reads the
 * files it finds, and that read is refused if turbo does not hash it.
 */
export function listRepositoryDirectory(path: string): string[] {
  const inputs = testTaskInputs();
  if (!inputs.some((input) => input.startsWith(`${path}/`))) {
    throw new Error(refusal(`${path}/`, inputs));
  }
  return readdirSync(join(REPOSITORY_ROOT, path)).sort();
}

/**
 * Every TypeScript source of this package, relative to the repository root.
 *
 * Read from disk rather than from the cache key, because the question this answers
 * is what exists: a source that turbo somehow did not hash is exactly what a
 * caller scanning this package would want to be told about, and reading the cache
 * key would hide it. Installed packages and coverage output are not this package's
 * sources and are skipped by name.
 */
export function packageSources(): string[] {
  const skipped = new Set(['coverage', 'dist', 'node_modules']);
  const found: string[] = [];
  const walk = (directory: string): void => {
    for (const entry of readdirSync(join(REPOSITORY_ROOT, directory), { withFileTypes: true })) {
      if (entry.isDirectory()) {
        if (!skipped.has(entry.name)) walk(`${directory}/${entry.name}`);
      } else if (entry.name.endsWith('.ts')) {
        found.push(`${directory}/${entry.name}`);
      }
    }
  };
  walk(PACKAGE_DIRECTORY);
  return found.sort();
}

/** The reading modules a source imports, by whichever grammar it imports them
 * with. Composed from the specifiers rather than spelled as one expression, so
 * that the module asking the question is the one module allowed to answer yes. */
export function readingImportsOf(contents: string): string[] {
  return READING_MODULES.filter((specifier) => new RegExp(
    String.raw`(?:from|import|require)\s*\(?\s*['"]${specifier.replace('/', '\\/')}['"]`,
  ).test(contents));
}
