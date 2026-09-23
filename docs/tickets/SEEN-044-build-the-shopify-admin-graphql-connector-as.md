---
id: SEEN-044
title: "Build the Shopify Admin GraphQL connector as product and stock truth"
epic: E1
epic_name: "Connectors and ingest"
sprint: 3
sprint_dates: "9 - 20 Nov 2026"
gate: G3
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [shopify]
depends_on: [SEEN-009, SEEN-014, SEEN-038]
status: todo
---
# SEEN-044: Build the Shopify Admin GraphQL connector as product and stock truth

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 3 (9 - 20 Nov 2026), gate G3 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | shopify |
| Status | todo |

## Description

Implement packages/connectors/shopify against the Admin GraphQL API: products and variants with SKU, barcode and inventory levels into products and listings, orders into orders and order_lines, Shopify Payments payouts and balance transactions into settlements and settlement_lines, plus the orders/create and products/update webhooks in apps/api. Design decision: Shopify is the source of truth for product identity and stock, so marketplace listings link to products by SKU or GTIN from Shopify.

## Acceptance criteria

- [ ] Products, variants and inventory levels of the friendly brand ingested with GTIN and SKU on products
- [ ] Marketplace listings link to a product by GTIN or SKU for at least 95% of the friendly brand's listings
- [ ] Payouts and balance transactions map to settlements and settlement_lines with idempotent re-runs
- [ ] Webhook HMAC verification rejects an unsigned payload with HTTP 401

## Depends on

- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access
- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences
- [SEEN-038](SEEN-038-verify-shopify-payments-payout-scopes-and.md): Verify Shopify Payments payout scopes and create the custom app

## Blocks

- [SEEN-050](SEEN-050-ingest-listings-with-content-hash-and-drift.md): Ingest listings with content hash and drift detection
- [SEEN-071](SEEN-071-model-net-margin-per-marketplace-from-cost.md): Model net margin per marketplace from cost layers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
