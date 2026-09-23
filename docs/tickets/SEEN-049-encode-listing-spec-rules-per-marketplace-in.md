---
id: SEEN-049
title: "Encode listing spec rules per marketplace in core"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-008]
status: todo
---
# SEEN-049: Encode listing spec rules per marketplace in core

| | |
|---|---|
| Epic | E7 Modules: Reconcile, Comply, Serve |
| Sprint | 4 (23 Nov - 4 Dec 2026), gate G4 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Add packages/core/comply with rule sets per marketplace: required attributes per category, image count and size, GPSR responsible person contact, title and bullet limits, and fitment coverage for parts using eBay compatibility (a parts listing must carry a compatibility list with at least one vehicle). Each rule is a pure function over a listing snapshot returning a defect with severity and a proposed fix where one is computable.

## Acceptance criteria

- [ ] Rule sets exist for Bol, Amazon and eBay with unit tests per rule
- [ ] GPSR rule flags a listing without a responsible person contact on every marketplace
- [ ] Fitment rule flags an eBay parts listing with an empty compatibility list
- [ ] Rules run over 1,000 listings in under 5 seconds

## Depends on

- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table

## Blocks

- [SEEN-050](SEEN-050-ingest-listings-with-content-hash-and-drift.md): Ingest listings with content hash and drift detection

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
