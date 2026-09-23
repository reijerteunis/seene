---
id: SEEN-042
title: "Ship the Reconcile module with margin and fee-change alerts"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 3
sprint_dates: "9 - 20 Nov 2026"
gate: G3
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-018, SEEN-021]
status: todo
---
# SEEN-042: Ship the Reconcile module with margin and fee-change alerts

| | |
|---|---|
| Epic | E7 Modules: Reconcile, Comply, Serve |
| Sprint | 3 (9 - 20 Nov 2026), gate G3 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Build Reconcile in packages/core and apps/worker: a nightly job that marks every settlement as matched, partially matched or unmatched, computes margin per marketplace after commission, fixed fee, ad cost and returns from settlement_lines, and raises a fee-change alert when the effective commission rate for a category moves by more than 0.5 percentage points against the previous 30 days. Results show on the Reconcile page of the customer inbox and the job runs only where the module is on.

## Acceptance criteria

- [ ] Every settlement of a tenant has a match status and the unmatched amount is shown per settlement
- [ ] Margin per marketplace equals revenue minus the typed settlement_lines for the period in a fixture to the cent
- [ ] A fee-change alert is raised in a test where commission on a category moves from 12% to 13%
- [ ] Reconcile runs only for tenants with the module switched on

## Depends on

- [SEEN-018](SEEN-018-match-settlement-lines-to-order-lines.md): Match settlement_lines to order_lines deterministically
- [SEEN-021](SEEN-021-persist-findings-with-rule-confidence-evidence.md): Persist findings with rule, confidence, evidence refs and deadline

## Blocks

- [SEEN-047](SEEN-047-issue-the-first-invoice-and-send-the-signed.md): Issue the first invoice and send the signed statement

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
