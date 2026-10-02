/**
 * Mutation testing of the money core, SEEN-116.
 *
 * Stryker mutates the product code under src/ and runs the database-free tests
 * against every mutant: vitest's `core` project limited to src/, the test:unit
 * path. db/ is left out on purpose (SEEN-116 clarify, record 6): its tests need
 * the local Supabase stack and hold no money arithmetic, and a mutant waiting on
 * Postgres is a CI job tied to docker for nothing.
 *
 * The floor is not here. Stryker's own `thresholds.break` would make the gate a
 * number the harness cannot read, so Stryker only writes the JSON report and the
 * harness computes the score over the files a slice names and holds it to
 * [mutation] in harness/thresholds.toml.
 *
 * `pnpm --filter @seen/core mutation` runs it. CI adds --incremental and --mutate
 * with the files a pull request changed; incrementalFile is where the previous
 * run's results are kept between those runs.
 */
export default {
  packageManager: 'pnpm',
  // Named rather than discovered. Stryker's default looks for @stryker-mutator/*
  // beside its own install, and pnpm keeps that directory to core's own
  // dependencies, so neither plugin is found there.
  plugins: ['@stryker-mutator/vitest-runner', '@stryker-mutator/typescript-checker'],
  testRunner: 'vitest',
  vitest: { configFile: 'vitest.config.ts', dir: 'src' },
  checkers: ['typescript'],
  tsconfigFile: 'tsconfig.json',
  mutate: ['src/**/*.ts', '!src/**/*.test.ts'],
  coverageAnalysis: 'perTest',
  reporters: ['json', 'clear-text', 'progress'],
  jsonReporter: { fileName: 'reports/mutation/mutation.json' },
  incrementalFile: 'reports/stryker-incremental.json',
  tempDirName: '.stryker-tmp',
  cleanTempDir: true,
};
