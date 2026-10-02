// Refused by tsconfig/noUncheckedIndexedAccess. A marketplace sends a shorter
// array than the one before it, and without the flag this reads undefined as a
// settlement line.
export function firstReferenceLength(references: readonly string[]): number {
  return references[0].length;
}
