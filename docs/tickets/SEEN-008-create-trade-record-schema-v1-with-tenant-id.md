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
status: review
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
| Status | review |

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

Left open, named rather than done: `pg_default_acl` still grants the four write privileges to `anon` and
`authenticated` on tables that do not exist yet, so the next migration's table is born writable by the role a
browser is bound to. The new privilege assertion fails loudly when that happens, which is detection rather than
prevention; narrowing it with `alter default privileges` changes every future migration and was not in the
decision above.

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
roll back, and each asserts it left no tombstone. It is worth saying what this half was not: every tenant id
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

**Where the schema ended up.** Eight migrations rather than four: the original set, then tenant-scoped
foreign keys, then relations that are not tables, then the free-text classification, then the erased-tenant
registry. 95 tests in 6 files. Every finding of the second review is closed and each was verified by
someone other than the agent that fixed it, which is the only reason this section can say so.

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
