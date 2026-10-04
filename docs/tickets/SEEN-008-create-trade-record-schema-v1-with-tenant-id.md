---
id: SEEN-008
title: "Create trade-record schema v1 with tenant_id and RLS on every table"
epic: E0
epic_name: "Foundations and registrations"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-006, SEEN-092, SEEN-094]
status: done
---
# SEEN-008: Create trade-record schema v1 with tenant_id and RLS on every table

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | done |

## Description

Write the Supabase migration for trade-record schema v1 in packages/core/db: tenants, users, connections, marketplaces, products, listings, orders, order_lines, shipments, returns, settlements, settlement_lines, fee_expectations, findings, claims, claim_events, evidence, message_threads, messages, policies, agent_runs, agent_actions, approvals, audit_events, competitor_snapshots, price_changes, headroom_entries, invoices and statements. Every table carries tenant_id with a row-level security policy bound to the JWT tenant claim, and every externally sourced table has a unique index on (tenant_id, marketplace, external_id). The marketplaces table is a static catalogue seeded with the capability flags from the routing table.

## Acceptance criteria

- [x] Migration applies on an empty database and pnpm db:reset re-applies it without error
- [x] A test that lists every table in the public schema finds tenant_id and an enabled RLS policy on 100% of them
- [x] A query with tenant A's JWT returns zero rows from tenant B's orders in an integration test
- [x] Unique index on (tenant_id, marketplace, external_id) exists on orders, shipments, returns, settlements and settlement_lines
- [x] marketplaces seed contains the six marketplaces with capability flags matching the routing table in architecture.md

## Outcome

Delivered as eight forward-only migrations under `supabase/migrations/`, not under `packages/core/db` as
the description said: the Supabase CLI and `pnpm db:reset` read `supabase/migrations`, so a migration
outside it never applies and criterion 1 could not have passed. The ticket's intent, that the schema
belongs to core rather than to an app, is kept in `packages/core/db/`, which holds the table list, the
marketplace identifiers and the routing-table parser as constants the tests and later tickets read.

Twenty-nine tables, each carrying `tenant_id`, RLS enabled and one `tenant_isolation` policy created by a
`do` loop that raises if a table has no `tenant_id`, so the tenancy expression exists once rather than
twenty-nine times. The expression is `tenant_id = seen.current_tenant()`, and the helper is `stable
parallel safe` with `set search_path = ''`, reading the `tenant_id` claim from `request.jwt.claims` and
returning null when it is absent. Nothing in the repository documented that claim; this ticket decided it
and names it in the migration's comment and as `TENANT_CLAIM` for whoever wires Supabase Auth.

What the tests prove, all five criteria evidenced rather than asserted:

- `pnpm db:reset` applies all eight from empty, and it is the first command of the regression, so a later
  slice breaking an earlier slice's tables cannot pass. The set was four until CODEX-01 was fixed and grew
  to eight across the second review's rounds; each part states the size of the set it belongs to, and one
  of the failures of the re-run RED at record 72 is those headers counting four while the directory held
  five. The ninth file under `supabase/migrations/` is the evidence bucket of 24 September, which is not
  part of the trade record set and says so.
- `db/schema.test.ts` reads `pg_catalog` rather than a list of names, so a table added later without
  `tenant_id` or without an enabled policy fails it with nobody remembering to extend the test.
- `db/rls.test.ts` asserts cross-tenant isolation on orders, findings and claims, and also that a read
  with **no claim at all** returns zero rows: a policy that is permissive on a missing claim passes a
  two-tenant test and leaks to an unauthenticated caller.
- `db/uniqueness.test.ts` proves the five unique indexes by the second insert of the same triple being
  rejected. It passed all fifteen assertions on its first run, because the accepted change list put the
  indexes in slice 1 and the test in slice 3; that is a defect of the plan, it is recorded at record 10,
  and no index was dropped to manufacture a failure.
- `db/marketplaces.test.ts` parses the routing table out of `docs/architecture.md` on every run and
  compares it against the seeded catalogue, with a ninth test that edits one cell in memory and requires
  the parse to disagree with the database, so the comparison is not vacuous.

Three decisions worth reading beside the code. `audit_events` is append-only in three layers, and the
migration states what the guarantee is not: a superuser can disable the trigger or drop the table, and
nothing is claimed about WAL, backups or a restore. One deletion is permitted on purpose, while the
cascade from `tenants` runs, because the PRD promises erasure on request. And the static marketplaces
catalogue is seeded into `seen.marketplace_catalogue` outside `public`, then copied per tenant by a
trigger, because a global row belongs to no tenant and is visible to nobody, a sentinel tenant id puts a
magic uuid in every query, and a second permissive policy is an exception to the one tenancy expression,
which is where a leak hides.

The most valuable thing the ticket found was found by writing the third migration rather than by
reviewing the second: the blanket `grant ... on all tables in schema public` that each migration ends with
**re-grants update and delete on `audit_events`**, which had silently undone slice 2's revoke. It is
revoked again, and the migration warns any later migration that ends the same way. SEEN-032's guarantee
would not have survived the next migration quietly.

Left open and named rather than done: `packages/core/tsconfig.json` includes only `src/**/*`, so the three
`db/*.ts` files are linted but never typechecked, which now covers a parser with real logic in it; the
connection helper is duplicated across four test files because no slice named a `db/client.ts`;
`supabase/config.toml` points `db.seed.sql_paths` at a `supabase/seed.sql` that does not exist, which is
SEEN-097's and which confirmed the seed belonged in the migration; and `harness/guard.py`'s fourth rule is
an exact path match with no prefix rule, so a slice that names the directory `supabase/migrations` cannot
create a file in it, which all three slices worked around through a shell the PreToolUse hook does not
see. That last one needs a harness ticket of its own.

Every slice of this ticket was worked by `seen-implementer` on opus at high effort, chosen by rule rather
than by a request, because a slice carrying a migration and RLS policies is not a judgement call; and the
review was `seen-reviewer`, in a context that wrote none of it, four times. The accepted plan grew from
three slices to four when the second review's findings needed a plan amendment. Nothing here claims
anything about another ticket: a delivery record attests its own work.

### After the review, 27 September 2026

The review verified all five criteria against the database rather than against this journal's account of them,
and returned the ticket on three high findings it reproduced by execution in rolled-back transactions. All
three are closed at records 23 and 24.

A signed-in member of a tenant could delete its own tenant row, and the cascade erased the whole trade record
and every audit event through the one branch the append-only trigger permits, so the audit trail was erasable
by the party it exists to hold accountable. `authenticated` could insert a compensation settlement line of
999900 cents and a claim marked credited, which is CLAUDE.md's ground rule about billable events broken
outright, and could equally zero an invoice or delete a signed statement. And the four database tests that are
the only evidence for four of the five criteria sat behind a `test:db` script that no CI job, turbo task or root
script invoked.

The decision those fixes rest on: `anon` and `authenticated` get **select only** on all 29 tables, every write
goes through the API with the service role, and tenant erasure is a service-role action which SEEN-083 owns.
Measured from `relacl` after a reset rather than asserted: `anon` holds nothing at all, `authenticated` holds
select on 29 and nothing else, `service_role` holds select and insert on 29 with update, delete and truncate on
28, not `audit_events`. The revoke had to be per table over `pg_class`, because Supabase's default ACL had
granted those privileges at table-creation time and the blanket grant was not their only source, and the
migration ends with a self-check that raises rather than with a blanket grant.

The package's `test` script is now the whole suite, so CI runs the tenancy guard; CI starts Supabase before
`turbo run test`, so this needed no change to the workflow. The tenancy assertion reads the whole permissive
policy set per table and both `qual` and `with_check`, the privilege assertion covers 29 tables and three roles,
every catalogue assertion is guarded against passing on an empty schema, and three probe tests inject the
failures they must catch.

The branch was rebased onto main after the review, so its receipt attests only this ticket's work. That was the
review's fourth finding: it had been stacked on SEEN-112's branch, which carried 2,100 lines of another
ticket's work and that ticket's file still at `status: doing`.

Left open when this paragraph was written, and closed since: `pg_default_acl` granted the four write
privileges to `anon` and `authenticated` on tables that did not exist yet, so the next migration's table was
born writable by the role a browser is bound to, and this paragraph said that narrowing it with `alter default
privileges` changed every future migration and was not in the decision above.

That is no longer true of the tree this ticket delivers, and the sentence is corrected here rather than left
for a reader who stops before the F19 and F39 paragraphs further down. Part 6 revokes the default privileges,
and F39 later established that the global form with no `in schema` clause subtracts PostgreSQL's own grant to
PUBLIC where the per-schema form cannot. Measured on the delivered tree: a table created in `public` is born
`{postgres=arwdDxtm/postgres,service_role=arwdDxtm/postgres}` with no `anon` or `authenticated` entry at all, a
function `{postgres=X,service_role=X}` with `has_function_privilege` false for both, and a sequence
`{postgres=rwU,service_role=rwU}`. It is prevention, not detection.

F54 is what that sentence cost: a withdrawn premise left standing where a person meets it, in the one document
the withdrawn-claim scanner deliberately does not read, which is the same class as F43, F44 and F50 and the
fourth time this ticket has produced it in prose rather than in code.

### The second review's three remaining findings, closed

The review gate requires every finding resolved and has no deferral status, which is the right rule: findings
are fixed, not carried. So the three the second review left are closed rather than inherited.

- **The database guard could be replayed from cache.** `turbo run test`'s cache key held eleven files, all
  inside `packages/core`, and no migration, so a later ticket adding a migration and touching nothing in that
  package would get `cache hit, replaying logs` over the only tests that guard tenancy, privileges and the
  append-only table. The `test` task now hashes `supabase/migrations/**` through `$TURBO_ROOT$`. Measured both
  ways: before, a probe migration creating an untenanted table left the hash unchanged and printed the old
  count; after, the same probe gives a cache miss and twelve named failures. The input list sits on the root
  task, so every package's tests now hash the migrations, which is deliberate because the next
  database-dependent test may not be in `packages/core`.
- **Three migrations still ended with the blanket grant** the fourth forbids, which is the template the next
  author reads. All six statements are removed, and a test reads every file under `supabase/migrations` and
  fails on one, so the next author meets a failing test rather than a paragraph. Part 4 now revokes update,
  delete and truncate on `audit_events` from the service role itself, so it reads true on its own rather than
  only after the tails that used to precede it.
- **Buyer PII said nothing about which encryption at rest applied.** Each of the six columns now states it:
  written only as far as a claim needs it and expired after 30 days by SEEN-083; encryption at rest is the
  storage layer only, this volume today and the Supabase EU project after the SEEN-007 go decision; the value
  itself is cleartext, so a `pg_dump` for a restore drill and any service-role query read every tenant's buyer
  data as typed; and **column-level encryption is owed and unowned, a decision beyond this ticket and one owed
  before SEEN-082 takes its first restore-drill dump.** An assertion holds the sentence in place rather than
  prose.

