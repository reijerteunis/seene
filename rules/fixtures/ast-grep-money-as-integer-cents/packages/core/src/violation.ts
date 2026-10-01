/**
 * Two ways an amount stops being integer cents: decimal parsing on the way in,
 * and a decimal literal bound to a name that says it is money.
 */
export function toCents(text: string): number {
  return Math.round(parseFloat(text) * 100);
}

export const shippingFee = 1.95;
