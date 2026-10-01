---
id: SEEN-134
title: "Storefront pilot: one supplier live on Bol under Seen's account, first statement paid"
epic: E11
epic_name: "Seller of record"
sprint: 8
sprint_dates: "1 - 12 Feb 2027"
gate: G8
estimate: 2
executor: human
changes_agent_action: false
marketplaces: [bol]
depends_on: [SEEN-129, SEEN-130, SEEN-131, SEEN-132, SEEN-133]
status: todo
---
# SEEN-134: Storefront pilot: one supplier live on Bol under Seen's account, first statement paid

| | |
|---|---|
| Epic | E11 Seller of record |
| Sprint | 8 (1 - 12 Feb 2027), gate G8 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | bol |
| Status | todo |

## Description

Run the storefront end to end with the friendly brand on Bol: catalogue listed under Seen's account, orders dropshipped, invoices issued, returns handled, the first statement computed, signed and paid. Record what the numbers say against the fee decided in SEEN-127 and whether a second supplier should follow on Amazon. The decision that matters: a paid statement that a supplier's finance lead accepted is the proof, not a listing that went live.

## Acceptance criteria

- [ ] The friendly brand's catalogue is live under Seen's Bol account and at least twenty orders have been dropshipped
- [ ] The first supplier statement is computed, signed, paid and accepted by the supplier's finance lead
- [ ] Invoices, credit notes and the OSS CSV for the period reconcile and are handed to the accountant
- [ ] A go or no-go for a second supplier on Amazon is recorded with the reasons

## Depends on

- [SEEN-129](SEEN-129-list-a-supplier-s-catalogue-under-seen-s.md): List a supplier's catalogue under Seen's accounts with brand mapping and GPSR data
- [SEEN-130](SEEN-130-dropship-flow-a-purchase-order-to-the-supplier.md): Dropship flow: a purchase order to the supplier on every storefront order, shipment and tracking back
- [SEEN-131](SEEN-131-consumer-invoices-with-vat-by-destination-and.md): Consumer invoices with VAT by destination and the OSS return
- [SEEN-132](SEEN-132-supplier-statements-and-payouts-net-proceeds.md): Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through
- [SEEN-133](SEEN-133-returns-withdrawals-and-guarantee-cases-handled.md): Returns, withdrawals and guarantee cases handled as the seller of record

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged.
