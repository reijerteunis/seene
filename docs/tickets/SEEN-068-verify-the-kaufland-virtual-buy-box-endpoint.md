---
id: SEEN-068
title: "Verify the Kaufland virtual buy box endpoint"
epic: E8
epic_name: "Price module"
sprint: 6
sprint_dates: "4 - 15 Jan 2027"
gate: G6
estimate: 1
executor: human
changes_agent_action: false
marketplaces: [kaufland]
depends_on: [SEEN-054]
status: todo
---
# SEEN-068: Verify the Kaufland virtual buy box endpoint

| | |
|---|---|
| Epic | E8 Price module |
| Sprint | 6 (4 - 15 Jan 2027), gate G6 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | kaufland |
| Status | todo |

## Description

Confirm whether the Kaufland Seller API exposes the virtual buy box (which offer is shown on the product page) and competing offers, record the endpoint, fields and rate limit, and decide whether Kaufland joins the Price module in Sprint 6 or after day 120. The decision that matters: Kaufland pricing is scoped out of Sprint 6 if the endpoint is absent, with no manual workaround.

## Acceptance criteria

- [ ] Endpoint and fields recorded in packages/connectors/kaufland/README.md or a documented absence
- [ ] Decision recorded in the Sprint 6 plan note
- [ ] If present, a manual call returns buy box data for a pilot's product

## Depends on

- [SEEN-054](SEEN-054-build-the-kaufland-connector-with-tickets-as.md): Build the Kaufland connector with tickets as the claims rail

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Snapshot competing offers, model net margin per marketplace and move prices inside bands through a governor, counting headroom captured from ingested orders.
