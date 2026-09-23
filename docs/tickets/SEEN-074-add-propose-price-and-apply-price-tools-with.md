---
id: SEEN-074
title: "Add propose_price and apply_price tools with buy-box tracking"
epic: E8
epic_name: "Price module"
sprint: 6
sprint_dates: "4 - 15 Jan 2027"
gate: G6
estimate: 5
executor: claude-code
changes_agent_action: true
marketplaces: [bol, ebay]
depends_on: [SEEN-034, SEEN-045, SEEN-069, SEEN-072, SEEN-073]
status: todo
---
# SEEN-074: Add propose_price and apply_price tools with buy-box tracking

| | |
|---|---|
| Epic | E8 Price module |
| Sprint | 6 (4 - 15 Jan 2027), gate G6 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | yes: goes through the policy gate, see PRD section 8 (FR-19 to FR-27) |
| Marketplaces | bol, ebay |
| Status | todo |

## Description

Add propose_price and apply_price to packages/agent with action type price_change, reversible true and euro impact from delta times trailing daily units; apply_price runs the governor and the gate, writes price_changes (from, to, reason, band check result, buy box before) and, after the next snapshot, buy box after. Writes go through the adapters from SEEN-073 and the module switch is checked in the gate.

## Acceptance criteria

- [ ] A proposed move that the governor refuses is never sent to a marketplace
- [ ] price_changes rows record from, to, reason, band check and buy box before for every applied move
- [ ] Buy box after is filled from the next competitor snapshot within 24 hours
- [ ] Live moves applied on the friendly brand's Bol and eBay listings inside bands with the outcome recorded

## Depends on

- [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md): Build agent runtime v1 with the fixed tool set and cost accounting
- [SEEN-045](SEEN-045-add-module-switches-per-tenant-with-scheduling.md): Add module switches per tenant with scheduling and billing hooks
- [SEEN-069](SEEN-069-snapshot-competing-offers-from-bol-by-ean-and.md): Snapshot competing offers from Bol by EAN and eBay by GTIN
- [SEEN-072](SEEN-072-implement-the-price-governor-with-bands.md): Implement the price governor with bands, ceilings and cooldowns
- [SEEN-073](SEEN-073-write-prices-through-bol-offers-and-ebay.md): Write prices through Bol Offers and eBay Inventory offers

## Blocks

- [SEEN-075](SEEN-075-meter-headroom-entries-and-show-the-price-view.md): Meter headroom_entries and show the Price view
- [SEEN-076](SEEN-076-run-the-daily-bol-buy-box-feedback-loop.md): Run the daily Bol buy-box feedback loop

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Snapshot competing offers, model net margin per marketplace and move prices inside bands through a governor, counting headroom captured from ingested orders.
