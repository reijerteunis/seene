// Refused by tsconfig/exactOptionalPropertyTypes. An optional field set to
// undefined overwrites what the marketplace sent last time; an absent one does
// not, and without the flag the two are the same type.
interface SettlementLineUpsert {
  externalReference?: string;
}

export const withoutReference: SettlementLineUpsert = { externalReference: undefined };
