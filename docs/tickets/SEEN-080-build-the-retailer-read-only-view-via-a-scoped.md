---
id: SEEN-080
title: "Build the retailer read-only view via a scoped link"
epic: E9
epic_name: "Grow, retailer view, hardening and day-120 metrics"
sprint: 7
sprint_dates: "18 - 29 Jan 2027"
gate: G7
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay, kaufland, otto]
depends_on: [SEEN-046]
status: todo
---
# SEEN-080: Build the retailer read-only view via a scoped link

| | |
|---|---|
| Epic | E9 Grow, retailer view, hardening and day-120 metrics |
| Sprint | 7 (18 - 29 Jan 2027), gate G7 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay, kaufland, otto |
| Status | todo |

## Description

Add a retailer view in apps/web: a tenant generates a scoped, expiring link for one marketplace so that marketplace's account manager sees the open claims, their evidence and status for that tenant only, with no login and no write access. Implemented with a signed token that maps to an RLS policy restricted to (tenant, marketplace, claims and evidence).

## Acceptance criteria

- [ ] A link scoped to Bol shows only Bol claims of that tenant and returns HTTP 403 for any other data
- [ ] Links expire after 30 days and can be revoked from the inbox
- [ ] Every access is logged with the link id and IP address in audit_events
- [ ] Evidence downloads through the link are read-only signed URLs valid for 10 minutes

## Depends on

- [SEEN-046](SEEN-046-build-customer-facing-findings-and-claims-views.md): Build customer-facing findings and claims views

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Read ad reports into margin, give retailers a scoped read-only view, pass load, security and restore drills, and produce the day-120 metrics pack.
