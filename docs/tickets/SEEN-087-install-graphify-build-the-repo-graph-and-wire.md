---
id: SEEN-087
title: "Install graphify, build the repo graph and wire it into both assistants"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086]
status: todo
---
# SEEN-087: Install graphify, build the repo graph and wire it into both assistants

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Install graphify (uv tool install graphifyy), register it for Claude Code and Codex, build the graph of the repository, docs and SQL schema into graphify-out/, install the git hook so the graph rebuilds on commit and branch switch, run python -m graphify.serve graphify-out/graph.json as an MCP server in both assistants, and add graphify extract to CI so GRAPH_REPORT.md is produced on every run. Add harness graph <ticket> <impact|path|explain|prs> in harness/run.py as a thin wrapper that writes the answer into the journal. The decision that matters: graphify-out/graph.json is committed so a fresh clone has context before its first build; code extraction is local and deterministic, and only the docs pass uses a model.

## Acceptance criteria

- [ ] graphify claude install and graphify install --platform codex both succeed and /graphify query works in a Claude Code session on this repository
- [ ] graphify hook install is in place and a commit changing packages/core updates graphify-out/graph.json in the same commit
- [ ] The MCP server exposes query_graph, get_neighbors, shortest_path and get_pr_impact to Claude Code and Codex and a query for the policy gate returns its callers
- [ ] CI runs graphify extract and fails when the graph does not parse; GRAPH_REPORT.md is an artefact of the run
- [ ] harness graph SEEN-087 impact writes the impact set into the journal as a note

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts

## Blocks

- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
