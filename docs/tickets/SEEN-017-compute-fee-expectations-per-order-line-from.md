---
id: SEEN-017
title: "Compute fee_expectations per order line from schedules and APIs"
epic: E2
epic_name: "Reconciliation, findings and audit"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon]
depends_on: [SEEN-011, SEEN-014, SEEN-016, SEEN-116]
status: todo
---
# SEEN-017: Compute fee_expectations per order line from schedules and APIs

| | |
|---|---|
| Epic | E2 Reconciliation, findings and audit |
| Sprint | 1 (12 - 23 Oct 2026), gate G1 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon |
| Status | todo |

## Description

Add a reconcile-stage worker in apps/worker that writes one fee_expectations row per order line: expected commission, fixed fee and ad cost, preferring the Bol Commissions API value per EAN and the Amazon fee preview report per SKU over the static schedule, and recording the source of each figure. Design decision: the expectation is stored, not recomputed, so a later schedule change never rewrites history.

## Acceptance criteria

- [ ] Every order_line of the friendly brand has exactly one fee_expectations row after the worker runs
- [ ] For Bol the expected commission equals the Commissions API value for the EAN on the order date in 100% of a 50-line sample
- [ ] Each fee_expectations row records source (commissions_api, fee_report or schedule) and the schedule version
- [ ] Re-running the worker changes zero existing rows when inputs are unchanged
- [ ] A fast-check property, named after its invariant, shows that the fee expectation for an order line is deterministic and never exceeds the gross line amount

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Fee expectation model and schedule lookup as pure functions (2 pt). RED: an order line with a known category yields the schedule's commission and fixed fee
2. Bol Commissions API and Amazon fee preview as preferred sources, with the source recorded (2 pt). RED: a Bol line takes the Commissions API value over the schedule and records commissions_api
3. The reconcile-stage worker: one row per order line, idempotent re-runs (1 pt). RED: a second run changes zero rows when inputs are unchanged

## Depends on

- [SEEN-011](SEEN-011-build-bol-retailer-api-v10-connector-for-orders.md): Build Bol Retailer API v10 connector for orders to commissions
- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences
- [SEEN-016](SEEN-016-encode-fee-schedules-per-marketplace-and.md): Encode fee schedules per marketplace and category in core
- [SEEN-116](SEEN-116-property-based-and-mutation-tests-on-the-money.md): Property-based and mutation tests on the money core, as a gate

## Blocks

- [SEEN-019](SEEN-019-implement-fee-detectors-as-pure-tested-functions.md): Implement fee detectors as pure tested functions
- [SEEN-071](SEEN-071-model-net-margin-per-marketplace-from-cost.md): Model net margin per marketplace from cost layers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Match every settlement line to an order line, detect fee errors, lost shipments and return shortfalls with tested code, and deliver the audit PDF with a measured recoverable pool.
