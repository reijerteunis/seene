---
id: SEEN-084
title: "Build the day-120 metrics dashboard and CSV export"
epic: E9
epic_name: "Grow, retailer view, hardening and day-120 metrics"
sprint: 7
sprint_dates: "18 - 29 Jan 2027"
gate: G7
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-034, SEEN-040, SEEN-045, SEEN-065]
status: todo
---
# SEEN-084: Build the day-120 metrics dashboard and CSV export

| | |
|---|---|
| Epic | E9 Grow, retailer view, hardening and day-120 metrics |
| Sprint | 7 (18 - 29 Jan 2027), gate G7 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Add the metrics pack to the ops console in apps/web: brands live, euros identified, filed and credited per marketplace, module MRR from tenant_modules and invoices, autonomy rate per action type from agent_actions, gross margin per tenant (module and share revenue minus agent cost and infrastructure cost from the cost logs) and agent cost per claim, as a dashboard with a period selector and GET /ops/metrics.csv in apps/api. Design decision: every metric is a SQL view over the trade record, so the CSV and the dashboard cannot diverge.

## Acceptance criteria

- [ ] Dashboard shows the eight metrics with a period selector and each metric links to its SQL view
- [ ] CSV export contains the same figures as the dashboard for the period
- [ ] Gross margin per tenant uses agent_runs cost and per-tenant infrastructure cost from Cloud Logging
- [ ] Autonomy rate per action type equals autonomous decisions over all decisions in agent_actions

## Depends on

- [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md): Build agent runtime v1 with the fixed tool set and cost accounting
- [SEEN-040](SEEN-040-issue-invoices-with-recovery-share-lines-from.md): Issue invoices with recovery-share lines from credited claims only
- [SEEN-045](SEEN-045-add-module-switches-per-tenant-with-scheduling.md): Add module switches per tenant with scheduling and billing hooks
- [SEEN-065](SEEN-065-implement-the-trust-ramp-with-autonomy-per.md): Implement the trust ramp with autonomy per action type

## Blocks

- [SEEN-085](SEEN-085-run-restore-drill-close-pen-test-findings-sign.md): Run restore drill, close pen-test findings, sign metrics pack

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Read ad reports into margin, give retailers a scoped read-only view, pass load, security and restore drills, and produce the day-120 metrics pack.
