---
id: SEEN-058
title: "Verify eBay messaging deprecation and choose the message path"
epic: E1
epic_name: "Connectors and ingest"
sprint: 5
sprint_dates: "7 - 18 Dec 2026"
gate: G5
estimate: 1
executor: human
changes_agent_action: false
marketplaces: [ebay]
depends_on: [SEEN-012]
status: todo
---
# SEEN-058: Verify eBay messaging deprecation and choose the message path

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 5 (7 - 18 Dec 2026), gate G5 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | ebay |
| Status | todo |

## Description

Confirm the current status of the Trading API messaging calls (GetMyMessages, AddMemberMessageRTQ) and whether a Sell messaging API replaces them, check the scopes and rate limits, and record the path the Serve module uses for eBay in packages/connectors/ebay. The decision that matters: if the Trading calls are deprecated with no replacement, eBay correspondence joins Bol on the forwarded mailbox path.

## Acceptance criteria

- [ ] Decision recorded in packages/connectors/ebay/README.md with the documentation date
- [ ] A manual call on the chosen path returns messages for the friendly brand
- [ ] Scopes added to the eBay OAuth consent if needed and the token refreshed

## Depends on

- [SEEN-012](SEEN-012-build-ebay-connector-for-orders-returns.md): Build eBay connector for orders, returns, transactions and payouts

## Blocks

- [SEEN-061](SEEN-061-ingest-message-threads-from-amazon-ebay.md): Ingest message_threads from Amazon, eBay, Kaufland and Otto

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
