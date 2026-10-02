// Refused by biome/recommended, through suspicious/noImplicitAnyLet: a binding
// declared without a type and assigned afterwards is an evolving any that the
// compiler's noImplicitAny permits.
export function latestSettlementPeriod(): string {
  let period;
  period = '2026-09';
  return period;
}
