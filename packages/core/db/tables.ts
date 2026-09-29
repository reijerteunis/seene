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
 * Every clause a permissive policy in the public schema is allowed to carry,
 * spelled as `pg_policies` renders it back.
 *
 * An allow-list, and that is the whole point of it. The first version of the
 * tenancy checker asked whether a clause contained the text `current_tenant`,
 * which is a deny-list of one pattern written the other way round, and the second
 * Codex review of SEEN-008 (CODEX-02) ran two clauses straight past it: `using
 * (seen.current_tenant() IS NOT NULL)`, which admits every row to any caller who
 * has any tenant claim at all, and `using (tenant_id = seen.current_tenant() OR
 * true)`, which names the tenant and then throws the comparison away. Both
 * mention `current_tenant`; neither compares anything to it. The next expression
 * past a deny-list is always cheap to write, so the checker does not try to
 * recognise the bad ones: a clause is bound when it is one of these and unbound
 * otherwise, and there is no third answer for an expression nobody anticipated.
 *
 * The cost is that a policy which legitimately narrows further, say the tenancy
 * comparison AND a status, is reported until its exact clause is added here. That
 * is the trade taken on purpose: adding a line to this list is a decision somebody
 * writes down and a reviewer reads, and a conjunct that only narrows is safe to
 * add, while an `OR` that widens is exactly what should cost an argument. What
 * proves a clause on this list does not expose another tenant's rows is not its
 * text at all, it is the cross-tenant read `rls.test.ts` performs against every
 * governed table.
 *
 * Compared after whitespace is collapsed, so a Postgres release that re-renders
 * the same expression with different spacing does not read as a leak.
 */
export const TENANCY_CLAUSES = ['(tenant_id = seen.current_tenant())'] as const;

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

/**
 * The foreign keys allowed to join two tenant-owned tables without carrying
 * `tenant_id` across the join. There are none, and the list is empty on purpose.
 *
 * Every table here carries `tenant_id` and a row-level security policy, and both
 * were read as the whole of tenant isolation until the first Codex review of
 * SEEN-008 (CODEX-01). They are not. A policy decides which rows a request sees;
 * it says nothing about whether a child row's parent belongs to the same tenant,
 * and a key written `references public.connections (id)` accepts any connection
 * in the database beside any `tenant_id`. Measured against the local stack before
 * the fifth migration: `service_role` wrote an order with tenant B's `tenant_id`
 * and tenant A's `connection_id`, both keys accepted it, and erasing tenant A
 * then deleted that order through the cascade while tenant B stood. One tenant's
 * deletion on request destroyed another tenant's trade record.
 *
 * So every foreign key between two tables that carry `tenant_id` maps `tenant_id`
 * to `tenant_id` as part of the key, which the database then enforces on every
 * insert and update with no code on the ingest side having to remember. The keys
 * to `public.tenants` already satisfy this by their nature, because the column
 * they reference is `tenant_id` itself.
 *
 * `schema.test.ts` reads this list rather than a hard-coded set of key names, so
 * an exemption is possible and costs whoever wants one an entry here with the
 * reason. An empty list is the claim that no key in the schema needs one.
 */
export const CROSS_TENANT_FOREIGN_KEY_EXEMPTIONS: readonly string[] = [];

/** Where the migrations live, relative to the repository root. */
export const MIGRATIONS_DIRECTORY = 'supabase/migrations';

/**
 * The documents outside this package that its tests read as an authority, so the
 * turbo cache has to hash them, relative to the repository root.
 *
 * `marketplaces.test.ts` parses the routing table of `docs/architecture.md` and
 * compares it cell by cell with the seeded catalogue, with the document as the
 * authority. The task's cache key is the files of its own package plus whatever is
 * named in `turbo.json`, so an edit to a routing cell changed nothing turbo
 * hashed: the second Codex review of SEEN-008 (CODEX-03) measured sixteen inputs,
 * every migration among them and no document, and a cached pass could therefore be
 * replayed over a document the catalogue no longer matches. The migrations were
 * added to the input list for the same reason one round earlier; this is the other
 * file the suite reads from outside its own package.
 */
export const HASHED_REPOSITORY_DOCUMENTS = ['docs/architecture.md'] as const;

