// Refused by biome/useAwaitThenable. An await on something that is not thenable
// is an await on the wrong call, and it reads as though the asynchronous one had
// been made.
export async function settledTotalCents(): Promise<number> {
  const total = await 1250;
  return total;
}
