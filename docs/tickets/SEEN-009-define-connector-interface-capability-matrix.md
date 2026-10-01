---
id: SEEN-009
title: "Define connector interface, capability matrix and credential access"
epic: E1
epic_name: "Connectors and ingest"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay, kaufland, otto, shopify]
depends_on: [SEEN-006, SEEN-008]
status: todo
---
# SEEN-009: Define connector interface, capability matrix and credential access

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay, kaufland, otto, shopify |
| Status | todo |

## Description

In packages/connectors define the Connector interface (listOrders, listShipments, listReturns, listSettlements, listSettlementLines, plus optional capabilities such as fileClaim, listMessages, updateListing and listCompetingOffers) with a typed capability matrix per marketplace that mirrors the routing table. Add a credential provider that reads each connection's secret from the secrets provider at job time (a .env.local-backed provider in development, Secret Manager after go-live, chosen by configuration) and refreshes OAuth tokens (Amazon LWA refresh, eBay user token refresh, Bol client credentials) under a per-connection lock. Design decision: capabilities are data, not subclass checks, so the claims rail and the agent can ask whether a marketplace can do something at runtime.

## Acceptance criteria

- [ ] Connector interface and CapabilityMatrix type exported from packages/connectors with unit tests for the matrix lookup
- [ ] Capability matrix for the six marketplaces matches every row of the routing table in architecture.md
- [ ] Credential provider returns a fresh token for Amazon, eBay and Bol test connections and caches it until 60 seconds before expiry
- [ ] No credential value appears in logs or in the database; connections store only the secret reference, never the value, for both providers

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Connector interface and capability matrix types (2 pt). RED: a matrix that contradicts a routing-table row fails the unit test
2. Credential provider with the .env.local and Secret Manager implementations (2 pt). RED: a token is refreshed after expiry and never appears in a log line
3. Connection records hold only the secret reference (1 pt). RED: a connection written with a raw credential is rejected

## Depends on

- [SEEN-006](SEEN-006-scaffold-the-pnpm-turborepo-monorepo-with-all.md): Scaffold the pnpm turborepo monorepo with all six packages
- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table

## Blocks

- [SEEN-115](SEEN-115-generate-the-marketplace-clients-from-the.md): Generate the marketplace clients from the official OpenAPI specs and validate every fixture against them
- [SEEN-010](SEEN-010-add-per-marketplace-rate-limiting-with-header.md): Add per-marketplace rate limiting with header-driven backoff
- [SEEN-011](SEEN-011-build-bol-retailer-api-v10-connector-for-orders.md): Build Bol Retailer API v10 connector for orders to commissions
- [SEEN-012](SEEN-012-build-ebay-connector-for-orders-returns.md): Build eBay connector for orders, returns, transactions and payouts
- [SEEN-013](SEEN-013-build-amazon-sp-api-connector-for-orders.md): Build Amazon SP-API connector for orders, reports and Finances
- [SEEN-038](SEEN-038-verify-shopify-payments-payout-scopes-and.md): Verify Shopify Payments payout scopes and create the custom app
- [SEEN-044](SEEN-044-build-the-shopify-admin-graphql-connector-as.md): Build the Shopify Admin GraphQL connector as product and stock truth
- [SEEN-048](SEEN-048-verify-kaufland-settlement-and-ticket-endpoints.md): Verify Kaufland settlement and ticket endpoints and obtain keys
- [SEEN-054](SEEN-054-build-the-kaufland-connector-with-tickets-as.md): Build the Kaufland connector with tickets as the claims rail
- [SEEN-059](SEEN-059-verify-otto-rate-limits-and-obtain-otto-api-keys.md): Verify Otto rate limits and obtain Otto API keys
- [SEEN-060](SEEN-060-build-the-otto-connector-for-orders-returns.md): Build the Otto connector for orders, returns, receipts and messages
- [SEEN-077](SEEN-077-read-ad-reports-from-amazon-ads-bol-advertising.md): Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted
- [SEEN-128](SEEN-128-connection-ownership-and-storefront-mode-on-the.md): Connection ownership and storefront mode on the trade record

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
