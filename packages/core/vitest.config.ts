import { defineConfig, type TestProjectInlineConfiguration } from 'vitest/config';

const PROJECTS: TestProjectInlineConfiguration[] = [
  { extends: true, test: { name: 'unit', include: ['src/**/*.test.ts'] } },
  { extends: true, test: { name: 'db', include: ['db/**/*.test.ts'] } },
  { extends: true, test: { name: 'fixtures', include: ['fixtures/**/*.test.ts'] } },
];

/**
 * The projects a run may see. A package script selects with --project, but
 * Stryker's vitest runner hands vitest a fixed set of options with no project
 * filter in it (its own options are dir, related and configFile, and dir is
 * ignored under projects), so stryker.config.mjs names the project in
 * SEEN_VITEST_PROJECT and its workers inherit it. That is what keeps a product
 * mutant run off db/, whose tests need the local Supabase stack. A name that
 * matches no project is refused rather than read as every project.
 */
function selected(projects: TestProjectInlineConfiguration[]): TestProjectInlineConfiguration[] {
  const name = process.env.SEEN_VITEST_PROJECT;
  if (name === undefined || name === '') return projects;
  const chosen = projects.filter((project) => project.test?.name === name);
  if (chosen.length === 0) {
    throw new Error(`SEEN_VITEST_PROJECT names no vitest project of @seen/core: ${name}`);
  }
  return chosen;
}

export default defineConfig({
  test: {
    environment: 'node',
    // One test file at a time. Vitest runs files in parallel workers by default,
    // and every file under db/ connects to the same local Postgres: the
    // schema-mutating ones drop and re-add a foreign key, create roles, policies
    // and views, while another file is seeding the very tables those statements
    // take an ACCESS EXCLUSIVE lock on. The two wait on each other and Postgres
    // breaks the cycle by refusing one of them, which surfaces as a test failing
    // with SQLSTATE 40P01 and an assertion message that blames the schema. It
    // needs the timing to line up, so it is rare and cannot be asked for on
    // demand, which is what makes it expensive: a green suite is not evidence the
    // hazard is gone. Speed is not what this costs, because the whole suite runs
    // in about a second either way. db/parallelism.test.ts asserts this setting.
    fileParallelism: false,
    coverage: {
      provider: 'v8',
      // json-summary is what the harness reads; text is for a person watching.
      reporter: ['text', 'json-summary'],
      include: ['src/**/*.ts'],
      exclude: ['src/**/*.test.ts'],
    },
    // Three named projects, selected by name, because under projects vitest
    // ignores --dir: `vitest run --project core --dir src` ran db/ as well
    // (SEEN-116 record 12). `unit` is the pure functions under src/, `db` the
    // database tests under db/, and `fixtures` the seeded-bug detector SEEN-116
    // proves its machinery on, which is not product code and runs only by
    // `test:fixtures` and stryker.fixture.config.mjs. All three inherit everything
    // above, the one-file-at-a-time rule included.
    projects: selected(PROJECTS),
  },
});
