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
