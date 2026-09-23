/**
 * Deterministic reconciliation. Matching, fee expectations and euro arithmetic live
 * here as pure functions with tests, because the model reasons and code reconciles.
 */

export const packageName = '@seen/core';

/** The currency every amount in the trade record is denominated in. */
export const LEDGER_CURRENCY = 'EUR';

/** Amounts are integer cents: floating point money is how reconciliations drift. */
export function sumCents(amounts: readonly number[]): number {
  return amounts.reduce((total, amount) => total + amount, 0);
}
