---
id: SEEN-079
title: "Propose campaign budgets through the gate, no autonomous creation"
epic: E9
epic_name: "Grow, retailer view, hardening and day-120 metrics"
sprint: 7
sprint_dates: "18 - 29 Jan 2027"
gate: G7
estimate: 3
executor: claude-code
changes_agent_action: true
marketplaces: [amazon, bol, ebay]
depends_on: [SEEN-033, SEEN-034, SEEN-077]
status: todo
---
# SEEN-079: Propose campaign budgets through the gate, no autonomous creation

| | |
|---|---|
| Epic | E9 Grow, retailer view, hardening and day-120 metrics |
| Sprint | 7 (18 - 29 Jan 2027), gate G7 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | yes: goes through the policy gate, see PRD section 8 (FR-19 to FR-27) |
| Marketplaces | amazon, bol, ebay |
| Status | todo |

## Description

Add propose_campaign_budget to packages/agent with action type campaign_budget, reversible true and euro impact of the budget delta; the gate mode for this action type is fixed to approval in the MVP and no tool creates campaigns. Applying an approved budget change goes through the marketplace ads APIs and is logged like every other action.

## Acceptance criteria

- [ ] propose_campaign_budget always returns decision approval even for a tenant with autonomous mode on other action types
- [ ] An approved budget change is applied through the ads API and recorded in audit_events
- [ ] No tool in packages/agent can create a campaign, checked by a test over the tool registry

## Depends on

- [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md): Implement policy gate v1 with caps and reversibility
- [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md): Build agent runtime v1 with the fixed tool set and cost accounting
- [SEEN-077](SEEN-077-read-ad-reports-from-amazon-ads-bol-advertising.md): Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Read ad reports into margin, give retailers a scoped read-only view, pass load, security and restore drills, and produce the day-120 metrics pack.
