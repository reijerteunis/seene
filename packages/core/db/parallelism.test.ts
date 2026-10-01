/**
 * F25: the test files of this package may not run against the local database at
 * the same time as each other.
 *
 * Every file under `db/` connects to one Postgres, the local Supabase stack, and
 * several of them do more than read it. `schema.test.ts` drops and re-adds a
 * foreign key on `public.claims`, creates roles, policies, views and a
 * materialised view; `rls.test.ts` injects policies and seeds all twenty-nine
 * tables. A `drop constraint` takes an ACCESS EXCLUSIVE lock on the table it
 * names, and it takes it inside a transaction that is holding other locks
 * already, so a second file seeding the same table at that moment is not slowed
 * down by it: the two wait on each other and Postgres breaks the cycle by
 * refusing one of them with SQLSTATE 40P01, `deadlock_detected`.
 *
 * That is what a run with coverage enabled reported once as an assertion failure
 * inside the foreign-key test, saying the tenant's erasure answered 40P01 where
 * the test expected `accepted`. Nothing was wrong with the schema or with the
 * test: the statement was refused because another file was writing the same
 * table, which is a property of how the runner was told to schedule the files and
 * of nothing else. Vitest runs files in parallel workers by default, so the
 * default was the defect.
 *
 * So this asserts the setting rather than the absence of the failure, because the
 * failure needs the timing to line up and cannot be asked for on demand: twenty
 * consecutive runs of the suite with coverage enabled are green with the parallel
 * default still in place. What a test can say honestly is that the configuration
 * this package is run with forbids the schedule that makes it possible.
 *
 * It lives under `db/` rather than beside the pure functions because the shared
 * database is the whole of the reason the setting exists, and it needs no
 * database of its own to say so.
 */
import { describe, expect, it } from 'vitest';

import configuration from '../vitest.config';

/** `defineConfig` hands back the object it was given, so the test reads the same
 * values the runner does rather than a copy of them parsed out of the file. */
const config = configuration as { test?: { fileParallelism?: boolean; pool?: string } };

describe('the vitest configuration this package is run with', () => {
  it('runs its test files one at a time, because they share one database', () => {
    expect(
      config.test?.fileParallelism,
      'Vitest is left to its default, which runs the test files of this package in parallel '
      + 'workers. They all connect to the one local Postgres, and the schema-mutating files take '
      + 'ACCESS EXCLUSIVE locks on tables the other files are seeding, which deadlocks (40P01) '
      + 'whenever the timing lines up. `fileParallelism: false` is what forbids that schedule',
    ).toBe(false);
  });
});
