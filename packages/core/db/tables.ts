/**
 * The trade record's tables, as one list the tests and the later tickets read.
 *
 * The migrations under `supabase/migrations/` create the tables; this is the
 * TypeScript side of the same fact, so a test asserts against one list rather
 * than against a second copy of the names. The list grew with each migration:
 * the thirteen tables of the tenancy, orders and settlement migration, the eleven
 * of the findings, claims and agent migration, and the five of the commerce and
 * billing migration, which is twenty-nine in all.
 *
 * `schema.test.ts` reads it in both directions. Every name here must exist in the
 * public schema, and every table in the public schema must carry `tenant_id`, an
 * enabled row-level security policy and the one tenancy expression, whether or
 * not it is named here: the catalogue is the authority, so a table added later
 * without tenancy fails the test without anyone remembering to extend it.
 */
export const TRADE_RECORD_TABLES = [
  'agent_actions',
  'agent_runs',
  'approvals',
  'audit_events',
  'claim_events',
  'claims',
  'competitor_snapshots',
  'connections',
  'evidence',
  'fee_expectations',
  'findings',
  'headroom_entries',
  'invoices',
  'listings',
  'marketplaces',
  'message_threads',
  'messages',
  'order_lines',
  'orders',
  'policies',
  'price_changes',
  'products',
  'returns',
  'settlement_lines',
  'settlements',
  'shipments',
  'statements',
  'tenants',
  'users',
] as const;

export type TradeRecordTable = (typeof TRADE_RECORD_TABLES)[number];

/**
 * The tables whose rows arrive from a marketplace and are therefore upserted on
 * the marketplace's own identifier: each carries a unique index on
 * `(tenant_id, marketplace, external_id)`, which is what makes an ingest run
 * idempotent rather than duplicating what it has already read.
 */
export const EXTERNALLY_SOURCED_TABLES = [
  'orders',
  'returns',
  'settlement_lines',
  'settlements',
  'shipments',
] as const;

/** The name of the JWT claim every tenancy policy reads, through `seen.current_tenant()`. */
export const TENANT_CLAIM = 'tenant_id';

/**
 * The tables no row may ever be rewritten in.
 *
 * `audit_events` is the record the policy gate writes before every side effect
 * (SEEN-032), so an update to one of its rows is a rewrite of what the agent is
 * accountable for. `schema.test.ts` asserts both halves of the guarantee against
 * each name here: no application role holds the update or delete privilege, no
 * policy permits either command, and a trigger refuses both even for the role
 * that owns the table. The one delete that is allowed is a tenant's erasure,
 * which takes the audit rows with the tenant.
 */
export const APPEND_ONLY_TABLES = ['audit_events'] as const;

/**
 * Every column in the trade record that holds buyer-identifying data, as
 * `table.column`.
 *
 * SEEN-083 has to expire this data after 30 days, and it should find a list
 * rather than search for one. `schema.test.ts` reads it in both directions: each
 * column here exists and says in its own comment that it is PII with a 30-day
 * expiry owed, and no other column in the public schema is named for the buyer
 * without being on this list, so a later migration that adds one without saying
 * so fails the test.
 */
export const BUYER_PII_COLUMNS = [
  'evidence.buyer_address',
  'evidence.buyer_name',
  'returns.buyer_address',
  'returns.buyer_name',
  'shipments.buyer_address',
  'shipments.buyer_name',
] as const;
