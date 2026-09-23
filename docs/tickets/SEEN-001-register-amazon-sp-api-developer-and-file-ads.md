---
id: SEEN-001
title: "Register Amazon SP-API developer and file Ads API application"
epic: E0
epic_name: "Foundations and registrations"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: human
changes_agent_action: false
marketplaces: [amazon]
depends_on: []
status: todo
---
# SEEN-001: Register Amazon SP-API developer and file Ads API application

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | amazon |
| Status | todo |

## Description

Register a public SP-API developer application in Seller Central on day 0 and request the Finance and Accounting, Product Listing, Pricing and Buyer Communication roles, then file the Amazon Ads API application the same day. Record the application ids, the LWA client id and the expected approval lead time in the ops runbook so the connector work in packages/connectors/amazon runs on sandbox credentials until approval. The decision that matters: every role is filed on day 0 because approval takes weeks and Sprint 2 runs on eBay and Bol if Amazon is late.

## Acceptance criteria

- [ ] SP-API developer profile submitted with all four roles requested and the submission date recorded in the runbook
- [ ] Amazon Ads API application submitted and its case id recorded
- [ ] LWA client id and secret stored in Secret Manager under the friendly brand's Amazon connection
- [ ] Approval lead time from Amazon's first response noted in the plan risks section

## Depends on

- none

## Blocks

- [SEEN-013](SEEN-013-build-amazon-sp-api-connector-for-orders.md): Build Amazon SP-API connector for orders, reports and Finances
- [SEEN-077](SEEN-077-read-ad-reports-from-amazon-ads-bol-advertising.md): Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
