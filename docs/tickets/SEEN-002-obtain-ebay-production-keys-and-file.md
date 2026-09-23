---
id: SEEN-002
title: "Obtain eBay production keys and file Application Growth Check"
epic: E0
epic_name: "Foundations and registrations"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: human
changes_agent_action: false
marketplaces: [ebay]
depends_on: []
status: todo
---
# SEEN-002: Obtain eBay production keys and file Application Growth Check

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | ebay |
| Status | todo |

## Description

Create the eBay developer account, generate production keys, configure the OAuth consent flow (RuName) for the Sell Fulfillment, Post-Order, Finances and Inventory scopes and file the Application Growth Check request to lift the default call limits. Complete the consent flow once for the friendly brand and store the user token reference in the secrets provider (.env.local in development, Secret Manager after go-live) for the eBay connector in packages/connectors/ebay.

## Acceptance criteria

- [ ] Production app id, cert id and RuName exist and are stored in the secrets provider (.env.local in development, Secret Manager after go-live)
- [ ] Friendly brand's OAuth user token obtained with the sell.fulfillment, sell.finances and sell.inventory scopes
- [ ] Application Growth Check request filed and its reference recorded in the runbook
- [ ] A manual call to GET /sell/fulfillment/v1/order with the token returns HTTP 200

## Depends on

- none

## Blocks

- [SEEN-012](SEEN-012-build-ebay-connector-for-orders-returns.md): Build eBay connector for orders, returns, transactions and payouts
- [SEEN-077](SEEN-077-read-ad-reports-from-amazon-ads-bol-advertising.md): Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