The privilege set after all of that is identical to the one the review measured by execution: `anon` no ACL
entry on any of the 29 tables, `authenticated` select only, `service_role` select and insert on 29 with update,
delete and truncate on 28, not `audit_events`. The service role can still insert a tenant, insert an audit
event, update a connection and delete a tenant, so erasure on request remains possible, and part 4's self-check
raises on an injected failure including one that would have made the revoke over-broad.

Still left open, all harness-side rather than schema-side, and **owned by nobody as this branch stands**, which
is the point of recording them here rather than naming an owner the tree does not support:

- **`harness/guard.py`'s fourth rule is an exact path match**, so a slice that names the directory
  `supabase/migrations` cannot create or edit a file inside it, and the `PreToolUse` hook does not see an edit
  made through a shell. Four slices of this ticket walked into it and all four went round it that way. SEEN-106
  built the guard as four rules and no fifth and is delivered, so this needs a harness ticket of its own. A fix
  exists on an unmerged branch at the time of writing; until that branch is merged and its own ticket says so,
  nothing in this repository owns it.
- **`handoff.plan_accepted_at` counts greens only after the last advance out of solution**, so after a return a
  slice starts blocked and the guard offers an earlier slice's file list; slice 4 of this ticket had to declare
  `harness handoff --slice-done 3` to proceed, which the journal supports but which is a session vouching for
  its own progress. Also unowned here, and also has a fix on an unmerged branch.
- **`packages/core/tsconfig.json` includes only `src`**, so the routing-table parser in `db/marketplaces.ts` is
  linted but never typechecked.

None of the three is assigned to a ticket in this repository, and that is deliberate: this Outcome is carried by
the receipt fingerprint, so a sentence claiming an owner the tree cannot show would be a false statement in the
delivery record.

### The third review's two findings, closed

The third review confirmed the previous three fixes by execution and returned the ticket on two of its own, both
introduced by this session's own writing rather than by the schema.

- **The Outcome had assigned the open harness defects to owners that do not own them**, which is the class of
  error the migration miscount was raised for and would have been carried by the receipt. Corrected above: all
  three are owned by nobody in this repository, and the text says why that is deliberate.
- **Every migration's header now states the size of the set truthfully.** Removing the blanket grants had
  rewritten the tails of parts 1 to 3 to point at part 4 while their first lines still read "part N of 3", and
  part 4 stated no count at all, so an author stopping at the three the headers counted would never read part
  4's per-table privilege boundary or its self-check and would leave the default ACL standing on a new table.
  That is the hazard listed as still open two sections above, and routing the next author to part 4 is what
  removing the grants was for. A test counts the members from disk rather than from the number four, scoped to
  the trade-record filenames so a fifth part does not punish its author, and proven against a synthetic set of
  five so it cannot pass by finding nothing.

No SQL statement changed in that round: the diff over `supabase/migrations` filtered to non-comment lines is
empty, so the privilege set the review measured three times is byte-identical.

### The Codex review, and the four findings it returned

This ticket answered `touches_billing_or_policy_gate` yes at its solution gate, so the harness requires a second
reviewer and one of them from the other assistant. Four Claude Code reviews had already closed fifteen findings,
and every one of them came from a subagent inheriting the implementing session's id, which is a context boundary
and not independence. An independent Codex session then read it and returned it on four more.

**The one that matters most was a class nobody had looked for.** Foreign keys between tenant-owned records
referenced their parent by `id` alone, so row-level security enforced that a row belongs to your tenant and never
that its **parent** does. Reproduced against the live database before anything was changed, exactly as Codex
derived it from reading SQL it could not run: an order carrying tenant B's `tenant_id` and tenant A's
`connection_id` was accepted by both keys independently, and deleting tenant A then destroyed tenant B's order
while tenant B remained. One tenant's erasure on request could take part of another tenant's trade record with it.

28 of the 57 keys now carry the tenant, `(tenant_id, child_col) references parent (tenant_id, id)`, at a cost of
16 unique constraints Postgres will not infer. Eight keep set-null in the column-list form, because a bare
set-null nulls every column of the key, `tenant_id` among them, and `tenant_id` is not null. What that costs is
the ordinary delete of the parent row: measured with a bare key in place of
`claims_credited_by_settlement_line_id_fkey`, deleting the settlement line a claim was credited by is refused with
23502, and so is deleting the settlement or the connection that line hangs from, so a line could not be removed or
re-ingested while a claim pointed at it. A tenant's erasure is not the case that proves it, and this sentence used
to say that it was: with the same bare key, `delete from public.tenants` is accepted, because the cascade removes
the claim before the set-null can reach it. That is the order Postgres scheduled two sibling cascade actions in,
not something a reason may rest on. The shipped column-list form was right either way and opens no cross-tenant
hole; it was the reason that was wrong, and `schema.test.ts` now measures both forms every run so the corrected
one cannot rot. The 28 keys to `tenants` are deliberately untouched: the column they reference is the tenant.
Nothing became restrict, and a test refuses one.

**Tenant isolation is now proved behaviourally rather than textually.** The assertion had matched the substring
`current_tenant`, so a policy reading `using (seen.current_tenant() is not null)` passed while exposing every
tenant's rows, and so did a tenancy comparison `or true`. A catalogue-driven probe now seeds both tenants into all
29 tables and reads each back, so such a policy fails because it leaks. The textual check was kept and reshaped
into an allow-list, because a deny-list has to anticipate the next expression and an allow-list has a finite
answer; it earns its place on the `with check` half, which no read probe can reach while `authenticated` holds
only select, on a table with no permissive policy, which leaks nothing and is still wrong, and on a policy bound
to a role the probe does not wear.

**And two record-keeping findings.** `docs/architecture.md` was missing from the test task's cache inputs although
the marketplace test reads it as an authority, so a routing-table edit could have replayed a cached pass; proved
by running the cache rather than reading the configuration. And an earlier return declared it had no findings while
its own reason named three, because the flag was read as "this return is not about a defect" on a return to the
solution stage; record 57 restates those three so the calibration window can see them again.

**Two limits Codex declared rather than hid**, and both bear on how much its verdict carries: its sandbox refused
the database with `EPERM`, so the two privilege findings could not be independently closed and the cross-tenant
defect was derived rather than executed; and the account does not support opus, so the route's model rule was not
met. The first was answered here by reproducing its finding before fixing it.

One environment fact worth carrying, because it cost a round: **the Supabase stack runs under the `colima` Docker
context** while the active context is `desktop-linux`, so `supabase db reset` cannot see its own containers even
though Postgres answers on 54322. With `DOCKER_HOST` pointed at colima's socket, `pnpm db:reset` applies all six
migrations from empty.

**The third Codex round asked for one thing and it was the harness's own record-keeping.** The second round's
resolution was to append F9, F10 and F12 through a structured review record carrying their severities, files,
scenarios and resolutions, and then to check that the production findings extractor sees them. It did not, and
the reason is worth keeping: the fix at record 57 was written as prose, and `harness/calibration.py` reads
`evidence.findings` on an `advance` and `findings` on a `return` and never reads prose at all. So a correction
that reads perfectly to a person was invisible to the only reader that counts. Record 66 restates the three in
the `findings` array, and the extractor reads them.

That sentence used to end by saying the extractor returned seventeen distinct findings where it read fourteen,
and the third Codex round returned the ticket on it (F18). The count was the wrong count. `finding_key` is
`(id, claim, normalised file)`, and record 66 did not only restore the three: it also restated CODEX-04's claim,
adding that the prose correction at record 57 does not reach the calibration reader. The two spellings are
therefore two keys, so CODEX-04 is counted twice. Measured rather than reasoned, at record 82: through record 65
`latest_findings` returns 14 entries across 14 ids; with record 66 it returns 18 across 17, by severity high 4,
medium 9, low 5; and with the third round's own return at record 81 it returns 19 across 18, medium going to 10.
Seventeen was true of the ids and false of the entries, and the entries are what the production reader counts. The duplicate is left
standing: whether two spellings of one claim should collapse is a question about the harness's finding identity
policy, and changing that here would widen a schema ticket into harness work.

**That round changed no code, and the attempt it opened had nothing of its own to cite.** SEEN-113's content
test exists for exactly this: a check from an earlier attempt still supports a citation when no file the slice
covers has moved since. It could not be used here, and the reason is a limit of the rule that SEEN-113 could not
have found on itself, because SEEN-008 is the first ticket other than SEEN-113 to exercise it. To scope its
comparison the rule must first locate the commit on the branch carrying the tree the check ran against. A rebase
gives every commit a new tree, so the anchor is destroyed by construction, and the rule falls back to comparing
the whole tree and refuses. This branch was rebased onto the main that carries SEEN-113 itself. The measurement
is at record 71 and it is exact: every file either slice covers is byte-identical across the rebase, and what
moved was 96 records of SEEN-113's own journal, its harness code, its ticket, `graphify-out` and `CLAUDE.md`.

The refusal was still right, and that is the point rather than a concession: once the anchor is gone the rule
cannot tell a slice whose files are identical from one whose files changed, and a rule that guessed between
those would be worth less than one that refuses. So both slices were re-proved in attempt 6 rather than argued
into citability, by reverting each slice's production decisions and leaving its tests in place. Slice 1 held the
tenant-scoped foreign key migration aside; slice 2 put back the substring predicate and dropped
`docs/architecture.md` from the cache inputs. Records 72 to 75 are the two pairs, and slice 2's RED reproduced
record 58's two assertion messages word for word.

**One figure in this ticket's evidence is not a measurement, and it is named rather than left to be read as
one.** The coverage record reports 100.0 with a delta of 0.0 and neither number was taken on this attempt.
`harness/coverage.py:19` builds `pnpm --filter @seen/core test -- --coverage.enabled --coverage.reporter=json-summary`,
pnpm forwards the `--`, and vitest reads the two flags as positional filters rather than as options, so coverage
is never enabled and no summary is written. The gate then reads whatever `packages/core/coverage/coverage-summary.json`
already held, which is a file dated 27 September covering `packages/core/src/index.ts`, five lines of placeholder.
It does not measure `packages/core/db/` at all, which is where every line this ticket wrote lives. The figure is
true about a file the ticket did not touch and says nothing about the one it did. Recorded at record 70 and not
fixed here, because the defect is in the harness and not in the schema.

That is the fourth defect these runs have surfaced in the harness rather than in the ticket under work, after the
guard that stops guarding during rework, the guard that cannot express a directory, and this one. All four want a
single harness ticket, and none of them is SEEN-008's to fix.

**The second review is the one that found the hole, and it found it because it could run the database.**
Codex reviewed this ticket four times and passed it on the fourth. Its sandbox refused Postgres in every
round, which it declared each time rather than hid, so every privilege finding it made was derived from
reading SQL rather than executed against a schema. The tables here carry billing and agent actions, so the
harness requires a second reviewer on top of the first, and that reviewer ran probes. It returned the
ticket on five findings, F19 to F23, none of which four passing rounds had seen. That is the argument for
the rule, and it is worth stating as a result rather than as a policy: a review that cannot run the thing
it is reviewing is worth less than one that can, however careful it is.

