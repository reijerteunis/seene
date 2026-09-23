---
id: SEEN-048
title: "Verify Kaufland settlement and ticket endpoints and obtain keys"
epic: E1
epic_name: "Connectors and ingest"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 1
executor: human
changes_agent_action: false
marketplaces: [kaufland]
depends_on: [SEEN-009]
status: todo
---
# SEEN-048: Verify Kaufland settlement and ticket endpoints and obtain keys

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 4 (23 Nov - 4 Dec 2026), gate G4 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | kaufland |
| Status | todo |

## Description

Obtain Kaufland seller API keys from a pilot, confirm in the Seller API documentation which endpoints return settlement detail (reports or invoices) and how tickets are opened and answered, and record request signing and rate limits for packages/connectors/kaufland. The decision that matters: Kaufland is only added to the capability matrix once these endpoints are confirmed, so the connector ticket builds against verified numbers.

## Acceptance criteria

- [ ] Kaufland client key and secret stored in the secrets provider (.env.local in development, Secret Manager after go-live) for one pilot connection
- [ ] Settlement detail source and ticket endpoints recorded in packages/connectors/kaufland/README.md with the documentation date
- [ ] A signed test call to the orders endpoint returns HTTP 200

## Depends on

- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access

## Blocks

- [SEEN-054](SEEN-054-build-the-kaufland-connector-with-tickets-as.md): Build the Kaufland connector with tickets as the claims rail

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
