---
id: SEEN-031
title: "Match credits to claims as the only billable event"
epic: E3
epic_name: "Claims rail and evidence"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-027]
status: todo
---
# SEEN-031: Match credits to claims as the only billable event

| | |
|---|---|
| Epic | E3 Claims rail and evidence |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Implement credit matching in packages/core/reconcile: a settlement line of type compensation, correction, reimbursement or dispute payout is linked to a claim by external case id, order id or amount and date window, sets the claim and its findings to credited, and writes the credited amount. The invariant is that no credit exists outside a settlement line, so the billing meter reads the same table as the ledger.

## Acceptance criteria

- [ ] A credit matches a claim by external id first, then by order id and amount within 5% and 60 days
- [ ] claims.credited_amount and credited_settlement_line_id are set and the finding status becomes credited
- [ ] A settlement line can credit at most one claim, enforced by a unique constraint
- [ ] GET /tenants/:id/claims?status=credited returns the credited amount per claim and marketplace

## Depends on

- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes

## Blocks

- [SEEN-040](SEEN-040-issue-invoices-with-recovery-share-lines-from.md): Issue invoices with recovery-share lines from credited claims only
- [SEEN-046](SEEN-046-build-customer-facing-findings-and-claims-views.md): Build customer-facing findings and claims views

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: File claims by API where a marketplace allows it and as one-click case packs where it does not, track each to a credit in an ingested settlement line, and keep hashed evidence.