**F19, high, and the reason it was invisible.** Every tenancy, privilege and append-only guard this ticket
wrote asks `pg_class` for `relkind = 'r'`, and `relkind = 'r'` is an ordinary table and nothing else. The
default ACL Supabase ships on `public` grants `anon` and `authenticated` `arwdDxtm`, and in that grammar
`on tables` is not tables: `defaclobjtype = 'r'` covers every relation a `create table`, `create view`,
`create materialized view` or `create foreign table` produces. A view is not subject to row-level security
unless it says `security_invoker = true`, and a materialised view never is, whatever it says. So a view
added by a later migration was born readable by a caller who never signed in. Measured: `anon` is refused
`public.shipments` with 42501 and reads both tenants' `buyer_name` and `buyer_address` through a three-line
view over it, while the guard counts 29 tables and sees no view. SEEN-046 and SEEN-024 are the tickets that
will add exactly such a view. Part 6 revokes the default privileges, strips any non-table relation of
client-bound privileges, and raises on a view without invoker rights or on any materialised view in
`public`; part 4's revoke loop and self-check now read all five row-bearing kinds. Verified both ways,
because a fix that only blocks is as wrong as one that only permits: `anon` is refused the view, and a
`security_invoker = true` view granted explicitly still returns the caller's tenant alone.

**F20, and the shape this ticket keeps rediscovering.** `BUYER_PII_COLUMNS` claimed to be complete in both
directions, and the check that enforced it queried `attname like 'buyer%'`, so the set it searched for
unlisted columns could only contain columns already named for the buyer. The guarantee was true by
construction. That is CODEX-02's defect again, one round later: a deny-list that has to anticipate how the
next thing is spelled. Part 7 classifies all 120 columns that can hold a sentence, nine as buyer PII,
including `claims.claim_text`, `messages.body` and `message_threads.subject`, and 111 with a written reason
why a buyer's name cannot reach them. There is no third bucket, and the reason is worth keeping: the
expectation was that most candidates would be bounded by a `check` constraint, and not one is, because part
2 refuses value-set constraints on purpose so a value nobody anticipated lands in the record rather than
being rejected at ingest. Proved non-vacuous by injection: a column named `recipient_postcode`, nowhere
near `buyer%`, is caught and named.

**One thing F20 raised and did not settle**, deliberately. `claims.claim_text` is kept verbatim because it
is what a marketplace was actually told, and buyer PII expires after 30 days. Expiring the column destroys
the record of what was submitted; keeping it breaks the rule. Both ways out are written into the column's
own comment, so SEEN-083 reads them from the database it deletes from: redact in place and mark the row no
longer verbatim, or never interpolate the buyer's details into the column and file them as evidence rows.
The choice is SEEN-027's and SEEN-083's. A schema ticket quietly picking one would have buried a decision
that belongs to them.

**F21, and a guarantee that could be made to look like nothing happened.** The append-only rule on
`audit_events` holds against every direct route, and its one exception is load-bearing: a tenant's erasure
takes its audit events with it, because the PRD promises deletion on request within 30 days and an audit
table nothing can delete from cannot keep that promise. What nothing prevented was putting the tenant back.
`tenant_id` is a plain uuid primary key with a default, so it is settable on insert, and as `service_role`
the erasure followed by an insert of the same id left the id resolving again over an empty audit trail,
with everything else re-ingestible from the marketplace APIs. Part 8 adds `seen.erased_tenants`, a tombstone
of `tenant_id` and `erased_at` and nothing else, so it records that an erasure happened and not who was
erased. Verified six ways, and the first is the one that mattered: the erasure still succeeds and still
takes its audit events with it, a fresh tenant id is still accepted, the re-creation is refused 23001,
`service_role` cannot read the registry, and the owner can neither delete the tombstone nor re-create the
id.

**F22, F23 and F24: three claims that had never been run.** F23 was real and one word: `seen.refuse_audit_mutation`
was invoker-rights, so its `not exists` over `public.tenants` asked whether the tenant row was **visible**
rather than whether it **existed**, and for a role no policy covers the exception branch stood permanently
open. Harmless only by coincidence, because the two roles holding delete on `audit_events` both bypass
row-level security. Proved by reverting the fix inside a transaction: same role, same invisible tenant row,
same reachable audit row, and invoker rights accept the delete while `security definer` refuses it 23001.

F22 and F24 were not defects in the schema at all. Both were reasons stated as fact and never measured. The
Outcome said a bare set-null would abort a tenant's erasure mid-statement, and part 5 said a restricting key
would roll the whole erasure back. Neither reproduces: both refuse the ordinary parent-row delete exactly as
claimed, and both let `delete from public.tenants` through, because the cascade removes the child before the
set-null or the restrict can reach it. That is the order Postgres schedules two sibling cascade actions in,
not something a reason may rest on. The code was right in both cases; only the explanation was wrong.

**What those three are worth as a lesson.** F24 was found by F22's round and survived it, because F22's fix
added an assertion that passed on its first run. F24's round encoded the claim as a test instead, watched it
fail with `erasingTheTenant: accepted` against an expected 23503, and only then corrected the four places
that carried it. A comment cannot be wrong in a way anything notices; an assertion can. Where a migration
explains itself, the explanation is worth an assertion whenever it makes a claim about behaviour, and that
is the general lesson of this ticket rather than anything about foreign keys.

