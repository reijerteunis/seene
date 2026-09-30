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
 * The registry of tenant ids an erasure has consumed, and the two columns it is
 * allowed to hold.
 *
 * F21: the one delete the append-only guarantee permits is the cascade from
 * `public.tenants`, and nothing stopped the tenant being put back afterwards.
 * `tenant_id` is a plain uuid primary key with a default, so it is settable on
 * insert, and a tenant re-created under its old id resolves in every token and
 * every invoice that names it with no audit events behind it. An erasure and an
 * absence of one become the same observation.
 *
 * The registry is in `seen` rather than `public` for the same reason
 * `seen.marketplace_catalogue` is: only `public` is exposed through the Data API,
 * and a list of erasures belongs to no tenant and must not be readable by one.
 *
 * The columns are the whole of what a tombstone may say. An erased tenant's name,
 * its users and its buyers are what the erasure was for, so the registry records
 * that an id is spent and when, and nothing that would make it a retained record
 * of an erased customer. `schema.test.ts` reads the two lists against the
 * catalogue so a later migration cannot widen it quietly.
 */
export const ERASURE_REGISTRY_TABLE = 'seen.erased_tenants' as const;

/** @see ERASURE_REGISTRY_TABLE */
export const ERASURE_REGISTRY_COLUMNS = ['erased_at', 'tenant_id'] as const;

/**
 * The name fragment that finds part 8, the member of the set that makes an erased
 * tenant id unusable.
 *
 * A fragment rather than the whole name, for the reason
 * `RELATION_RULE_MIGRATION_MARKER` records: the timestamp in front of it is the
 * CLI's. The suite executes that file's own `do` block against a registry it has
 * re-keyed, rather than restating what the block asks in TypeScript beside it,
 * because the check and the test would then be two rules and this ticket has
 * produced a finding for nearly every place a statement and a sentence about it
 * drifted apart.
 */
export const ERASURE_REGISTRY_MIGRATION_MARKER = 'erased_tenant_ids';

/**
 * The catalogue's own type names for a column that can hold a sentence, and
 * therefore a buyer's name or address whatever the column is called.
 *
 * This is the search set the buyer PII inventory is read out of, and widening it
 * to this is the whole of the fix for F20. The inventory used to be read out of
 * the columns whose name begins with `buyer`, so the only columns it could find
 * were the ones already named for the buyer: it answered its own premise, and the
 * claim above `BUYER_PII_COLUMNS` that no column named for the buyer could escape
 * it was true and worth nothing. It is CODEX-02's shape a third time, a set
 * narrowed by how the next thing is spelled. `claims.claim_text` holds the text a
 * marketplace was told, which for a lost parcel is the buyer's name and address;
 * `messages.body` and `message_threads.subject` hold what a buyer typed, which is
 * where a buyer writes their own delivery address. None of the three is spelled
 * `buyer` and none was ever a candidate.
 *
 * `pg_type.typname` rather than the SQL spelling, so `character varying(64)` and
 * `character varying` are one name. An array of any of them counts too: a list of
 * strings holds an address as readily as one string does, which is how
 * `connections.scopes` becomes the hundred and twentieth candidate to the hundred
 * and nineteen the third review measured. `json` and `bpchar` are here although
 * the schema has neither, because the set is what can hold prose and not what
 * happens to exist today.
 */
export const FREE_TEXT_TYPE_NAMES = ['bpchar', 'json', 'jsonb', 'text', 'varchar'] as const;

/**
 * How a column tells the catalogue which of the two it is, as the first words of
 * its own comment.
 *
 * Every candidate is classified by hand, one at a time, because nothing in the
 * schema classifies one for us. The review that found F20 expected most of the
 * hundred and twenty to be bounded by a `check` constraint to a fixed value set,
 * which would have settled them without an author's opinion. Measured against the
 * stack: not one column is. Part 2 decided that on purpose, and says so, because
 * "a value nobody anticipated must land in the record and be reconciled, not
 * rejected at ingest", so `status`, `mode` and `direction` are unconstrained text
 * with their vocabulary in a comment. The `currency` columns carry the only check
 * there is and it bounds a length, not a value set.
 *
 * `marketplace` was in that list and is no longer, which is a distinction worth
 * keeping rather than a correction. Part 2's principle governs a value a
 * marketplace supplies, where the vocabulary is somebody else's and the honest
 * answer to an unanticipated one is to store it. A marketplace identifier is not
 * supplied by anybody: this schema invents it, part 3 seeds the six from the
 * routing table, and part 9 keys every column holding one to the catalogue, by the
 * parent the row already hangs from wherever there is one. So a marketplace column
 * is now bounded, and it is bounded by a key to a table of rows rather than by a
 * check constraint, which is what keeps adding a marketplace a row rather than a
 * migration over six tables.
 * Reversing that decision to make this assertion cheaper would be paying for a
 * test with an ingest that rejects rows, so the classification is written out
 * instead, and each line is a reason a reviewer can disagree with.
 *
 * It lives in the column's own comment rather than in a second list here for two
 * reasons. A list would be a copy of the schema maintained by hand, and the copy
 * is what drifts; and SEEN-083 has to find this from the database it is deleting
 * from, not from a TypeScript file it does not import. A marker phrase rather
 * than free prose because the assertion has to tell a classification from a
 * description: a column that merely explains itself has not been thought about
 * for this, and the migration that adds one has to say which it is.
 *
 * The limit, stated rather than hidden: this governs stored columns, `relkind`
 * `r` and `p`. A view's columns are derived from them and can rename or
 * concatenate what they expose, which no classification here would follow; what
 * governs a view is part 6, which makes it read its base tables as the caller.
 */
export const BUYER_PII_MARKER = 'Buyer PII';

/** The other answer. Neither marker is a prefix of the other, so a comment
 * begins with exactly one of them or the column is unclassified. */
export const NOT_BUYER_PII_MARKER = 'Not buyer PII';

/**
 * Every column in the trade record that holds buyer-identifying data, as
 * `table.column`.
 *
 * SEEN-083 has to expire this data after 30 days, and it should find a list
 * rather than search for one. `schema.test.ts` reads it in both directions
 * against what the schema declares: each column here says in its own comment that
 * it is buyer PII with a 30-day expiry owed, and each column whose comment so
 * declares itself is here, so a migration that marks a new one and stops there
 * fails the test.
 *
 * The other direction used to be read out of the columns whose name begins with
 * `buyer`, which could only ever find the six that were already listed. Part 7 is
 * why the list is now nine: every column in the schema that can hold prose says
 * which of the two it is, and three that hold a buyer's name and address by their
 * own documented purpose had never been looked at.
 *
 * `claims.claim_text` carries a tension this ticket records and does not settle.
 * It is kept verbatim because it is what a marketplace was actually told, and
 * buyer PII expires after 30 days: expiring it destroys the record, keeping it
 * breaks the rule. Its column comment states the two ways out, redaction in place
 * or never interpolating the buyer's details into the column at all, and leaves
 * the choice to SEEN-027 and SEEN-083, whose tickets it is.
 */
