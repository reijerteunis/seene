---
id: SEEN-038
title: "Verify Shopify Payments payout scopes and create the custom app"
epic: E1
epic_name: "Connectors and ingest"
sprint: 3
sprint_dates: "9 - 20 Nov 2026"
gate: G3
estimate: 1
executor: human
changes_agent_action: false
marketplaces: [shopify]
depends_on: [SEEN-009]
status: todo
---
# SEEN-038: Verify Shopify Payments payout scopes and create the custom app

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 3 (9 - 20 Nov 2026), gate G3 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | shopify |
| Status | todo |

## Description

Create the custom app on the friendly brand's Shopify store, confirm the Admin API scopes needed for products, orders and Shopify Payments payouts (read_products, read_orders, read_shopify_payments_payouts) and whether payouts require the store to be on Shopify Payments, then store the token in the secrets provider (.env.local in development, Secret Manager after go-live) for packages/connectors/shopify. The decision that matters: Shopify is only ever read, never written, so the scope set is the minimum for products, orders and payouts.

## Acceptance criteria

- [ ] Custom app installed with the verified scopes and the token stored in the secrets provider (.env.local in development, Secret Manager after go-live)
- [ ] A manual GraphQL query for shopifyPaymentsAccount payouts returns data or a documented reason it cannot
- [ ] Scope list recorded in packages/connectors/shopify/README.md with the documentation date

## Depends on

- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access

## Blocks

- [SEEN-044](SEEN-044-build-the-shopify-admin-graphql-connector-as.md): Build the Shopify Admin GraphQL connector as product and stock truth

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