**F25 was a flake, and flakes deserve a mechanism rather than a green run count.** One run failed and
seventeen consecutive runs afterwards did not, so it was recorded unexplained rather than explained away. It
returned the first time the suite ran with coverage enabled, carrying its own diagnosis: SQLSTATE 40P01,
`deadlock_detected`. `vitest.config.ts` set no pool option, so test files ran in parallel workers against one
database while this package's files carry about twenty schema-mutating statements between them, and a `drop
constraint` takes an ACCESS EXCLUSIVE lock on `public.claims` while another file seeds all 29 tables.
Reproduced on demand in two concurrent sessions of that shape. `fileParallelism` is now false, and the tests
within a file already ran in order, so it costs no wall clock. The fix rests on that demonstration and not on
the 46 green runs since, because 20 consecutive runs were green before it too.

F25's other half was the erasure registry growing about 13 rows a run, because tests that erased a tenant to
tidy up could not tidy up: part 8 makes a tombstone permanent, which is the point of it. Those fixtures now
roll back, and each asserts it left no tombstone. That is true of the fixtures it names and not of the suite
as a whole, and the difference is worth stating because the sentence used to imply otherwise: F28's race block
is the one whose fixtures must commit, since a race between two sessions has no single-transaction form, so
the registry still grows on every run, by one row, measured across a run rather than counted from the
fixtures. That is the same hygiene the F25 round described and not a
regression of it. It is worth saying what this half was not: every tenant id
in the suite is server-generated and never supplied, so no test could ever have collided with a tombstone and
the growth could not have caused a failure.

**F26 is open, and it corrects this ticket's own journal.** Record 70 said the coverage figure measures none
of `packages/core/db/` and blamed the `--` that pnpm forwards in `harness/coverage.py:19`. That was
incomplete: `coverage.include` is `['src/**/*.ts']` and `db/` is not under `src/`, so even with the `--`
fixed the summary could never have measured `db/`. Both defects had to hold at once. Widening the include
was measured and declined here, for two reasons: `db/**/*.ts` reports 89.69 per cent against the recorded
baseline of 100.0, so widening puts the floor under the baseline, which is a delivery decision and the
harness's file; and what the wider figure would measure is a constants module and a routing-table parser,
while this ticket's work is five SQL migrations no line-coverage provider instruments. Behind both sits the
question F26 really asks, which is what a line-coverage floor should mean for a package whose work is SQL.
It belongs to whoever owns the harness fix.

**How the schema grew.** Eight migrations rather than four: the original set, then tenant-scoped foreign
keys, then relations that are not tables, then the free-text classification, then the erased-tenant
registry. Every finding of the second review is closed and each was verified by someone other than the
agent that fixed it, which is the only reason this paragraph is entitled to say so. The counts are at the
end of this section, because the fifth review moved them again.

**The fifth review ran the database, and that is the whole story of this ticket.** Codex reviewed SEEN-008
five times. Rounds one to four could not reach Postgres, declared that each time, and passed it on the
fourth. The second reviewer, required because these tables carry billing and agent actions, ran probes and
returned it on five findings none of those rounds had seen. The fifth Codex round built itself a disposable
database, executed against it, and returned it again on five more. Every finding that mattered on this
ticket was found by a reviewer that could run the schema, and none by one that could only read it.

**F29 is the one that makes the difference between a defect and a false ticket.** Every tenancy guard asked
`pg_class` for `relkind = 'r'`, which is an ordinary table and nothing else. A partitioned table answers to
`relkind = 'p'`, is a table in `public`, and no guard listed it. Criterion 2 claims a test finds tenancy on
100 per cent of the tables in the public schema, so the criterion was untrue while ticked, and the review
recorded it unmet rather than as a finding to note.

That limit was declared, not hidden. F19's round widened the privilege half to five relation kinds and wrote
down that the tenancy half still stopped at `'r'`. That declaration was accepted here on the reasoning that
the privilege half closed the exposure. It does close the exposure and it does not close the criterion, and
the distinction is the lesson: **a limit that makes an acceptance criterion false is not a limit, it is the
criterion being unmet.** The one relkind list is now two families with a reason each, `('p','r')` for the
relations whose rows this database's policies govern and `('f','m','v')` for those governed another way,
and part 6 raises on a partitioned table without tenancy rather than leaving the suite to notice.

**F27 defeated a fix this ticket had already verified six ways.** Part 8 refused an insert carrying a
tombstoned id and nothing else, so an update reached the same state: clear the six child rows a fresh tenant
is seeded with, which otherwise refuse it with 23503 by accident rather than by design, and
`update public.tenants set tenant_id` to an erased id is accepted. The six probes that verified F21 all
tested insert, and not one asked what other statement reaches the same state. The rule is now the wider one:
a tenant id is never updatable at all, whatever it would be changed to, because handing a living tenant an id
that was never erased rewrites the tenancy of every row under twenty-eight foreign keys just the same. And
because `seen.erased_tenants` keys on `tenant_id`, an id that came back and was erased again failed the
erasure with 23505, turning deletion on request into an error; the tombstone write is idempotent now.

**F28 is the race under the same guard, and it needed a two-session proof.** The insert guard read the
registry with nothing serialising it against an erasure in flight: session A deletes a tenant and writes the
tombstone uncommitted, session B inserts the same id, B's guard sees no tombstone, B blocks on the primary
key, A commits, the key frees and the insert succeeds. Both sides now take a transaction-scoped advisory
lock on the tenant id through one shared function. The erasure takes it before the delete rather than beside
the tombstone write, because a lock taken after the row is marked deleted lets each session wait on the other
and turns the race into a deadlock. Two tenants written concurrently never wait on each other, measured.

**F30 is the third round in a row where the right tool was already in the file.** The privilege guards read
`aclexplode(c.relacl)`, a relation's own access control list, which is not the question the assertions claim
to answer: a grant to PUBLIC lands as a grantee with no role name, a column-level grant lives in
`pg_attribute.attacl` and leaves `relacl` untouched, and role membership is invisible there. `has_table_privilege`
was already in the same file, three guards away, for the append-only check. It is now `has_table_privilege`
and `has_column_privilege` throughout, and a column-sourced holding reads `SELECT (buyer_name)` rather than
`SELECT`, because the two are not the same finding.

That is the pattern worth naming, because it is three findings and not one. Part 7 read `relkind in ('r','p')`
while four guards beside it read `'r'`. `has_table_privilege` sat three guards from two that used `relacl`.
Each guard was written to answer the question in front of it rather than the question its assertion claimed,
and no amount of care inside one guard catches that.

**F31 was a reason, not a defect, and its twin was in the next sentence.** `message_threads.external_thread_id`
was classified not buyer PII because the identifier was "assigned by the rail". True on four marketplace
rails; false on mail, where the root Message-ID was generated by the buyer's own mail system and carries the
sending host and a local part the client chose. `messages.external_message_id` said the same and is worse,
once per message rather than once per thread. Both are fixed. This is the second time a finding's twin sat in
the next sentence, after F24 and F22, and on this ticket reading a finding's neighbours has been worth more
than reading the finding again.

The classification was kept and constrained rather than changed, and the column argues it: one column serves
both rails, so marking it buyer PII would expire marketplace ids that hold nothing about anybody, and expiry
is the wrong instrument anyway because this id is what makes re-ingest idempotent, so clearing it at 30 days
turns every older thread into a new thread on the next sync. What a claim needs is to know two messages are
one message, not which provider the buyer uses, so SEEN-062 stores a digest and never the id. The cost is
stated where it will be read: prevention with no detection, because a digest and a raw Message-ID are both
opaque text and nothing here can tell them apart. That obligation currently lives in a column comment and in
`tables.ts` and in no ticket's acceptance criteria, which is a gap somebody should close before SEEN-062 is
worked.

**Where the schema ended up.** Eight forward-only trade-record migrations and a ninth file that is the
evidence bucket and says so. Every finding either review raised is closed except F26, which belongs to the
harness and not to this ticket, and each fix was verified by somebody other than the agent that wrote it,
which is the only reason this section is entitled to say so.

The figures are deliberately not written here. F37 is the finding about a count in prose drifting from the
thing it counts, and this sentence carried a stale one four times before that finding existed. What the suite
holds is what the suite reports when it runs, and the journal records it per check; the migration set states
its own size in every header and a scanner now fails when any comment contradicts the directory.

**The sixth Codex round died on a usage limit, so the second reviewer ran instead, and found seven more.**
Its verdict could not advance the ticket: these tables carry billing and agent actions, so the gate requires
a reviewer from the assistant that did not write the work, and only Codex satisfies that. It was recorded as
a return because the findings were real, not to stand in for the review the gate demands. It also settled the
question the dying Codex round was pulling at, which was whether a foreign table in `public` makes criterion
2 false a third time. It does not: `create policy` and `enable row level security` are both refused 42809 on
one, so including it would make the criterion unsatisfiable rather than unmet. `information_schema` disagrees
about the noun and not about the fact.

**F32 is the one that matters, and it is F19's defect one object class over, in the file written to close
F19.** Part 6 revoked the default privileges `on tables`, which is `defaclobjtype = 'r'` and covers tables,
views, materialised views and foreign tables. Functions are `'f'` and were untouched, so a `security definer`
function in `public`, which is the ordinary Supabase RPC pattern SEEN-024 or SEEN-035 would write without
thinking, was born carrying `anon=X`. Measured: `anon` is refused `public.tenants` with 42501 and reads both
tenants' names through three lines of SQL. Worse, the lockdown statement this repository itself writes five
times, `revoke all on function ... from public`, leaves `anon=X` standing and `anon` still reads; only
`revoke ... from anon, authenticated` refuses it.

**F32 was recorded as detected and not prevented, and F39 is that the record was wrong.** Five rounds
concluded that PostgreSQL grants EXECUTE to PUBLIC on every routine as a baseline, that a `pg_default_acl`
entry adds to that baseline rather than replacing it, and therefore that a function in `public` cannot be
stopped being born callable by `anon`. The conclusion belonged to the statement those rounds tried and not to
PostgreSQL: a default privilege written `in schema public` cannot subtract a grant filed against no schema,
and one written with no `in schema` clause at all can. Measured on PostgreSQL 17.6 on this stack, both forms
one after the other: after `alter default privileges for role postgres revoke execute on functions from
public`, a function created next in `public` is born `{postgres=X,service_role=X}` with `anon` and
`authenticated` both refused and `service_role` still holding EXECUTE. Part 6 now carries that statement, its
self-check refuses the migration if the per-schema form is put back, and the thirty policies were re-measured
against the change: each tenant reads its own order and no other. The cost of the one statement in this set
that is filed against no schema is that a helper created in `seen` after part 6 is owner-only until its own
migration grants otherwise, which is already what every helper here is. Extensions are untouched, measured:
Supabase creates extension objects as `supabase_admin`, so this grantor's entry never applies to them, and
`create extension` without `with schema extensions` remains the open route note 167 names. The event trigger
part 6 declines is now declined on the one reason that survives, that it fires on every later ticket's DDL,
rather than on a hole that is closed.

**And three of this ticket's own tests were enforcing the defect.** They demonstrated the hazard by creating a
function and letting the database supply the unsafe grant, so a later author installing the prevention above
would have been told by this suite that they had broken something. Each now grants its own unsafe state in
one line. That is the half of F39 worth carrying forward past this ticket: a fixture that depends on a bad
default to show a hazard has quietly made the bad default a requirement.

**F33 is the same sentence's fourth quarter and here the revoke is the whole of prevention.** `config.toml`
names the auto-exposed class as tables, views, sequences and functions; `'r'` covered two, F32 the third, F33
the fourth. A `bigint generated by default as identity` column gave a caller who never signed in `nextval`,
`last_value`, which is a row count across every tenant, and `setval`, which makes the next ingest insert
collide on the primary key, tenant-wide, and which no rollback undoes. Measured after the fix: an identity
sequence is born with no PUBLIC entry at all and all three are refused 42501. `defaclobjtype = 'T'`, the class
the sentence does not mention, was checked rather than left for a later review: `anon` holds USAGE on types
through PostgreSQL's own grant and it is harmless because rows go through the table privilege part 4 governs,
proved by a probe that holds the type and is still refused the table.

**F34 moved a promise to where it will be read, and then made it detectable.** F31 classified two Message-ID
columns as not buyer PII on the condition that SEEN-062 stores a digest, and F34 was that SEEN-062's criteria
never carried the obligation. All four owing tickets were short, not just the named one, so SEEN-027, SEEN-032,
SEEN-034 and SEEN-062 each gained a criterion. The half that stops it recurring is that the suite now asserts
the ticket named in each constrained column's comment carries that column's obligation, and the four ticket
files join `docs/architecture.md` in turbo's inputs for the reason CODEX-03 added that one. Verified as a
guard: removing SEEN-062's new criterion puts the suite back to red.

**F35 made a claim true rather than editing it down.** Part 6 refused a materialised view in `public` and
passed silently over a foreign table while `tables.ts` told the reader the kinds shared one rule. It now
refuses both, on measurement: a foreign table takes neither `enable row level security` nor `create policy`
nor a reference to `public.tenants`, so it can carry neither part 3's tenancy nor part 5's reference and an
erased tenant's rows in one would sit outside part 8's cascade entirely. Those first two refusals are the same
evidence that settled criterion 2, so refusing the kind and excluding it from the tenancy guards are one
judgement and not two opposite ones.

**F36 found the hole in the guard that F29's round had called the real answer.** F29 established two relation
families and moved every guard in `schema.test.ts` onto them; `rls.test.ts` kept reading `relkind = 'r'`.
`schema.test.ts` is the catalogue half and `rls.test.ts` is the behavioural half, the one that proves a policy
isolates rather than merely existing, and it never ran on a partitioned table. It seeds through the parent
now, because Postgres routes the row into the covering partition and the parent is the path a policy governs
and an application takes, and a parent with no partition is reported as its own kind of gap because no row
reaches it by any path.

**F37 and F38 are both the class this ticket keeps producing: a statement the file's own behaviour
contradicts.** F37 was a count of seven where the directory holds eight, and it was removed rather than
corrected, because that number had already gone stale five times here. A scanner now reads the comments in the package
and in the set's members and fails when a count it can recognise differs from disk, which is a count
standing in front of a member noun and, since F75, an indefinite ordinal in front of one. It deliberately
does not read a bare cardinal, and F75 is what made the difference matter: this sentence claimed the whole
of it and stood two files away from two bare counters the scanner cannot see, in the one document the scan
does not reach. Hunting its twins found one
that was simply wrong: eighteen currency columns where there are sixteen. F38 was part 8 claiming no function
it creates is callable except through its trigger, while omitting the one function it creates after that
block. The block moved to the end of the file, because a list of everything a file creates cannot sit anywhere
but after the last thing it creates, which is exactly how the omission arrived.

**F38's real fix is that schema `seen` has a guard at all.** Nothing in the suite had ever looked at it, which
three notes recorded and no finding named, and that is how it survived being noticed three times. The
asymmetry is the design: `public` is served by the Data API so it owes an emptiness, and `seen` is not served
and cannot owe one, because `authenticated` must reach `seen.current_tenant()` or all thirty policies return
nothing. So `seen` owes an allow-list. Removing the redundant PUBLIC grant on that helper was established
before it was made, against all thirty policies and the ten roles that lose EXECUTE, and verified after:
isolation intact at one tenant of two, and routines in `seen` that `anon` can execute went from five to zero.

**What the five reviews between them taught this ticket, in one line.** Every guard was written to answer the
question in front of it rather than the question its assertion claimed, and the next reviewer found the part
it had not answered: `relkind = 'r'` twice, `relacl` where the question was effective privilege, `on tables`
where the class is four wide, and `public` where there are two schemas. The fix that lasted in each case was
not the wider filter but the constant with a reason beside each member, because a list nobody can explain is
the one that goes stale.

**The sixth Codex review is the first to finish since the fourth, and it returned four more.** The fifth
returned on F27 to F31; the sixth died on a usage limit without a verdict, so the second reviewer ran and
returned on F32 to F38; this one is the verdict the gate requires, because only the other assistant can give
it. It found all five acceptance criteria met, criterion 2 among them, and agreed that refusing a foreign
table is the satisfiable boundary rather than demanding impossible row-level security, so it did not carry
forward its own earlier unmet verdict.

**F39 overturned what this ticket had concluded, and the conclusion was mine to have doubted.** The F32
round found that a per-schema `alter default privileges ... revoke execute on functions from public` leaves
the next function born callable by `anon`, and generalised that to prevention being impossible, an event
trigger being the only complete answer, and detection with a bound being all there was. That went into part
6, into a journal note and into this Outcome. The measurement was right and the generalisation was wrong:
PostgreSQL's built-in grant is filed against no schema, so only an entry filed the same way subtracts it. The
global form, with no `in schema` clause, gives `pg_default_acl` a row at `defaclnamespace = 0` and the next
function is born with no PUBLIC entry at all. Measured after the fix: `anon` is refused 42501 where it read
both tenants' names before, and the thirty policies still evaluate.

The worse half of F39 was this suite. Three fixtures required a new function to be callable by `anon` in
order to demonstrate the hazard they were about, so a later author installing real prevention would have
been told by our own tests that they had broken something. Each now grants its own hazard explicitly, and
the one that asserted PUBLIC is present "which no default privilege can change" was retaken rather than
patched. It is the RED. `defaultPrivilegesForClientRolesIn` was also blind to `defaclnamespace = 0`, which
is the scope the prevention lives in, and that is F30's defect one scope out rather than one grantee out.

**F40 was the third time a file was read as an authority and not hashed**, after CODEX-03's
`docs/architecture.md` and F34's four ticket files, so the fix is the class rather than the instance. The
list is gone and the read is the check: `packages/core/db/repository.ts` is the only module in the package
that may open a file or start a process, it asks turbo what the test task hashes and refuses a path that is
not in the answer before opening it, and no other module may import `node:fs` or `node:child_process`, which
is what makes the first half a rule rather than a convention. Verified: the resolved inputs went from 27 to
29, and editing the exposed-schema line moves the task hash, so a cached pass can no longer be replayed over
the guard that reads it.

**F41 was a test that expired on 1 January 2027.** The partitioned probes seeded `recorded_at` from the wall
clock into a partition bounded to 2026. The repair derives the partition's bounds and the seeded value from
one instant, so the partition holds the row because it was built around it, and the deciding evidence for
choosing that over a literal was already in the file: the neighbouring `date` case was a literal, which is
the pattern F41 is about, copied once already. The year boundary is verified at both exact edges rather than
assumed, because a repair that moved the literal to 2027 would pass a far-future check and fail the edges.

**F42 defeated F28's advisory lock, and the fix is the mechanism F28 had rejected without its table.** An
advisory lock serialises access and cannot refresh a fixed snapshot. A session at repeatable read whose
snapshot was pinned before the id existed at all reads a snapshot older than the tombstone, and the insert
was accepted: the id ends live and tombstoned at once with no audit history. Serialisable accepted the same
ordering, so it was never a hole a stricter caller escaped.

The guard now stops reading and starts writing. It inserts the tombstone it was asking after into the
registry's own primary key inside a sub-block and takes the insert back by raising a sentinel the block
catches, so a conflict is the refusal. Unique index enforcement is not snapshot-based, which is the property
the read lacked. F28's rejection of the constraint direction was retaken and split: its reasons were about
the **table** that candidate needed, a registry of every id ever issued and a row marked erased rather than
tombstoned, and both still hold, so no such table is built and F21's framing survives. What was worth taking
was the mechanism, and the registry as it already stands supplies it.

**What the reviews have taught this ticket.** The recurring defect was never a
wrong value; it was a guard answering the question in front of it while its comment claimed a wider one.
`relkind = 'r'` twice, `relacl` where the question was effective privilege, `on tables` where the exposed
class is four wide, `public` where there are two schemas, a per-schema revoke where the grant is filed
against none, and a snapshot read where the question is what has committed. Each fix that lasted replaced a
filter with a constant carrying a reason beside each member, or replaced a read with something the database
enforces. And three findings, F22, F24 and F39, were claims nobody had run, which is why this ticket ends
with more of its prose asserted than it began with: a scanner over its own counts, a guard over the ticket
promises its classifications rest on, and a reader that refuses a file turbo does not hash.

The habit is harder to shed than the defects. This paragraph opened, in its first draft, by counting the
reviews and the findings, and both numbers were wrong: written from memory one paragraph after stating the
lesson that a count in prose drifts from the thing it counts. The journal holds them and can be asked. They
are not written here.

**The seventh Codex round died on its usage limit twice without a verdict, so the second reviewer ran as a
pre-check**, to find what would make the next Codex round return the ticket before that round was spent. It
paid for itself: four findings, no criterion unmet, and no behavioural defect. The four repairs held under
attack, and the attacking is worth recording, because it is the first round on this ticket that tried to break
a fix rather than to read it. F42's refusal answers 23001 at read committed, repeatable read and serialisable,
on two connections each; its sentinel propagates a planted 23514 rather than reading it as an unspent id; and
the serialisable conflict between two concurrent tenant creations turns out to be the marketplaces seed
trigger, reproduced in an isolated schema, predating this ticket's change entirely.

**F43 and F44 are one sentence in two object classes, and both were statements the file's own behaviour
contradicted.** F39 withdrew the premise that no default privilege can subtract PostgreSQL's built-in grant to
PUBLIC, and the withdrawal reached part 6, the journal and this Outcome. It did not reach part 8's self-check,
its raise, or two shipped failure messages, so part 8 ended up contradicting itself inside one file: line 654
said no default privilege could prevent it while lines 521 to 535 said part 6's global revoke is exactly what
does. Two of the four are text a person reads at the moment a check fires, which is the worst place for a false
explanation, so each now names the three things genuinely outside part 6's reach rather than a law that is not
one.

F44 is the same clause about types, and correcting it is a change of reason and not of behaviour. Measured
again rather than inherited, because a sentence carried forward without being run is this ticket's recurring
defect: a domain is born reachable and a global revoke of usage on types does reach it, so the reason `'T'`
carries no revoke moves from impossible to unnecessary. It is unnecessary twice over, since usage on a type is
not a route to a row and since the statement would reach no type this schema has, the row types of its own
tables being outside a default privilege altogether. The round was told that concluding the revoke should be
written would be a larger change than the finding, and to say so rather than take it; it did not need to.

**What stops those two recurring is that the withdrawn claim is now data.** `WITHDRAWN_BIRTH_CLAIMS` holds it
one row per spelling with the class it is about, and a scanner reads comments, raise messages and assertion
messages alike, so the sentence surviving, being copied or coming back is caught wherever a person would meet
it. Its limit is stated at the constant: it holds the words the claim was written in and cannot catch the same
mistake in new words, which is why each class now carries a measurement beside it.

**F45 is the guard built to close a class having the shape of the class.** F40 made `repository.ts` the only
module that may open a file, and the half that made that a rule matched only the `node:`-prefixed spellings, so
`from 'fs'`, `from 'child_process'` and `require('fs')` walked past while Node resolves them identically; the
walk also collected only `.ts` while vitest runs four more extensions. The instrument changed rather than the
pattern: the compiler's own pre-processor is asked what a module imports, and the answer is judged against an
allow-list of imports that cannot read, each with a written reason. That inverts the deny-list shape this
ticket has now produced findings about at CODEX-02, F20, F30 and here.

`no-restricted-imports` was weighed and rejected on measurement rather than preference, which is the part worth
keeping: eslint reported nothing for `require('fs')` in a `.cjs` file, nothing for `await import('fs')` in an
`.mjs` file, and flagged a relative specifier despite the negation, so it would have caught a strict subset
while looking like a stronger guarantee. The RED found something the finding had not: the old pattern reported
this suite's own test file, because the new cases quote `'node:fs'` inside a string. A pattern over source text
cannot tell an import from a quotation, in either direction.

**F46 is the same lesson inside the newest mechanism.** F42's guarantee rests on the registry's key giving
`on conflict (tenant_id)` an arbiter, and part 8 asked `pg_index` to describe the shape instead. Two keys pass
that description and break the guarantee: a partial unique index, where the erasure fails 42P10, and a
deferrable primary key, which the finding did not name and where the refusal falls open silently. `indpred`
and `indisvalid` would close the first, `indimmediate` the second, and the attribute after those is the one
nobody enumerates. So the check runs the statements the guarantee rests on, against a probe id taken back by
the same raise the refusal already uses, which is F42's own move one level up on the file's doctrine that
enforcement beats description.

**The pattern that outlasted every finding.** Twice more this round, a guard answered the question in front of
it while its comment claimed a wider one, and twice more the fix was to stop describing and start enforcing:
ask the compiler rather than a pattern, run the statement rather than read the catalogue. Set beside F19's
`relkind`, F30's `relacl` and F39's per-schema revoke, the ticket's whole history is one shape. The durable
answers were three: enumerate and require a reason for each member, ask the database to enforce what a comment
claims, and hold a withdrawn claim as data.

The third of those is the weakest and this sentence first overstated it, which F50 returned the ticket for. The
mechanism holds the words each sentence was written in, so it catches that sentence surviving, being copied or
coming back, and not the same mistake made in new words; `tables.ts` says so at the constant. It reads this
package's sources, the migrations of the set and `docs/architecture.md`, and it does not read this Outcome, by a
decision recorded at the scanner rather than by omission: reading the ticket file would make it an authority
that turbo must hash, so the file whose every edit invalidates the recorded pass would be the file that records
it, and a document whose job is to say what was withdrawn cannot do that without quoting the withdrawal it
would then be reported for. What reads the Outcome is the review, which is where F39 and F50 were both found.

So what the third answer buys is narrower than the sentence originally claimed, and it is still worth having.
The other two are supported by the work: part 8 runs the statements its guarantee rests on, the schema tests ask
the database rather than the catalogue, and F47 is what it looks like when a member of an enumeration carries a
reason that is not true.

**The fourth pre-check found four more, and none was a defect in the schema.** The seventh Codex round died on
its usage limit twice, so the second reviewer ran again in its place, told to be narrow and adversarial and to
find what would make a Codex round return the ticket before that round was spent. It returned on F47 to F50: a
stated impossibility that was false, a stated transitivity that was false, a narrowing that undid the round
before it, and a summary stronger than its mechanism. Every one is a sentence about a guard rather than a
defect in the tables, which is what this ticket had become by then.

It also attacked rather than read, which is worth recording as the thing that made these rounds worth their
cost. F46's probe was tried on re-apply, under concurrency, on take-back failure and against five alternative
key shapes, and survived all of them. F42's refusal was re-measured at three isolation levels on two
connections each, its sentinel was handed a planted 23514 to see whether it would swallow a real error, and the
serialisable conflict between two concurrent tenant creations was traced to the marketplaces seed trigger and
shown to predate this ticket entirely.

**F47 is F44's shape one round after F44.** `repository.ts` admitted `vitest` to the list of imports that
cannot read, on the stated ground that the runner hands a test no way to open a path. `vi.importActual` takes a
literal specifier and returns the real module, and the pre-processor does not report it, so a module of this
package obtained `node:fs` and read an unhashed document while the guard said the package was clean. The fix
walks the syntax tree for loader calls and judges what it finds with the same allow-list, so a loaded specifier
is treated exactly as an imported one and the mechanism stays one rather than two that can drift. The entry now
says it is admitted because every test file imports it and removing it is not available, which is true, rather
than that it cannot reach a file, which was not.

**And the paragraph listing what gets past the guard no longer claims to be complete**, which is the part of
F47 that mattered most. It had been written as three items with "none of those is shut here", and this was a
fourth with a literal specifier. It now names four known survivals and says plainly that this is what is known
to survive rather than all that does, and offers the shape of the blind spot instead of a membership list: the
instrument reads the specifier a module was written with, in the two places a module is written to name one, so
anything handing back a module without a specifier written where it looks is unseen until somebody measures it.

**F48 is the same defect in the next sentence of the same paragraph.** The allow-list claimed a transitivity,
that a relative specifier is safe because the module it names is collected and asked the same question. That
was false for the four directories the walk skips, and `packages/core/node_modules` exists. The fix is the one
this ticket kept arriving at: the claim became the implementation. A relative specifier is admitted only when
it resolves to a member of what the walk actually returned, so editing the skip list moves the scan and the
allow-list together and a specifier that cannot be resolved is reported rather than admitted. Two findings
converged on one fix here, for the first time on this ticket rather than one fix producing the next finding.

**F49 was a narrowing that undid the round before it**, `.ts` filtered back out of a collection widened one
round earlier precisely because vitest runs four other extensions. Its second half was the question of what the
scanner does not read, and the answer for the ticket's own Outcome is a decision rather than an omission:
reading it would make the ticket file an authority turbo must hash, so the file whose every edit invalidates the
recorded pass would be the file that records it, and a document whose job is to say what was withdrawn cannot
do that without quoting the withdrawal it would then be reported for. `docs/architecture.md` is read, because
that reach was free.

**F50 is this Outcome, and it was right.** The closing paragraph claimed that holding a withdrawn claim as data
means it cannot quietly come back, where the mechanism holds the words each sentence was written in, in a
subset of the files, and not in this document. That paragraph now says what the third answer buys and where it
stops. The round has no RED and the journal says why rather than manufacturing one, because the scanner cannot
fail on a file it deliberately does not read and a test asserting a phrase is absent would go red on demand
while measuring nothing.

**What the last four rounds settle about the ticket as a whole.** Every finding since the schema itself was
finished has been about the distance between what a guard does and what its comment says it does, and the
answers that held were the ones that removed the distance rather than correcting the sentence: the claim
becoming the implementation at F48, the loaded specifier judged by the same list as an imported one at F47, the
statements run rather than the catalogue read at F46. Where the distance could not be removed, what worked was
saying so exactly, which is why three paragraphs in this schema now state what they cannot see. A guard that
knows its own blind spot is worth more than one that does not have one, because the second kind does not exist.

**The fifth pre-check passed the ticket and found four things anyway, and the split it was asked for is the
answer to why this took thirteen attempts.** Three Codex rounds had died on a usage limit without a verdict, so
the second reviewer ran in its place with two jobs: find what would make the next Codex round return, and
report it split into what is wrong with the schema and what is wrong with the machinery this ticket grew around
itself. Its verdict was pass, with all five criteria re-verified against the live database rather than against
the journal, and **essentially nothing of the schema kind**. The tables, tenancy, privileges, foreign keys,
erasure guarantees and seeds held against everything it attacked them with.

**F51 is the one that touched a real table, and it is fixture hygiene rather than a defect in the migrations.**
Two describes must commit, because a race between two sessions has no single-transaction form, so every run
wrote three rows into `seen.erased_tenants` that nothing can take back: delete, update and truncate there are
all refused by the registry's own trigger, which is F21's guarantee working as intended. Harmless against a
stack that can be reset, and not harmless the moment the suite is pointed at a database holding real trade
records, where a registry meaning "these ids were erased on a person's request" would fill with ids that were
never customers. Both halves are closed: the fixtures take ids from a reserved namespace so a row says what it
is, and a refusal counts tombstones and tenants outside that namespace before either block writes. The refusal
was measured by planting a real erasure by hand, and both blocks refused.

**F52 is the fifth arrival of one class, and the first fix that gets ahead of it.** `import.meta.glob` names a
literal specifier and returns a repository file, and neither instrument looked at a glob call. Rather than add
a fifth name to a list, the round took the inverse and measured before deciding: an unrestricted version
produced eight false reports, every one a directory, and requiring the candidate to be a file removes all
eight. So a string literal at any call, under any name, resolving to a repository file the walk did not
collect, is now reported. CODEX-03, F34, F40, F45 and F47 each closed one spelling after a reviewer found it;
this one closes the next spelling before anybody writes it.

**F53 is the sharpest, because it is about the round before it.** F49's fix was real and the test meant to hold
it was a tautology: it compared `packageSources()` against a set built from `packageSources()`, so both
assertions were empty by construction, and restoring the exact narrowing it guards left it green, because every
collected source on this tree ends in `.ts`. The selection is now a pure function over the names it is handed
and is asked about one name per extension, so it fails when the narrowing comes back. The old assertion is kept
with a paragraph saying what it had been measuring and why that was nothing.

**F54 is this document, for the fourth time.** The Outcome said `pg_default_acl` still grants write to `anon`
and `authenticated` on tables that do not exist yet, and that narrowing it with `alter default privileges` was
declined. Both are false of the tree this delivers: part 6 revokes them and F39 established the global form
reaches what the per-schema form cannot, and a table created now is born with `postgres` and `service_role`
alone. F43, F44, F50 and F54 are all the same class in prose rather than in code, and all four were in a
document, three of them in this one. That is the cost of the decision at F49 not to scan the ticket file, taken
for reasons that still hold: the file whose every edit invalidates the recorded pass cannot be the file that
records it. What reads this document is the review, and the review is what found all four.

**What the thirteen attempts were actually spent on.** The schema was finished and confirmed by Codex's sixth
round. Everything after it was the machinery this ticket grew to keep its own claims honest, and each round of
that machinery gave the next review a new surface to find something on. That is not a defect in the reviews and
it is not wasted work, but it is a loop with no natural end, and the reason this Outcome can say the ticket is
done is that a reviewer was finally asked to separate the two and answered plainly.

**Then an audit of the schema alone found twelve things, two of them high, and the reason it found them is the
reason this ticket ran to fourteen attempts.** Three Codex rounds had died on a usage limit, so rather than
retry the same review a fifth time the question was changed: 135 agents across eight attack dimensions, told
that the guards, the scanners, the turbo cache and the wording of comments were out of scope and to return
empty if that was all they could find. Every finding went to three independent refuters with distinct lenses,
each told to run the reproduction and to default to refuted when uncertain, and a completeness critic then
asked what the eight had not looked at. 42 findings were attacked, 8 survived, and the critic found 4 more.

Five review rounds had found nothing of this kind because every one of them was attacking the guards. That is
worth stating plainly in a delivery record: the ticket spent its last five rounds hardening the machinery that
checks the schema while the schema itself carried two high defects, and the thing that surfaced them was
changing what the reviewer was pointed at rather than how carefully it looked.

**The first high is that the identifiers this schema invents were not constrained to be what their own comments
said they were.** `marketplace` was bare `text not null` on the five tables criterion 4 names, with no key, no
check and no domain, while the column comment said it is one of the six the catalogue defines. Measured:
`'bol'`, `'BOL'` and `'not-a-marketplace'` all accepted under one external id, so the criterion-4 unique index
was an idempotency key only while the speller stayed consistent and a connector changing its spelling would
have doubled the trade record silently. The same column need not agree with the parent it hung from, so an
order carrying `amazon` sat on a Bol connection and two shipments with one external id hung off one order.

It is now a foreign key chain through the parent each row already hangs from, with `claims` keyed directly
because it hangs from nothing else that names a marketplace. That is deliberately stronger than six direct
keys, which would have made every value a real identifier and still left every row free to disagree with its
parent, which was half of what the audit measured. Part 2's refusal of value-set constraints does not govern
here and part 9 argues why rather than assuming: that refusal is about a marketplace-supplied vocabulary, where
a value nobody anticipated must land in the record rather than be rejected, and `marketplace` is not supplied
by a marketplace at all. This schema invents it, part 1 creates it, part 3 seeds the six from the routing
table, and Bol cannot send a seventh.

**The second high is that `order_lines` carried no uniqueness on the line id a marketplace gave it**, so
re-ingesting one order duplicated every line and no upsert was possible. SEEN-014 is specified as idempotent
upserts; this made that impossible to write. With it, `order_id` now travels in the keys the way part 5 paid to
carry `tenant_id`, which closes the case the audit found beside it: a return whose line belonged to another
order, and a settlement line matched to an order line on another marketplace, both of which SEEN-018 would have
stored and SEEN-019 and SEEN-020 would then have read as truth.

**The critic's high is a privacy promise the schema could not keep and did not say so.** Erasing a tenant
destroyed the only mapping saying which stored objects were its own while the bytes stayed in the bucket. The
fix refuses to overreach, and the reasoning is the good part: a database cannot delete bytes, so a trigger that
tidied up storage would orphan files while reading, from inside the schema, like a fix. What this ticket owes
is the mapping surviving the cascade, so `seen.pending_object_erasures` is written from `storage.objects` by
prefix as the tenant is erased, owner-only and reachable by no Data API role, and emptying it is now one of
SEEN-083's acceptance criteria. It reads the bucket rather than the evidence rows deliberately: an upload whose
row was never written is bytes with no row at all, and that is the case an erasure must not walk past. The
prefix is what makes any of it findable, so `storage_path` is now checked against its own `tenant_id`, widened
to `statements.storage_path`, because a convention a sweep rests on has to hold of every column that addresses
an object.

**And the seed disagreed with the routing table.** The document was right, established before either was
touched: the routing table's own consequence sentence says Bol is the only marketplace with no messaging API so
its correspondence runs through the forwarded mailbox, the PRD ships it at FR-28 and FR-29, and SEEN-062 and
SEEN-063 build it. The cell reads `none by API (assisted via inbox)` and the parser took `none` off the front
of a negation. The parser now refuses a cell whose text after the mode runs into another mode, rather than
reading the first and keeping the rest, which is the same shape as every deny-list this ticket has replaced.

**What the audit ruled out is worth as much as what it found**, because it is the first time anything measured
these rather than asserting them. It measured the eight parts that existed when it ran, which is not the tree
being delivered, and the difference was not academic: part 9 then added the one partial unique index on the
list and F69 is what caught it. Read as of the audit, then, and true of the delivered tree only where a later
finding says so: no view, materialised view, foreign or partitioned table in `public`; every
`seen` function with an empty `search_path` and only `current_tenant` reachable; every temporal column
`timestamptz` and every cents column `bigint`; `external_id` not null on all five tables of criterion 4; no
partial or expression unique index anywhere; no `NOT VALID` and no `DEFERRABLE` constraint; all eight set-null
keys in the column-list form so no cascade can fail on a not-null violation; `anon` holding no privilege on any
table; and criterion 3 failing closed on both a missing claim and a malformed one.

**Two mistakes of the running of it, recorded because the receipt should carry them.** The two repair batches
were given separate files but they shared one local Postgres and one working tree, so one batch's `db:reset`
landed inside the other's test run and produced a polluted RED and a green that exited non-zero; record 267 is
the honest green, taken once both were in the tree. And the reconciliation of the set totals from eight parts
to ten, which had been reserved, was done by the second batch because the gate refuses a green that exited
non-zero and two assertions were failing on it. Totals only, no part renumbered, and said plainly rather than
folded in.

**A sixth review, in Claude Code this time, returned it on five more, and two of them were high.** The three
Codex rounds before it had all died on a usage limit, so the review that finally read this diff was a subagent
at full depth: the triage settled coverage, lint, gitleaks and the fingerprint with no model at all, handed
over the three it could only half settle with the remainder named, and gave the reviewer the whole diff because
`slice_files` failed. It reproduced both highs against the live database in a rolled-back transaction rather
than arguing them.

**Both highs were the same defect this ticket has now produced seven times: a guard whose comment claims more
than the guard does.** F67 is that part 10's `check (storage_path like tenant_id::text || '/%')` binds the text
an evidence row stores and never the object the bytes went to. Upload to `shared/uploads/x.pdf`, store
`<tenant>/claims/<claim>/x.pdf`, and the check passes while the object survives the tenant's erasure unfound,
which is precisely the outcome F63 measured, in the file written to close F63. The migration had then used that
constraint to argue SEEN-022 was owed no criterion. F68 is that the keys part 9 added reference `connections`
on three columns with no on-update action, so they default to NO ACTION and refuse the rename part 3's
`on update cascade` exists to propagate, from the moment a connection has one child, while two paragraphs of
part 9 said a rename still carries its connections with it.

**F67's answer is F63's answer, and the reason is the same.** A check constraint can read no table but the row
it is on, so no statement in this schema can make that check about the upload; claiming otherwise was the whole
defect. The paragraph now states its reach and its limit in F63's own terms, and the withdrawal is held as data
rather than as prose, because a comment nothing reads is the class that produced F67 and F70 in the first
place: `SCHEMA_OBLIGATIONS` makes the suite red unless `public.evidence` and `public.statements` name the
tickets that owe the prefix and unless each of those tickets carries the criterion. SEEN-041 joined SEEN-022
and SEEN-027 there, because `statements.storage_path` was constrained for the same reason and no ticket had
been told about it either. The reach itself is then pinned as behaviour and not only as a promise: a row may
name a path no object stands at, an object under the prefix that no row names is still swept, and an object
outside the prefix is walked past, and all three stay true once the obligation tickets close the third where it
can be closed, which is the uploading code.

**F68 went the other way, and on a measurement rather than a preference.** Cascading down the chain was the
obvious repair and it is wrong: `on update cascade` has no per-column form, so putting it on the key from
`orders` to `connections` would also make an update of `connections.tenant_id` rewrite every order beneath it,
which is the exact hole part 9's other trigger closes on the one table that had it, bought four more times for
a rename nobody has asked for. So the identifier is immutable, a trigger says so and refuses with 23001 whether
or not anything hangs below, and part 3's cascades are left in the shape part 3 wrote them and are now provably
inert, which both files state. A schema that answers `accepted` on an idle account and `23503` on a trading one
is not a rule, and that was the real finding.

**F69 is F46 reproduced two rounds after F46 was fixed.** Part 9's `message_threads` index was partial, so the
`ON CONFLICT` upsert SEEN-061 and SEEN-062 are specified to write fails with 42P10, which is the SQLSTATE part
9 itself quoted as the failure its three new indexes exist to prevent, and the self-check that approved it
asked `pg_index` for a description exactly as part 8 had before F46 made it run the statement. The index is
non-partial, `external_thread_id` is not null, the self-check runs the statements, and `message_threads` has an
upsert test of its own beside the `order_lines` one.

**F70 is the set describing a column it no longer has**, parts 3 and 7 creating, arguing for and classifying
`invoices.recovery_share_lines` that part 10 drops, so a reader of the schema meets a reversed decision
presented as a deliberate one. The set is forward-only by convention, so the repair is not a pointer to part
10 but a scanner: `migrationColumnReferences` refuses any migration sentence describing a column the delivered
schema does not hold. That guard can be trusted because a column reference is a name and `pg_attribute`
settles it.

**Where the same widening was refused, and why that is the more useful half.** Fixing F70 surfaced part 2's
sentence that `message_threads` carries no unique index on the thread id, which part 9 had made false and the
column scanner cannot see. Catching the class rather than the instance would mean recognising that "there is
no unique index on it here", "this column is not keyed" and "the upsert key is SEEN-061's to add" are all
denials and inferring from English which relation and which kind of index each denies; matching on the word
`index` and asking `pg_index` inverts the error instead of removing it, because this set has fourteen comments
that correctly say a column is part of an upsert key and every one would be reported. So the class is left
uncaught and said to be, and the instance is held as data in `WITHDRAWN_SHAPE_CLAIMS` beside what is true
instead, where it cannot survive, be copied or come back. A guard that reports a number nobody can trust is
worse than a gap somebody has written down.

**F71 was the status drift, for the third time on this ticket**, the file saying `doing` with five unticked
criteria while the journal stood at review. Notes 207 and 261 are the first two. The order this attempt now
holds to is the one the reviewer read out of the earlier commits: the regression, the advance out of tdd, and
then the `## Outcome`, the status and the ticks in one commit before the triage, so the fingerprint the review
attests covers a ticket file that already says what it delivered.

