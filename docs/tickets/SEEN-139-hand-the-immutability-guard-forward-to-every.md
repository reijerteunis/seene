---
id: SEEN-139
title: "Hand the immutability guard forward to every migration that adds a table"
epic: E0
epic_name: "Foundations and registrations"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-008]
status: todo
---
# SEEN-139: Hand the immutability guard forward to every migration that adds a table

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

SEEN-008 closed F78, a cross-tenant credential move, by deriving from `pg_catalog` the set of columns this schema authors and refusing an update of every one of them. The derivation is sound and six reviews could not break it. What it does not do is survive the next migration, and that was declared rather than fixed because it fell outside that ticket's criteria.

`seen.guard_authored_identifiers()` is called from exactly one place: the `do` block at the foot of the migration that defines it. So the whole-set check, the one that raises when a derived member carries no trigger, runs at apply time and nowhere else. A later migration that adds a table carrying `tenant_id` gets no immutability trigger unless its author knows to call the function, nothing hands that obligation forward, and `SCHEMA_OBLIGATIONS` does not carry an entry of this kind. The tickets that will add tables are SEEN-021, SEEN-027, SEEN-050, SEEN-061 and SEEN-069 among others, and none of them is told.

The standing suite does not catch it either, and this is the part worth understanding before writing any of it. `packages/core/db/rls.test.ts` proves that the schema refuses an update of each derived member; it does not prove that part 9's trigger is what refuses it. Measured on the delivered schema: **17 of the 29 tenancy members carry a mandatory composite foreign key including `tenant_id` to a parent other than `public.tenants`**, so for those 17 the update is refused 23503 by the parent key whether the trigger stands or not. Drop `immutable_tenant_id` from any of the 17 and the suite stays green. Only the three authored identifiers and the twelve unpinned tenancy members carry evidence that the trigger is an author of the refusal.

The two halves compound. A new table of the parent-key-pinned shape would arrive with no trigger, and the suite would report nothing at all: the probe would see its update refused, by the parent key, and pass. So the guard's reach and the guard's proof have to be fixed together or the first is untestable.

The F85 test is not a substitute and the reason is specific: it does call `seen.guard_authored_identifiers()` a second time, but the function creates a missing trigger before it would complain about one, so a missing trigger is silently repaired inside the rolled-back transaction rather than reported.

What this ticket must not do is make the schema's guard depend on a TypeScript constant. SEEN-008 settled that direction once, at F85: the exemption list lives in `seen.mutable_identifiers()` and the module mirrors it, because a list the database does not read is a list the database does not honour. The obligation handed forward has to be enforceable from inside the schema, from the suite, or from both, and the suite's half must fail on a tree where the schema's half was skipped.

## Acceptance criteria

- [ ] A migration that adds a table carrying `tenant_id` and does not guard that column makes the suite red, naming the table and the column, and the proof is a fixture migration rather than an edit to a delivered one
- [ ] The whole-set check runs against the delivered schema and not only at the moment its own migration applies, so a tree whose later migration skipped the obligation is red without anybody re-running `db:reset` differently
- [ ] For every derived member whose update a parent key would refuse anyway, the suite proves part 9's trigger is an author of the refusal, by dropping that trigger in a rolled-back transaction and measuring what the update then answers
- [ ] The number of members whose evidence is the trigger rather than a parent key is derived from the catalogue and never written by hand, which is the rule SEEN-008 arrived at after F72, F80 and F82 each cost a round to a count in a comment
- [ ] The obligation is carried where a later migration's author will meet it, and a ticket that will add a table carries it as a criterion, in the shape `SCHEMA_OBLIGATIONS` already uses for the evidence and statement prefixes
- [ ] No part of the guard's enforcement moves into a TypeScript constant: whatever the suite reads, the database reads too, and a disagreement between them fails closed and loudly

## Slices

1. The obligation handed forward and enforced against the delivered schema, with a fixture migration proving an unguarded new table is red (1 pt). RED: a fixture migration adds a table carrying `tenant_id` with no immutability trigger and the suite passes
2. The trigger proven to be an author of the refusal on every parent-key-pinned member, with the count derived (1 pt). RED: `immutable_tenant_id` is dropped from a pinned member and the suite stays green

## Depends on

- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- `supabase/migrations/20260930000000_trade_record_v1_referential_integrity.sql`: `seen.guard_authored_identifiers()`, `seen.mutable_identifiers()`, `seen.refuse_identifier_change()` and the `do` block that is the only caller
- `packages/core/db/rls.test.ts`: `authoredIdentifiers`, `derivationAsMeasured` and the exemption probe, which is where the proof of authorship belongs
- `packages/core/db/tables.ts`: `SCHEMA_OBLIGATIONS` for the shape an obligation handed to a later ticket already takes, and `IMMUTABLE_IDENTIFIER_EXCEPTIONS` for the rule that the database reads what the module mirrors
- SEEN-008's `## Outcome`, the paragraph beginning "Two limits of the verification": both halves of this ticket as its author declared them
- SEEN-008's journal, record 314: the decision to merge without a receipt, which names this gap as worth a ticket
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