export const BUYER_PII_COLUMNS = [
  'claims.claim_text',
  'evidence.buyer_address',
  'evidence.buyer_name',
  'message_threads.subject',
  'messages.body',
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
 * The columns classified `Not buyer PII` on a promise rather than on a fact, and
 * the ticket each promise falls to.
 *
 * Almost all of the hundred and eleven are not buyer PII because of what they
 * are: a three-letter currency code held to three characters, or a vocabulary of
 * four statuses, cannot hold a name whoever writes it. Four are not like that.
 * `audit_events.payload`, `claim_events.detail`,
 * `message_threads.external_thread_id` and `messages.external_message_id` are
 * free text a ticket nobody has written yet will fill, and each would hold a
 * buyer's data if that ticket wrote the obvious thing: the gate copying a draft
 * reply into the payload, the claim event copying the submitted text, and the
 * mail rail storing the Message-ID it was handed. Their classification is a
 * constraint on the writer, so it has to name the writer.
 *
 * What the assertion over this list can and cannot do. It cannot decide whether a
 * reason is true, which is what a reviewer is for: F31 is a reason that read as
 * true through four reviews and was false on one of the column's two rails. It
 * can require that a classification resting on a promise says so and names the
 * ticket that owes it, in both directions. A column listed here whose comment
 * states no obligation has had the promise edited out from under it while the
 * classification stayed, and a column whose comment states an obligation and is
 * not listed here is a promise nobody is tracking.
 *
 * Naming the ticket in a comment is not the same as the ticket carrying the
 * obligation, which is what the second review found as F34: all four of these
 * promises were made in a migration none of the four owing tickets links to, and
 * none of the four carried a word of it in its acceptance criteria, which are the
 * definition of done a ticket is worked against. So each entry also carries the
 * obligation in a sentence and the terms one acceptance criterion of each owing
 * ticket has to contain, and `schema.test.ts` reads those tickets off disk.
 *
 * What the terms are and are not. Not the criterion's sentence, because a
 * reworded criterion that still carries the obligation would fail and the next
 * author would delete the assertion rather than keep the promise. Not one word
 * either: `digest` alone passes on a criterion about digesting an attachment,
 * which SEEN-062 nearly has already. They are the two or three nouns the
 * obligation cannot be stated without, required together in one criterion so that
 * they have to be about one sentence, matched whole-word and case-insensitively
 * so that spelling a term differently is allowed and using it inside another word
 * is not.
 */
export interface ConstrainedNotBuyerPiiColumn {
  /** The tickets whose code has to keep the classification true. */
  readonly tickets: readonly string[];
  /** Every term one acceptance criterion of each of those tickets has to carry. */
  readonly terms: readonly string[];
  /** The obligation itself, for whoever the assertion fails in front of. */
  readonly obligation: string;
}

export const CONSTRAINED_NOT_BUYER_PII_COLUMNS:
Readonly<Record<string, ConstrainedNotBuyerPiiColumn>> = {
  'audit_events.payload': {
    tickets: ['SEEN-032', 'SEEN-034'],
    terms: ['audit_events', 'payload', 'buyer'],
    obligation: 'the payload holds what the gate decided and the identifiers it decided about, '
      + 'and never the buyer\'s own words: a draft reply belongs in messages.body and a '
      + 'submitted claim text in claims.claim_text, where the 30-day expiry job can find them, '
      + 'and neither can be reached by an expiry once it is copied into an append-only table',
  },
  'claim_events.detail': {
    tickets: ['SEEN-027'],
    terms: ['claim_events', 'detail', 'buyer'],
    obligation: 'the detail records what happened to the claim and when, by reference, and never '
      + 'a copy of the buyer\'s words: the submitted text stays in claims.claim_text, where the '
      + '30-day expiry job looks, and a second copy here is one nobody is looking for',
  },
  'message_threads.external_thread_id': {
    tickets: ['SEEN-062'],
    terms: ['digest', 'Message-ID'],
    obligation: 'on the mail rail a thread is identified by the root message\'s own Message-ID, '
      + 'generated by the buyer\'s mail system where the buyer opened the thread and carrying '
      + 'their sending host and a local part their client chose, so SEEN-062 stores a digest of '
      + 'it and never the id itself',
  },
  'messages.external_message_id': {
    tickets: ['SEEN-062'],
    terms: ['digest', 'Message-ID'],
    obligation: 'every inbound mail message carries a Message-ID its sender generated, which on '
      + 'an inbound message is the buyer\'s, so SEEN-062 stores a digest of it and never the id '
      + 'itself, once per message rather than once per thread',
  },
};

/**
 * How such a column says its classification is an obligation and not an
 * observation, in the words the first two already used: "and it falls to SEEN-032
 * and SEEN-034 to keep it so".
 *
 * A phrase rather than a ticket id, because an id appears in plenty of comments
 * that promise nothing, and this has to find the columns whose non-PII status
 * depends on somebody keeping it.
 */
export const CONSTRAINED_NOT_BUYER_PII_MARKER = 'to keep it so';

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

/** One column the schema may change after it has been written, and why. */
export interface MutableIdentifier {
  /** The column, written `table.column` and unqualified by schema, because the set
   * is derived over `public` and nothing else. */
  readonly column: string;
  /** The operation that legitimately changes it, which is what a reviewer argues
   * with. */
  readonly reason: string;
}

/**
 * The columns the derived immutable set holds that may nonetheless be changed by an
 * `UPDATE`. There are none, and the list is empty on purpose.
 *
 * What the set is, and why it is derived rather than written here. Every finding
 * from F55 onwards was one column that should not change with nothing stopping it,
 * found one at a time, and each repair enumerated the columns it happened to be
 * looking at: part 9 said it made the identifier immutable "in both places this
 * schema writes one" when `public.claims.marketplace` is a third, and the F72
 * section said it had taken "one of the two columns that hold one" when nine columns
 * hold the identifier and three of them are authored. A count written by hand is
 * wrong one migration later, so `rls.test.ts` asks `pg_catalog` for the set instead,
 * by two rules:
 *
 *   - `tenant_id` on every table of `public` that carries one, because part 8
 *     settled that a tenant id is an identity and not a value.
 *   - every column holding an identifier this schema authors rather than derives
 *     from a parent: the key column of a catalogue, meaning a unique key of exactly
 *     `(tenant_id, X)` whose `X` the schema does not mint per row and which a
 *     foreign key points at, plus every column keyed straight to that pair. A
 *     column keyed to a parent row instead, as `public.orders.marketplace` is to
 *     `connections (tenant_id, id, marketplace)`, derives its value from the parent
 *     and is held in place by the parent's own entry in this set.
 *
 * So a table a later migration adds is in the set the moment it carries `tenant_id`,
 * and a second catalogue is in it the moment a key points at one, without anybody
 * remembering to extend a list. What the rules cannot see is an authored identifier
 * that no key points at, which is a value with no catalogue behind it at all: that
 * one has to be noticed by a person, and it is the gap this file writes down rather
 * than papers over.
 *
 * An empty list is the claim that nothing in this schema changes one of these after
 * the row is written: a tenant id never moves, because a new tenant gets a new uuid
 * and the rows of the old one are not carried over; and a marketplace identifier
 * never changes, because an account at another marketplace is another connection and
 * a claim filed on one rail is not the claim on another.
 *
 * Where the list lives, and what an entry here is and is not. F85: this constant was
 * read by `rls.test.ts` and by nothing in the schema. The loop in part 9 that creates
 * a trigger for every member of the derived set read no exception list and there is
 * no route by which a TypeScript constant could reach a `DO` block, so an entry here
 * stopped the suite probing that member while the trigger went on refusing the
 * update in production: the one documented way to argue with the derived set silenced
 * the measurement without changing the schema. So the list the schema honours is
 * `seen.mutable_identifiers()`, written in the migration beside the loop that reads
 * it, and this constant is its mirror rather than its source. `rls.test.ts` reads
 * both and refuses to differ from what the database returns, so neither can be
 * changed alone.
 *
 * What an exemption costs, said in full because it is the thing a later author
 * weighs. Three edits in one migration: the member and its reason added to
 * `seen.mutable_identifiers()`, a `drop trigger` for the trigger the loop has
 * already created on the existing database, since the loop only declines to create
 * one and never removes one, and this constant brought level with it. The reason is
 * the third column and not a comment, because it is what a reviewer argues with.
 */
export const IMMUTABLE_IDENTIFIER_EXCEPTIONS: readonly MutableIdentifier[] = [];

/** Where the migrations live, relative to the repository root. */
export const MIGRATIONS_DIRECTORY = 'supabase/migrations';

/** The document the marketplace routing table is the authority in, relative to the
 * repository root. */
export const ARCHITECTURE_DOCUMENT = 'docs/architecture.md';

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
 *
 * The ticket files of `CONSTRAINED_NOT_BUYER_PII_COLUMNS` are read as an authority
 * too and are not listed here, because a ticket's filename carries a slug from its
 * title and this list would then be stale rather than wrong when one is retitled.
 * `schema.test.ts` resolves them from the ticket id and asks the same question of
 * turbo about each, so both sets are checked by one assertion.
 *
 * This list is no longer where the rule lives, and a later author should not have
 * to find it. The Data API configuration became an authority in the same way and
 * was not hashed either (F40), which is the third time the class arrived, so
 * `repository.ts` is now the only module here that can open a file and it refuses
 * a path the test task does not hash before it reads it. What remains true of this
 * list is that it asks the question up front rather than at the moment of a read,
 * which is worth keeping for the document every run depends on.
 */
export const HASHED_REPOSITORY_DOCUMENTS = [ARCHITECTURE_DOCUMENT] as const;

/** Where the ticket files live, relative to the repository root. */
export const TICKETS_DIRECTORY = 'docs/tickets';

/**
 * How a file under `supabase/migrations` declares itself a member of the trade
 * record v1 set, and the header line every member has to carry.
 *
 * The set is this ticket's own migrations, recognised by the `trade_record_v1` segment
 * of their filenames, and not every file in the directory: the evidence bucket
 * migration of 24 September creates a storage bucket for the environment, takes no
 * part in the privilege boundary the parts hand to each other, and numbering it in
 * would make every later ticket's migration renumber these headers. So the header
 * reads `Trade record v1, part N of M`, counting the set it names, and
 * `schema.test.ts` compares M with the number of members on disk rather than with
 * a literal: a part is added by numbering it and correcting the totals in front of
 * it, and a migration belonging to another ticket changes nothing here.
 *
 * How large the set is, this comment does not say, and that is the second thing it
 * is for. The size is on disk, every member's header states it and the assertion
 * reads the two against each other, so a copy of the number here is a second
 * authority nothing checks: the sentence above once gave the set a smaller size
 * than the directory held, through a round in which every header on disk was
 * right, which is F37. `schema.test.ts` now reports a comment about this set that
 * counts its members to a number the directory contradicts, in this file and in
 * the members themselves. Part 4's preamble is the one place that still counts
 * them, and the assertion reads that count against the directory too, because it
 * is what explains the set to an author writing SQL and reading no TypeScript.
 *
 * Why the count is asserted and not just written. Part 3 ends by saying it grants
 * no table privilege because part 4 decides the privileges of every table per
 * table and by name. An author told by line 1 that the set ends at part 3 stops
 * there, never reads part 4's boundary or its self-check, writes their table with
 * Supabase's default ACL standing, and it is born writable by `anon` and
 * `authenticated`. The headers are the route to part 4, so they have to count.
 */
export const TRADE_RECORD_MIGRATION_MARKER = 'trade_record_v1';

/** The `part N of M` header, matched against a member's first line. */
export const MIGRATION_SET_HEADER = /^--\s+Trade record v1, part (\d+) of (\d+)\b/;

/**
 * The name fragment that finds part 6, the member of the set that carries the
 * rules for the relation kinds no policy of this database governs.
 *
 * A fragment of the name rather than the whole of it, because the timestamp in
 * front of it is the CLI's and a part renamed or re-timestamped should move the
 * test that replays it rather than break it. The suite executes that file's own
 * `do` blocks against a schema it has planted a probe in, instead of restating the
 * rule in TypeScript beside it: a rule written twice is two rules, and this ticket
 * has produced a finding for all but one of the places a comment and a statement
 * drifted apart. What a later migration is actually held to is the text on disk,
 * so the text on disk is what the suite runs.
 */
export const RELATION_RULE_MIGRATION_MARKER = 'relations_that_are_not_tables';

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
 * And `on tables` is only one of the classes it can be written about. The same
 * statement spelled `on functions` grants EXECUTE on a function that does not exist
 * yet, which in a schema the Data API serves is an RPC endpoint reachable with the
 * anon key before the migration that creates the function has been read by anybody.
 * That is F32, and the pattern above catches it already because it matches the
 * statement rather than the object class.
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
 * The governed privileges that can be held on one column rather than on the
 * whole relation, which is the second question every privilege guard has to ask.
 *
 * `grant select (buyer_name) on public.shipments to anon` is filed in
 * `pg_attribute.attacl` and leaves `pg_class.relacl` untouched, so a relation
 * reads as holding nothing for a role while that role reads a buyer's name out of
 * it, and a table-level answer cannot see it either. The fifth Codex review of
 * SEEN-008 (F30) found the guards asking the relation's own list and so missing
 * this route along with a grant to PUBLIC and a privilege held through membership
 * of another role; `has_table_privilege` and `has_column_privilege` answer all
 * three, because they answer what a role can do rather than what a list says.
 *
 * Delete and truncate are not here, and they cannot be: neither takes a column
 * list in the grammar, and `has_column_privilege` refuses the privilege name
 * outright, so asking either of a column would be an error rather than an answer.
 */
export const COLUMN_GRANTABLE_PRIVILEGES = ['INSERT', 'SELECT', 'UPDATE'] as const;

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
 * The relation kinds whose rows this database's own policies govern, named as a
 * failure message should name them.
 *
 * These two are what criterion 2's sentence, "every table in the public schema",
 * is about, and what every tenancy, `tenant_id`, row-level security and privilege
 * guard asks the catalogue for. An ordinary table answers to `'r'`. A partitioned
 * table answers to `'p'`: it holds its rows in its partitions, it is read through
 * the Data API exactly as a table is, and it can carry the whole of this schema's
 * tenancy, because `enable row level security` and `create policy` are both
 * accepted on one and the policy is applied to every row a query through the
 * parent returns.
 *
 * Every guard this ticket wrote asked for `'r'` alone until the fifth Codex review
 * of SEEN-008 (F29). A partitioned table added by a later migration would have
 * been asked for neither a `tenant_id` column nor an enabled policy, and every
 * hundred-per-cent sentence in this ticket would have gone on passing. F19's round
 * widened the privilege half to the kinds below and wrote the tenancy half down as
 * a limit it was not closing; this is that limit closed.
 *
 * A partition of a partitioned table is a relation in its own right and answers to
 * `'r'`, so it is asked these questions on its own account rather than through its
 * parent, and that is what the guarantee needs rather than an accident of the
 * filter. Measured against the local stack in a rolled-back transaction: enabling
 * row-level security on the parent leaves `relrowsecurity` false on the partition,
 * the policy created on the parent is the parent's alone in `pg_policies`, and
 * `authenticated` reading the partition directly with select granted on it sees
 * both tenants' rows where the same role reading through the parent sees one
 * tenant's. A partition therefore owes its own enabled policy, and asking every
 * relation of kind `'r'` for one is how it is asked for.
 *
 * The seventh review of SEEN-008 (F36) is that the two families were agreed on in
 * `schema.test.ts` and nowhere else: `rls.test.ts` and `uniqueness.test.ts` still
 * read `relkind = 'r'` beside it, and the first of those is the behavioural half,
 * which seeds a row of each tenant into every governed relation and reads each back
 * as `authenticated`. So the guard F29's round rested on as the real answer, rather
 * than the textual one CODEX-02 defeated, was the one guard that did not run on the
 * relation kind F29 was about: a partitioned table would have passed the catalogue
 * and never had a read made through its policy. Both files are on these two kinds
 * now.
 *
 * What that costs the fixture is one rule, and it is the parent's: a row is written
 * through the partitioned table and Postgres routes it into the partition covering
 * its values, because that is the path a policy on the parent governs and the path
 * an application takes. A partition is therefore read and never written to, which
 * leaves one case no row reaches at all, a partitioned table with no partition
 * under it, and `rls.test.ts` names that as its own kind of gap rather than letting
 * it pass as a table that happened to be empty.
 */
export const TABLE_RELKINDS: Readonly<Record<string, string>> = {
  p: 'a partitioned table',
  r: 'an ordinary table',
};

/**
 * The relation kinds that hold rows and that this schema's tenancy cannot be
 * expressed over at all, named the same way.
 *
 * Each of them is reachable through the Data API exactly as a table is, and none
 * of them was looked at by anything this ticket wrote until the third Codex review
 * of SEEN-008 (F19) measured what that costs on the two that matter:
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
 * A **foreign table** is rows on another server, and a policy of this database is
 * not what decides which of them a caller sees. It is in this list and not in
 * `TABLE_RELKINDS` for that reason and not because it is harmless: asking one for
 * a `tenant_id` column and an enabled policy would be asking for a guarantee this
 * database cannot keep. Measured on this stack, `enable row level security` and
 * `create policy` are each refused 42809 on one, which is what makes that
 * exclusion sound rather than convenient.
 *
 * The rule for one is the materialised view's, and the seventh review of SEEN-008
 * (F35) is that this comment said so while part 6 refused only the materialised
 * view. It refuses both now, so the sentence is true rather than trimmed to fit:
 * every reason a materialised view does not belong in a schema the Data API serves
 * holds for a foreign table, and one more does. A materialised view is a copy of
 * rows this database produced; a foreign table's rows were never here, it cannot
 * reference `public.tenants` at all, refused 0A000, so part 8's cascade from an
 * erased tenant does not reach one, and `information_schema.tables` reports it in
 * this schema regardless, as FOREIGN beside the twenty-nine BASE TABLEs.
 *
 * What the refusal costs a later ticket is one qualified name: a foreign table over
 * a reporting warehouse, a second Postgres or a Supabase wrapper goes in a schema
 * the Data API does not serve, which `seen` already is, and rows that have to reach
 * the trade record are ingested into a table of it as every connector's are.
 *
 * SEEN-046 and SEEN-024 are the tickets that will want exactly such a view.
 */
export const NON_TABLE_RELKINDS: Readonly<Record<string, string>> = {
  f: 'a foreign table',
  m: 'a materialised view',
  v: 'a view',
};

/**
 * Both families in one lookup, for a failure message that has to name a relation
 * without knowing which family the caller drew it from.
 */
export const RELKIND_NAMES: Readonly<Record<string, string>> = {
  ...TABLE_RELKINDS,
  ...NON_TABLE_RELKINDS,
};

/**
 * The classes of object `pg_default_acl` files a default privilege under, and the
 * word a failure message should call each of them by.
 *
 * `defaclobjtype` is not the same alphabet as `relkind` and the overlap is a trap:
 * `'f'` here is a function and `'f'` in `relkind` is a foreign table. `'S'` is the
 * one letter that means the same thing in both alphabets, a sequence, which is why
 * the sequence guards can be written over `relkind` and over this record in the
 * same breath without a reader having to check which of the two is in hand.
 *
 * Every class is read, rather than the ones a round happened to be looking at.
 * `supabase/config.toml` names the set it auto-exposes as "tables, views, sequences
 * and functions", and each review of SEEN-008 found the previous round had answered
 * one quarter of that sentence: `'r'` was F19's quarter, `'f'` was F32's and `'S'`
 * is F33's. Asking for the whole of `pg_default_acl` is what stops there being a
 * fifth quarter nobody named.
 *
 * `'r'` covers every relation kind a `create table`, `create view`, `create
 * materialized view` or `create foreign table` produces, which is why part 6's one
 * `on tables` statement closed the whole of F19's class. `'f'` covers a function, a
 * procedure and an aggregate alike, so `on functions` is one statement for all
 * three; the grammar spells it `on functions` and `on routines` means the same
 * thing. `'S'` is a sequence, whether `create sequence` made it or a `bigserial` or
 * identity column did, and it is the one class of the three where one revoke is the
 * whole of prevention: a routine needs two, because PostgreSQL grants EXECUTE to
 * PUBLIC on every one it creates and only a default privilege filed against no
 * schema subtracts that, which is the seventh review of SEEN-008 (F39) and part 6's
 * global statement. `SEQUENCE_PRIVILEGES` records the measurement for `'S'`.
 *
 * `'T'` is a type or a domain, and it is here for detection alone, because this set
 * writes no revoke for one. Measured on this stack: `pg_default_acl` holds no `'T'`
 * row at all for schema public, from either grantor, and `alter default privileges
 * ... revoke all on types from anon, authenticated` records no row when it is run,
 * because a revoke of a grant nobody made writes nothing down. `anon` does hold
 * USAGE on every type in this schema, through the grant PostgreSQL makes to PUBLIC
 * on a type it creates, and that grant is reachable. The form with no `in schema`
 * clause, which F39 established on a routine, reaches a type as well: a domain, an
 * enum and a composite created after `alter default privileges for role postgres
 * revoke usage on types from public` are born `{postgres=U/postgres}` with `anon`
 * refused, in `public` and in `seen` alike. So the statement is absent because it
 * is unnecessary and not because it would fail to arrive, which is the ninth
 * review's F44 and the difference between a decision and a limit.
 *
 * Unnecessary twice over, and the reason is stated rather than assumed because
 * "nobody thought about it" is how the other quarters got here. USAGE on a type is
 * not a route to a row: it permits naming the type in a cast, a column or a
 * declaration; no type in this schema holds data; the composite types here are the
 * row types of the twenty-nine tables, and reading a table's rows goes through the
 * table's own privilege, which part 4 governs; and PostgREST serves no type as an
 * endpoint, which is why `config.toml` names four classes and not five. And the
 * statement would change nothing that is here: measured, a table's row type is born
 * with a null `typacl` and USAGE for PUBLIC whether it has run or not, and a row
 * type or the array type beside it is every type these two schemas hold. What is
 * asserted about `'T'`, then, is only that no later migration grants one.
 */
export const DEFAULT_ACL_OBJECT_CLASSES: Readonly<Record<string, string>> = {
  S: 'sequence',
  T: 'type',
  f: 'function',
  r: 'relation',
};

/** One sentence this set wrote about how an object is born, and withdrew. */
export interface WithdrawnBirthClaim {
  /** The class it was written about, in the words `DEFAULT_ACL_OBJECT_CLASSES` uses. */
  objectClass: string;
  /** How it was spelled, in fragments, joined by a space before it is looked for. */
  spelling: readonly string[];
  /** What is true instead, for the reader who has just been sent here by a guard. */
  instead: string;
}

/**
 * The claims about an object's birth this set has made and withdrawn, as the
 * fragments they were written in.
 *
 * One claim, in two classes. Five rounds of this ticket recorded that PostgreSQL's
 * built-in EXECUTE to PUBLIC on a new routine is beyond every default privilege, so
 * a routine was callable until its own migration revoked it, prevention was
 * unavailable and detection was the whole of the defence. The seventh review (F39)
 * showed that this is a property of `alter default privileges ... in schema public`
 * and not of PostgreSQL: the built-in grant is filed against no schema, and the
 * form with no `in schema` clause is filed the same way and does subtract it. Part
 * 6 writes that form. The withdrawal reached part 6, the journal and the ticket's
 * Outcome and left four other sentences standing for a round, each of which went on
 * telling the author of a later migration that detection was the only shape
 * available to them, which is the ninth review's F43.
 *
 * The last two rows are the same claim about a type, which the ninth review's F44
 * found a round later, made by name and with the clause "exactly as for a function"
 * carrying it across. It is false there for the same reason and it was measured the
 * same way, and what changes when it goes is the reason `'T'` carries no revoke:
 * the statement is not written here because it is unnecessary, and not because it
 * would fail to arrive.
 *
 * Held as data rather than as a sentence inside the guard so that the next class
 * this happens to is a row here rather than an argument about whether it is the
 * same defect: `objectClass` says which measurement decides a row, and a class with
 * no row here is one nothing has been withdrawn about yet.
 *
 * Each spelling is kept in fragments and joined before it is looked for, because
 * every file the guard scans includes the file this list is written in: a phrase
 * written here whole would be found here whole, and a guard that reports itself
 * reports nothing.
 *
 * What this is and is not. It catches a withdrawn sentence surviving, being copied
 * or coming back, because it holds the words it was written in rather than a
 * paraphrase of them; it does not catch a new sentence making the same mistake in
 * new words, and nothing textual could. What catches the claim becoming true again,
 * because somebody dropped the statement that makes it false, is the measurement
 * beside the guard in `schema.test.ts`, and that is the half that does not depend
 * on how anybody writes.
 */
export const WITHDRAWN_BIRTH_CLAIMS: readonly WithdrawnBirthClaim[] = [
  {
    objectClass: 'function',
    spelling: ['no default privilege that prevents it', 'and none that could'],
    instead: 'part 6 files one that does, against no schema, so a routine created in `seen` '
      + 'after it runs is born out of reach of every role a request is bound to',
  },
  {
    objectClass: 'function',
    spelling: ['until its own migration', 'revokes it'],
    instead: 'a routine created after part 6 runs carries no grant to PUBLIC to be revoked, and '
      + 'the revokes beside each function close a routine created before part 6 ran',
  },
  {
    objectClass: 'function',
    spelling: ['which no default privilege', 'can do for it'],
    instead: 'the default privilege part 6 files with no `in schema` clause does exactly that',
  },
  {
    objectClass: 'function',
    spelling: ['no statement of this kind', 'can reach that'],
    instead: 'a statement filed against no schema reaches it, which is what part 6 writes; what '
      + 'an assertion about this schema\'s own `pg_default_acl` cannot see is that statement, '
      + 'because it is filed against namespace 0',
  },
  {
    objectClass: 'function',
    spelling: ['each function\'s own revoke', 'is what closes it'],
    instead: 'part 6 closes a routine created after it, and each function\'s own revoke closes '
      + 'one created before it',
  },
  {
    objectClass: 'type',
    spelling: ['which no default privilege', 'can reach, exactly as for a function'],
    instead: 'a statement filed against no schema reaches a type as it reaches a routine: after '
      + '`alter default privileges for role postgres revoke usage on types from public`, the '
      + 'next domain, enum and composite are born `{postgres=U/postgres}` with `anon` refused, '
      + 'in `public` and in `seen` alike. This set writes no such statement because it is '
      + 'unnecessary, not because it would miss',
  },
  {
    objectClass: 'type',
    spelling: ['which no default privilege', 'can take away'],
    instead: 'the form with no `in schema` clause takes it away from every type created after '
      + 'it runs, which is what makes the absence of that statement here a decision and not a '
      + 'limit. What it does not reach is a table\'s row type, which is born holding USAGE for '
      + 'PUBLIC whether the statement has run or not, and which is every type this schema has',
  },
];

/** One sentence this set wrote about the shape of a relation, and withdrew. */
export interface WithdrawnShapeClaim {
  /** The relation it was written about, schema-qualified. */
  readonly relation: string;
  /** How it was spelled, in fragments, joined by a space before it is looked for. */
  readonly spelling: readonly string[];
  /** What is true instead, for the reader who has just been sent here by a guard. */
  readonly instead: string;
}

/**
 * The claims about what keys and indexes a relation carries that this set has made
 * and withdrawn, in the same shape and for the same reason as
 * `WITHDRAWN_BIRTH_CLAIMS` above.
 *
 * The first claim. Part 2 created `public.message_threads` and wrote above the
 * column that the upsert key for message ingest belonged to SEEN-061 and that there
 * was therefore no unique index on it here. Part 9 added one, because SEEN-061 and
 * SEEN-062 cannot write their upsert without it, so the sentence is false of the
 * delivered schema and it is in the file a person opens to find out what the table
 * is. That is F70's class one step over: F70 is a comment describing a column that
 * is not there, this is a comment describing the absence of an index that is.
 *
 * The four after it are one round's worth of the same class, and each of them is in
 * a shape a scanner cannot reach. Two are part 9's claim that all nine keys carrying
 * `marketplace` are NO ACTION, written once as a comment and once inside the
 * `raise` a person meets when the rename is refused, where the catalogue answers
 * that `connections_marketplace_fkey` and `claims_marketplace_fkey` both name `on
 * update cascade` and part 9 wrote the second of them itself (F73). One is part 3's
 * comment on `public.invoices` asserting the contract of `recovery_share_lines`,
 * which part 10 drops: F70's guard removed the sentence above the column and could
 * not see this one, because it is prose inside a `comment on table` statement and
 * names no `table.column` pair anywhere (F74). One is the rename sentence F68
 * withdrew from part 3, left standing in `rls.test.ts` as a present-tense quotation
 * of a file that now says the opposite (F76).
 *
 * The three after those are the fourth review's, and all three are a sentence that
 * outlived what it described rather than a sentence that was wrong when it was
 * written. One is part 9's declaration that a childless row's `tenant_id` can still
 * be moved and that the question is wider than F65 and unsettled, standing 200 lines
 * above the section of the same file that settles it over every table in `public`
 * (F81): record 292 quoted that sentence as the place the gap was declared, so it
 * had already cost one round of rework by being read as current. One is the head of
 * part 9 counting the triggers that refuse a catalogue rename, in the paragraph that
 * has just said it writes no count because a count in a comment is wrong at the next
 * migration, where the last section of the same file installs a third (F82); that
 * sentence was repaired one round earlier for the same reason and made wrong again by
 * the section that repaired it. One is part 5 naming 23502 for a refusal the
 * delivered schema answers 23001, corrected in the assertion that measures it and
 * not in the comment that argues for it (F83).
 *
 * The SQLSTATE class, measured rather than declared unreachable. The fourth review
 * offered the widening in a shape with a fact behind it, unlike the bare cardinal and
 * the English noun phrase this file refuses below: the corpus is small and countable,
 * and a scanner could read a five-character code out of a migration comment and
 * measure it against what the database answers. Counted: 28 comment lines in the ten
 * migrations of this set carry a SQLSTATE token, 29 occurrences across 9 distinct
 * codes, one line carrying `42809` twice. What the count does not support is the
 * scanner. Nine of the 29 state a code the database no longer answers for the
 * statement their sentence names, and eight of the nine are true of what they
 * describe. Measured on the delivered stack as `service_role` in a rolled-back
 * transaction: `update public.marketplaces set marketplace` answers 23001 and
 * `update public.tenants set tenant_id` answers 23001, where part 9's head says the
 * rename the cascade was for is refused 23503 by the keys and part 8 says the
 * tenant's foreign keys refuse the move with 23503. Both sentences are about a
 * layer, both were measured before the trigger that now fires first existed, and
 * both are the argument for putting that trigger there: five of the eight are the
 * before-and-after measurement a section writes to justify itself, and three are
 * present-tense statements of what a key buys in the absence of the trigger above
 * it. A scanner measuring each code against what the database answers now would
 * report all nine and be right about one, a precision of one in nine on the only
 * class it exists for, and telling the eight from the one means deciding whether a
 * sentence is about the delivered statement or about the layer underneath it, which
 * is a tense and a subject read out of English. That is the guess this file declines
 * two paragraphs below for the noun phrase, and it is declined here for the same
 * reason: a guard whose report cannot be trusted is worse than none, because it is
 * read as coverage. So the SQLSTATE is held as the sentence, exactly as the denial
 * of an index is, and the half that can be believed is the assertion in the suite
 * that runs the statement and prints the code the database gave it.
 *
 * Why this is held as the sentence and not caught by a scanner, which is a decision
 * and not an omission. `migrationColumnReferences` can be believed because it
 * compares a name against `pg_attribute`: the reference is a name, and a name is
 * either in the catalogue or not. The claim here is a negation in English. To catch
 * the class rather than this instance, a guard would have to recognise that "there
 * is no unique index on it here", "this column is not keyed", "the upsert key is
 * SEEN-061's to add" and whatever the next author writes are all denials, and then
 * decide which relation and which kind of index each denies, from prose. Every one
 * of those steps is a guess, and a guard whose report cannot be trusted is worse
 * than none, because it is read as coverage. Matching on `index` and asking
 * `pg_index` inverts the error rather than removing it: a comment that correctly
 * says a column is part of the upsert key would be reported, and this set has
 * fourteen of those.
 *
 * The same decision, taken again for F74 and measured rather than assumed.
 * `migrationColumnReferences` reads three shapes, and the shape it cannot read is a
 * sentence inside `comment on table` that describes a column without naming it: "a
 * recovery share line exists only for a claim credited by an ingested settlement
 * line" is about `recovery_share_lines`, and to see that a guard would have to turn
 * an English noun phrase into an identifier and ask `pg_attribute` for it. There is
 * no fact to compare against on the way: a phrase that maps to no column is
 * indistinguishable from a phrase that was never a column name, so every sentence in
 * every table comment would be a candidate. The reachable half is the one already
 * built, a reference that names the pair, and the rest is held here as the sentence.
 *
 * So what is held here is the sentence, in the fragments it was written in, which
 * catches it surviving, being copied or coming back, exactly as the birth claims
 * are. The half that catches the claim becoming true again, because somebody
 * dropped the index, is `pg_index` beside the guard in `schema.test.ts`, and the
 * half that catches the index being there and useless is the upsert the same file
 * runs.
 */
export const WITHDRAWN_SHAPE_CLAIMS: readonly WithdrawnShapeClaim[] = [
  {
    relation: 'public.message_threads',
    spelling: ['upsert key for message ingest belongs to SEEN-061,', 'so there is no unique'],
    instead: 'part 9 creates one, on (tenant_id, connection_id, external_thread_id) and with no '
      + 'predicate, because the upsert SEEN-061 and SEEN-062 have to write needs a unique index '
      + 'to arbitrate and cannot infer a partial one. The key is not SEEN-061\'s to add: what is '
      + 'SEEN-061\'s is the statement that uses it',
  },
  {
    relation: 'public.marketplaces',
    spelling: ['and none of them names an update action,', 'so all nine are NO ACTION'],
    instead: 'seven of the nine are NO ACTION and two name `on update cascade`: part 3\'s '
      + '`connections_marketplace_fkey`, and `claims_marketplace_fkey`, which part 9 writes 140 '
      + 'lines above the sentence and argues for in the paragraph beside it. Both are kept in '
      + 'that shape and both are inert, because the pair they point at cannot be updated at all; '
      + 'what refuses a rename is the seven that carry the value from a child to its parent',
  },
  {
    relation: 'public.marketplaces',
    spelling: ['back to this row and none of them', 'cascades on update'],
    instead: 'two of them do, and a reader who meets this sentence at the moment the trigger '
      + 'refuses them is told the repair is to add `on update cascade` to the connections key so '
      + 'the rename can propagate, where the clause has been there since part 3. So the message '
      + 'states what the refusal means and counts nothing: a number in a `raise` is a claim that '
      + 'rots where nobody reads it until it is quoted back at them',
  },
  {
    relation: 'public.invoices',
    spelling: [
      'A recovery share line exists only for a', 'claim credited by an ingested settlement line',
    ],
    instead: 'part 10 drops `recovery_share_lines`, for F66\'s reason: the column carried no key, '
      + 'no check and no counterpart on the claim, and accepted a recovery share against a claim '
      + 'that was never credited and against a claim id present in no table. The rule the '
      + 'sentence states is CLAUDE.md\'s and stands; what does not stand is this table holding '
      + 'the lines it is stated of, and the obligation is in the comment part 10 writes in its '
      + 'place, which supersedes this one in the catalogue',
  },
  {
    relation: 'public.connections',
    spelling: [
      'renaming an identifier in the catalogue carries the',
      'connections with it rather than orphaning them',
    ],
    instead: 'part 3 says the opposite: the cascade is there so the key can never be the thing '
      + 'that orphans a connection, and not as an invitation to rename an identifier, which the '
      + 'value is to be treated as immutable against once a connection exists. F68 withdrew the '
      + 'claim from part 3 and from the head of part 9, and part 9 now refuses the rename by '
      + 'trigger on the catalogue and on the connection alike. What the two remaining mentions in '
      + 'part 9 are, and why they are deliberately outside these words: both are written in the '
      + 'past tense about a choice that was made and a sentence that was withdrawn, and a '
      + 'withdrawal cannot be recorded by a set forbidden to quote it',
  },
  {
    relation: 'public.claims',
    spelling: [
      'make a marketplace identifier immutable in both places this',
      'schema writes one, the catalogue row and the connection keyed to it',
    ],
    instead: 'there are three places this schema writes one, and `public.claims.marketplace` is '
      + 'the third: it is keyed straight at the catalogue, because a claim hangs from nothing '
      + 'else that names a marketplace, so every one of the six is a valid new value and nothing '
      + 'held the one it was filed on in place. Measured as `service_role`, one update repointed a '
      + 'submitted claim onto a rail it was never filed on while its external case id and its '
      + 'claim text stayed as filed, which is what the claims rail, the capability matrix, '
      + "SEEN-066's deadline watch and SEEN-031's credit match all read. Part 9 counts nothing "
      + 'here now: the last section of it derives from the catalogue every column holding an '
      + 'identifier the schema authors, and refuses an update of each',
  },
  {
    relation: 'public.tenants',
    spelling: [
      'and a childless row\'s tenant_id can still be moved by a role that can write it.',
      'That is a wider question than F65 and it is not settled here',
    ],
    instead: 'no tenant_id in schema `public` can be moved by any role at all, childless or not. '
      + 'The sentence is in the section that takes the catalogue\'s own tenant_id, 200 lines above '
      + 'the section that derives every column holding an identifier this schema authors and '
      + 'refuses an update of each, and it was written before the second one existed. Measured on '
      + 'the delivered database by part 9\'s own two rules: every member of the derived set carries '
      + 'a trigger refusing the update, the ones the sections above write by hand and the rest '
      + 'created by the loop at the foot of the file, with nothing left over. Two costs, and '
      + 'neither is theoretical: a later author who needs the onboarding repair path this file '
      + 'names service_role for twice reads the sentence as permission, writes the UPDATE and is '
      + 'refused 23001 at runtime; and the next reviewer reads it as the declaration of an open '
      + 'gap and reports F78 again, which is what record 292 quoted it as',
  },
  {
    relation: 'public.marketplaces',
    spelling: [
      'so a trigger on each of the two columns refuses it outright, with a message',
      'saying what a real rename would be: a migration that says so, drops the trigger',
      'and moves the rows itself. Both columns',
    ],
    instead: 'the file installs a third such trigger, on `public.claims.marketplace`, and '
      + '`claims_marketplace_fkey` cascades on update, so the rename reaches it. Following the '
      + 'runbook this paragraph gives - drop the two triggers it names, move the rows - and '
      + 'measured in a rolled-back transaction, `update public.marketplaces set marketplace` is '
      + 'accepted for a tenant with no claim and refused 23001 for a tenant with one, by '
      + '`immutable_marketplace` on `public.claims` through the cascade. That is exactly the '
      + 'two-answer shape the section exists to remove, reintroduced in the instructions for the '
      + 'one operation it calls a migration. The count is the defect and not the sentence: the '
      + 'same paragraph says two lines earlier that it writes no count because a count in a '
      + 'comment is wrong at the next migration, and this is the second round that sentence has '
      + 'been repaired for counting. What a rename drops is what the last section derives, which '
      + 'is why the paragraph now names none of them',
  },
  {
    relation: 'public.claims',
    spelling: [
      'settlement or the connection it hangs from, is refused with 23502, so a line',
      'cannot be removed or re-ingested while a claim points at it',
    ],
    instead: 'the delivered schema answers 23001. The not-null constraint on tenant_id was the '
      + 'only thing in the way of a referential action that blanked one when part 5 was written; '
      + 'part 9\'s last section puts a before-update trigger on every tenant_id in `public`, and a '
      + 'before-update trigger runs ahead of the not-null check, so what refuses the bare '
      + 'set-null is the trigger. What the column-list form buys is unchanged, because both '
      + 'refusals fall on the same delete; what is no longer true is the reason, and a reader '
      + 'weighing whether the column list is still worth naming, or adding a ninth set-null key, '
      + 'is sent to a layer that has been superseded. The twin of this sentence in '
      + '`schema.test.ts` was corrected in the same commit that made this one false',
  },
  {
    relation: 'public.claims',
    spelling: ['It made one of the two columns that', 'hold one immutable'],
    instead: 'nine columns hold the marketplace identifier and three of them are authored rather '
      + 'than derived from a parent, so the section that wrote this had taken the catalogue row '
      + 'and one of the two columns keyed straight at it. The number is the defect and not the '
      + 'sentence: F55 onwards is one column at a time, each repair counting the columns it '
      + 'happened to be looking at, so part 9 ends by deriving the set from the catalogue and '
      + 'guarding every member, and a column that enters the set later fails the suite on arrival',
  },
];

/**
 * The relation kind a sequence answers to, in `pg_class` and in `pg_default_acl`
 * alike.
 *
 * A sequence is in neither relation family above and it is not a routine, so it was
 * in no inventory this suite kept: `relkind = 'S'` appeared in no guard in this
 * package until the sixth review of SEEN-008 (F33), and neither did
 * `has_sequence_privilege`. This schema's tenancy cannot be written on one, because
 * it holds no row and no `tenant_id`; and the tenancy cannot be waived for one
 * either, because the number it does hold is derived from every tenant's rows at
 * once.
 *
 * No migration in this set creates one, and that is not the safeguard it reads as: a
 * `bigserial` or a `bigint generated by default as identity` column creates
 * `public.<table>_<column>_seq` without the word sequence appearing in the
 * migration at all, which is how SEEN-014's ingest or SEEN-021's findings would add
 * one without deciding to.
 */
export const SEQUENCE_RELKIND = 'S';

/**
 * The three privileges a sequence can carry, and what each of them lends the caller
 * who holds it, so that a failure says what was reachable and not merely that
 * something was.
 *
 * Measured on this stack in a rolled-back transaction with the default privileges
 * standing, which is how the sixth review of SEEN-008 (F33) measured them: a
 * sequence is born `{postgres=rwU/postgres,anon=rwU/postgres,
 * authenticated=rwU/postgres,service_role=rwU/postgres}`, `anon` called `nextval`
 * and was accepted, read `last_value` and got a count of rows aggregated over every
 * tenant, and called `setval(seq, 1)` and was accepted, which makes the next ingest
 * insert collide on the primary key until the sequence catches up, tenant-wide,
 * from a caller who never signed in.
 *
 * What makes this class unlike a function is worth being exact about, because the
 * two revokes in part 6 read alike and do not buy the same thing. PostgreSQL grants
 * a new sequence nothing to PUBLIC, so there is no built-in grant underneath the
 * default privilege for a revoke to fail to reach, and prevention here is complete
 * rather than bounded. Measured after part 6's revoke: the sequence is born
 * `{postgres=rwU/postgres,service_role=rwU/postgres}`,
 * `has_sequence_privilege('anon', ...)` is false for all three privileges, and
 * `nextval`, `select last_value` and `setval` are each refused 42501. The same
 * holds for the sequence an identity column creates, which is the route a later
 * ticket takes without meaning to.
 */
export const SEQUENCE_PRIVILEGES: Readonly<Record<string, string>> = {
  SELECT: 'read its last value, which is a count of rows across every tenant',
  UPDATE: 'set it with setval, which collides the next insert on the primary key',
  USAGE: 'advance it with nextval',
};

/**
 * The only privilege a function can carry, named rather than spelled inline.
 *
 * `has_function_privilege` accepts EXECUTE and nothing else, because EXECUTE is the
 * whole of what a function grants: there is no column half to this question as
 * there is for a relation, and no read and write to tell apart. What a function
 * lends the caller who holds it is decided by the function's own body and by
 * whether it is `security definer`, not by the privilege.
 */
export const FUNCTION_PRIVILEGE = 'EXECUTE';

/**
 * What `pg_proc.prokind` calls the four kinds of routine, for a message that has to
 * say which one it found.
 *
 * All four are one class to the privilege system and to `alter default privileges`,
 * and all four are exposed by PostgREST as `POST /rpc/<name>` when they are in a
 * schema the Data API serves. They are told apart here only so that a failure names
 * what it found: an aggregate reachable by `anon` and a `security definer` function
 * reachable by `anon` are not the same finding to read about, and a reader sent to
 * the wrong grammar cannot revoke it.
 */
export const PROKIND_NAMES: Readonly<Record<string, string>> = {
  a: 'an aggregate',
  f: 'a function',
  p: 'a procedure',
  w: 'a window function',
};

/**
 * The schema the tenancy helpers and the erasure registry live in.
 *
 * Every guard in this package asked about `public` and nothing else until the
 * second review of SEEN-008 (F38), which is how two functions here came to be
 * executable by `anon` with no test in the suite able to see it. What makes this
 * schema worth its own guards rather than the same ones is that it is the one
 * place the trade record keeps objects the Data API does not serve, so the rules
 * `public` owes and the rules `seen` owes are not the same rules and a guard that
 * copied them across would be wrong in one direction or the other.
 */
export const HELPER_SCHEMA = 'seen';

/**
 * The routines in schema `seen` a browser-bound role is meant to be able to
 * execute, of the eleven that are here.
 *
 * An allow-list where the guard on schema `public` is an emptiness, and the
 * asymmetry is the point rather than an inconsistency. `public` is served by the
 * Data API, so a routine there is a `POST /rpc/<name>` endpoint and the rule can
 * be that no browser-bound role executes anything at all. `seen` is not served,
 * and the rule cannot be that: `seen.current_tenant()` is evaluated as the caller
 * inside every one of the thirty policies, so `authenticated` has to hold USAGE on
 * this schema and EXECUTE on this function or every table in the trade record
 * reads as empty for every request. The exception is safe for a reason that is a
 * property of the function rather than of the list: it is not `security definer`,
 * so it runs as the caller and lends them nothing, and its body reads a setting
 * and touches no relation at all. The guard reports `security definer` beside
 * every routine it finds, so the allow-list stops matching if that ever changes.
 *
 * Why an allow-list is needed here at all, when nothing in `seen` is reachable
 * through an endpoint. A routine is born `proacl` null, which is PostgreSQL's own
 * EXECUTE to PUBLIC, and `anon` holds USAGE on this schema, so a function added
 * here was callable by name by a caller who never signed in unless its own
 * migration revoked that, and part 6's global `alter default privileges ... revoke
 * execute on functions from public` is what stopped it being born that way. That
 * statement is filed against no schema, so it reaches this one; the rounds that
 * wrote F32 concluded no statement could, on a measurement of the per-schema form,
 * and the seventh review (F39) showed the conclusion belonged to the form rather
 * than to PostgreSQL. The allow-list is still needed, for two reasons neither of
 * which the fix touches: a routine created before part 6 runs is born with the
 * built-in grant, and a grant somebody writes on purpose is not a default at all.
 * The two F38 found, `seen.touch_updated_at()` and
 * `seen.refuse_erasure_registry_mutation()`, were harmless only because both return
 * `trigger` and answer 0A000, "trigger functions can only be called as triggers",
 * which is a property of what they happened to return and not of anything the
 * migrations did.
 */
export const HELPER_SCHEMA_CALLABLE_ROUTINES = ['current_tenant()'] as const;

/** Where the Data API's schema list is written, relative to the repository root. */
export const DATA_API_CONFIG = 'supabase/config.toml';

/**
 * How that file spells the list, and the schemas it is allowed to hold.
 *
 * The premise underneath every sentence in this ticket that says an object is out
 * of reach because of where it lives: `seen.erased_tenants` is outside `public` so
 * that a list of which brands have left is outside the Data API, part 6 sends a
 * materialised view and a foreign table to a schema the Data API does not serve,
 * and the allow-list above is an allow-list rather than an emptiness for the same
 * reason. All of that was written down in prose and in no assertion, so a later
 * ticket adding `seen` to this line would publish the erasure registry and the
 * helpers as endpoints and every one of those sentences would quietly become
 * false while the suite stayed green.
 *
 * Read from the file rather than from the running stack, because the file is the
 * only place this repository states it: PostgREST is configured from here, a
 * cloud project would be configured from here too, and asking the container over
 * HTTP would make the suite depend on a service it does not otherwise need to
 * answer a question about a committed line of configuration.
 */
export const DATA_API_SCHEMAS = ['graphql_public', 'public'] as const;

/** The `schemas = [...]` line of the `[api]` section, matched rather than parsed:
 * the repository has no TOML reader, and a regular expression that finds the one
 * array this assertion is about is a smaller dependency than one that would parse
 * a file to read a single line of it. */
export const DATA_API_SCHEMAS_SETTING = /^\s*schemas\s*=\s*\[([^\]]*)\]/m;

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