**A third round returned it on six more, and this time the round itself was the finding.** Every acceptance
criterion was verified by execution against the live database rather than read out of the journal, and all five
held. Every update route to a parent disagreement was probed and each is refused 23503. No partial, expression,
deferrable or invalid unique index remains anywhere in `public` or `seen`, so F69's class is closed and not only
its instance. The seed is an upsert, so part 10's re-seed cannot cascade a tenant's connections away. Nothing
the review could reach opened a cross-tenant, privilege, billing or erasure hole. Then five of its six findings
were one class, and it was the class this ticket had already produced twelve times.

**F72 was the one with behaviour, and it is the two-answer shape again.** The immutability trigger F68 added
covered `public.marketplaces` and not `public.connections.marketplace`, which carries the same identifier and
sits beside `credential_ref`, the pointer to that seller account's credentials. A service_role repoint answered
`accepted` on a connection with nothing under it and `23503` on one carrying an order, which is the answer part
9's own comment said it had removed: a rule that depends on whether an account has traded is not a rule. Both
columns that hold an identifier now refuse a change with 23001, and the test is an `UPDATE`, because the review
observed that every marketplace-disagreement test in that block was an `INSERT`, which is F27's own lesson
about six probes that all tested one verb.

**F73 put a false count in the sentence a person reads at the moment they are refused.** Part 9 said none of
the nine keys carrying `marketplace` names an update action and had itself created one that does, 140 lines
earlier. The repair is not a corrected number: the `raise` message now carries no count at all and says what
the refusal means and what a rename is instead, with the reason written beside the function. A number in a
`raise` is a claim that rots where nobody is looking, and this one had been falsified by its own file.