/**
 * How a file under `supabase/migrations` declares itself a member of the trade
 * record v1 set, and the header line every member has to carry.
 *
 * The set is the six SEEN-008 migrations, recognised by the `trade_record_v1`
 * segment of their filenames, and not every file in the directory: the evidence
 * bucket migration of 24 September creates a storage bucket for the environment,
 * takes no part in the privilege boundary the parts hand to each other, and
 * numbering it in would make every later ticket's migration renumber these
 * headers. So the header reads `Trade record v1, part N of M`, counting the set it
 * names, and `schema.test.ts` compares M with the number of members on disk rather
 * than with the number four: a fifth part is added by writing `part 5 of 5` and
 * correcting the four in front of it, and a migration belonging to another ticket
 * changes nothing here.
 *
 * Why the count is asserted and not just written. Part 3 ends by saying it grants
 * no table privilege because part 4 decides the privileges of every table per
 * table and by name. An author told by line 1 that the set is three files stops at
 * part 3, never reads part 4's boundary or its self-check, writes their table with
 * Supabase's default ACL standing, and it is born writable by `anon` and
 * `authenticated`. The headers are the route to part 4, so they have to count.
 */
export const TRADE_RECORD_MIGRATION_MARKER = 'trade_record_v1';

/** The `part N of M` header, matched against a member's first line. */
export const MIGRATION_SET_HEADER = /^--\s+Trade record v1, part (\d+) of (\d+)\b/;

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
 * `alter default privileges ... grant` is the same hazard one level up: it grants
 * on relations that do not exist yet, which is how `anon` and `authenticated` held
 * four privileges on all twenty-nine tables from the moment each was created, and
 * it is not only tables it reaches. `defaclobjtype = 'r'` covers every relation
 * kind a `create table`, `create view`, `create materialized view` or `create
 * foreign table` produces, so the same default made a view born readable by a
 * caller who never signed in, and a view is not subject to row-level security
 * unless it says `security_invoker = true`. That is F19.
 *
 * Only the granting form is forbidden, and the narrowing is deliberate rather
 * than a softening. The revoking form is the only statement in Postgres that can
 * take a default privilege away, and part 6 is made of one: a rule that refused
 * `alter default privileges` outright would have refused the fix for the hazard it
 * was written about, and the way out of that is not an exception in a comment but
 * a rule that says which direction is the hazard. A revoke can only narrow.
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
    name: 'alter default privileges ... grant',
    pattern: /\balter\s+default\s+privileges\b[^;]*\bgrant\b/i,
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

/**
 * The two Data API roles a browser request is bound to.
 *
 * `service_role` is the third, and it is deliberately not here. It bypasses
 * row-level security by design, no request from a browser is ever bound to it,
 * and part 4 grants it per table by name. The question these two answer is a
 * different one: what a caller holding nothing but a session cookie, or not even
 * that, can reach.
 */
export const CLIENT_BOUND_ROLES = ['anon', 'authenticated'] as const;

/**
 * The relation kinds that hold rows and are not an ordinary table, named as a
 * failure message should name them.
 *
 * Every tenancy, privilege and append-only guard this ticket wrote asks
 * `pg_class` for `relkind = 'r'`, which is an ordinary table and nothing else,
 * and so does part 4's per-table revoke and its self-check. Four other kinds hold
 * rows and are reachable through the Data API exactly as a table is, and the
 * third Codex review of SEEN-008 (F19) measured what that costs on the two that
 * matter:
 *
 * A **view** is not subject to the row-level security of the tables underneath it
 * unless it is created `with (security_invoker = true)`; by default it runs with
 * its owner's rights, and the owner of every relation in this schema is the
 * migration role. `anon` is refused `public.shipments` with SQLSTATE 42501 and
 * reads both tenants' `buyer_name` and `buyer_address` through a three-line view
 * over it.
 *
 * A **materialised view** is never subject to row-level security at all, whatever
 * it is created with: it is a stored copy of the rows the owner could see, so
 * there is no request for a policy to be applied to. That is why the rule for one
 * is not `security_invoker` but "not in the public schema".
 *
 * A **partitioned table** carries rows in its partitions and answers to `relkind
 * = 'p'`, so the tenancy guard would not have seen one either. A **foreign table**
 * is rows on another server with no policy of this database's on them.
 *
 * SEEN-046 and SEEN-024 are the tickets that will want exactly such a view.
 */
export const ROW_BEARING_RELKINDS: Readonly<Record<string, string>> = {
  f: 'a foreign table',
  m: 'a materialised view',
  p: 'a partitioned table',
  v: 'a view',
};

/**
 * The option a view in the public schema has to carry, and the values Postgres
 * accepts for it.
 *
 * `security_invoker = true` makes the view read its base tables with the rights
 * and the claims of the caller, which is what puts the tenancy policy back in
 * force underneath it. Postgres normalises a boolean storage parameter as it was
 * written rather than to one spelling, so `on`, `yes` and `1` are the same option
 * set and all four are read as set.
 */
export const VIEW_SECURITY_OPTION = 'security_invoker';

/** The values of that option which mean it is on. */
export const VIEW_SECURITY_OPTION_TRUE = ['1', 'on', 'true', 'yes'] as const;
