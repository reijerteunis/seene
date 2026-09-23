---
id: SEEN-043
title: "Export finance CSV of settlements and matched lines"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 3
sprint_dates: "9 - 20 Nov 2026"
gate: G3
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-018]
status: todo
---
# SEEN-043: Export finance CSV of settlements and matched lines

| | |
|---|---|
| Epic | E7 Modules: Reconcile, Comply, Serve |
| Sprint | 3 (9 - 20 Nov 2026), gate G3 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Add GET /tenants/:id/exports/finance.csv in apps/api that streams settlements and settlement_lines for a period with matched order id, line type, amount, VAT flag, currency, marketplace and the ledger account from a per-tenant mapping table, so a bookkeeper can import it. The mapping table is editable in the customer inbox.

## Acceptance criteria

- [ ] CSV for a month with 10,000 lines streams in under 10 seconds
- [ ] Every line carries marketplace, settlement external id, type, amount, currency, matched order id and ledger account
- [ ] Column sums per type equal the settlement totals for the period
- [ ] Ledger account mapping is editable per tenant and unmapped types export with account UNMAPPED

## Depends on

- [SEEN-018](SEEN-018-match-settlement-lines-to-order-lines.md): Match settlement_lines to order_lines deterministically

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
