---
id: SEEN-051
title: "Add propose_listing_fix and apply_listing_fix tools with diff"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 5
executor: claude-code
changes_agent_action: true
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-033, SEEN-034, SEEN-045, SEEN-050]
status: todo
---
# SEEN-051: Add propose_listing_fix and apply_listing_fix tools with diff

| | |
|---|---|
| Epic | E7 Modules: Reconcile, Comply, Serve |
| Sprint | 4 (23 Nov - 4 Dec 2026), gate G4 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | yes: goes through the policy gate, see PRD section 8 (FR-19 to FR-27) |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Add the two tools to packages/agent: propose_listing_fix produces a field-level diff for a listing defect and apply_listing_fix sends the diff through the marketplace write adapter; both declare action type listing_fix, reversible true for content and false for anything that removes an offer, and pass the policy gate. A before and after snapshot with hashes is stored on each applied fix.

## Acceptance criteria

- [ ] propose_listing_fix returns a JSON diff with field, before and after for each defect
- [ ] apply_listing_fix is refused by the gate when the diff would set an offer to unavailable
- [ ] Every applied fix stores before and after content hashes and its audit event chain
- [ ] Fixes for a tenant with Comply disabled are refused with reason module_disabled

## Depends on

- [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md): Implement policy gate v1 with caps and reversibility
- [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md): Build agent runtime v1 with the fixed tool set and cost accounting
- [SEEN-045](SEEN-045-add-module-switches-per-tenant-with-scheduling.md): Add module switches per tenant with scheduling and billing hooks
- [SEEN-050](SEEN-050-ingest-listings-with-content-hash-and-drift.md): Ingest listings with content hash and drift detection

## Blocks

- [SEEN-052](SEEN-052-write-listing-content-through-bol-and-ebay-apis.md): Write listing content through Bol and eBay APIs
- [SEEN-053](SEEN-053-write-listing-content-through-amazon-listings.md): Write listing content through Amazon Listings Items and Feeds
- [SEEN-056](SEEN-056-show-comply-defects-and-fix-diffs-in-the-inbox.md): Show Comply defects and fix diffs in the inbox

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
