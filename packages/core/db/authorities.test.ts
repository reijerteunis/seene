/**
 * F40: the files this package reads as an authority and the files turbo hashes
 * into `@seen/core#test` have to be the same set, and nothing made them so.
 *
 * A test here reads something the repository states outside this package and
 * compares the database, or the migrations, against it: the routing table of
 * `docs/architecture.md`, the acceptance criteria of the tickets a column
 * classification rests on, and now the `schemas` line of `supabase/config.toml`,
 * which is the premise underneath every sentence in this ticket that says an
 * object is out of reach because of the schema it lives in. The cache key of the
 * task is the package's own contents plus whatever `turbo.json` names, so an
 * authority that is not named there can be edited with nothing turbo hashes
 * changing, and turbo replays the recorded pass over a version of it that no test
 * ever read.
 *
 * That has now happened three times in this ticket, with the same shape each time
 * and a different authority: CODEX-03 for the architecture document, F34 for the
 * tickets, F40 for the Data API configuration. Each was repaired by adding an
 * entry to a list, which is why the next one arrived: nothing connected what the
 * suite reads to what turbo hashes, so the connection held only as long as an
 * author remembered to make it by hand.
 *
 * So what is asserted here is the connection itself. Every read of a file outside
 * this package goes through one reader, the reader refuses a path the task does
 * not hash before it opens it, and no module here keeps a way of reading a file
 * around the reader. An authority added later is then hashed or it is unreadable,
 * and neither outcome is a green suite over a document nobody read.
 */
import { describe, expect, it } from 'vitest';

import {
  INERT_EXTENSIONS, PACKAGE_DIRECTORY, packageFiles, packageSources, readingImportsOf,
  readRepositoryFile, READER_MODULE, repositoryPathExists, SOURCE_EXTENSIONS, testTaskInputs,
} from './repository';
import { DATA_API_CONFIG, HASHED_REPOSITORY_DOCUMENTS } from './tables';

/** A file this repository holds and this task has no reason to hash: the reader's
 * refusal is shown on something that is really there, so that a refusal cannot be
 * mistaken for a path spelled wrongly. */
const UNHASHED_AUTHORITY = 'docs/prd/prd.md';

describe('the authorities this package reads and the cache key it runs under', () => {
  it('hashes the Data API configuration, which four rules in this schema rest on', () => {
    // F40. The exposed-schema guard reads `supabase/config.toml` and compares its
    // `schemas` line with DATA_API_SCHEMAS, because `seen` being absent from that
    // line is why the erasure registry is not a table endpoint, why part 6 can send
    // a materialised view and a foreign table outside public, and why the routines
    // of `seen` owe an allow-list where the routines of public owe an emptiness.
    // Nothing under packages/core changes when that line does, so turbo replays the
    // recorded pass and the guard that would have caught it never runs. Measured by
    // the sixth Codex review before this line was written: 27 inputs, every
    // migration and every authority read so far among them, and no configuration.
    const inputs = testTaskInputs();
    expect(inputs.length, 'turbo reported no inputs at all for @seen/core#test').toBeGreaterThan(0);
    expect(
      inputs.includes(DATA_API_CONFIG),
      `The cache key of @seen/core#test covers ${inputs.length} files and not ${DATA_API_CONFIG}, `
      + 'which this suite reads as the authority on what the Data API serves. A change confined '
      + 'to its `schemas` line therefore leaves the task inputs untouched and a cached pass is '
      + `replayed over it. turbo hashes: ${inputs.join(', ')}`,
    ).toBe(true);
  });

  it('refuses to read a repository file the test task does not hash', () => {
    // The general form of the same defect, demonstrated rather than described. The
    // reader is asked for a file this repository really holds and this task has no
    // reason to hash, which is exactly the shape a new authority arrives in, and it
    // has to refuse before it opens it. The list of authorities is then not a list
    // anybody maintains: a read of an unhashed file is the failure.
    expect(
      repositoryPathExists(UNHASHED_AUTHORITY),
      `${UNHASHED_AUTHORITY} is not in the repository, so a refusal to read it would prove `
      + 'nothing about hashing. Name a file that is there and is not hashed.',
    ).toBe(true);
    expect(
      testTaskInputs().includes(UNHASHED_AUTHORITY),
      `${UNHASHED_AUTHORITY} is in the cache key now, so being refused it would prove nothing `
      + 'about hashing. Name a file this task has no reason to hash instead.',
    ).toBe(false);
    expect(() => readRepositoryFile(UNHASHED_AUTHORITY)).toThrow(/turbo hashes/);
    expect(
      readRepositoryFile(HASHED_REPOSITORY_DOCUMENTS[0]).length,
      `The reader refused ${HASHED_REPOSITORY_DOCUMENTS[0]}, which the test task does hash, so it `
      + 'refuses everything and the refusal above says nothing about hashing.',
    ).toBeGreaterThan(0);
  });

  it('leaves this package no way to read an authority around that reader', () => {
    // The other half, and the half that makes the first one a rule rather than a
    // convention. A module that imports node:fs can open any path it likes with
    // nobody asking whether turbo hashes it, which is how each of the three rounds
    // got here: an author read a new authority the way the file next to them did.
    // The reader is the one module in this package that opens a file or starts a
    // process, so an author who needs a new authority has to go through it, and the
    // refusal above then applies to them without their having heard of it.
    const offenders = packageSources()
      .filter((source) => source !== READER_MODULE)
      .map((source) => ({
        source,
        imported: readingImportsOf(readRepositoryFile(source), source),
      }))
      .filter((entry) => entry.imported.length > 0)
      .map((entry) => `${entry.source} imports ${entry.imported.join(' and ')}`);
    expect(
      offenders,
      'These sources can open a file or start a process without going through the reader at '
      + `${READER_MODULE}, so an authority read through one of them is hashed only if its author `
      + `remembered to say so in turbo.json: ${offenders.join('; ')}`,
    ).toEqual([]);
  });
});

