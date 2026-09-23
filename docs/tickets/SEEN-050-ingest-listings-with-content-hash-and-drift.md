---
id: SEEN-050
title: "Ingest listings with content hash and drift detection"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-044, SEEN-049]
status: todo
---
# SEEN-050: Ingest listings with content hash and drift detection

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

Extend the connectors to read listings (Bol Offers and product content, Amazon Listings Items, eBay Inventory items and offers) into listings with a normalised content hash; a daily job in apps/worker compares the hash with the previous snapshot and the last applied fix and records drift (marketplace changed content or a fix was reverted), then runs the spec rules and stores spec issues on the listing. Design decision: the content hash is computed on a normalised subset of fields, so a marketplace reformatting whitespace never counts as drift.

## Acceptance criteria

- [ ] Listings for the friendly brand ingested from Bol, Amazon and eBay with content hash and spec issues
- [ ] A changed title on a marketplace is detected as drift within one daily run
- [ ] Content hash is identical across two ingests of unchanged content
- [ ] Listings page in the customer inbox shows defects by severity per marketplace

## Depends on

- [SEEN-044](SEEN-044-build-the-shopify-admin-graphql-connector-as.md): Build the Shopify Admin GraphQL connector as product and stock truth
- [SEEN-049](SEEN-049-encode-listing-spec-rules-per-marketplace-in.md): Encode listing spec rules per marketplace in core

## Blocks

- [SEEN-051](SEEN-051-add-propose-listing-fix-and-apply-listing-fix.md): Add propose_listing_fix and apply_listing_fix tools with diff
- [SEEN-055](SEEN-055-monitor-unauthorised-sellers-from-competing.md): Monitor unauthorised sellers from competing offers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
