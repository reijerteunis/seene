import { updateOffer } from '../../../packages/connectors/src/writes/offers.ts';

/** A price written to a marketplace with no gate decision and no audit event. */
export const raise = updateOffer;
