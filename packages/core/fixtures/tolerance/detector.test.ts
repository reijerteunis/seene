/**
 * SEEN-116's proof that the machinery catches a money bug, on a fixture that is
 * not product code: an overcharge detector in its correct form (detector.ts) and
 * with its tolerance sign flipped (seeded.ts), held to one stated invariant.
 *
 * The property is written to the convention in docs/harness/workflow.md: its
 * title begins `invariant: ` and states the invariant as a sentence, and it runs
 * through @fast-check/vitest's test.prop, so a failure prints the counterexample
 * and the seed that replays it. The seed is fixed (SEEN-136): the same inputs on
 * every run, so a green here is the same green everywhere.
 *
 * The inputs are built around the edge of the tolerance rather than at random
 * charges: the charge is the expected fee plus the tolerance plus an offset, so
 * the charge is outside the tolerance exactly when the offset is positive. That
 * makes the oracle a fact about the inputs and not a second copy of the
 * comparison under test, and it puts the boundary, where a flipped or loosened
 * comparison hides, in reach of every run.
 *
 * This file runs only by `pnpm --filter @seen/core test:fixtures` and under
 * stryker.fixture.config.mjs, never in `test` or `test:unit`.
 */
import { fc, test } from '@fast-check/vitest';
import { expect } from 'vitest';

import { exceedsTolerance } from './detector.ts';
import { exceedsTolerance as seededExceedsTolerance } from './seeded.ts';

type Detector = typeof exceedsTolerance;

/** Fixed so that a failure replays exactly, as SEEN-136's hermetic rule asks. */
const SEED = 116;

const expectedCents = fc.integer({ min: 0, max: 1_000_000 });
const toleranceCents = fc.integer({ min: 0, max: 500 });
/** Near the edge as often as far from it: an offset of zero is the boundary itself. */
const offsetCents = fc.oneof(
  fc.integer({ min: -3, max: 3 }),
  fc.integer({ min: -100_000, max: 100_000 }),
);

/** The invariant, once, so the correct and the seeded detector face the same statement. */
function staysInsideTheTolerance(detect: Detector) {
  return (expected: number, tolerance: number, offset: number): boolean =>
    detect(expected, expected + tolerance + offset, tolerance) === offset > 0;
}

test.prop([expectedCents, toleranceCents, offsetCents], { seed: SEED })(
  'invariant: the overcharge detector never raises inside the tolerance and always raises outside it',
  staysInsideTheTolerance(exceedsTolerance),
);

test('the same invariant finds a counterexample in the detector with the tolerance sign flipped', () => {
  const result = fc.check(
    fc.property(
      expectedCents,
      toleranceCents,
      offsetCents,
      staysInsideTheTolerance(seededExceedsTolerance),
    ),
    { seed: SEED },
  );

  expect(result.failed, 'the property passed on the seeded bug, so it states nothing').toBe(true);
  expect(result.counterexample).not.toBeNull();
});
