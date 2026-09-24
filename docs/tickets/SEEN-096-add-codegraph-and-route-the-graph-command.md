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
status: done
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
| Status | done |

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

- [x] codegraph_explore answers a question about a symbol's callers in one MCP call in both Claude Code and Codex
- [x] The index updates within five seconds of a file save, with no git hook involved
- [x] harness graph <ticket> impact and explain route to codegraph and write its answer into the journal
- [x] .codegraph/ is gitignored and doctor is quiet about it

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

## Outcome

codegraph 1.6.0 is installed, wired into both assistants, and answering. `harness graph <ticket>
impact --about state_for` returns twenty affected symbols with file and line in 227 milliseconds,
recorded at record 17; `explain` at record 18; `prs` still goes to graphify, recorded at record 19 with
its graph hash. codegraph answers about symbols, graphify about files, commits and pull requests, and
the record says which one spoke.

**The assumption the ticket got wrong.** It said the index updates within five seconds of a save with
no git hook involved, and took the watcher for granted. There is no standing daemon. With no
`codegraph serve --mcp` process running, five saves went unindexed for fifteen seconds each; with one
running, the same five indexed in 0.43, 0.10, 0.10, 0.10 and 0.10 seconds. The watcher belongs to the
MCP server an assistant starts, so it is a property of the session and not of the repository.

That is why `harness graph` syncs before every codegraph query, 55 milliseconds on 75 files, and
records `synced` in the note. A shell command cannot assume an assistant was here recently. The
criterion is met while a session is attached, which is when it matters, and the harness closes the gap
for when one is not. Measured at record 13.

**`.codegraph/` ignores itself**, shipping a `.gitignore` that excludes everything but that file, so
this repository's own `.gitignore` gained nothing and doctor is quiet. The next reader who looks for
the line will not find it, which is why it is written here.

**Two things done to the founder's machine, on the record.** Telemetry was turned off before anything
was indexed; it ships on. The install wrote to `~/.claude.json`, `~/.claude/settings.json`,
`~/.claude/CLAUDE.md`, `~/.codex/config.toml` and `~/.codex/AGENTS.md`, adding the MCP server, an
`mcp__codegraph__*` permission entry, and a CodeGraph section between marker comments in both sets of
global instructions. A tool that edits a user's global instructions should be seen doing it.

This ticket parked twice, once behind SEEN-100 and once behind SEEN-101, both times because the gate
judging it was wrong rather than the record being judged. Its clarify record, untouched since
23 September, went from 0.46 to 0.79 on those two fixes alone.
