---
id: SEEN-104
title: "Cap a session at one slice: the slice plan, the budget and the handoff pack"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-099, SEEN-103, SEEN-091]
status: doing
---
# SEEN-104: Cap a session at one slice: the slice plan, the budget and the handoff pack

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

The baseline in docs/harness/reports/context-tools-baseline.json says 40,600 output tokens and 18.5 tool calls per point, so a three-point ticket worked start to receipt in one session is 120,000 output tokens and a context that compacts at least once, and compaction is where evidence quietly becomes summary. Make the slice the unit of context and keep the ticket the unit of delivery (one branch, one pull request, one receipt). harness/thresholds.toml gains a [session] section: max_points_per_slice = 2, max_slices_per_ticket = 4, output_token_budget = 60000, handoff_token_limit = 2000. The solution template gains slices (name, points, files, the RED each must demonstrate); advance from solution refuses a slice above the cap, a plan above the slice cap (the ticket is too big and is split, as SEEN-089 and SEEN-096 were) and a code-mode record without a plan. harness handoff <ticket> writes .harness-drafts/<ticket>-handoff.md (stage, current slice, criteria restated as checks, files, decisions taken, graph answers already recorded, the next command) and appends a handoff record carrying the pack's sha256; harness status --brief prints the pack; harness budget <ticket> reads the current session's output tokens and tool calls from the session logs the way cost.py already does and reports them against the budget. The tdd gate records the session id of every check so the KPI can count sessions per ticket and tokens per slice. The skill then says: PRD and architecture are read once, at clarify; every later session starts from the handoff pack; one slice per session, then handoff and a fresh session. The decision that matters: a fresh context per slice is cheaper than a compacted one, and the handoff pack is the only thing that crosses the boundary.

## Acceptance criteria

- [ ] advance from solution refuses a slice over max_points_per_slice and a plan over max_slices_per_ticket, naming the slice, and refuses a code-mode solution record without a slice plan
- [ ] harness handoff writes the pack under handoff_token_limit, appends a handoff record carrying the pack's sha256, and status --brief prints it; a test proves the pack carries no environment value
- [ ] harness budget reports the current session's output tokens and tool calls against the budget, null rather than zero where no session log exists, and names the slice boundary as the next stop when over budget
- [ ] kpi.json carries slices, sessions per ticket and output tokens per slice, and harness report --sprint shows tokens per slice beside tokens per point
- [ ] docs/harness/skill.md says one slice per session and that later sessions start from the handoff pack, and sync regenerates both copies

## Depends on

- [SEEN-099](SEEN-099-set-the-context-budget-and-measure-the-tools.md): Set the context budget and measure what the tools changed
- [SEEN-103](SEEN-103-declare-non-code-mode-at-the-solution-stage.md): Declare non-code mode at the solution stage, not after it
- [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md): Collect harness KPIs per ticket and produce weekly and sprint reports

## Blocks

- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants
- [SEEN-106](SEEN-106-enforce-the-harness-with-hooks-in-both.md): Enforce the harness with hooks in both assistants, generated from one source

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