/**
 * The bucket the storage provider holds evidence and rendered documents in, as
 * `supabase/migrations/20260924000000_evidence_bucket.sql` names it.
 *
 * Named here because part 10 makes the bucket part of the schema's argument
 * rather than part of its environment: an erasure that cannot reach a bucket is
 * an erasure that does not happen, so the suite has to be able to put an object
 * in one and ask what a deletion on request did about it.
 */
export const EVIDENCE_BUCKET = 'evidence';

/**
 * The columns that address a stored object, and which may therefore only ever
 * name an object of their own row's tenant.
 *
 * F64 measured the first of these accepting
 * `<tenant B>/claims/secret/buyer-invoice.pdf` on a row whose `tenant_id` was
 * tenant A, while the tenant-scoped foreign key beside it refused the same
 * crossing through `claim_id` with 23503. Part 5 carried the tenant along every
 * key precisely so that a row cannot reach another tenant's row; the column that
 * addresses the buyer's document was free text and reached anyway, because
 * `storage.objects` carries no tenant of its own and no policy to compensate.
 *
 * So the prefix is a fact of the schema rather than a convention of whoever
 * writes the row: every such column is constrained to begin with its own row's
 * `tenant_id` and a slash. That is also what makes the erasure worklist below
 * able to find a tenant's objects at all, so the two findings have one fix.
 */
