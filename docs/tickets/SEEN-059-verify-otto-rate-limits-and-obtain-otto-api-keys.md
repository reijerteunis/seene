---
id: SEEN-059
title: "Verify Otto rate limits and obtain Otto API keys"
epic: E1
epic_name: "Connectors and ingest"
sprint: 5
sprint_dates: "7 - 18 Dec 2026"
gate: G5
estimate: 1
executor: human
changes_agent_action: false
marketplaces: [otto]
depends_on: [SEEN-009]
status: todo
---
# SEEN-059: Verify Otto rate limits and obtain Otto API keys

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 5 (7 - 18 Dec 2026), gate G5 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | otto |
| Status | todo |

## Description

Obtain Otto Market API credentials from a pilot, record the rate limits per endpoint and the token flow, and confirm that the receipts endpoint returns settlement detail and that the messaging endpoints are enabled for the account, so the Otto connector in packages/connectors/otto is built against verified numbers. The decision that matters: if messaging is not enabled for the account, Otto correspondence runs through the forwarded mailbox.

## Acceptance criteria

- [ ] Otto credentials stored in the secrets provider (.env.local in development, Secret Manager after go-live) for one pilot connection
- [ ] Rate limits and token lifetime recorded in packages/connectors/otto/README.md
- [ ] A test call to orders and receipts returns HTTP 200

## Depends on

- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access

## Blocks

- [SEEN-060](SEEN-060-build-the-otto-connector-for-orders-returns.md): Build the Otto connector for orders, returns, receipts and messages

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
