---
id: SEEN-025
title: "Run three real 90-day audits and deliver the PDFs"
epic: E2
epic_name: "Reconciliation, findings and audit"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 2
executor: human
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-022, SEEN-023]
status: todo
---
# SEEN-025: Run three real 90-day audits and deliver the PDFs

| | |
|---|---|
| Epic | E2 Reconciliation, findings and audit |
| Sprint | 1 (12 - 23 Oct 2026), gate G1 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Connect three brands (the friendly brand and two from the design partner list, using exported settlement files where an API key is late), run reconciliation and the audit PDF, review every finding above EUR 50 by hand against the marketplace portal, and deliver the PDF to each brand with its recoverable pool figure. Record false positives as detector issues.

## Acceptance criteria

- [ ] Three audit PDFs delivered to three named brands by 23 October
- [ ] Every finding above EUR 50 in the three audits checked by hand and marked confirmed or false positive
- [ ] False positive rate per rule recorded and any rule above 20% has a follow-up ticket
- [ ] Recoverable pool per marketplace for each brand written into the G1 gate note

## Depends on

- [SEEN-022](SEEN-022-generate-the-audit-pdf-with-scorecard-and-line.md): Generate the audit PDF with scorecard and line annex
- [SEEN-023](SEEN-023-measure-the-recoverable-pool-per-marketplace.md): Measure the recoverable pool per marketplace

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Match every settlement line to an order line, detect fee errors, lost shipments and return shortfalls with tested code, and deliver the audit PDF with a measured recoverable pool.
