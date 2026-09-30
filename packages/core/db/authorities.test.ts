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
  packageSources, readingImportsOf, readRepositoryFile, READER_MODULE, repositoryPathExists,
  testTaskInputs,
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
        imported: readingImportsOf(readRepositoryFile(source)),
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
