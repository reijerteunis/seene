---
id: SEEN-061
title: "Ingest message_threads from Amazon, eBay, Kaufland and Otto"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 5
sprint_dates: "7 - 18 Dec 2026"
gate: G5
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [amazon, ebay, kaufland, otto]
depends_on: [SEEN-054, SEEN-058, SEEN-060]
status: todo
---
# SEEN-061: Ingest message_threads from Amazon, eBay, Kaufland and Otto

| | |
|---|---|
| Epic | E7 Modules: Reconcile, Comply, Serve |
| Sprint | 5 (7 - 18 Dec 2026), gate G5 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | amazon, ebay, kaufland, otto |
| Status | todo |

## Description

Add the Serve ingest in apps/worker: Amazon Messaging API (buyer messages where the Buyer Communication role allows, plus Solicitations for review requests), eBay on the path chosen in SEEN-058, Kaufland tickets and Otto messaging into message_threads and messages with direction, marketplace, order link and read state, polled hourly per connection. Design decision: one message_threads shape for every source, so reply_message never needs to know where a thread came from.

## Acceptance criteria

- [ ] Threads and messages for the friendly brand ingested from Amazon and eBay with the order id linked where present
- [ ] Kaufland tickets and Otto messages appear as threads with the marketplace field set
- [ ] Re-ingest produces zero duplicate messages
- [ ] Unanswered threads older than the marketplace's response window are flagged on the thread

## Depends on

- [SEEN-054](SEEN-054-build-the-kaufland-connector-with-tickets-as.md): Build the Kaufland connector with tickets as the claims rail
- [SEEN-058](SEEN-058-verify-ebay-messaging-deprecation-and-choose.md): Verify eBay messaging deprecation and choose the message path
- [SEEN-060](SEEN-060-build-the-otto-connector-for-orders-returns.md): Build the Otto connector for orders, returns, receipts and messages

## Blocks

- [SEEN-062](SEEN-062-parse-the-forwarded-mailbox-via-postmark.md): Parse the forwarded mailbox via Postmark inbound into threads
- [SEEN-063](SEEN-063-add-reply-message-tool-bound-to-tenant-service.md): Add reply_message tool bound to tenant service policies

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
