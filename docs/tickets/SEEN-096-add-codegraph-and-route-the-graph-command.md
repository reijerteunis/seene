---
id: SEEN-096
title: "Add codegraph and route the graph command to it"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086, SEEN-087]
status: parked
---
# SEEN-096: Add codegraph and route the graph command to it

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 1 point (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | parked (waiting for SEEN-101) |

## Description

Install CodeGraph (`npm i -g @colbymchenry/codegraph`, `codegraph install`, `codegraph init`) and let it
register itself for Claude Code and Codex, so `codegraph_explore` and its node, callers, callees and
impact questions are available while writing code. Route `harness graph <ticket> impact` and
`explain` to it, writing the answer into the journal as the graphify routing already does.

No git hook. CodeGraph's watcher fires 300 milliseconds after a save and syncs in well under a second,
which is what the five-second criterion is about, and graphify's post-commit hook was removed on
24 September after it broke seven git operations in a day. `.codegraph/` is gitignored, unlike
graphify's committed graph, because it rebuilds itself in seconds while graphify's exists so a fresh
clone has context before its first build.

## Acceptance criteria

- [ ] codegraph_explore answers a question about a symbol's callers in one MCP call in both Claude Code and Codex
- [ ] The index updates within five seconds of a file save, with no git hook involved
- [ ] harness graph <ticket> impact and explain route to codegraph and write its answer into the journal
- [ ] .codegraph/ is gitignored and doctor is quiet about it

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts
- [SEEN-087](SEEN-087-install-graphify-build-the-repo-graph-and-wire.md): Install graphify, build the repo graph and wire it into both assistants
- [SEEN-101](SEEN-101-let-a-journal-survive-its-ticket-being-renamed.md): Let a journal survive its ticket being renamed

## Blocks

- none

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- The baseline captured before any of these tools existed: `docs/harness/reports/context-tools-baseline.json`, ten delivered tickets, 27 points, 40,581 output tokens and 18.5 tool calls per point.
- Split out of SEEN-096 on 24 September 2026: one clarify record covering two tool installations, the routing, the budget rules and a five-ticket measurement scored 0.67, 0.68 and 0.62, while the same question asked about one tool scored 0.81.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
