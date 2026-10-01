---
id: SEEN-124
title: "Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due"
epic: E11
epic_name: "Seller of record"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 2
executor: human
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-005]
status: todo
---
# SEEN-124: Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due

| | |
|---|---|
| Epic | E11 Seller of record |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Brands that cannot be the seller of record on a marketplace (channel conflict with their own retailers, no entity in the country, no appetite for consumer obligations) can sell through Seen's accounts instead. That makes Seen the seller toward the consumer and the marketplace, and the brand a supplier. Two legal shapes exist and the choice drives everything after it: a commission arrangement in which Seen sells in its own name for the brand's account and title passes at the sale (VAT treats an undisclosed agent as buying and reselling, so Seen invoices the consumer and receives a supply from the brand), or an outright purchase in which Seen buys stock at a transfer price. Settle with the tax adviser: the shape, where VAT is due for cross-border consumer sales (the Union One Stop Shop for distance sales, local registration wherever stock is stored, for instance in an Amazon fulfilment centre), invoicing sequences per country, DAC7 reporting of Seen's sales by the marketplaces, and the accounting of supplier payouts. Record the decision and the adviser's memo in the ticket. The decision that matters: nothing is built or registered until the shape is chosen, because the invoice, the statement and the VAT return each follow from it.

## Acceptance criteria

- [ ] The legal shape (commission or buy-resell) is decided with the tax adviser and the reasoning recorded under Outcome, with the adviser's memo attached as evidence
- [ ] Where VAT is due is written down per case: domestic sale, EU distance sale under OSS, stock stored in another member state, and the invoice sequence per case
- [ ] The supplier payout is characterised (purchase price against a self-billing invoice, or commission settlement) so SEEN-132 can build it
- [ ] The list of registrations the shape requires is handed to SEEN-126 with owners and lead times

## Depends on

- [SEEN-005](SEEN-005-review-partao-contract-and-draft-dpa-and-amazon.md): Review Partao contract and draft DPA and Amazon data statement

## Blocks

- [SEEN-125](SEEN-125-open-seen-s-own-seller-accounts-on-bol-and.md): Open Seen's own seller accounts on Bol and Amazon EU and obtain the brand authorisation pack
- [SEEN-126](SEEN-126-register-the-storefront-entity-for-epr-gpsr.md): Register the storefront entity for EPR, GPSR responsible-person data and product liability cover
- [SEEN-127](SEEN-127-write-the-storefront-agreement-supply-terms-the.md): Write the storefront agreement: supply terms, the statement, the payout schedule, returns and the fee
- [SEEN-128](SEEN-128-connection-ownership-and-storefront-mode-on-the.md): Connection ownership and storefront mode on the trade record
- [SEEN-131](SEEN-131-consumer-invoices-with-vat-by-destination-and.md): Consumer invoices with VAT by destination and the OSS return

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged.
