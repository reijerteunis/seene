---
id: SEEN-077
title: "Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted"
epic: E9
epic_name: "Grow, retailer view, hardening and day-120 metrics"
sprint: 7
sprint_dates: "18 - 29 Jan 2027"
gate: G7
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [amazon, bol, ebay]
depends_on: [SEEN-001, SEEN-002, SEEN-009, SEEN-014]
status: todo
---
# SEEN-077: Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted

| | |
|---|---|
| Epic | E9 Grow, retailer view, hardening and day-120 metrics |
| Sprint | 7 (18 - 29 Jan 2027), gate G7 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | amazon, bol, ebay |
| Status | todo |

## Description

Implement ad report ingest in packages/connectors: Amazon Ads API (sponsored products campaign and advertised product reports), Bol Advertising API (campaign and per-EAN reports) and eBay Marketing API Promoted Listings reports, into an ad_spend view built from settlement_lines of type ad_charge and campaign report rows keyed by campaign, SKU or EAN and day. Uses the Ads approvals from SEEN-001 and the eBay keys from SEEN-002.

## Acceptance criteria

- [ ] Daily ad spend per campaign and SKU ingested from all three ad APIs for the friendly brand
- [ ] Ad spend per marketplace per day reconciles to ad charge settlement lines within 5% over a month
- [ ] Re-ingest produces zero duplicate report rows
- [ ] Ads credentials are read from Secret Manager per connection like every other credential

## Depends on

- [SEEN-001](SEEN-001-register-amazon-sp-api-developer-and-file-ads.md): Register Amazon SP-API developer and file Ads API application
- [SEEN-002](SEEN-002-obtain-ebay-production-keys-and-file.md): Obtain eBay production keys and file Application Growth Check
- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access
- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences

## Blocks

- [SEEN-078](SEEN-078-attribute-ad-cost-into-margin-and-publish-the.md): Attribute ad cost into margin and publish the weekly Grow report
- [SEEN-079](SEEN-079-propose-campaign-budgets-through-the-gate-no.md): Propose campaign budgets through the gate, no autonomous creation

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Read ad reports into margin, give retailers a scoped read-only view, pass load, security and restore drills, and produce the day-120 metrics pack.
