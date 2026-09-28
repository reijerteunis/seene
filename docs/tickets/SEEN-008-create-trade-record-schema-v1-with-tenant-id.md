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
status: doing
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
| Status | doing |

## Description

Write the Supabase migration for trade-record schema v1 in packages/core/db: tenants, users, connections, marketplaces, products, listings, orders, order_lines, shipments, returns, settlements, settlement_lines, fee_expectations, findings, claims, claim_events, evidence, message_threads, messages, policies, agent_runs, agent_actions, approvals, audit_events, competitor_snapshots, price_changes, headroom_entries, invoices and statements. Every table carries tenant_id with a row-level security policy bound to the JWT tenant claim, and every externally sourced table has a unique index on (tenant_id, marketplace, external_id). The marketplaces table is a static catalogue seeded with the capability flags from the routing table.

## Acceptance criteria

- [ ] Migration applies on an empty database and pnpm db:reset re-applies it without error
- [ ] A test that lists every table in the public schema finds tenant_id and an enabled RLS policy on 100% of them
- [ ] A query with tenant A's JWT returns zero rows from tenant B's orders in an integration test
- [ ] Unique index on (tenant_id, marketplace, external_id) exists on orders, shipments, returns, settlements and settlement_lines
- [ ] marketplaces seed contains the six marketplaces with capability flags matching the routing table in architecture.md

## Outcome

Delivered as four forward-only migrations under `supabase/migrations/`, not under `packages/core/db` as
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

- `pnpm db:reset` applies all four migrations from empty, and it is the first command of the regression
  at record 18, so a later slice breaking an earlier slice's tables cannot pass.
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