export const TENANT_PREFIXED_PATH_COLUMNS = [
  'evidence.storage_path',
  'statements.storage_path',
] as const;

/** The worklist an erasure leaves behind, so the bytes outlive nothing. */
export const PENDING_OBJECT_ERASURES_TABLE = 'seen.pending_object_erasures';

/**
 * The json-typed columns `public.invoices` is allowed to carry.
 *
 * `recovery_share_lines` is not among them, and its absence is the point. F66
 * measured EUR 124,000 of recovery share accepted into that column against a
 * claim still at status `draft` with no credit link, and a second line citing a
 * claim id present in no table at all. CLAUDE.md's rule is that a credit is
 * billable only as an ingested settlement line linked to a claim and that neither
 * a person nor the agent may create a billable event directly, and a jsonb array
 * defaulting to `[]` is exactly a place where one can.
 *
 * The typed relation that replaces it is SEEN-040's, by that ticket's own text:
 * its description names an `invoice_claims` link table and its second acceptance
 * criterion already requires a unique constraint on `invoice_claims.claim_id`. So
 * this schema does not invent that table one sprint early and guess its shape; it
 * stops offering the shape that cannot carry the rule, and the obligation below is
 * what tells SEEN-040 that the free-text path is gone rather than optional.
 *
 * `module_lines` stays. A module subscription is a price for a period, no rule in
 * CLAUDE.md or the architecture makes it a metered event, and SEEN-045 owns it.
 */
