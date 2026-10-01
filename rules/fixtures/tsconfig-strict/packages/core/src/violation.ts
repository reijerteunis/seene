// Refused by tsconfig/strict. An untyped parameter in a detector is a detector
// whose inputs nobody declared, and this is the money core.
export function commissionFor(line) {
  return line.amountCents;
}
