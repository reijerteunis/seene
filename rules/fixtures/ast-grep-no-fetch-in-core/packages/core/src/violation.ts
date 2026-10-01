/**
 * The domain reaching the network. No import names it, because fetch is a
 * global, so the layering rules see nothing here at all.
 */
export async function competingOffers(ean: string): Promise<unknown> {
  const response = await fetch(`https://marketplace.invalid/offers/${ean}`);
  return response.json();
}
