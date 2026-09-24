---
id: SEEN-020
title: "Implement shipment, return and inventory detectors"
epic: E2
epic_name: "Reconciliation, findings and audit"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-015, SEEN-018]
status: todo
---
# SEEN-020: Implement shipment, return and inventory detectors

| | |
|---|---|
| Epic | E2 Reconciliation, findings and audit |
| Sprint | 1 (12 - 23 Oct 2026), gate G1 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Add four more pure detectors to packages/core/detectors: lost shipment without compensation (shipment lost or undelivered after the carrier window with no compensation line), return compensation shortfall using the Bol 25% rule for returns with damaged or missing items, FBA lost or damaged inventory without a reimbursement row within 30 days, and refund without a return received. Each uses the same finding shape as the fee detectors and includes the marketplace's claim deadline.

## Acceptance criteria

- [ ] Bol return shortfall computes expected compensation as 25% of the item price for the qualifying handling results and flags a shortfall above EUR 0.50
- [ ] Lost shipment raises only after the carrier window (Bol 30 days, Amazon 45 days, eBay 30 days) with no compensation line
- [ ] FBA detector reads the inventory adjustment and reimbursement report names verified in SEEN-015
- [ ] Each detector has unit tests with at least 5 true positives and 5 true negatives

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Lost shipment without compensation, with the carrier windows (2 pt). RED: a shipment past the window with no compensation line raises, one inside the window does not
2. Return compensation shortfall with the Bol 25% rule (1 pt). RED: a damaged return credited below 25% of the item price raises the shortfall
3. FBA lost or damaged inventory and refund without return received (2 pt). RED: an inventory adjustment with no reimbursement row within 30 days raises

## Depends on

- [SEEN-015](SEEN-015-verify-amazon-report-names-and-finances.md): Verify Amazon report names and Finances transactions version
- [SEEN-018](SEEN-018-match-settlement-lines-to-order-lines.md): Match settlement_lines to order_lines deterministically

## Blocks

- [SEEN-021](SEEN-021-persist-findings-with-rule-confidence-evidence.md): Persist findings with rule, confidence, evidence refs and deadline

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Match every settlement line to an order line, detect fee errors, lost shipments and return shortfalls with tested code, and deliver the audit PDF with a measured recoverable pool.
