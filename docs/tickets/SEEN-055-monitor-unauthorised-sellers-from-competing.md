---
id: SEEN-055
title: "Monitor unauthorised sellers from competing offers"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon]
depends_on: [SEEN-010, SEEN-050]
status: todo
---
# SEEN-055: Monitor unauthorised sellers from competing offers

| | |
|---|---|
| Epic | E7 Modules: Reconcile, Comply, Serve |
| Sprint | 4 (23 Nov - 4 Dec 2026), gate G4 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon |
| Status | todo |

## Description

Add a daily job in apps/worker that reads competing offers for each product (Bol Competing Offers by EAN, Amazon Product Pricing item offers) into competitor_snapshots and flags seller ids not on the tenant's authorised seller list as unauthorised, with a report in the customer inbox and an escalate action for the agent. Design decision: the job reuses competitor_snapshots so the Price module in Sprint 6 inherits the same table and rate budget.

## Acceptance criteria

- [ ] Tenant can maintain an authorised seller list per marketplace in the inbox
- [ ] A seller not on the list is flagged within one daily run with the offer price and first seen date
- [ ] Report lists unauthorised offers per marketplace with a count over the last 30 days
- [ ] Snapshot calls stay inside the rate limiter budget from SEEN-010 with zero HTTP 429 in a daily run

## Depends on

- [SEEN-010](SEEN-010-add-per-marketplace-rate-limiting-with-header.md): Add per-marketplace rate limiting with header-driven backoff
- [SEEN-050](SEEN-050-ingest-listings-with-content-hash-and-drift.md): Ingest listings with content hash and drift detection

## Blocks

- [SEEN-069](SEEN-069-snapshot-competing-offers-from-bol-by-ean-and.md): Snapshot competing offers from Bol by EAN and eBay by GTIN

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