/** The synthetic package a source is judged as a member of, so that a relative
 * specifier in one of the cases below resolves the way it would on disk. */
const SYNTHETIC_SOURCE = 'packages/core/db/synthetic.ts';

/** A source that reads a file, one row per grammar and spelling a person could
 * write it with, and beside each the specifier the guard has to name. Node treats
 * `fs` and `node:fs` as the same module, and `require`, `import` and `import()`
 * as three ways of asking for it, so a guard that names one and not the others
 * reports nothing about a module that is reading the repository.
 *
 * The runner's own loaders are two more ways of asking, and F47 is what it cost to
 * leave them out: `vi.importActual` and `vi.importMock` take a literal specifier
 * and hand back the module, `vitest` is allow-listed because every test file here
 * imports it, and a module written this way read `docs/prd/prd.md` with the guard
 * reporting nothing. Written with no type annotation, which is how an author
 * avoiding the guard writes it and is the only form that proves anything: with
 * `typeof import('node:fs')` in a type position the pre-processor reports the
 * specifier from the type and the loader is never the reason. */
const READING_SOURCES: [source: string, reported: string][] = [
  ["import { readFileSync } from 'node:fs';", 'node:fs'],
  ["import { readFileSync } from 'fs';", 'fs'],
  ["import { execFileSync } from 'child_process';", 'child_process'],
  ["import { execFileSync } from 'node:child_process';", 'node:child_process'],
  ["const { readFileSync } = require('fs');", 'fs'],
  ["const { readFile } = await import('node:fs/promises');", 'node:fs/promises'],
  ["const { readFile } = await import('fs/promises');", 'fs/promises'],
  ["import { createRequire } from 'module';", 'module'],
  ["export { readFileSync } from 'fs';", 'fs'],
  ["import 'fs';", 'fs'],
  ["import { helper } from '../../../scripts/helper';", '../../../scripts/helper'],
  ["import { vi } from 'vitest';\nconst fs: any = await vi.importActual('node:fs');", 'node:fs'],
  ["import { vi } from 'vitest';\nconst cp: any = await vi.importMock('child_process');", 'child_process'],
];

/** Sources that read nothing, so that the guard is not passing by objecting to
 * everything. Every one of these is imported by this package today. */
const SETTLED_SOURCES = [
  "import { describe, expect, it } from 'vitest';",
  "import { defineConfig } from 'vitest/config';",
  "import { Client } from 'pg';",
  "import { randomUUID } from 'node:crypto';",
  "import { TRADE_RECORD_TABLES } from './tables';",
  "import { config } from '../vitest.config';",
];

