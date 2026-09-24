---
id: SEEN-098
title: "Add repowise and carry its risk answer into the gate"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086, SEEN-088]
status: doing
---
# SEEN-098: Add repowise and carry its risk answer into the gate

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |

## Description

Install Repowise (`pip install repowise`, `repowise init --no-prose -y`,
`repowise agents add --target=claude-code` plus the Codex `mcp_servers` entry) so `get_risk`,
`get_change_risk`, `get_health`, `get_dead_code` and `get_why` are available at clarify, solution and
review. Route `harness graph <ticket> why`, `health` and `risk` to it, and carry its change-risk answer
into the state `harness decide risk` is judged on, so a gate decision reads evidence rather than
impressions. Add its zero-LLM PR bot to pull requests.

`repowise serve` runs on demand at those three stages, with no git hook: its hooks are optional by its
own documentation, and graphify's post-commit hook was removed on 24 September after breaking seven git
operations. Its local index is gitignored for the same reason CodeGraph's is.

## Acceptance criteria

- [ ] repowise get_change_risk on a diff touching packages/core returns a risk and a test gap
- [ ] harness graph <ticket> why, health and risk route to repowise and write the answer into the journal
- [ ] harness decide risk reads the change-risk answer as part of its state, evidenced by the decision record
- [ ] The PR bot comments on a pull request with no LLM call
- [ ] The local index is gitignored and doctor is quiet about it

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts
- [SEEN-088](SEEN-088-integrate-jev-ai-typed-decisions-into-the.md): Integrate Jev AI typed decisions into the harness gates

## Blocks

- none

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- The baseline captured before any of these tools existed: `docs/harness/reports/context-tools-baseline.json`, ten delivered tickets, 27 points, 40,581 output tokens and 18.5 tool calls per point.
- Split out of SEEN-096 on 24 September 2026: one clarify record covering two tool installations, the routing, the budget rules and a five-ticket measurement scored 0.67, 0.68 and 0.62, while the same question asked about one tool scored 0.81.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