export const INVOICE_JSON_COLUMNS = ['module_lines'] as const;

/**
 * An obligation this schema states on a relation of its own and a later ticket
 * has to keep, and the terms one acceptance criterion of that ticket has to
 * carry.
 *
 * The same shape and the same reasoning as `CONSTRAINED_NOT_BUYER_PII_COLUMNS`
 * one level up: that one is about a column's classification, this one is about
 * what a table means. F34 established the rule both are read by, which is that a
 * promise written only in a comment is a promise its promiser never hears, and
 * that the criteria are what a ticket's author is held to.
 */
export interface SchemaObligation {
  /** The relation whose own comment states it, schema-qualified. */
  readonly relation: string;
  /** The tickets whose code has to keep it true. */
  readonly tickets: readonly string[];
  /** Every term one acceptance criterion of each of those tickets has to carry. */
  readonly terms: readonly string[];
  /** The obligation itself, for whoever the assertion fails in front of. */
  readonly obligation: string;
}

export const SCHEMA_OBLIGATIONS: readonly SchemaObligation[] = [
  {
    relation: PENDING_OBJECT_ERASURES_TABLE,
    tickets: ['SEEN-083'],
    terms: ['seen.pending_object_erasures', 'storage object', 'bucket'],
    obligation: 'an erasure can record which stored objects a deleted tenant left behind, and '
      + 'nothing in a database can delete the bytes: only the storage provider can. So the '
      + 'worklist is the whole of what this schema can carry, and it is worth nothing until '
      + 'SEEN-083, which owns deletion on request, empties it by deleting each object from its '
      + 'bucket and removing the row',
  },
  {
    relation: 'public.invoices',
    tickets: ['SEEN-040'],
    terms: ['credited_by_settlement_line_id', 'recovery share', 'invoice_claims'],
    obligation: 'the recovery share lines are rows of the link table SEEN-040 builds, each '
      + 'naming a claim whose credited_by_settlement_line_id is set, and no column of '
      + 'public.invoices holds them as json any more: the untyped one was dropped rather than '
      + 'left beside the typed relation, because two representations of one relation means the '
      + 'unenforced one is the one somebody writes',
  },
  {
    relation: 'public.evidence',
    tickets: ['SEEN-022', 'SEEN-027'],
    terms: ['evidence bucket', 'tenant_id', 'prefix'],
    obligation: 'the check on storage_path binds the text a row may hold and cannot ask the '
      + 'storage provider anything, so an object uploaded to a name outside its tenant\'s prefix '
      + 'is accepted by the database as long as the row names a compliant path, and the erasure '
      + 'worklist, which sweeps storage.objects by that same prefix, never sees it. Measured as '
      + 'F63: the bytes stand in the bucket after the tenant is erased with nothing in any table '
      + 'able to say whose they were. Only the code that performs the upload can close it, so '
      + 'SEEN-022 and SEEN-027 upload under `<tenant_id>/` and nowhere else',
  },
  {
    relation: 'public.statements',
    tickets: ['SEEN-041'],
    terms: ['storage_path', 'tenant_id', 'prefix'],
    obligation: 'the same half-guarantee as on public.evidence, on the column that addresses a '
      + 'rendered statement: the check constrains what the row may name and not where the bytes '
      + 'were written, and a statement PDF uploaded outside its tenant\'s prefix survives that '
      + 'tenant\'s erasure unfound. SEEN-041 renders and stores the statement, so the upload it '
      + 'writes is the only place the object\'s own name is decided',
  },
];

