---
id: SEEN-023
title: "Measure the recoverable pool per marketplace"
epic: E2
epic_name: "Reconciliation, findings and audit"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-021]
status: todo
---
# SEEN-023: Measure the recoverable pool per marketplace

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

Add a metric job and SQL view that computes, per tenant and marketplace, the recoverable pool as the sum of open and claimed findings over settled revenue for the window, with a breakdown by rule and confidence band, exposed in the ops console and at GET /tenants/:id/metrics/pool. The number is the measured figure for G1 and the day-120 pack, never the US benchmark.

## Acceptance criteria

- [ ] Pool percentage and amount per marketplace visible in the ops console for each audited tenant
- [ ] Breakdown by rule sums to the total within EUR 0.01
- [ ] Metric excludes findings below the configured confidence threshold and shows the excluded amount separately
- [ ] Values for the three audited brands are recorded in the G1 gate note

## Depends on

- [SEEN-021](SEEN-021-persist-findings-with-rule-confidence-evidence.md): Persist findings with rule, confidence, evidence refs and deadline

## Blocks

- [SEEN-025](SEEN-025-run-three-real-90-day-audits-and-deliver-the.md): Run three real 90-day audits and deliver the PDFs

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Match every settlement line to an order line, detect fee errors, lost shipments and return shortfalls with tested code, and deliver the audit PDF with a measured recoverable pool.
