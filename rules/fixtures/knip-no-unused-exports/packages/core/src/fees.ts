/**
 * `expectedFeeCents` is exported and nothing imports it: a second definition of
 * the same arithmetic that no test and no caller ever reads.
 */
export function commissionCents(amountCents: number): number {
  return Math.round(amountCents * 15) / 100;
}

export function expectedFeeCents(amountCents: number): number {
  return Math.round(amountCents * 15) / 100;
}