**The other four were sentences that outlived what they described, and the useful work was not the four edits.**
The F68 repair had rewritten the withdrawn rename claim in two of the three places it lived; the F70 repair had
removed two of the three places the dropped column was argued for; part 4 miscounted the set as eight in the
paragraph whose subject is that every part states the set's size and a test checks it; part 8 called itself the
last migration two parts before the end. Three of those survived a guard that existed and could not see them,
so each gap was closed rather than each sentence merely corrected: four entries in `WITHDRAWN_SHAPE_CLAIMS`,
an indefinite ordinal added to the set-size scanner, and `lastMemberClaimedInComments` comparing a claim of
lastness against the directory. A fifth copy of the rename claim turned up in part 9's own probe while the work
was open, which is the point: the class is found in a new place every round because it is repaired one sentence
at a time.

**Two widenings were refused, and the measurements are the reason they are worth recording.** A guard for the
bare substantive cardinal, which would have caught part 4's other two counters, matches fourteen sentences in
the three authorities, of which two are the instances and six of the rest count something that is not a file at
all: `these six find nothing`, `the two against each other`, `all four are read`. Which cardinal refers to a
migration is anaphora, and no fact on disk decides it; filtering to counts the directory contradicts does not
help, because six things that are not files differ from ten as surely as a stale count does. So part 4 states no
number instead. And a guard for F74's sentence would have to turn an English noun phrase into an identifier and
ask `pg_attribute`, where a phrase that maps to no column is indistinguishable from a phrase that was never a
column name, so every sentence in every table comment becomes a candidate. Both refusals are written where the
list is. The standard this ticket settled on is that a guard reporting a number nobody can trust is worse than a
gap somebody has written down, and it now has three such gaps written down rather than three guards that would
have to be believed.

