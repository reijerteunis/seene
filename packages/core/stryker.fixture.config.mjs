/**
 * Mutation testing of the SEEN-116 fixture, and nothing else.
 *
 * The same toolchain as stryker.config.mjs pointed at the seeded-bug fixture
 * under fixtures/tolerance, so the proof that a property kills the mutant which
 * flips the detector's comparison or its tolerance sign runs on code that is not
 * product code. It writes its own report and its own incremental file, so the
 * fixture never enters the product mutation score.
 *
 * `pnpm --filter @seen/core mutation:fixture` runs it.
 */
import product from './stryker.config.mjs';

// The fixtures project rather than the product's `unit`, which the import above
// has just named: an import is evaluated first, so this assignment is the one
// Stryker's workers inherit.
process.env.SEEN_VITEST_PROJECT = 'fixtures';

export default {
  ...product,
  tsconfigFile: 'fixtures/tolerance/tsconfig.json',
  mutate: ['fixtures/tolerance/detector.ts'],
  jsonReporter: { fileName: 'reports/mutation/fixture.json' },
  incrementalFile: 'reports/stryker-fixture-incremental.json',
};
