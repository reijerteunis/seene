---
id: SEEN-078
title: "Attribute ad cost into margin and publish the weekly Grow report"
epic: E9
epic_name: "Grow, retailer view, hardening and day-120 metrics"
sprint: 7
sprint_dates: "18 - 29 Jan 2027"
gate: G7
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [amazon, bol, ebay]
depends_on: [SEEN-045, SEEN-071, SEEN-077]
status: todo
---
# SEEN-078: Attribute ad cost into margin and publish the weekly Grow report

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

Add ad cost attribution per order line (campaign report by SKU and day, falling back to the marketplace's share of spend) into fee_expectations.ad_cost and the net-margin model in packages/core, and a weekly Grow report in apps/api (spend, sales, ACoS, margin after ads per campaign and marketplace, budget proposals) as a PDF and inbox page sent by Postmark to tenants with Grow enabled. Design decision: attribution writes into fee_expectations.ad_cost, so the Reconcile margin and the Grow report share one number per order line.

## Acceptance criteria

- [ ] fee_expectations.ad_cost is populated for order lines with a matching campaign report row
- [ ] Weekly report shows spend, sales, ACoS and margin after ads per campaign and marketplace
- [ ] Report totals equal the ad_spend view for the week to the cent
- [ ] Report sent by Postmark only to tenants with Grow enabled

## Depends on

- [SEEN-045](SEEN-045-add-module-switches-per-tenant-with-scheduling.md): Add module switches per tenant with scheduling and billing hooks
- [SEEN-071](SEEN-071-model-net-margin-per-marketplace-from-cost.md): Model net margin per marketplace from cost layers
- [SEEN-077](SEEN-077-read-ad-reports-from-amazon-ads-bol-advertising.md): Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Read ad reports into margin, give retailers a scoped read-only view, pass load, security and restore drills, and produce the day-120 metrics pack.
