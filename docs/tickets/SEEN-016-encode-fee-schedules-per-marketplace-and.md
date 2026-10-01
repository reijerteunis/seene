---
id: SEEN-016
title: "Encode fee schedules per marketplace and category in core"
epic: E2
epic_name: "Reconciliation, findings and audit"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-008]
status: todo
---
# SEEN-016: Encode fee schedules per marketplace and category in core

| | |
|---|---|
| Epic | E2 Reconciliation, findings and audit |
| Sprint | 1 (12 - 23 Oct 2026), gate G1 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Add packages/core/fees with versioned fee schedules per marketplace and category (Bol commission percentage and fixed fee by category and price band, Amazon referral and FBA fees by category and size tier, eBay final value fee by category and store level) with effective dates, loaded from JSON files a human can update. Provide a pure function expectedFees(orderLine, schedule, date) that returns the schedule version with its result so every expectation is traceable.

## Acceptance criteria

- [ ] Fee schedule JSON exists for Bol, Amazon and eBay covering at least the top 20 categories of the friendly brands
- [ ] expectedFees returns commission, fixed fee and ad cost with the schedule version for a given date
- [ ] Schedules with overlapping effective dates fail validation with a clear error
- [ ] Unit tests cover a category change on a date boundary and a price band boundary

## Depends on

- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table

## Blocks

- [SEEN-116](SEEN-116-property-based-and-mutation-tests-on-the-money.md): Property-based and mutation tests on the money core, as a gate
- [SEEN-017](SEEN-017-compute-fee-expectations-per-order-line-from.md): Compute fee_expectations per order line from schedules and APIs

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Match every settlement line to an order line, detect fee errors, lost shipments and return shortfalls with tested code, and deliver the audit PDF with a measured recoverable pool.