/**
 * How a relation says its meaning depends on somebody keeping it, in the words
 * the buyer-PII classifications already use.
 *
 * One phrase, so that a reader who has met it on a column meets the same phrase on
 * a table and does not have to learn a second convention. The guard that reads it
 * on columns asks only about columns of schema `public` whose comment opens with
 * the non-PII classification, so the two never report each other.
 */
export const SCHEMA_OBLIGATION_MARKER = 'to keep it so';

/** One column a migration's own words describe, and where they describe it. */
export interface MigrationColumnReference {
  /** The migration the words are in, as the caller named it. */
  readonly relationFile: string;
  /** The line they start on, counting from 1, so a failure can be opened. */
  readonly line: number;
  /** The table they are about, unqualified, as the schema names it. */
  readonly relation: string;
  /** The column they describe. */
  readonly column: string;
  /** The words themselves, so the failure quotes the sentence and not a position. */
  readonly quoted: string;
}

/**
 * Every column a migration's comments describe, so a comment describing a column
 * the delivered schema does not have can be refused rather than read as current.
 *
 * Why this exists. The set is forward only: a part is added, never rewritten, so
 * the paragraph that argued for a column stays in the file that created it after a
 * later part drops the column. `public.invoices.recovery_share_lines` is the
 * measured case (F70). Part 3 creates it and argues, in the comment above the
 * column, that the junction table the ER diagram draws is declined because the
 * lines carry the claim ids and SEEN-040 may normalise it later; part 7 classifies
 * it as not buyer PII; part 10 drops it. SEEN-040's author opens the migration that
 * creates `public.invoices`, which is where a person looks for the shape of a
 * table, and is told that a reversed decision is a deliberate one. The convention
 * that every part points backwards and none points forwards is what makes this
 * unfixable in prose: part 3 may not mention part 10.
 *
 * So the guard is the fix, and what it compares against is the catalogue rather
 * than another comment. `schema.test.ts` asks the delivered database for the
 * columns of every table and refuses any reference here that names one it does not
 * hold. A sentence about a dropped column then fails the suite in the file it is
 * written in, with the line to open, and the only ways through are to delete the
 * sentence or to keep the column.
 *
 * Three shapes of reference, because the words that mislead a reader take three
 * forms in this set:
 *
 *   - a `comment on column <table>.<column> is` statement, which is prose the
 *     database itself stores and which survives in the migration text after the
 *     column it names has been dropped;
 *   - a `--` block directly above a column in a `create table`, which is the shape
 *     of the case above and the one no `table.column` scanner would see, because
 *     the comment names the column nowhere: the column definition under it does;
 *   - a `--` line anywhere that names a `table.column` pair outright.
 *
 * What it is not. It reads the comments and not the statements, so a migration may
 * still create a column a later part drops; what it refuses is describing one. A
 * path like `packages/core/db/marketplaces.ts` is not a reference, and is excluded
 * by the character in front of it rather than by a list of file extensions. A
 * relation this database does not have is not reported at all, which is the caller's
 * decision and not this function's: `pg_catalog.pg_attribute` and `storage.objects`
 * are written about all over this set and belong to nobody here.
 */
