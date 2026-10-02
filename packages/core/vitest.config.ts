import { defineConfig } from 'vitest/config';

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
    // Two projects, so the fixture SEEN-116 proves its machinery on never runs
    // with the product tests. `core` is the package: the pure functions under
    // src/ and the database tests under db/, which every package script selects
    // by name. `fixtures` is the seeded-bug detector under fixtures/, run only by
    // `test:fixtures` and by stryker.fixture.config.mjs. Both inherit everything
    // above, the one-file-at-a-time rule included.
    projects: [
      {
        extends: true,
        test: { name: 'core', include: ['src/**/*.test.ts', 'db/**/*.test.ts'] },
      },
      {
        extends: true,
        test: { name: 'fixtures', include: ['fixtures/**/*.test.ts'] },
      },
    ],
  },
});
