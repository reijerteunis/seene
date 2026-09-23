---
id: SEEN-030
title: "Build the Amazon assisted case pack with report tracking"
epic: E3
epic_name: "Claims rail and evidence"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [amazon]
depends_on: [SEEN-027]
status: todo
---
# SEEN-030: Build the Amazon assisted case pack with report tracking

| | |
|---|---|
| Epic | E3 Claims rail and evidence |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | amazon |
| Status | todo |

## Description

Implement the Amazon assisted mode in packages/core/claims/amazon: Seller Central case text in English with the reimbursement policy clause per rule, the evidence bundle and the deep link to open a case, confirmed by the human in one click. Tracking reads the reimbursement report and settlement report for a reimbursement id or adjustment referencing the order or FNSKU, and inbound mail for the case id.

## Acceptance criteria

- [ ] Case pack renders the text template for each Amazon rule (FBA lost, FBA damaged, fee overcharge, refund without return)
- [ ] Confirm action records submitted_at and asks the human to paste the Seller Central case id, stored as external case id
- [ ] A reimbursement report row referencing the order or FNSKU sets the claim to credited and links the settlement line
- [ ] Case packs for findings older than the Amazon claim window (18 months for FBA) are refused with a reason

## Depends on

- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes

## Blocks

- [SEEN-037](SEEN-037-file-the-first-ten-claims-across-two.md): File the first ten claims across two marketplaces from the inbox

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: File claims by API where a marketplace allows it and as one-click case packs where it does not, track each to a credit in an ingested settlement line, and keep hashed evidence.
