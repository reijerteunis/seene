---
id: SEEN-012
title: "Build eBay connector for orders, returns, transactions and payouts"
epic: E1
epic_name: "Connectors and ingest"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [ebay]
depends_on: [SEEN-002, SEEN-009, SEEN-010]
status: todo
---
# SEEN-012: Build eBay connector for orders, returns, transactions and payouts

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | ebay |
| Status | todo |

## Description

Implement the eBay adapter in packages/connectors/ebay: Sell Fulfillment API for orders and shipping fulfilments, Post-Order API for returns and cases, and Sell Finances API for transactions and payouts. Transactions map to settlement_lines typed by transactionType (sale, refund, fee, dispute, adjustment) and payouts to settlements; the Finances method names are confirmed against the current documentation as part of this ticket.

## Acceptance criteria

- [ ] Adapter passes recorded-fixture tests for orders, fulfilments, returns, transactions and payouts
- [ ] Every transaction is linked to its payout by payoutId and to its order by orderId where eBay provides one
- [ ] Fee transactions map to settlement_lines of type commission or fixed_fee with the eBay feeType kept in the raw reference
- [ ] A 90-day backfill for the friendly brand completes and the sum of transactions equals the sum of payouts within EUR 1

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Orders and fulfilments from Sell Fulfillment fixtures (2 pt). RED: an order with a fulfilment maps to orders, order_lines and shipments
2. Returns and cases from Post-Order fixtures (1 pt). RED: a return with a case maps to returns with the case reference kept
3. Transactions and payouts from Sell Finances, linked by payoutId and orderId (2 pt). RED: the sum of a payout's transactions equals the payout amount in the fixture

## Depends on

- [SEEN-002](SEEN-002-obtain-ebay-production-keys-and-file.md): Obtain eBay production keys and file Application Growth Check
- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access
- [SEEN-010](SEEN-010-add-per-marketplace-rate-limiting-with-header.md): Add per-marketplace rate limiting with header-driven backoff

## Blocks

- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences
- [SEEN-028](SEEN-028-contest-ebay-payment-disputes-and-cases-by-api.md): Contest eBay payment disputes and cases by API
- [SEEN-058](SEEN-058-verify-ebay-messaging-deprecation-and-choose.md): Verify eBay messaging deprecation and choose the message path
- [SEEN-064](SEEN-064-apply-return-and-cancellation-decisions-through.md): Apply return and cancellation decisions through returns APIs
- [SEEN-069](SEEN-069-snapshot-competing-offers-from-bol-by-ean-and.md): Snapshot competing offers from Bol by EAN and eBay by GTIN
- [SEEN-073](SEEN-073-write-prices-through-bol-offers-and-ebay.md): Write prices through Bol Offers and eBay Inventory offers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