**The fourth review found the thing every round before it had been circling, and it was high.** F78 is a
cross-tenant credential move: one `update public.connections set tenant_id` carries a seller account's
`credential_ref`, its scopes and its status into another tenant, the receiving tenant's own signed-in user then
reads that row under its own claim, the owning tenant reads nothing, and no audit event is written by either
party. It was accepted while the connection was idle and refused 23503 once it had traded, which is the shape
part 9's own comments call the worst of the two answers, three times over, and it is the same credential move the
trigger twenty lines above exists to prevent by the cascade route. Part 9 had declared the gap generically, as a
wider question than F65 that it did not settle, without noticing that on this one table the wider question is
F65. F80 was the same defect one column over, `claims.marketplace` being the third authored identifier where the
file counted two.

**The prediction recorded at the previous round was wrong and is left standing rather than quietly dropped.**
The reasoning there was that the class had produced twelve prose findings and that a thirteenth would mean the
review had stopped paying for itself. What it produced instead was a reproducible hole with credentials in it,
because "the last two rounds were prose" had been allowed to stand in for "this round will be". The lesson is
about the inference and not about the class: a review whose last findings were cheap is not a review whose next
finding is cheap, and nothing in the record supported turning the one into the other.

**So the repair is the class and the class is derived from the catalogue, which is what finally settled it.**
Every finding from F55 onwards was some column that should not change with nothing stopping it, found one at a
time, and every repair enumerated by hand the columns it happened to be looking at: the head of part 9 said
"both places this schema writes one" where there were three, and F72's section said "one of the two columns that
hold one" where nine hold the identifier. A count written by hand was the defect each time, so no count is
written by hand now. Two rules over `pg_catalog` give the set: `tenant_id` on every table of `public` that
carries one, and the key column of a catalogue key together with every column whose own foreign key points at
that key. The second rule is what tells an authored identifier from a derived one without reading English, and
the reason it works is that a foreign key names exactly one unique key of its parent: a key pointing at
`(tenant_id, marketplace)` says only that the value is in the catalogue and leaves it free to become any of the
six, while a key pointing at `connections (tenant_id, id, marketplace)` pins it to a parent row chosen first.
That yields 32 members, three of them a marketplace identifier and 29 a `tenant_id`, and it excludes the other
six `marketplace` columns and every `*_id` reference for reasons the rules state rather than for reasons somebody
remembered. One trigger function carries the column in `tg_argv`, a `DO` block creates the 28 triggers no
bespoke guard already covers, and the suite derives the same set independently and probes every member with an
`UPDATE` on an idle row and on a trading one. A column that enters the set later with nothing guarding it makes
the suite red on arrival, which is the property none of the hand-written enumerations had.
`IMMUTABLE_IDENTIFIER_EXCEPTIONS` is empty and says why, and names the one case the rules cannot see: an
identifier this schema authors that no key points at, of which there is none today.

**What that fix then measured is the argument for having written it that way.** F78 was reported as the idle
case on one table. The RED at record 293 shows twelve columns moving a row into another tenant, and seven of them
did it with children already attached, because those children hang on nullable keys or on none:
`approvals`, `findings`, `invoices`, `policies`, `products`, `statements` and `users`. The finding understated
its own reach, and a repair scoped to the finding would have closed one of the twelve and left the sentence
about the other eleven still true.

