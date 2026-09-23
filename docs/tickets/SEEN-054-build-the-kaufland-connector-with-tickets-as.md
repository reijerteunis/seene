---
id: SEEN-054
title: "Build the Kaufland connector with tickets as the claims rail"
epic: E1
epic_name: "Connectors and ingest"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [kaufland]
depends_on: [SEEN-009, SEEN-014, SEEN-027, SEEN-048]
status: todo
---
# SEEN-054: Build the Kaufland connector with tickets as the claims rail

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 4 (23 Nov - 4 Dec 2026), gate G4 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | kaufland |
| Status | todo |

## Description

Implement packages/connectors/kaufland: orders, returns, settlement detail per SEEN-048, listings (units) and the tickets API for opening and reading tickets, with request signing and the recorded rate limits. Register Kaufland in the capability matrix with claims mode api through tickets and add its detector constants so reconciliation runs on its settlements.

## Acceptance criteria

- [ ] Orders, returns and settlement lines for a pilot ingested with idempotent re-runs
- [ ] A claim for a Kaufland finding is filed by opening a ticket by API and the ticket id is the external case id
- [ ] Ticket replies appear as claim_events within one polling cycle
- [ ] Capability matrix row for Kaufland matches the routing table in architecture.md

## Depends on

- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access
- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences
- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes
- [SEEN-048](SEEN-048-verify-kaufland-settlement-and-ticket-endpoints.md): Verify Kaufland settlement and ticket endpoints and obtain keys

## Blocks

- [SEEN-057](SEEN-057-verify-listing-fixes-on-three-marketplaces-and.md): Verify listing fixes on three marketplaces and file Kaufland tickets
- [SEEN-061](SEEN-061-ingest-message-threads-from-amazon-ebay.md): Ingest message_threads from Amazon, eBay, Kaufland and Otto
- [SEEN-068](SEEN-068-verify-the-kaufland-virtual-buy-box-endpoint.md): Verify the Kaufland virtual buy box endpoint

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
