---
id: SEEN-011
title: "Build Bol Retailer API v10 connector for orders to commissions"
epic: E1
epic_name: "Connectors and ingest"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol]
depends_on: [SEEN-003, SEEN-009, SEEN-010]
status: todo
---
# SEEN-011: Build Bol Retailer API v10 connector for orders to commissions

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol |
| Status | todo |

## Description

Implement the Bol adapter in packages/connectors/bol against Retailer API v10: orders and order items, shipments, returns, invoices with their specifications, and commissions per EAN from the Commissions API for the fee-expectation model. Map each response to the trade-record types with the Bol identifiers as external ids and keep the invoice specification line types (commission, fixed fee, compensation, correction). Design decision: the invoice specification is the settlement of record, not the payout summary.

## Acceptance criteria

- [ ] Adapter passes recorded-fixture tests for each of the five streams using stored Bol v10 responses
- [ ] Invoice specification lines map to settlement_lines with a type from the settlement_lines enum and the invoice id as the settlement external id
- [ ] Commissions per EAN return percentage and fixed fee for at least 20 EANs of the friendly brand
- [ ] A 90-day backfill for the friendly brand completes without an unhandled error

## Depends on

- [SEEN-003](SEEN-003-obtain-bol-credentials-and-verify-oauth-grant.md): Obtain Bol credentials and verify OAuth grant and rate limits
- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access
- [SEEN-010](SEEN-010-add-per-marketplace-rate-limiting-with-header.md): Add per-marketplace rate limiting with header-driven backoff

## Blocks

- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences
- [SEEN-017](SEEN-017-compute-fee-expectations-per-order-line-from.md): Compute fee_expectations per order line from schedules and APIs
- [SEEN-064](SEEN-064-apply-return-and-cancellation-decisions-through.md): Apply return and cancellation decisions through returns APIs
- [SEEN-069](SEEN-069-snapshot-competing-offers-from-bol-by-ean-and.md): Snapshot competing offers from Bol by EAN and eBay by GTIN
- [SEEN-073](SEEN-073-write-prices-through-bol-offers-and-ebay.md): Write prices through Bol Offers and eBay Inventory offers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
