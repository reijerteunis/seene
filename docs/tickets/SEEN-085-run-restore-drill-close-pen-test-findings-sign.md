---
id: SEEN-085
title: "Run restore drill, close pen-test findings, sign metrics pack"
epic: E9
epic_name: "Grow, retailer view, hardening and day-120 metrics"
sprint: 7
sprint_dates: "18 - 29 Jan 2027"
gate: G7
estimate: 2
executor: human
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-081, SEEN-082, SEEN-084]
status: todo
---
# SEEN-085: Run restore drill, close pen-test findings, sign metrics pack

| | |
|---|---|
| Epic | E9 Grow, retailer view, hardening and day-120 metrics |
| Sprint | 7 (18 - 29 Jan 2027), gate G7 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Execute the restore drill from SEEN-082 on the production backup, review the penetration test report and close every finding, then review the day-120 metrics pack for the seed narrative and sign it off with the measured figures. The measured figures are filed as they are, including any marketplace whose pool came in under the plan.

## Acceptance criteria

- [ ] Restore drill executed on the production backup with the timing recorded
- [ ] Every pen test finding closed or accepted in writing
- [ ] Day-120 metrics pack exported as CSV and filed with the G7 gate note by 29 January

## Depends on

- [SEEN-081](SEEN-081-load-test-ingest-on-50-tenants-and-run-rate.md): Load test ingest on 50 tenants and run rate-limit chaos
- [SEEN-082](SEEN-082-run-rls-penetration-tests-and-the-restore-drill.md): Run RLS penetration tests and the restore drill
- [SEEN-084](SEEN-084-build-the-day-120-metrics-dashboard-and-csv.md): Build the day-120 metrics dashboard and CSV export

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Read ad reports into margin, give retailers a scoped read-only view, pass load, security and restore drills, and produce the day-120 metrics pack.
