---
id: SEEN-073
title: "Write prices through Bol Offers and eBay Inventory offers"
epic: E1
epic_name: "Connectors and ingest"
sprint: 6
sprint_dates: "4 - 15 Jan 2027"
gate: G6
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, ebay]
depends_on: [SEEN-011, SEEN-012]
status: todo
---
# SEEN-073: Write prices through Bol Offers and eBay Inventory offers

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 6 (4 - 15 Jan 2027), gate G6 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, ebay |
| Status | todo |

## Description

Implement price writes in packages/connectors: Bol Offers price update with process status polling and eBay Inventory offer price update through updateOffer, with error mapping and a read-back that confirms the new price before a price change is marked applied. Design decision: the adapters expose one setPrice call, so apply_price never contains marketplace-specific code.

## Acceptance criteria

- [ ] A price update on Bol is confirmed by process status and a read-back within 5 minutes
- [ ] A price update on eBay is confirmed by reading the offer back
- [ ] A rejected update maps to a price_change outcome with the marketplace error
- [ ] Recorded-fixture tests cover success and rejection for both marketplaces

## Depends on

- [SEEN-011](SEEN-011-build-bol-retailer-api-v10-connector-for-orders.md): Build Bol Retailer API v10 connector for orders to commissions
- [SEEN-012](SEEN-012-build-ebay-connector-for-orders-returns.md): Build eBay connector for orders, returns, transactions and payouts

## Blocks

- [SEEN-074](SEEN-074-add-propose-price-and-apply-price-tools-with.md): Add propose_price and apply_price tools with buy-box tracking

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