describe('the spelling a reading import is written with', () => {
  it('names the module a source reads through, however the import is written', () => {
    // F45. The guard matched the three `node:`-prefixed specifiers as text, so
    // `import { readFileSync } from 'fs'` was invisible to it and so was every
    // `require` and `import()` of the same module. A module that reads an
    // authority that way is refused by nothing and hashed by nothing, which is
    // the fourth arrival of the class F40 was built to close.
    const missed = READING_SOURCES
      .filter(([source, reported]) => !readingImportsOf(source, SYNTHETIC_SOURCE).includes(reported))
      .map(([source]) => source);
    expect(
      missed,
      'These sources reach the filesystem and the guard does not name what they reach it '
      + `through, so a module written this way reads an authority nothing hashes: ${missed.join(' | ')}`,
    ).toEqual([]);
  });

  it('judges a specifier the runner is handed by the list that judges an import', () => {
    // F47. The loader calls are read from the syntax tree rather than from the
    // pre-processor, and what the tree says is put to the same allow-list, so
    // there is one rule about what this package may reach and not two. The three
    // cases below are the three answers that rule has: a specifier nothing
    // vouches for is named, a relative specifier that resolves to a file this
    // scan collects is not, because that file is asked the same question, and a
    // computed specifier is not, because there is nothing written to report. The
    // last of those is a survival and is asserted here so that the paragraph at
    // `readingImportsOf` claiming it is a paragraph something checks.
    const typed = "import { vi } from 'vitest';\n"
      + "const fs = await vi.importActual<typeof import('node:fs')>('node:fs');";
    expect(
      readingImportsOf(typed, SYNTHETIC_SOURCE),
      'A loader call with the module named in a type position as well as in the argument is '
      + 'reported by the pre-processor alone, so this form proves nothing about the loader and '
      + 'has to hold whichever instrument answers.',
    ).toContain('node:fs');
    const insidePackage = "import { vi } from 'vitest';\n"
      + "const tables: any = await vi.importActual('./tables');";
    expect(
      readingImportsOf(insidePackage, SYNTHETIC_SOURCE),
      'A loader handed a relative specifier inside this package is judged more harshly than an '
      + 'import written with the same specifier, so the guard has two rules and a test that '
      + 'mocks a sibling module is an offender.',
    ).toEqual([]);
    const computed = "import { vi } from 'vitest';\n"
      + 'const fs: any = await vi.importActual(specifier);';
    expect(
      readingImportsOf(computed, SYNTHETIC_SOURCE),
      'A computed specifier is named by something, so the guard is reporting a name it did not '
      + 'read and the paragraph that gives this as a survival is describing something else.',
    ).toEqual([]);
  });

  it('admits a relative specifier only when it resolves to a file this scan collects', () => {
    // F48. The rule for a relative specifier was that its joined path starts
    // with this package's directory, and the reason given for it was a
    // transitivity: the module named is collected by `packageSources` and asked
    // the same question. That was false for the four directory names the walk
    // skips, and one of them is on disk. So a module here could write
    // `../node_modules/anything`, be filtered out as inside the package, and
    // never be asked what the module at the other end imports, because the walk
    // passed over the directory it lives in. The predicate is now the mechanism
    // rather than a restatement of it: what is admitted is what the walk returns,
    // so the sentence holds by construction and goes on holding if somebody
    // edits the skip list without ever hearing of this finding.
    const skipped = `${PACKAGE_DIRECTORY}/node_modules`;
    expect(
      repositoryPathExists(skipped),
      `${skipped} is not on disk, so a specifier into it would prove nothing about a directory `
      + 'the walk skips. Name one of the four that is there.',
    ).toBe(true);
    expect(
      packageSources().filter((source) => source.startsWith(`${skipped}/`)),
      `The walk collects files under ${skipped} after all, so a specifier into it is asked the `
      + 'same question and this case says nothing.',
    ).toEqual([]);
    const reported: [source: string, why: string][] = [
      ["import { readFileSync } from '../node_modules/pg';",
        'a relative specifier into a directory the walk skips is admitted, and nothing asks the '
        + 'module at the other end what it imports'],
      ["import { vi } from 'vitest';\nconst pg: any = await vi.importActual('../node_modules/pg');",
        'the loader route into the same directory is open, so the two instruments disagree about '
        + 'one specifier'],
      ["import { helper } from './nowhere';",
        'a specifier that resolves to nothing is admitted, which is how this hole was shaped: the '
        + 'unresolvable is the case a guard has to report rather than trust'],
    ];
    const admitted = reported
      .filter(([source]) => readingImportsOf(source, SYNTHETIC_SOURCE).length === 0)
      .map(([source, why]) => `${source.replace('\n', ' ')} -> ${why}`);
    expect(
      admitted,
      `These sources are admitted by the relative rule and should not be: ${admitted.join(' | ')}`,
    ).toEqual([]);
    const settled = [
      "import { TRADE_RECORD_TABLES } from './tables';",
      "import { TRADE_RECORD_TABLES } from './tables.js';",
      "import { config } from '../vitest.config';",
      "import { vi } from 'vitest';\nconst tables: any = await vi.importActual('./tables');",
    ];
    const objected = settled
      .map((source) => [source, readingImportsOf(source, SYNTHETIC_SOURCE)] as const)
      .filter(([, named]) => named.length > 0)
      .map(([source, named]) => `${source.replace('\n', ' ')} -> ${named.join(', ')}`);
    expect(
      objected,
      'These specifiers name a file this scan collects, spelled as TypeScript allows them to be '
      + `spelled, and the guard reports them, so resolution is stricter than the runtime: ${objected.join(' | ')}`,
    ).toEqual([]);
  });

  it('names nothing in a source that imports only what this package already imports', () => {
    const objected = SETTLED_SOURCES
      .map((source) => [source, readingImportsOf(source, SYNTHETIC_SOURCE)] as const)
      .filter(([, reported]) => reported.length > 0)
      .map(([source, reported]) => `${source} -> ${reported.join(', ')}`);
    expect(
      objected,
      'The guard objects to imports this package makes in every test file, so it would fail '
      + `whatever anybody wrote and says nothing about reading: ${objected.join(' | ')}`,
    ).toEqual([]);
  });
});

