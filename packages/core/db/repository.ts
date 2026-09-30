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
 *
 * F45 is the fourth arrival of the same class, and it arrived past that second
 * half rather than around the first. The half was a pattern over source text
 * naming three `node:`-prefixed specifiers, over the files whose names end `.ts`.
 * `import { readFileSync } from 'fs'` is the same module by the same resolver and
 * was invisible to it, so were `require` and `import()`, and a test file named
 * `.test.mts` runs under vitest and was never collected to be asked. Measured
 * before this was written: a module reading `docs/prd/prd.md` through either hole
 * left the guard reporting nothing, while the same pattern reported this suite's
 * own test file as an offender for quoting `'node:fs'` inside a string.
 *
 * Both halves of that are properties of asking a pattern. So the question is put
 * to the TypeScript compiler's own pre-processor, which answers with the
 * specifiers a module actually imports by any grammar, and the answer is judged
 * against an allow-list of what this package may import rather than a list of
 * what it may not. A deny-list has to anticipate how the next thing is spelled,
 * which is the shape this ticket has now produced findings about four times
 * (CODEX-02's clause search, F20's `attname like 'buyer%'`, F30's `relacl`, and
 * this); an allow-list has a finite answer and refuses the specifier nobody
 * thought of.
 *
 * F47 is the fifth arrival, and it came through the allow-list rather than past
 * it. `vitest` was admitted on the ground that the runner hands a test no way to
 * open a path, which is false: `vi.importActual` takes a literal specifier and
 * hands back the real module, and the pre-processor does not report it, so a
 * module of this package read an unhashed authority with the guard silent. An
 * entry's reason is load-bearing, and one that is false is a hole the shape of
 * whatever it admits. So the loaders are read from the compiler's syntax tree as
 * well, and the specifier they name is judged by the same allow-list. What is
 * known to survive both instruments, and why that is not offered as the whole of
 * it, is stated at `readingImportsOf`.
 *
 * F48 is the sixth, and it is F47's defect in F47's paragraph: a stated property
 * of the guard that was not true of the guard. A relative specifier was admitted
 * without being listed, on the ground that the module it names is collected by
 * `packageSources` and asked the same question, and that held everywhere except
 * the four directories the walk skips. `node_modules` is one of them and is on
 * disk, so `../node_modules/anything` was admitted as inside the package and
 * asked nothing. The repair is not a fifth name in a list but the predicate
 * itself: a relative specifier is resolved against the files the walk returns, so
 * the transitivity is what the code does rather than what a sentence beside it
 * says, and it survives somebody editing the skip list without ever hearing of
 * this finding.
 */
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { extname, join, posix, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

// The compiler this repository already builds with, resolved from the workspace
// root the way `vitest` and `tsc` are: both are root devDependencies that every
// package here uses without declaring them, and adding one to this package's
// manifest without a matching lockfile entry is what `--frozen-lockfile` refuses
// in CI. `preProcessFile` and `createSourceFile` are used, and both are handed
// source text somebody else has already read and open nothing themselves; the
// file reading in this module is still the four functions below.
import ts from 'typescript';

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
 * Everything a module of this package may import without the guard objecting,
 * beside the reason each one cannot put a repository file in front of a test.
 *
 * An allow-list, and that is the whole point of it. The three specifiers this
 * used to forbid were `node:child_process`, `node:fs` and `node:fs/promises`,
 * which left `fs`, `child_process`, `fs/promises`, `module` and every other
 * spelling of the same reach permitted by omission. Naming what is permitted
 * inverts that: a specifier nobody anticipated is reported until somebody adds it
 * here with a reason, and the reason is the work rather than the entry.
 *
 * A relative specifier is not listed and does not need to be, as long as it
 * resolves to a file `packageFiles` collects: a source there is asked this same
 * question, and an inert file there carries no code to ask about, so the
 * allow-list holds transitively for exactly the specifiers `resolvedInPackage`
 * admits. Anything else is reported, whether it leaves the package, lands in a
 * directory the walk skips, or resolves to nothing at all.
 *
 * That last clause is F48. The rule used to be that the joined path starts with
 * this package's directory, with the transitivity given as the reason, and the
 * two were not the same set: the walk skips `.turbo`, `coverage`, `dist` and
 * `node_modules`, `packages/core/node_modules` holds pg and two more links today,
 * and a module writing `../node_modules/anything` was filtered out as inside the
 * package and never collected to be asked what it imports. The reason is now the
 * rule rather than a claim about it.
 */
export const IMPORTS_THAT_CANNOT_READ: Record<string, string> = {
  // The runner, admitted because every test file here imports it and removing it
  // is not available, not because it cannot reach a file. It can: `vi` hands out
  // `importActual` and `importMock`, which take a literal specifier and return the
  // real module, and F47 measured one of them handing `node:fs` to a module of
  // this package that then read `docs/prd/prd.md`. What the entry costs is
  // therefore paid at `readingImportsOf`, which finds those calls in the syntax
  // tree and judges the specifier they name by this same list. What that does not
  // cover is the loader reached under another name, and anything else the runner
  // may hand out that this list has not been taught to look for.
  vitest: 'the test runner, imported by every test file here, whose module loaders are named '
    + 'at readingImportsOf rather than admitted by this entry',
  'vitest/config': 'the runner\'s configuration type, read by vitest.config.ts',
  // The Postgres client. It reaches a socket rather than the working tree for
  // everything a test here asks of it, so a fact it brings back is a fact about
  // the database, which is what every guard here is comparing against an
  // authority in the first place. Not that it opens nothing at all: it depends on
  // `pgpass`, which reads `$PGPASSFILE` or `~/.pgpass` when a connection is made
  // without a password. That is a file of the machine and not of this repository,
  // so it is no route to an authority, and the entry says what it means rather
  // than claiming the stronger thing.
  pg: 'the Postgres client, which reaches a socket for everything asked of it here; the '
    + 'password file its own dependency can open is a file of the machine, not of this '
    + 'repository',
  // Identifiers for the two-tenant probes. It computes and does not open.
  'node:crypto': 'uuid generation, which opens nothing',
};

/**
 * The extensions this package's own modules are written with, which is every
 * extension the runtime can load through an import specifier.
 *
 * Wider than the `.ts` this used to collect, and wider than what the package
 * holds today, on purpose. vitest's default include matches `.test.mts`,
 * `.test.cts` and `.test.js` as readily as `.test.ts`, so a file at any of them
 * runs, imports what it likes and was never collected to be asked about it.
 */
export const SOURCE_EXTENSIONS = ['.cjs', '.cts', '.js', '.jsx', '.mjs', '.mts', '.ts', '.tsx'];

/**
 * The extensions that carry no code, so that a file at one of them is skipped
 * knowingly rather than by not matching anything.
 *
 * A file at neither list is reported by `packageFiles` as unclassified rather
 * than quietly dropped, which is the same inversion as the allow-list above: the
 * extension nobody anticipated stops the suite and is classified by a person.
 */
export const INERT_EXTENSIONS = [
  '.css', '.json', '.md', '.snap', '.sql', '.svg', '.toml', '.txt', '.yaml', '.yml',
];

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
 * Every file of this package, split into the ones that can run code, the ones
 * that cannot, and the ones neither list has an answer for.
 *
 * Read from disk rather than from the cache key, because the question this answers
 * is what exists: a source that turbo somehow did not hash is exactly what a
 * caller scanning this package would want to be told about, and reading the cache
 * key would hide it. Installed packages, coverage output and turbo's own logs are
 * not this package's sources and are skipped by name.
 *
 * What that skip list costs is paid at `resolvedInPackage`, which is F48. A
 * relative specifier used to be admitted for starting with this package's
 * directory, so `../node_modules/anything` was trusted as though it had been
 * collected here and asked what it imports, when the walk had passed over it. The
 * relative rule now resolves against what this returns, so adding a name here
 * closes a route at the same time as it stops a scan, and nobody has to remember
 * that the two are connected.
 *
 * The third bucket is what F45 cost. A walk that collects the extensions it knows
 * and says nothing about the rest reports a complete answer to a caller who asked
 * about every module in the package, and the file it silently passed over was a
 * `.test.mts` that vitest was running all along. A name this cannot classify is
 * therefore returned rather than dropped, and `authorities.test.ts` fails on it.
 * A name with no extension at all is inert: Node will not load one through an
 * import specifier, whatever it holds.
 */
export function packageFiles(): { sources: string[]; inert: string[]; unclassified: string[] } {
  const skipped = new Set(['.turbo', 'coverage', 'dist', 'node_modules']);
  const sources: string[] = [];
  const inert: string[] = [];
  const unclassified: string[] = [];
  const walk = (directory: string): void => {
    for (const entry of readdirSync(join(REPOSITORY_ROOT, directory), { withFileTypes: true })) {
      const path = `${directory}/${entry.name}`;
      if (entry.isDirectory()) {
        if (!skipped.has(entry.name)) walk(path);
      } else if (SOURCE_EXTENSIONS.includes(extname(entry.name))) {
        sources.push(path);
      } else if (extname(entry.name) === '' || INERT_EXTENSIONS.includes(extname(entry.name))) {
        inert.push(path);
      } else {
        unclassified.push(path);
      }
    }
  };
  walk(PACKAGE_DIRECTORY);
  return {
    sources: sources.sort(),
    inert: inert.sort(),
    unclassified: unclassified.sort(),
  };
}

/** Every source of this package that can run code, relative to the repository
 * root. The other two buckets are `packageFiles`'s and are asserted there. */
export function packageSources(): string[] {
  return packageFiles().sources;
}

/**
 * The calls that hand a module back from a literal specifier without importing
 * it, matched by the name they are called under.
 *
 * These are the runner's, and they are what F47 cost. `vi.importActual('node:fs')`
 * is an import in everything but grammar: a specifier written in the source, the
 * real module returned, and `ts.preProcessFile` reporting nothing, because no
 * import syntax is there for it to report. So the specifier is taken from the
 * syntax tree instead and put to `IMPORTS_THAT_CANNOT_READ` exactly as an
 * imported one is.
 *
 * Matched by the name at the call and not by what it was reached through, so
 * `vi.importActual`, `vitest.importActual` and a destructured `importActual` are
 * one case, and an alias bound to another name is not seen. A deny-list of names
 * has the weakness every deny-list here has had, and it is used anyway because
 * the alternative is reporting every string literal in the file, which is the
 * false positive the pattern this replaced was withdrawn for.
 */
export const MODULE_LOADING_CALLS = ['importActual', 'importMock'];

/** The specifiers a source hands to one of those calls, in the order they appear.
 * The parse is of text already in hand and opens nothing; a file that does not
 * parse yields the calls the parser did recover, which is more than none. */
function loadedSpecifiers(contents: string, source: string): string[] {
  const jsx = ['.jsx', '.tsx'].includes(extname(source));
  const parsed = ts.createSourceFile(
    `specifiers${jsx ? '.tsx' : '.ts'}`,
    contents,
    ts.ScriptTarget.Latest,
    false,
    jsx ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
  );
  const found: string[] = [];
  const visit = (node: ts.Node): void => {
    if (ts.isCallExpression(node)) {
      const { expression } = node;
      let called: string | undefined;
      if (ts.isPropertyAccessExpression(expression)) called = expression.name.text;
      else if (ts.isIdentifier(expression)) called = expression.text;
      const [first] = node.arguments;
      if (called !== undefined && MODULE_LOADING_CALLS.includes(called)
        && first !== undefined && ts.isStringLiteralLike(first)) {
        found.push(first.text);
      }
    }
    ts.forEachChild(node, visit);
  };
  ts.forEachChild(parsed, visit);
  return found;
}

/**
 * The extension a specifier is written with, beside the extensions the file it
 * names may actually be written with.
 *
 * A specifier ending `.js` is how TypeScript's own ESM output names a sibling
 * that is a `.ts` on disk, and nothing in this repository stops an author
 * spelling an import that way. Resolution that did not know it would report a
 * specifier the runtime resolves happily, which is a guard refusing what it
 * should admit, and a guard that cries at ordinary code is a guard somebody
 * loosens. The other direction is not here: a `.ts` specifier never names a
 * `.js` file.
 */
const COMPILED_TO_SOURCE_EXTENSIONS: Record<string, string[]> = {
  '.js': ['.ts', '.tsx'],
  '.jsx': ['.tsx'],
  '.mjs': ['.mts'],
  '.cjs': ['.cts'],
};

/**
 * Every path a relative specifier could mean, in the order a resolver would try
 * them: the path as written, the path with each extension this package's modules
 * are written with, the source a compiled extension was emitted from, and the
 * index file of a directory of that name.
 *
 * Deliberately generous about what a specifier may mean and not at all generous
 * about what that buys, because `resolvedInPackage` only admits a candidate that
 * is a file the walk collected. A candidate that resolves to nothing is the case
 * this exists for: `import.meta.resolve` and the TypeScript resolver are both
 * available and both would answer for a specifier into a skipped directory, and
 * an answer is not what is wanted here. The question is whether the module at the
 * other end is one this package's own guard has already asked.
 */
function candidatePaths(target: string): string[] {
  const extension = posix.extname(target);
  const stem = extension === '' ? target : target.slice(0, -extension.length);
  return [
    target,
    ...SOURCE_EXTENSIONS.map((suffix) => `${target}${suffix}`),
    ...(COMPILED_TO_SOURCE_EXTENSIONS[extension] ?? []).map((suffix) => `${stem}${suffix}`),
    ...SOURCE_EXTENSIONS.map((suffix) => `${target}/index${suffix}`),
  ];
}

/**
 * Whether a relative specifier written in `source` names a file this package's
 * own walk collected.
 *
 * This is the whole of F48's repair. What was asked before was whether the joined
 * path starts with this package's directory, which is the claim the doc comment
 * on `IMPORTS_THAT_CANNOT_READ` made, rather than the thing the claim was resting
 * on. The thing it rests on is that `packageFiles` collected the module at the
 * other end, so that `readingImportsOf` is asked about it too, and the two
 * differed by the four directory names the walk skips.
 *
 * A specifier this cannot place is reported rather than admitted, which is the
 * inversion every guard in this module has ended up at: admitting what could not
 * be accounted for is the shape of all six findings. The cost is a false positive
 * on a spelling no resolver here has been taught, and the price of that is a line
 * in `candidatePaths` with the measurement that says why.
 */
function resolvedInPackage(specifier: string, source: string, collected: Set<string>): boolean {
  const target = posix.join(posix.dirname(source), specifier);
  return candidatePaths(target).some((candidate) => collected.has(candidate));
}

/**
 * Everything a source imports that this package cannot vouch for as unable to
 * open a file, named as the source spells it.
 *
 * The specifiers come from the TypeScript compiler's own pre-processor rather
 * than from a pattern, so `import`, `export ... from`, a bare `import 'x'`,
 * `require('x')` and `import('x')` are one question with one answer, and a
 * specifier quoted inside a string or a comment is not an import. The regular
 * expression this replaces could do neither: measured before it was replaced, it
 * missed `fs`, `child_process`, `fs/promises`, `module`, every `require` of them
 * and every `import()` of them, and it reported `authorities.test.ts` as an
 * offender for holding the text `'node:fs'` in a test case.
 *
 * The pre-processor is not the whole question, which is F47. It answers with the
 * specifiers a module imports, and `vi.importActual('node:fs')` imports nothing
 * by that definition while returning the module all the same. So the calls at
 * `MODULE_LOADING_CALLS` are read from the syntax tree as well, and both answers
 * go to one judgement: `IMPORTS_THAT_CANNOT_READ`, plus relative specifiers that
 * `resolvedInPackage` places on a file the walk collected, which is a file asked
 * this same question. A loader handed `./tables` is as allowed as an import of
 * it, and a loader handed `node:fs` or `../node_modules/pg` is as reported,
 * because there is one list and one resolver and not two of either.
 *
 * What is known to survive both, and would survive a lint rule equally, because
 * all three read the specifier a module was written with: `import()`, `require()`
 * or a loader call given a computed specifier, since there is no literal to
 * report; a loader reached under a name this does not match, such as a local
 * binding of `vi.importActual`; `createRequire` reached other than by importing
 * `node:module`, such as through `process.getBuiltinModule`; and anything
 * assembled and run through `eval` or `new Function`. None of those is shut here.
 *
 * That is what is known to survive and not a statement of all that does. It was
 * written as the whole list once, three items and the sentence that none of them
 * is shut here, and the fourth was `vi.importActual`: a literal specifier, in the
 * module this allow-list admitted on the ground that it could not reach a file,
 * found one round after a finding about a stated impossibility that was false.
 * What can honestly be said is the shape of the blind spot rather than its
 * membership. This reads the specifier a module was written with, in the two
 * places a module is written to name one, so anything that hands back a module
 * without a specifier written where this looks is unseen until somebody measures
 * it and adds it above. None of that is how an authority gets read by accident,
 * which is the case this guard is for; deliberate evasion is not what an
 * allow-list over one package's own sources can settle. A read from another
 * package's tests is out of reach for the separate reason that it runs under its
 * own task and its own cache key.
 */
export function readingImportsOf(contents: string, source: string): string[] {
  const imported = ts.preProcessFile(contents, true, true).importedFiles
    .map((reference) => reference.fileName)
    .concat(loadedSpecifiers(contents, source));
  // Measured once per call rather than once per specifier, and from disk rather
  // than from a cache, for the reason `packageFiles` gives: what is being asked
  // is what exists, and what exists does not change while the suite runs.
  const files = packageFiles();
  const collected = new Set([...files.sources, ...files.inert]);
  return [...new Set(imported)]
    .filter((specifier) => (specifier.startsWith('.')
      ? !resolvedInPackage(specifier, source, collected)
      : !(specifier in IMPORTS_THAT_CANNOT_READ)))
    .sort();
}
