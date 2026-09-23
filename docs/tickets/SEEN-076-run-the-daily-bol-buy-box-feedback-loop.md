---
id: SEEN-076
title: "Run the daily Bol buy-box feedback loop"
epic: E8
epic_name: "Price module"
sprint: 6
sprint_dates: "4 - 15 Jan 2027"
gate: G6
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol]
depends_on: [SEEN-069, SEEN-074]
status: todo
---
# SEEN-076: Run the daily Bol buy-box feedback loop

| | |
|---|---|
| Epic | E8 Price module |
| Sprint | 6 (4 - 15 Jan 2027), gate G6 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol |
| Status | todo |

## Description

Add a daily job in apps/worker that compares buy-box status before and after each Bol price change, computes win rate and margin delta per listing and per reason over the last 14 days, and stores a per-listing recommendation (hold, step down, step up) that propose_price reads for its next proposal. Design decision: the loop only recommends; every move still goes through propose_price, the governor and the gate.

## Acceptance criteria

- [ ] Daily buy-box win rate per listing computed from snapshots and stored
- [ ] A listing that lost the buy box after a move is marked for a step-down recommendation
- [ ] Recommendation is visible on the Price page and used by propose_price in its reasoning
- [ ] Job runs in under 5 minutes for 1,000 listings

## Depends on

- [SEEN-069](SEEN-069-snapshot-competing-offers-from-bol-by-ean-and.md): Snapshot competing offers from Bol by EAN and eBay by GTIN
- [SEEN-074](SEEN-074-add-propose-price-and-apply-price-tools-with.md): Add propose_price and apply_price tools with buy-box tracking

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Snapshot competing offers, model net margin per marketplace and move prices inside bands through a governor, counting headroom captured from ingested orders.
