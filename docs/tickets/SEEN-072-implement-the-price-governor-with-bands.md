---
id: SEEN-072
title: "Implement the price governor with bands, ceilings and cooldowns"
epic: E8
epic_name: "Price module"
sprint: 6
sprint_dates: "4 - 15 Jan 2027"
gate: G6
estimate: 5
executor: claude-code
changes_agent_action: true
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-033, SEEN-071]
status: todo
---
# SEEN-072: Implement the price governor with bands, ceilings and cooldowns

| | |
|---|---|
| Epic | E8 Price module |
| Sprint | 6 (4 - 15 Jan 2027), gate G6 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | yes: goes through the policy gate, see PRD section 8 (FR-19 to FR-27) |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Implement the governor in packages/core/pricing: tenant bands (minimum margin, minimum and maximum price per SKU), a per-marketplace ceiling relative to the brand's own trailing 30-day price (the Amazon Fair Pricing rule, applied everywhere), a cooldown per listing, meaningful increments on Bol (no move below EUR 0.05 or 0.5%), and no moves on Amazon in the MVP until the ceiling governor has run a month on eBay and Bol. It returns allow or refuse with a reason and the gate calls it for every price action.

## Acceptance criteria

- [ ] A move below the minimum margin band returns refuse with reason margin_band
- [ ] A move above the trailing 30-day own price plus the tenant ceiling returns refuse with reason ceiling
- [ ] A second move on the same listing inside the cooldown returns refuse with reason cooldown
- [ ] A move on an Amazon listing returns refuse with reason marketplace_disabled during the MVP
- [ ] A Bol move of EUR 0.02 returns refuse with reason increment

## Depends on

- [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md): Implement policy gate v1 with caps and reversibility
- [SEEN-071](SEEN-071-model-net-margin-per-marketplace-from-cost.md): Model net margin per marketplace from cost layers

## Blocks

- [SEEN-074](SEEN-074-add-propose-price-and-apply-price-tools-with.md): Add propose_price and apply_price tools with buy-box tracking

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Snapshot competing offers, model net margin per marketplace and move prices inside bands through a governor, counting headroom captured from ingested orders.
