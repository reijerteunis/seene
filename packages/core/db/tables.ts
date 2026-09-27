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

/**
 * What every buyer PII column's own comment has to say, phrase by phrase.
 *
 * CLAUDE.md requires buyer PII to be "encrypted at rest", and that sentence has
 * more than one reading: a volume the provider encrypts, or the column itself
 * encrypted so that a dump and a support query as `service_role` yield ciphertext.
 * This schema relies on the first and implements nothing of the second, and until
 * the second review of SEEN-008 said so nothing in the repository recorded which
 * reading was in force. So each column states it, and this list is what makes the
 * statement assertable: a migration that drops the sentence, or a later column
 * that repeats the old comment, fails `schema.test.ts` rather than quietly
 * shedding the obligation. Column-level encryption is a decision beyond this
 * ticket and the comment says so, with who is owed it and when.
 */
export const BUYER_PII_COMMENT_TERMS = [
  'PII',
  '30 days',
  'SEEN-083',
  'storage layer only',
  'cleartext',
  'column-level encryption is owed and unowned',
  'SEEN-082',
] as const;

/** Where the migrations live, relative to the repository root. */
export const MIGRATIONS_DIRECTORY = 'supabase/migrations';

/**
 * The privilege statements no migration may contain, and why each is a trap.
 *
 * `grant ... on all tables in schema public` reaches every table in the schema,
 * including the ones an earlier migration deliberately narrowed: parts 1, 2 and 3
 * of the trade record each ended with one, and each silently re-granted update and
 * delete on `audit_events` to the very roles the part before it had revoked them
 * from. Part 4 revokes per table and is last, so the end state was right, but the
 * next migration author copies the tail of the migration in front of them, and one
 * such copy hands `authenticated` insert, update and delete on `settlement_lines`,
 * `claims` and `invoices` back again, with no self-check re-running to notice.
 *
 * `alter default privileges` is the same hazard one level up: it grants on tables
 * that do not exist yet, which is how `anon` and `authenticated` held four
 * privileges on all twenty-nine tables from the moment each was created.
 *
 * Grant per table, by name, and say what each grant is for. A comment asking for
 * that was already in part 4 and was not enough; this is the failing test the next
 * author meets instead.
 */
export const FORBIDDEN_PRIVILEGE_STATEMENTS = [
  {
    name: 'grant ... on all tables in schema',
    pattern: /\bgrant\b[^;]*\ball\s+tables\s+in\s+schema\b/i,
  },
  {
    name: 'alter default privileges',
    pattern: /\balter\s+default\s+privileges\b/i,
  },
] as const;

/**
 * The three roles the Supabase Data API binds a request to.
 *
 * A browser request arrives as `anon` before sign-in and as `authenticated`
 * after it; the workers and the API connect as `service_role`, which bypasses
 * row-level security. There is no fourth: a privilege held by one of these three
 * is a privilege a request can reach.
 */
export const DATA_API_ROLES = ['anon', 'authenticated', 'service_role'] as const;

/**
 * The privileges the privilege assertion governs.
 *
 * These five are the ones that read or change a row. REFERENCES, TRIGGER and
 * MAINTAIN are not data access, and MAINTAIN only exists from Postgres 17, so
 * naming them would tie the assertion to a server version rather than to the
 * boundary it guards.
 */
export const GOVERNED_PRIVILEGES = [
  'DELETE', 'INSERT', 'SELECT', 'TRUNCATE', 'UPDATE',
] as const;

/**
 * What each Data API role may do to a trade-record table, sorted as the
 * catalogue reports it.
 *
 * `authenticated` reads and nothing else. Every write goes through the API as
 * `service_role`: the web application reads Postgres through row-level security
 * and nothing in the product writes from the client, so an insert, update or
 * delete privilege on the client's role is a privilege only an attacker has a
 * use for. It is what let a signed-in user delete their own tenant row and take
 * the whole trade record and every audit event with it through the cascade, and
 * what let the party being invoiced write its own settlement line, credit its
 * own claim, void its own invoice and state its own headroom figure.
 *
 * `anon` holds nothing at all, including select: it carries no tenant claim, so
 * the policy already yields it no rows, and a table that later loses its policy
 * should not also be readable by a caller who never signed in.
 */
export const TABLE_PRIVILEGES: Readonly<Record<string, readonly string[]>> = {
  anon: [],
  authenticated: ['SELECT'],
  service_role: ['DELETE', 'INSERT', 'SELECT', 'TRUNCATE', 'UPDATE'],
};

/**
 * The same, for the tables in `APPEND_ONLY_TABLES`, where `service_role` loses
 * update, delete and truncate as well: the gate writes an audit event and no
 * role the application uses may rewrite one. The trigger refuses the same two
 * commands for every role including the table's owner, and its one exception,
 * the delete that the cascade from an erased tenant performs, is now reachable
 * only by a role that holds delete on `public.tenants`, which is `service_role`
 * and the owner alone.
 */
export const APPEND_ONLY_PRIVILEGES: Readonly<Record<string, readonly string[]>> = {
  anon: [],
  authenticated: ['SELECT'],
  service_role: ['INSERT', 'SELECT'],
};

/**
 * The tables a billable event is assembled out of, which no client-bound role
 * may write to under any circumstances.
 *
 * A credit is billable only as an ingested settlement line linked to a claim, so
 * the party that would be invoiced must not be able to write either side of that
 * link, nor void the invoice, nor delete the statement that evidences it, nor
 * state its own headroom figure.
 */
export const BILLING_CRITICAL_TABLES = [
  'claims', 'headroom_entries', 'invoices', 'settlement_lines', 'statements',
] as const;
