---
id: SEEN-014
title: "Run ingest workers with idempotent upserts, raw archive and cadences"
epic: E1
epic_name: "Connectors and ingest"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-008, SEEN-011, SEEN-012, SEEN-013]
status: todo
---
# SEEN-014: Run ingest workers with idempotent upserts, raw archive and cadences

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Build the ingest stage in apps/worker: one BullMQ queue per connector, jobs keyed per tenant and stream, handlers that upsert on (tenant_id, marketplace, external_id) with an updated_at watermark, and a raw payload archive in Supabase Storage keyed by connection, stream and fetch time written before any mapping. Cloud Scheduler triggers orders hourly and settlements daily through an apps/api endpoint that enqueues the jobs, and last_sync per stream is written on connections.

## Acceptance criteria

- [ ] Running the same 90-day backfill twice produces zero duplicate rows in orders, shipments, returns, settlements and settlement_lines
- [ ] Every raw response is stored in the archive before its mapped rows, verified by a test that fails the mapping and still finds the archive object
- [ ] Cloud Scheduler jobs exist for orders (hourly) and settlements (daily) and enqueue a job for every active connection
- [ ] connections.last_sync per stream updates after each successful run and the log shows rows written per run
- [ ] 90 days of orders, shipments, returns and settlement lines from Bol, eBay and Amazon exist for the friendly brand

## Depends on

- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table
- [SEEN-011](SEEN-011-build-bol-retailer-api-v10-connector-for-orders.md): Build Bol Retailer API v10 connector for orders to commissions
- [SEEN-012](SEEN-012-build-ebay-connector-for-orders-returns.md): Build eBay connector for orders, returns, transactions and payouts
- [SEEN-013](SEEN-013-build-amazon-sp-api-connector-for-orders.md): Build Amazon SP-API connector for orders, reports and Finances

## Blocks

- [SEEN-017](SEEN-017-compute-fee-expectations-per-order-line-from.md): Compute fee_expectations per order line from schedules and APIs
- [SEEN-018](SEEN-018-match-settlement-lines-to-order-lines.md): Match settlement_lines to order_lines deterministically
- [SEEN-024](SEEN-024-ship-ops-console-v1-for-tenants-connections-and.md): Ship ops console v1 for tenants, connections and sync status
- [SEEN-044](SEEN-044-build-the-shopify-admin-graphql-connector-as.md): Build the Shopify Admin GraphQL connector as product and stock truth
- [SEEN-054](SEEN-054-build-the-kaufland-connector-with-tickets-as.md): Build the Kaufland connector with tickets as the claims rail
- [SEEN-060](SEEN-060-build-the-otto-connector-for-orders-returns.md): Build the Otto connector for orders, returns, receipts and messages
- [SEEN-077](SEEN-077-read-ad-reports-from-amazon-ads-bol-advertising.md): Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted
- [SEEN-081](SEEN-081-load-test-ingest-on-50-tenants-and-run-rate.md): Load test ingest on 50 tenants and run rate-limit chaos

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
