---
id: SEEN-128
title: "Connection ownership and storefront mode on the trade record"
epic: E11
epic_name: "Seller of record"
sprint: 7
sprint_dates: "18 - 29 Jan 2027"
gate: G7
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon]
depends_on: [SEEN-009, SEEN-124, SEEN-125]
status: todo
---
# SEEN-128: Connection ownership and storefront mode on the trade record

| | |
|---|---|
| Epic | E11 Seller of record |
| Sprint | 7 (18 - 29 Jan 2027), gate G7 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon |
| Status | todo |

## Description

The trade record assumes the tenant owns the marketplace account. In storefront mode Seen owns it and the brand is the supplier, so the model gains two facts and everything else stays: connections carry owner (brand or seen) and, for owner seen, the supplier tenant each SKU maps to; tenants carry selling_mode per marketplace (direct or storefront). Ingest from a Seen-owned connection attributes orders, shipments, returns and settlement lines to the supplier tenant by the SKU and EAN mapping, with the settlement line kept whole (the marketplace paid Seen) and the supplier share computed later by SEEN-132. RLS is unchanged because rows carry the supplier's tenant_id; Seen's operators see the storefront view through the ops console. Claims are filed by Seen as the seller, from Seen's account, through the same claims rail. The decision that matters: one record, one set of modules, and ownership as a column, so the storefront is a mode of the product, not a second product.

## Acceptance criteria

- [ ] connections carry owner and, for owner seen, a SKU and EAN mapping to supplier tenants; tenants carry selling_mode per marketplace; migration and RLS tests pass
- [ ] Ingest from a Seen-owned connection attributes every row to the supplier tenant by the mapping and refuses a row it cannot map, listing it as an exception
- [ ] The claims rail files from Seen's account for storefront orders, with the actor recorded as Seen
- [ ] The ops console shows the storefront view: Seen's accounts, their suppliers and unmapped rows

## Depends on

- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access
- [SEEN-124](SEEN-124-decide-the-storefront-legal-model-with-the-tax.md): Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due
- [SEEN-125](SEEN-125-open-seen-s-own-seller-accounts-on-bol-and.md): Open Seen's own seller accounts on Bol and Amazon EU and obtain the brand authorisation pack

## Blocks

- [SEEN-129](SEEN-129-list-a-supplier-s-catalogue-under-seen-s.md): List a supplier's catalogue under Seen's accounts with brand mapping and GPSR data
- [SEEN-130](SEEN-130-dropship-flow-a-purchase-order-to-the-supplier.md): Dropship flow: a purchase order to the supplier on every storefront order, shipment and tracking back
- [SEEN-131](SEEN-131-consumer-invoices-with-vat-by-destination-and.md): Consumer invoices with VAT by destination and the OSS return
- [SEEN-132](SEEN-132-supplier-statements-and-payouts-net-proceeds.md): Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through
- [SEEN-133](SEEN-133-returns-withdrawals-and-guarantee-cases-handled.md): Returns, withdrawals and guarantee cases handled as the seller of record

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged.
