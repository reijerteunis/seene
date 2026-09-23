---
id: SEEN-015
title: "Verify Amazon report names and Finances transactions version"
epic: E1
epic_name: "Connectors and ingest"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 1
executor: human
changes_agent_action: false
marketplaces: [amazon]
depends_on: [SEEN-013]
status: todo
---
# SEEN-015: Verify Amazon report names and Finances transactions version

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 1 (12 - 23 Oct 2026), gate G1 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | amazon |
| Status | todo |

## Description

Confirm against the current SP-API documentation the report type names for FBA inventory adjustments and reimbursements, the settlement report flat-file version, and which Finances API version (v0 financial events or the newer transactions endpoint) is available in the EU, then set the values in the connector configuration in packages/connectors/amazon. Also record whether getFeaturedOfferExpectedPriceBatch is available in EU marketplaces for the Sprint 6 pricing work.

## Acceptance criteria

- [ ] Report type enum in packages/connectors/amazon/config.ts holds the verified names with the documentation URL and date
- [ ] Finances version choice recorded with the reason and the connector uses it
- [ ] A live report request for each verified name succeeds in the sandbox or on the friendly brand
- [ ] Note on getFeaturedOfferExpectedPriceBatch EU availability added to the Sprint 6 plan note

## Depends on

- [SEEN-013](SEEN-013-build-amazon-sp-api-connector-for-orders.md): Build Amazon SP-API connector for orders, reports and Finances

## Blocks

- [SEEN-020](SEEN-020-implement-shipment-return-and-inventory.md): Implement shipment, return and inventory detectors
- [SEEN-070](SEEN-070-snapshot-amazon-pricing-on-a-tiered-clock.md): Snapshot Amazon pricing on a tiered clock

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