export function migrationColumnReferences(
  file: string, sql: string,
): MigrationColumnReference[] {
  const lines = sql.split('\n');
  const found: MigrationColumnReference[] = [];
  const add = (line: number, relation: string, column: string, quoted: string): void => {
    found.push({ relationFile: file, line, relation, column, quoted: quoted.trim() });
  };

  // A `table.column` or `schema.table.column` pair in a sentence. The character in
  // front of it decides whether it is a reference or part of a path or of a longer
  // dotted name, and a name followed by `(` is a call rather than a column.
  const pair = /(?<![\w./-])(?:(?:public|seen|storage)\.)?([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)(?![\w.(])/g;

  let table: string | null = null;
  let comment: { line: number; text: string[] } | null = null;

  lines.forEach((raw, index) => {
    const line = index + 1;
    const opening = /^create table (?:(?:public|seen)\.)?([a-z_][a-z0-9_]*)\s*\(/.exec(raw.trim());
    if (opening !== null) {
      table = opening[1] as string;
      comment = null;
      return;
    }
    const commented = /^\s*--\s?(.*)$/.exec(raw);
    if (commented !== null) {
      const text = commented[1] as string;
      for (const match of text.matchAll(pair)) {
        add(line, match[1] as string, match[2] as string, text);
      }
      if (table !== null) {
        comment = comment === null
          ? { line, text: [text] }
          : { line: comment.line, text: [...comment.text, text] };
      }
      return;
    }
    if (table !== null) {
      if (/^\s*\);/.test(raw)) {
        table = null;
        comment = null;
        return;
      }
      const column = /^\s{2}([a-z_][a-z0-9_]*)\s+[a-z]/.exec(raw);
      const keyword = /^\s{2}(unique|primary|foreign|constraint|check|exclude)\b/i.test(raw);
      if (column !== null && !keyword && comment !== null) {
        add(comment.line, table, column[1] as string, comment.text.join(' '));
      }
      comment = null;
      return;
    }
    comment = null;
  });

  // The comments the database stores, which outlive the column they are about in
  // the migration text even though the database drops them with it.
  //
  // Read with every comment blanked to spaces of its own length, so a statement
  // quoted inside a comment is not mistaken for one and the offsets, and so the
  // line numbers, are the file's own. Parts 4 and 6 both quote statements they are
  // undoing, which is why `statementsOf` in the suite does the same thing.
  const withoutComments = sql.replace(/--[^\n]*/g, (quotation) => ' '.repeat(quotation.length));
  const stated = /comment\s+on\s+column\s+(?:(?:public|seen)\.)?([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\s+is/gi;
  for (const match of withoutComments.matchAll(stated)) {
    const line = sql.slice(0, match.index ?? 0).split('\n').length;
    add(line, match[1] as string, match[2] as string, match[0]);
  }

  return found;
}
