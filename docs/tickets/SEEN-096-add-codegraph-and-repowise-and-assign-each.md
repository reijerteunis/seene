---
id: SEEN-096
title: "Add codegraph and repowise and assign each context tool its stage"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086, SEEN-087]
status: doing
---
# SEEN-096: Add codegraph and repowise and assign each context tool its stage

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |

## Description

Install CodeGraph (npm i -g @colbymchenry/codegraph, codegraph install, codegraph init) with its auto-sync watcher so codegraph_explore, codegraph node, callers, callees and impact are available in Claude Code and Codex during implementation, and Repowise (pip install repowise, repowise init --no-prose -y, repowise agents add --target=claude-code plus the Codex mcp_servers entry, repowise serve on the post-commit hook) so get_risk, get_change_risk, get_health, get_dead_code and get_why are available at clarify, solution and review, with its zero-LLM PR bot on every pull request. Route the harness graph command: impact goes to codegraph impact plus repowise get_change_risk, explain to codegraph node, why to repowise get_why, health to repowise get_health, map to graphify; write the context budget rules into policy.toml (one tool call per question, narrow codegraph_explore queries, no repository-wide reads). Measure the effect: tool calls and tokens per point on the first five tickets with the tools against the harness baseline. Design decision: three graph tools with one role each, not three tools for the same question.

## Acceptance criteria

- [ ] codegraph_explore answers a question about the policy gate's callers in one MCP call in both Claude Code and Codex, and the .codegraph index updates within 5 seconds of a file save
- [ ] repowise get_change_risk on a diff touching packages/core returns a risk and test-gap answer, and the repowise PR bot comments on a test pull request without any LLM call
- [ ] harness graph SEEN-096 impact writes both the codegraph blast radius and the repowise change risk into the journal, and harness decide risk reads them as state
- [ ] policy.toml carries the context budget rules and the skill text names which tool to ask at each stage
- [ ] The KPI report for the first five harness tickets shows tool calls and tokens per point against the baseline recorded before the tools were installed

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts
- [SEEN-087](SEEN-087-install-graphify-build-the-repo-graph-and-wire.md): Install graphify, build the repo graph and wire it into both assistants

## Blocks

- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
