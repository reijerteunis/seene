/**
 * A fixture, not product code. SEEN-116 proves its property and mutation
 * machinery on this function rather than on a detector in src/, so the proof
 * waits on no platform ticket. Nothing in src/ imports it, the package does not
 * export it, and the product mutation score never counts it.
 *
 * An overcharge detector in its correct form: it raises when the marketplace
 * charged more than the expected fee plus the tolerance. Every amount is integer
 * cents.
 */
export function exceedsTolerance(
  expectedCents: number,
  chargedCents: number,
  toleranceCents: number,
): boolean {
  return chargedCents > expectedCents + toleranceCents;
}