describe('the files that scan reaches', () => {
  it('classifies every file of this package as one that runs code or one that cannot', () => {
    // F45's second half. The walk collected the entries ending `.ts` and passed
    // over everything else without saying so, and vitest's default include runs
    // `.test.mts`, `.test.cts` and `.test.js` as readily as `.test.ts`. So a test
    // file at one of those extensions ran, imported what it liked, read an
    // authority and was never among the sources the guard above asks. Measured
    // before this was written: such a file reading docs/prd/prd.md left the guard
    // reporting nothing. An extension neither list has an answer for now fails
    // here rather than being dropped, which is the same inversion: the file
    // nobody anticipated stops the suite instead of escaping it.
    const files = packageFiles();
    expect(
      files.unclassified,
      'These files are neither a source this guard scans nor inert, so nobody has said whether '
      + `they can read an authority: ${files.unclassified.join(', ')}. Add the extension to `
      + `SOURCE_EXTENSIONS if the runtime can load it, or to INERT_EXTENSIONS with a reason.`,
    ).toEqual([]);
    expect(
      files.sources.length,
      'The walk found no sources at all, so the guard above scans nothing and passes for that '
      + 'reason rather than because this package reads through one reader.',
    ).toBeGreaterThan(0);
  });

  it('covers every extension vitest runs a test file at', () => {
    // vitest's default include is `**/*.{test,spec}.?(c|m)[jt]s?(x)`, so these are
    // the extensions a test can arrive at without anybody configuring anything.
    // Held as a list rather than as a sentence, so that a file at one of them
    // cannot be run by the suite and skipped by the suite's own guard.
    const runnable = ['.ts', '.tsx', '.mts', '.cts', '.js', '.jsx', '.mjs', '.cjs'];
    const missed = runnable.filter((extension) => !SOURCE_EXTENSIONS.includes(extension));
    expect(
      missed,
      `vitest runs a test file at ${missed.join(', ')} and this guard does not collect it, so a `
      + 'test written at that extension is never asked what it imports.',
    ).toEqual([]);
    const both = SOURCE_EXTENSIONS.filter((extension) => INERT_EXTENSIONS.includes(extension));
    expect(
      both,
      `${both.join(', ')} is listed as both able to run code and inert, so which of the two the `
      + 'walk does with it depends on the order of two lists.',
    ).toEqual([]);
  });
});
