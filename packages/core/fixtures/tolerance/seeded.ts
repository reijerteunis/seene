/**
 * A fixture, not product code: detector.ts with the bug SEEN-116 seeds on
 * purpose, the tolerance applied with the wrong sign. It raises on charges
 * inside the tolerance, which in a claims product is a claim filed for money
 * the marketplace never kept.
 *
 * Committed so the property can be shown to fail on it (detector.test.ts), and
 * the same change is the mutant Stryker makes of detector.ts and the property
 * kills (stryker.fixture.config.mjs). Never fix it: a seeded bug that is fixed
 * proves nothing.
 */
export function exceedsTolerance(
  expectedCents: number,
  chargedCents: number,
  toleranceCents: number,
): boolean {
  return chargedCents > expectedCents - toleranceCents;
}
