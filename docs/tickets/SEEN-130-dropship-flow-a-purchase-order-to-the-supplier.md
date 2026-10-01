---
id: SEEN-130
title: "Dropship flow: a purchase order to the supplier on every storefront order, shipment and tracking back"
epic: E11
epic_name: "Seller of record"
sprint: 8
sprint_dates: "1 - 12 Feb 2027"
gate: G8
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon]
depends_on: [SEEN-128, SEEN-014, SEEN-044]
status: todo
---
# SEEN-130: Dropship flow: a purchase order to the supplier on every storefront order, shipment and tracking back

| | |
|---|---|
| Epic | E11 Seller of record |
| Sprint | 8 (1 - 12 Feb 2027), gate G8 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon |
| Status | todo |

## Description

A storefront order lands on Seen's account; the brand ships it. On ingest of a storefront order, create a purchase order for the supplier (an order in the supplier's shop system through the Shopify connector, or an e-mail with a packing slip where the shop has no API) carrying the consumer's delivery address as processor data under the DPA and Seen's packing slip; ingest the supplier's shipment and tracking back and confirm the shipment to the marketplace through the existing connectors; escalate an unshipped order before the marketplace's late-shipment threshold. Cancellations flow both ways. The decision that matters: the marketplace never sees the brand, the brand never sees the consumer beyond the delivery address, and the trade record sees both sides of every order.

## Acceptance criteria

- [ ] Every storefront order creates one purchase order for the supplier within five minutes of ingest, idempotently, with the delivery address and Seen's packing slip
- [ ] The supplier's shipment and tracking are ingested and confirmed to the marketplace, and the order shows both sides in the trade record
- [ ] An order unshipped at the marketplace's threshold minus one day raises an inbox escalation
- [ ] A consumer cancellation cancels the purchase order and a supplier cancellation refunds the consumer through the marketplace

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Purchase order creation on storefront order ingest, through Shopify or e-mail (2 pt). RED: the same order ingested twice creates one purchase order
2. Shipment and tracking back to the marketplace (2 pt). RED: a supplier shipment confirms the marketplace order with the tracking number
3. Escalations and cancellations both ways (1 pt). RED: an unshipped order past the threshold raises the escalation once

## Depends on

- [SEEN-128](SEEN-128-connection-ownership-and-storefront-mode-on-the.md): Connection ownership and storefront mode on the trade record
- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences
- [SEEN-044](SEEN-044-build-the-shopify-admin-graphql-connector-as.md): Build the Shopify Admin GraphQL connector as product and stock truth

## Blocks

- [SEEN-134](SEEN-134-storefront-pilot-one-supplier-live-on-bol-under.md): Storefront pilot: one supplier live on Bol under Seen's account, first statement paid

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged.
