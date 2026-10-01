---
id: SEEN-121
title: "Bake-off: the TypeScript LSP plugin against codegraph, keep one"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-099, SEEN-096]
status: todo
priority: P1
---
# SEEN-121: Bake-off: the TypeScript LSP plugin against codegraph, keep one

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P1 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

Claude Code ships an official TypeScript LSP plugin: go to definition, find references, hover types and diagnostics after every edit, from the language server the editor already trusts, with no index of its own. codegraph answers the same questions from a SQLite graph it keeps beside the tree. Two tools answering one question is the thing SEEN-099's budget forbids, so measure and keep one: five tickets with the LSP plugin in place of codegraph, tokens and tool calls per point against the SEEN-099 baseline and against the codegraph tickets, plus the count of type errors caught before a test ran. The loser is removed from both assistants. Serena (an LSP-based MCP with symbol-level edits) is tried only if both lose; a paid context engine is not tried before this measurement exists. Prompt-cache hygiene lands in the same ticket: CLAUDE.md and the skill are the stable prefix, the SessionStart injection comes last, so the cache survives across sessions. The decision that matters: the cheapest context is the one the language server already has.

## Acceptance criteria

- [ ] The TypeScript LSP plugin is installed for Claude Code and diagnostics after an edit are recorded as a check in the journal
- [ ] Five tickets are worked with the LSP plugin and their tokens, tool calls and type errors caught before a test are compared with the codegraph tickets in harness report --sprint
- [ ] The losing tool is removed from both assistants and from harness graph routing, recorded in the journal of the deciding ticket
- [ ] The SessionStart hook injects after the stable prefix and a session log shows cache reads above cache writes on the second session of a ticket
- [ ] No paid context engine is added, and the workflow document says why

## Depends on

- [SEEN-099](SEEN-099-set-the-context-budget-and-measure-the-tools.md): Set the context budget and measure what the tools changed
- [SEEN-096](SEEN-096-add-codegraph-and-route-the-graph-command.md): Add codegraph and route the graph command to it

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
