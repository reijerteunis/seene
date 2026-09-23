---
id: SEEN-060
title: "Build the Otto connector for orders, returns, receipts and messages"
epic: E1
epic_name: "Connectors and ingest"
sprint: 5
sprint_dates: "7 - 18 Dec 2026"
gate: G5
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [otto]
depends_on: [SEEN-009, SEEN-014, SEEN-027, SEEN-059]
status: todo
---
# SEEN-060: Build the Otto connector for orders, returns, receipts and messages

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 5 (7 - 18 Dec 2026), gate G5 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | otto |
| Status | todo |

## Description

Implement packages/connectors/otto: orders, returns, receipts into settlements and settlement_lines, and messaging read and send, with the rate limits from SEEN-059. Register Otto in the capability matrix with claims mode assisted and tracking through receipts, and add its detector constants so reconciliation runs on its settlements.

## Acceptance criteria

- [ ] Orders, returns and receipt lines for a pilot ingested with idempotent re-runs
- [ ] Receipt lines map to settlement_lines with a type from the enum
- [ ] Messages read into message_threads and a reply sent by API in a test thread
- [ ] Capability matrix row for Otto matches the routing table in architecture.md

## Depends on

- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access
- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences
- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes
- [SEEN-059](SEEN-059-verify-otto-rate-limits-and-obtain-otto-api-keys.md): Verify Otto rate limits and obtain Otto API keys

## Blocks

- [SEEN-061](SEEN-061-ingest-message-threads-from-amazon-ebay.md): Ingest message_threads from Amazon, eBay, Kaufland and Otto

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
