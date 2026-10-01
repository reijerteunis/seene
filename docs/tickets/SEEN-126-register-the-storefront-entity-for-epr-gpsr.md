---
id: SEEN-126
title: "Register the storefront entity for EPR, GPSR responsible-person data and product liability cover"
epic: E11
epic_name: "Seller of record"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 2
executor: human
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-124]
status: todo
---
# SEEN-126: Register the storefront entity for EPR, GPSR responsible-person data and product liability cover

| | |
|---|---|
| Epic | E11 Seller of record |
| Sprint | 4 (23 Nov - 4 Dec 2026), gate G4 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

The seller of record carries the obligations a brand wanted to avoid: extended producer responsibility registrations where the seller places packaging, electrical goods or batteries on a market (LUCID in Germany, the French schemes, and the countries the pilot ships to), the General Product Safety Regulation's manufacturer and responsible-person data on every listing since 13 December 2024, the packaging regulation that applies from 12 August 2026, the fourteen-day right of withdrawal and the two-year legal guarantee toward consumers, and product liability cover for goods Seen sells but does not make. Register what the chosen shape requires, insure the rest, and write the data the brand must supply per product into the storefront agreement and the catalogue schema (SEEN-129). The decision that matters: Seen takes the obligations it can carry with registrations and insurance, and passes the ones only a manufacturer can carry (safety documentation, the responsible person) back to the brand in the agreement.

## Acceptance criteria

- [ ] EPR registrations exist for the pilot countries and categories, with numbers recorded where the marketplaces ask for them
- [ ] The GPSR data set per product (manufacturer, EU responsible person, warnings, identifiers) is defined and required by the storefront agreement and the catalogue schema
- [ ] Product liability insurance for goods sold as seller of record is in place, with the policy reference recorded
- [ ] The consumer obligations Seen carries (withdrawal, guarantee, invoicing) are written into the storefront terms and the Serve policies

## Depends on

- [SEEN-124](SEEN-124-decide-the-storefront-legal-model-with-the-tax.md): Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due

## Blocks

- [SEEN-127](SEEN-127-write-the-storefront-agreement-supply-terms-the.md): Write the storefront agreement: supply terms, the statement, the payout schedule, returns and the fee
- [SEEN-129](SEEN-129-list-a-supplier-s-catalogue-under-seen-s.md): List a supplier's catalogue under Seen's accounts with brand mapping and GPSR data

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged.
