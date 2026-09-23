---
id: SEEN-018
title: "Match settlement_lines to order_lines deterministically"
epic: E2
epic_name: "Reconciliation, findings and audit"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-014]
status: todo
---
# SEEN-018: Match settlement_lines to order_lines deterministically

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

Implement matchSettlementLines in packages/core/reconcile as a pure function that links settlement_lines to order_lines by external order id and line reference, then by EAN or SKU and amount within the settlement period, and marks the confidence of each match; a worker persists matched_order_line_id and the match method. Unmatched lines stay visible as an exception list so no fee is silently dropped.

## Acceptance criteria

- [ ] At least 98% of commission and fixed-fee settlement lines of the friendly brand match an order line
- [ ] A settlement line never matches an order line from another tenant or another marketplace in the test suite
- [ ] Match method (order_ref, sku_amount, manual) and confidence are stored on settlement_lines
- [ ] Unmatched lines are listed by GET /tenants/:id/settlements/:id/unmatched with their amount

## Depends on

- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences

## Blocks

- [SEEN-019](SEEN-019-implement-fee-detectors-as-pure-tested-functions.md): Implement fee detectors as pure tested functions
- [SEEN-020](SEEN-020-implement-shipment-return-and-inventory.md): Implement shipment, return and inventory detectors
- [SEEN-042](SEEN-042-ship-the-reconcile-module-with-margin-and-fee.md): Ship the Reconcile module with margin and fee-change alerts
- [SEEN-043](SEEN-043-export-finance-csv-of-settlements-and-matched.md): Export finance CSV of settlements and matched lines

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Match every settlement line to an order line, detect fee errors, lost shipments and return shortfalls with tested code, and deliver the audit PDF with a measured recoverable pool.
