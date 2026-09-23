---
id: SEEN-036
title: "Create the eval set of 30 real findings with expected drafts"
epic: E4
epic_name: "Agent runtime, policy gate, approvals and audit log"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-034]
status: todo
---
# SEEN-036: Create the eval set of 30 real findings with expected drafts

| | |
|---|---|
| Epic | E4 Agent runtime, policy gate, approvals and audit log |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Assemble packages/agent/evals with 30 anonymised real findings from the Sprint 1 audits across the eight rules and three marketplaces, each with the expected claim rule, expected evidence refs and a reference draft, and a runner that scores the runtime on rule choice, evidence completeness and draft similarity and prints cost per finding. The set gates prompt changes: no prompt merges with a lower score.

## Acceptance criteria

- [ ] 30 eval cases exist with at least 3 per rule and cover Bol, Amazon and eBay
- [ ] pnpm eval prints rule accuracy, evidence recall and mean cost per finding in EUR
- [ ] Baseline run scores at least 90% rule accuracy and 90% evidence recall
- [ ] CI fails a pull request that changes prompts when rule accuracy drops below the baseline

## Depends on

- [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md): Build agent runtime v1 with the fixed tool set and cost accounting

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Run every agent action through one policy gate with caps, reversibility and a trust ramp, approved from the inbox and written to an append-only audit log before the side effect.
