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
status: done
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
| Status | done |

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

- [x] repowise get_change_risk on a diff touching packages/core returns a risk and a test gap
- [x] harness graph <ticket> why, health and risk route to repowise and write the answer into the journal
- [x] harness decide risk reads the change-risk answer as part of its state, evidenced by the decision record
- [x] The PR bot is handed to a human decision, because it is a GitHub App authorised on a private repository that publishes a public page per pull request: SEEN-102
- [x] The local index is gitignored and doctor is quiet about it

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts
- [SEEN-088](SEEN-088-integrate-jev-ai-typed-decisions-into-the.md): Integrate Jev AI typed decisions into the harness gates

## Blocks

- [SEEN-102](SEEN-102-decide-on-the-repowise-pr-bot.md): Decide on the repowise PR bot for a private repository

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- The baseline captured before any of these tools existed: `docs/harness/reports/context-tools-baseline.json`, ten delivered tickets, 27 points, 40,581 output tokens and 18.5 tool calls per point.
- Split out of SEEN-096 on 24 September 2026: one clarify record covering two tool installations, the routing, the budget rules and a five-ticket measurement scored 0.67, 0.68 and 0.62, while the same question asked about one tool scored 0.81.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.

## Outcome

repowise 0.52.0 is installed, indexed, routed and feeding the risk decision. `harness graph why`,
`health` and `risk` answer from it, recorded at records 9, 10 and 11 against this repository: code
health 7.98 out of 10 with `harness/cli.py` the worst file at 2.5, and the working tree at the 68th
percentile of this repository's own commits. `harness decide risk` now reads that evidence, and the
decision at record 15 came back medium at 0.76 with the change-risk answer in its state.

**Three things installing it established**, at record 3. The five MCP tool names the ticket predicted
are real, among ten the server registers. Change risk works with no LLM key and no spend: percentile
against the repository's own commit distribution, plus tests that may break, missing co-changes and a
test to run. And it says when it cannot answer, withholding `missing_tests` rather than reporting an
empty list when coverage analysis is unavailable, which is the reason to trust the rest of it.

**It installed a post-commit hook without being asked.** This epic decided against git hooks on
24 September after graphify's broke seven git operations in a day, and the clarify record said so
before `init` ran. The hook was removed and `repowise doctor` confirms it is gone.

**An elided answer is not an empty one.** Past some payload size repowise elides the blast radius and
leaves a marker; 23 changed files did it here. Read naively that is an empty test gap, which is the
silent absence `harness/risk.py` exists to refuse, so the marker is carried and the fields stay null.
Two defects in that message, a doubled file count and a repeated expand instruction, were found by
reading real output rather than by reading the code.

**What is committed and what is not.** `.mcp.json` carries the repowise server, with the absolute path
repowise wrote removed: `repowise mcp` defaults to the current directory, and a path from one machine
is a broken path on the next. `.repowise/`, `.codex/` and the two `.vscode/` files are gitignored,
because they hold this machine's absolute paths and an index rebuilt from the tree.

**The PR bot was not installed and is not mine to install.** It is a GitHub App authorised on the
repository by its owner, it reads the whole private tree, and it publishes a public page per pull
request. That is a disclosure decision for Ruud, so it moved to SEEN-102 with both questions written
down. Recorded at record 4.

Telemetry was disabled before anything was indexed. The wiki was rendered from structure with
`--no-prose`, so no key was configured and nothing was spent, and `--no-claude-md --no-agents` kept it
away from this project's hand-written `CLAUDE.md`, which it generates over by default.
