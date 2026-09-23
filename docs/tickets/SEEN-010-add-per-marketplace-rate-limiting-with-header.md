---
id: SEEN-010
title: "Add per-marketplace rate limiting with header-driven backoff"
epic: E1
epic_name: "Connectors and ingest"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-009]
status: todo
---
# SEEN-010: Add per-marketplace rate limiting with header-driven backoff

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Implement a token-bucket limiter per connection and endpoint family in packages/connectors that reads each marketplace's rate-limit and Retry-After headers (Amazon x-amzn-RateLimit-Limit, Bol x-ratelimit-remaining and x-ratelimit-reset, eBay Retry-After) and feeds BullMQ exponential backoff with jitter on HTTP 429 and 503. Limiter state lives in Redis so two worker instances share one budget per connection.

## Acceptance criteria

- [ ] A unit test with a mocked 429 and Retry-After of 2 seconds delays the retry by at least 2 and at most 3 seconds
- [ ] Two worker processes against one mocked connection never exceed the configured requests per second in a 60-second test
- [ ] Backoff stops after 5 retries and moves the job to the failed queue with the last response body attached
- [ ] Rate-limit hits are counted per connection and visible as a metric in the local telemetry (Cloud Logging after go-live)

## Depends on

- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access

## Blocks

- [SEEN-011](SEEN-011-build-bol-retailer-api-v10-connector-for-orders.md): Build Bol Retailer API v10 connector for orders to commissions
- [SEEN-012](SEEN-012-build-ebay-connector-for-orders-returns.md): Build eBay connector for orders, returns, transactions and payouts
- [SEEN-013](SEEN-013-build-amazon-sp-api-connector-for-orders.md): Build Amazon SP-API connector for orders, reports and Finances
- [SEEN-055](SEEN-055-monitor-unauthorised-sellers-from-competing.md): Monitor unauthorised sellers from competing offers
- [SEEN-069](SEEN-069-snapshot-competing-offers-from-bol-by-ean-and.md): Snapshot competing offers from Bol by EAN and eBay by GTIN
- [SEEN-070](SEEN-070-snapshot-amazon-pricing-on-a-tiered-clock.md): Snapshot Amazon pricing on a tiered clock
- [SEEN-081](SEEN-081-load-test-ingest-on-50-tenants-and-run-rate.md): Load test ingest on 50 tenants and run rate-limit chaos

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
