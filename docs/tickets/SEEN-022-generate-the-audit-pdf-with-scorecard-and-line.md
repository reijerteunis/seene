---
id: SEEN-022
title: "Generate the audit PDF with scorecard and line annex"
epic: E2
epic_name: "Reconciliation, findings and audit"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-021]
status: todo
---
# SEEN-022: Generate the audit PDF with scorecard and line annex

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

Build the audit report in apps/api with a headless renderer: a cover with the 90-day window, a scorecard per marketplace (settled amount, fees charged, fees expected, findings by rule, recoverable amount, deadlines at risk) and a line-by-line annex listing every finding with its evidence refs. Report data comes from the findings view and settlement totals so the PDF never computes money itself.

## Acceptance criteria

- [ ] POST /tenants/:id/audits generates a PDF for a 90-day window in under 60 seconds for 10,000 settlement lines
- [ ] Scorecard totals equal the SQL view totals to the cent in a test fixture
- [ ] Annex lists every open finding with rule, amount, external ids and deadline
- [ ] PDF stored in the evidence bucket with its sha256 recorded on the audit row

## Depends on

- [SEEN-021](SEEN-021-persist-findings-with-rule-confidence-evidence.md): Persist findings with rule, confidence, evidence refs and deadline

## Blocks

- [SEEN-025](SEEN-025-run-three-real-90-day-audits-and-deliver-the.md): Run three real 90-day audits and deliver the PDFs

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Match every settlement line to an order line, detect fee errors, lost shipments and return shortfalls with tested code, and deliver the audit PDF with a measured recoverable pool.
