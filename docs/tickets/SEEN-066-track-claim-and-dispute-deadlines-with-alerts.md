---
id: SEEN-066
title: "Track claim and dispute deadlines with alerts"
epic: E3
epic_name: "Claims rail and evidence"
sprint: 5
sprint_dates: "7 - 18 Dec 2026"
gate: G5
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay, kaufland]
depends_on: [SEEN-021, SEEN-028]
status: todo
---
# SEEN-066: Track claim and dispute deadlines with alerts

| | |
|---|---|
| Epic | E3 Claims rail and evidence |
| Sprint | 5 (7 - 18 Dec 2026), gate G5 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay, kaufland |
| Status | todo |

## Description

Add a deadline tracker in apps/worker: each finding and claim carries a deadline (eBay payment dispute 5-day respond window, eBay and Amazon appeal windows, Bol and Kaufland claim windows) from a per-marketplace table, and a daily job raises priority in the agent queue and the inbox at 48 hours before the deadline and marks expired at the deadline. Design decision: deadlines are stored on the row at detection time from the per-marketplace table, so a table change never silently moves an existing deadline.

## Acceptance criteria

- [ ] An eBay dispute created today has a deadline 5 days out on its finding
- [ ] Items within 48 hours of their deadline are listed first in the approval inbox with a badge
- [ ] Expired items move to status expired and are excluded from the recoverable pool
- [ ] Deadline table per marketplace is editable in the ops console

## Depends on

- [SEEN-021](SEEN-021-persist-findings-with-rule-confidence-evidence.md): Persist findings with rule, confidence, evidence refs and deadline
- [SEEN-028](SEEN-028-contest-ebay-payment-disputes-and-cases-by-api.md): Contest eBay payment disputes and cases by API

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: File claims by API where a marketplace allows it and as one-click case packs where it does not, track each to a credit in an ingested settlement line, and keep hashed evidence.