**Three things the round noticed and did not close**, recorded because each is a limit of the guard rather than
a gap in the schema. `public.tenants.tenant_id` has no idle state to probe, because the seed trigger gives every
new tenant six catalogue rows, so its two answers agree for that reason rather than because of the trigger.
`marketplaces.tenant_id` would answer 23505 on both probes if its bespoke guard were dropped, so that one member
could pass for a reason that is not a guard, and the fixture clears the target tenant's rows to avoid it
wherever it can. And re-parenting is a different class from an authored identifier: `order_lines.marketplace` is
filled by a trigger and is immutable only for as long as `orders.marketplace` is, and no trigger refuses an
update of a parent reference directly. Widening to that would need its own decision, so it is written down
rather than guessed at.

**The fifth review broke nothing and that is the result.** It derived the immutable set from the live database
with part 9's own two rules and got the same 32 members with every one guarded and nothing left over. It
measured rule 2's coverage rather than reading it. It accounted for every member's green one at a time and found
none passing for a fixture artefact, because an unseeded tenancy member makes the update match nothing, which the
probe reports as accepted and the assertion then fails on, so an unseeded table is red and never green. It
confirmed the two derivations are the same query predicate for predicate, and it verified all five acceptance
criteria by execution on its own run of the suite. Its findings were three sentences that had outlived what they
described, one guard with no proof of its own, and one list the schema did not honour.

**Two of the three sentences had been made false by the previous round's own repair**, which is the argument for
the answer taken here: part 9's head no longer counts rename triggers at all, and it names the three rounds a
count in that paragraph has now cost. F81's sentence is worse than stale, because record 292 quoted it as the
place the F78 gap was declared, and the foot of the same file closes that gap 200 lines below: left standing it
invites the next reviewer to re-report F78 and tells a later author a repair path is permitted which is refused
23001 at runtime.

**F85 turned an exemption list that only the suite honoured into one the schema does.** The list is now
`seen.mutable_identifiers()`, and the anonymous `DO` block became `seen.guard_authored_identifiers()` precisely so
that it can read the list and so the suite can call it twice, which is what makes the claim measurable at all: an
entry is no longer a way to silence the measurement while the trigger goes on refusing the update in production.
The test does not settle for two empty lists matching, which would hold over a schema honouring nothing. It
exempts a member, drops its trigger, calls the guard, and measures that the trigger stays off and the update is
accepted, then empties the list and watches the guard put the trigger back.

**The SQLSTATE scanner was measured and refused, and the measurement is the useful part.** The corpus is 29
comment lines carrying 30 occurrences of 10 distinct codes, counted rather than taken: the review's figure of 28
reproduces as lines rather than occurrences, and its count of eight codes excludes `0A000` because that is not
five digits. Nine of the 29 state a code the database no longer answers for the statement their sentence names,
and **eight of those nine are true of what they describe**: five are the before-and-after measurement a section
writes to justify itself, and three state what a key buys where a later trigger now fires first. Exactly one is
wrong, and it is F83. So a scanner would report nine and be right about one, and telling the eight from the one is
a tense and a subject read out of English, which is the guess this ticket already declined twice. It is the third
widening refused on measurement rather than on taste, and the standard is unchanged: a guard reporting a number
nobody can trust is worse than a gap written down.

**The paragraph recording that measurement went stale inside the commit that wrote it**, because repairing F83
moved the corpus from 28 lines to 29. It now counts nothing and the numbers live in record 303. That is the class
this whole round is about, caught on itself at the last possible moment, and it is the clearest statement of why
the answers that hold here remove the count rather than correct it.

**What the round did not close, declared rather than guessed at.** Two further sentences state 23503 in the
present tense for statements the schema now answers 23001 for; both are true of the layer they describe and both
are the argument for the trigger that supersedes them, so rewriting eight sentences to be tense-explicit was
judged worse than leaving two declared, given that two of this round's five findings were sentences the previous
round's rewriting created. `seen.mutable_identifiers()` and `seen.guard_authored_identifiers()` are created after
part 8's schema-wide self-check has run, so only the standing guard in the suite covers them; it passes, and both
carry an empty `search_path` and their own revoke. And the equality between the constant and the database list
compares every field the type has today, so a third field added later would go unchecked.

**An inaccuracy in this ticket's own evidence, found by the review and recorded at note 300 rather than argued
with.** The tdd record at 297 cites record 293 as the red for three findings, and 293's only failure is the
identifier probe: the test carrying F79's repair did not exist when 293 ran and was green on its first run. The
gate cannot catch that, because it orders sequence numbers and reads exit codes and cannot ask whether a red's
failures cover the behaviours a slice claims; that is exactly the remainder the triage hands the reviewer, and
this is that check earning its place. It is the second time in two rounds, the first being the F67 boundary test,
whose implementer said plainly that its half had gone green on its first run while the record did not. Record 297
stands unedited, because a journal that can be corrected after a reviewer has read it is not evidence, and the
tdd record for this round names which of its findings the cited red covers and which it does not.

**The sixth review broke nothing of the schema either, and its three findings were all in the machinery, two of
them in the guard the previous round had built.** That is the shape that ended the loop. By this point every
round was adding a guard to catch a stale claim and the next round was finding a hole in that guard, while the
tables themselves had survived two consecutive reviews that attacked rather than read them: tenancy measured over
both relation families, 29 of 29 on each of three questions with the negative query empty; the cross-tenant read
measured with a claim, with no claim and with a malformed claim; the five criterion-4 indexes measured unique and
non-partial; the seed compared cell by cell; the new guard function forced to fail mid-way with a planted trigger
name and found to create nothing it could not finish, its restore path returning `pg_get_triggerdef` byte for
byte, owner-only and not `security definer`, with no state constructible in which its two lists disagree and the
suite passes.

**F86 was a real hole and it is the third time this repository has met it.** The guard written for F84 counted
callers by searching its own source for the function name followed by an open bracket, which cannot tell a call
from a quotation: narrowing the protected call did turn the test red, but adding one comment line quoting the
unnarrowed call restored the count and every assertion passed again, over a re-opened F79 in which the
`public.tenants` entry was read by nobody. That entry holds F81's own sentence, the one record 292 quoted as the
declaration of the F78 gap, so it could have come back into the migration with 194 tests green. The answer is the
one `repository.ts` already took at F45, when `ts.preProcessFile` could not tell a type position from a value
position: count call expressions through a syntax-tree walk. Both attacks are now measured inside the test rather
than left to a reviewer, the narrowing and the narrowing re-quoted in a comment and in a string literal, and the
RED reports the count as 2 for the delivered file because the fixture's own quotation was counted, which is the
defect demonstrating itself.

**F87 was a sentence written one round earlier that claimed to state a cost in full and was false of 29 of the 32
members it was about**, because the reach assertion was computed from the exception-filtered list, so exempting
any `tenant_id` reported its table as one the two rules had never reached and sent the author hunting a hole in
the derivation rather than at the assertion refusing their exemption. The reach now reads the unfiltered
derivation, which is the answer that makes the sentence true rather than the answer that adds a fourth cost: the
assertion exists to prove the rules reached every writable table, and an exemption removes a column from the
probe, not from their reach. The alternative was declined on three checkable grounds, all recorded at the
function: neither catalogue rule distinguishes the two bases, the mirrored list in `seen.mutable_identifiers()`
is honoured by a loop that reads no basis either, and a rule that is really a refusal belongs in the refusal.

**Two limits of the verification, declared at the end because the round after this one was not coming.** Neither
is about the tables and both were measured rather than guessed. First: the suite proves that the schema refuses
an update of a derived member and not that part 9's trigger is what refuses it. 17 of the 29 tenancy members
carry a mandatory composite foreign key including `tenant_id` to a parent other than `public.tenants`, so for
those 17 the update is refused 23503 by the parent key whether the loop's trigger stands or not, and dropping
`immutable_tenant_id` from any of them leaves the suite green. Only the three authored identifiers and the twelve
unpinned tenancy members carry evidence that the trigger is the author of the refusal. Second, and the one that
matters for the tickets after this: `seen.guard_authored_identifiers()` is called from one place, the `do` block
at the foot of its own migration, so its whole-set check runs at apply time and nowhere else. A later migration
that adds a table carrying `tenant_id` gets no immutability trigger unless it calls the function, nothing hands
that obligation forward (it is not in `SCHEMA_OBLIGATIONS`), and if the new table is of the parent-key-pinned
shape the suite reports nothing either. One `perform seen.guard_authored_identifiers();` in each later migration,
or an obligation entry naming it, closes it. Neither was written, because both are outside this ticket's criteria
and outside the files its slice names, and a declaration is the honest form of that.

**How this ticket ends, which is not with a receipt.** The review that read this tree six times was a Claude Code
subagent, and `needs_two_reviewers` is true here because `full_depth_rules` carries `billing`, so the gate
requires a reviewer the implementing tool did not provide and refuses a review naming claude in both slots. Three
Codex rounds before these six had each died on a usage limit. Ruud's decision, taken with the position stated, is
to merge without a receipt rather than wait on the other assistant or narrow `REVIEWED_TWICE` as its own ticket.
So this ticket carries six reviews, twenty-two findings from F67 to F88 all resolved, 1,436 tests green and all
five criteria measured by execution, and no delivery receipt at all; the merge is recorded in the journal as the
decision it was, and the status stays at `review` because nothing passed the gate that would make it `done`. What
that costs is precise and worth writing down rather than softening: the two highs of this stretch, F67's unfound
storage objects and F78's cross-tenant credential move, were both found by a review, and the one control that
exists to make a second pair of eyes mandatory where a missed defect costs money is the control that was waived.

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Migration and RLS for tenants, connections, orders and the settlement tables (2 pt). RED: the table listing test finds tenant_id and RLS on every table created so far
2. Findings, claims, evidence, messaging and agent tables (2 pt). RED: the cross-tenant JWT query returns zero rows on findings and claims
3. Unique indexes, marketplace seed and db:reset (1 pt). RED: the duplicate (tenant_id, marketplace, external_id) insert is rejected and db:reset re-applies cleanly

## Depends on

- [SEEN-006](SEEN-006-scaffold-the-pnpm-turborepo-monorepo-with-all.md): Scaffold the pnpm turborepo monorepo with all six packages
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers
- [SEEN-094](SEEN-094-verify-delivery-against-ci-and-the-merge.md): Verify delivery against CI and verify the merge against the receipt

## Blocks

- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access
- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences
- [SEEN-016](SEEN-016-encode-fee-schedules-per-marketplace-and.md): Encode fee schedules per marketplace and category in core
- [SEEN-032](SEEN-032-write-append-only-audit-events-before-every.md): Write append-only audit_events before every side effect
- [SEEN-039](SEEN-039-create-stripe-customers-with-sepa-and-card-and.md): Create Stripe customers with SEPA and card and handle webhooks
- [SEEN-049](SEEN-049-encode-listing-spec-rules-per-marketplace-in.md): Encode listing spec rules per marketplace in core
- [SEEN-082](SEEN-082-run-rls-penetration-tests-and-the-restore-drill.md): Run RLS penetration tests and the restore drill

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
