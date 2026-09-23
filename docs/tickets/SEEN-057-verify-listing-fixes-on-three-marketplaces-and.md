---
id: SEEN-057
title: "Verify listing fixes on three marketplaces and file Kaufland tickets"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 2
executor: human
changes_agent_action: false
marketplaces: [bol, amazon, ebay, kaufland]
depends_on: [SEEN-052, SEEN-053, SEEN-054, SEEN-056]
status: todo
---
# SEEN-057: Verify listing fixes on three marketplaces and file Kaufland tickets

| | |
|---|---|
| Epic | E7 Modules: Reconcile, Comply, Serve |
| Sprint | 4 (23 Nov - 4 Dec 2026), gate G4 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay, kaufland |
| Status | todo |

## Description

Approve listing fixes for the friendly brand on Bol, Amazon and eBay, check the result on each marketplace's seller portal against the before and after diff, and file at least one Kaufland ticket for a pilot finding by API from the inbox. Record any mismatch as a connector issue.

## Acceptance criteria

- [ ] At least one fix applied and verified on each of Bol, Amazon and eBay with a before and after diff
- [ ] At least one Kaufland ticket filed by API with the ticket id on the claim
- [ ] Any mismatch between the diff and the portal recorded as a connector issue with the listing id

## Depends on

- [SEEN-052](SEEN-052-write-listing-content-through-bol-and-ebay-apis.md): Write listing content through Bol and eBay APIs
- [SEEN-053](SEEN-053-write-listing-content-through-amazon-listings.md): Write listing content through Amazon Listings Items and Feeds
- [SEEN-054](SEEN-054-build-the-kaufland-connector-with-tickets-as.md): Build the Kaufland connector with tickets as the claims rail
- [SEEN-056](SEEN-056-show-comply-defects-and-fix-diffs-in-the-inbox.md): Show Comply defects and fix diffs in the inbox

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
