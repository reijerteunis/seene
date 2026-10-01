---
id: SEEN-127
title: "Write the storefront agreement: supply terms, the statement, the payout schedule, returns and the fee"
epic: E11
epic_name: "Seller of record"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 1
executor: human
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-124, SEEN-126]
status: todo
---
# SEEN-127: Write the storefront agreement: supply terms, the statement, the payout schedule, returns and the fee

| | |
|---|---|
| Epic | E11 Seller of record |
| Sprint | 4 (23 Nov - 4 Dec 2026), gate G4 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

The contract between Seen and a supplying brand: who owns the stock and when title passes, the retail price floor the brand sets and the bands Seen prices within, the dropship duty (ship within one working day in neutral packaging with Seen's packing slip), returns received by the brand and credited on the statement, the data the brand supplies (catalogue, GPSR, EPR), the weekly or monthly supplier statement, the payout schedule and the storefront fee. The fee proposal to decide: a percentage of net sales (after VAT, with marketplace fees passed through at cost) with a monthly minimum, all five modules included because Seen operates the account; the recovery share on credits unchanged. The decision that matters: the statement is the product the brand sees, so the agreement defines every line on it before the first line exists.

## Acceptance criteria

- [ ] The storefront agreement exists, reviewed by counsel, with title, pricing, dropship, returns, data, statement, payout and fee clauses
- [ ] The storefront fee and minimum are decided and recorded in the PRD pricing section
- [ ] The statement's line types are enumerated and handed to SEEN-132
- [ ] The first friendly brand has signed, or the objections are recorded

## Depends on

- [SEEN-124](SEEN-124-decide-the-storefront-legal-model-with-the-tax.md): Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due
- [SEEN-126](SEEN-126-register-the-storefront-entity-for-epr-gpsr.md): Register the storefront entity for EPR, GPSR responsible-person data and product liability cover

## Blocks

- [SEEN-132](SEEN-132-supplier-statements-and-payouts-net-proceeds.md): Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged.
