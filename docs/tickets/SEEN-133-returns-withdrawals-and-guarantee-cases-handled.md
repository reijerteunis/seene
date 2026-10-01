---
id: SEEN-133
title: "Returns, withdrawals and guarantee cases handled as the seller of record"
epic: E11
epic_name: "Seller of record"
sprint: 8
sprint_dates: "1 - 12 Feb 2027"
gate: G8
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon]
depends_on: [SEEN-128, SEEN-063, SEEN-064, SEEN-131]
status: todo
---
# SEEN-133: Returns, withdrawals and guarantee cases handled as the seller of record

| | |
|---|---|
| Epic | E11 Seller of record |
| Sprint | 8 (1 - 12 Feb 2027), gate G8 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon |
| Status | todo |

## Description

The consumer's counterparty is Seen, so withdrawals within fourteen days, returns, refunds and guarantee claims are Seen's to answer, inside the marketplace's flows and the law. Extend Serve: return requests on storefront orders are accepted by policy, the return goes to the supplier's address, the refund is issued through the marketplace once the supplier confirms receipt or the legal deadline arrives, whichever comes first, and the credit note follows; guarantee claims are routed to the supplier with the deadline tracked. Every decision is an agent action through the policy gate with Seen as actor. The decision that matters: the consumer never waits on the supplier, because the deadline is Seen's.

## Acceptance criteria

- [ ] A withdrawal or return on a storefront order is accepted by policy, routed to the supplier's return address and refunded on receipt or at the legal deadline, whichever comes first
- [ ] The refund issues a credit note through SEEN-131 and the statement shows the return against the supplier
- [ ] Guarantee cases are routed to the supplier with the deadline tracked in the inbox
- [ ] Every decision is an agent action through the policy gate with actor Seen, proven with a fixture

## Depends on

- [SEEN-128](SEEN-128-connection-ownership-and-storefront-mode-on-the.md): Connection ownership and storefront mode on the trade record
- [SEEN-063](SEEN-063-add-reply-message-tool-bound-to-tenant-service.md): Add reply_message tool bound to tenant service policies
- [SEEN-064](SEEN-064-apply-return-and-cancellation-decisions-through.md): Apply return and cancellation decisions through returns APIs
- [SEEN-131](SEEN-131-consumer-invoices-with-vat-by-destination-and.md): Consumer invoices with VAT by destination and the OSS return

## Blocks

- [SEEN-134](SEEN-134-storefront-pilot-one-supplier-live-on-bol-under.md): Storefront pilot: one supplier live on Bol under Seen's account, first statement paid

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged.
