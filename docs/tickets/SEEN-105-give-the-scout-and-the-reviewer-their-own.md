---
id: SEEN-105
title: "Give the scout and the reviewer their own context as subagents in both assistants"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-104, SEEN-092, SEEN-098]
status: doing
---
# SEEN-105: Give the scout and the reviewer their own context as subagents in both assistants

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

Two readers fill a session: the research at clarify and solution (graph answers, PRD sections, the files a change touches) and the review, which has to read the diff, the journal and the criteria. Both move into subagents with a context window of their own that return a bounded answer to the session working the ticket. harness/agents/ holds one source per agent: seen-scout (read-only tools plus the three graph MCP servers; returns a brief of at most 400 words with file paths, the answers it found and the questions it could not answer), seen-reviewer (fresh context, no Edit or Write; reads the diff, the journal and the criteria and returns findings in the review template's JSON with file, line, claim and failure scenario), and seen-implementer (optional: one slice per invocation, the handoff pack as its task, Edit, Write and the test runner). harness sync generates .claude/agents/<name>.md (name, description, tools, model, permissionMode, omitClaudeMd) and .codex/agents/<name>.toml (name, description, developer_instructions, sandbox_mode, model) from that source, and doctor reports drift the way it does for the skill copies. In Claude Code the skill invokes them by name (@agent-seen-reviewer; the scout can also run as a skill with context: fork and agent: Explore); in Codex the skill says to spawn them explicitly, because Codex spawns a subagent only when asked, and [agents] max_depth stays at 1. The review record carries the reviewer's session id and the review gate refuses a review from the implementer's own session. The decision that matters: a subagent is a context boundary, not independence by itself; the review by the other assistant stays required for tickets that change an agent action or touch billing.

## Acceptance criteria

- [ ] harness sync writes .claude/agents/seen-scout.md, seen-reviewer.md and .codex/agents/seen-scout.toml, seen-reviewer.toml from harness/agents/, and doctor reports a copy edited by hand
- [ ] The scout returns a brief of at most 400 words for a Sprint 0 ticket and harness note records it with the session id it came from; a brief over the limit is refused with the count
- [ ] The review gate refuses a review record whose reviewer session id equals the implementer's, and accepts one from a subagent or from the other assistant
- [ ] Tickets that change an agent action or touch billing still require a review from the other assistant, enforced at the review gate and proven with a fixture
- [ ] One ticket worked with the scout and the reviewer shows the main session's output tokens per point below the SEEN-099 baseline, recorded in the sprint report

## Depends on

- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers
- [SEEN-098](SEEN-098-add-repowise-and-carry-risk-into-the-gate.md): Add repowise and carry its risk answer into the gate

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
