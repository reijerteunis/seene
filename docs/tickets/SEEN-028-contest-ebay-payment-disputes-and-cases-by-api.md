---
id: SEEN-028
title: "Contest eBay payment disputes and cases by API"
epic: E3
epic_name: "Claims rail and evidence"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [ebay]
depends_on: [SEEN-012, SEEN-027]
status: todo
---
# SEEN-028: Contest eBay payment disputes and cases by API

| | |
|---|---|
| Epic | E3 Claims rail and evidence |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | ebay |
| Status | todo |

## Description

Implement the eBay api mode in packages/connectors/ebay: Sell Fulfillment payment disputes (fetch, contest with reason, add evidence) and the Post-Order case flow (respond, provide tracking, escalate) mapped to the claims rail, with the dispute id as the claim external id and dispute status polling into claim_events. Evidence files go through the API's evidence upload endpoints and are referenced from the evidence table.

## Acceptance criteria

- [ ] A dispute in the eBay sandbox is contested by API with one evidence file and the claim shows the dispute id
- [ ] Dispute status changes (open, under review, closed won, closed lost) appear as claim_events within one polling cycle
- [ ] Filing is refused by code when the dispute's respond-by date is in the past
- [ ] Recorded-fixture tests cover contest, add evidence and status polling

## Depends on

- [SEEN-012](SEEN-012-build-ebay-connector-for-orders-returns.md): Build eBay connector for orders, returns, transactions and payouts
- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes

## Blocks

- [SEEN-037](SEEN-037-file-the-first-ten-claims-across-two.md): File the first ten claims across two marketplaces from the inbox
- [SEEN-066](SEEN-066-track-claim-and-dispute-deadlines-with-alerts.md): Track claim and dispute deadlines with alerts

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: File claims by API where a marketplace allows it and as one-click case packs where it does not, track each to a credit in an ingested settlement line, and keep hashed evidence.
