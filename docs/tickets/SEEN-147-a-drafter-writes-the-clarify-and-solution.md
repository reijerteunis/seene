---
id: SEEN-147
title: "A drafter writes the clarify and solution records, so the orchestrator holds only the gate answers"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-105, SEEN-112]
status: todo
priority: P1
---
# SEEN-147: A drafter writes the clarify and solution records, so the orchestrator holds only the gate answers

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P1 (SEEN-112's criterion 1 cannot be met while the orchestrator drafts) |

## Description

SEEN-112's loop delegates the slices to `seen-implementer` and the review to `seen-reviewer`, so the orchestrating session was meant to hold the pack, the ticket and the gate answers and nothing else. The second proof run, on SEEN-141 on 3 October 2026, measured what it actually holds: 89,674 output tokens of its own against a 60,000 budget, on a 2-point ticket, with both slices delegated. Most of it was the two records the orchestrator still writes itself: reading what the scout found, writing the clarify record's acceptance checks and decisions, writing the solution's approach, slices and risks, and after a return measuring the amended plan against the history and writing it again. Those are the stages where the reading happens, and the reading is what fills a context.

So the drafting moves into a context of its own, as the slices and the review already have. A new agent, `seen-drafter`, is spawned by the run at clarify and at solution with the ticket file, the template, the scout briefs and the records already in the journal, and writes the draft into `.harness-drafts/`. The orchestrator then runs `advance` and reads the gate's answer, not the draft. A draft that carries an open question still stops the run at `question_open` with every question in one batch, exactly as SEEN-112 settled; the drafter asks nothing of a person itself. After a return to solution the drafter is given the return's reason and the record it returns from, and amends rather than starts again.

The disclosure follows the pattern `--agent` set on checks: `advance --drafted-by seen-drafter` records who wrote the evidence, it is checked against `[agents] names` and nothing further, and it is never typed by a party that did not do the work. The judgement stays where it is. The gate decides with Jev, a person settles what Jev cannot, and the orchestrator remains the one session that runs every writing command, so nothing about who may advance a ticket changes.

The KPI it moves (SEEN-123): output tokens of the orchestrating session per point, as `harness budget` already reports it apart from each subagent's. The decision that matters: a context grows with what it reads, and at clarify and solution the orchestrator was still the one reading.

## Acceptance criteria

- [ ] `seen-drafter` is defined in `harness/agents.py` with its instructions in `harness/agents/seen-drafter.md`, generated into both assistants by `sync` and checked by `doctor` like the other three; it holds Read, Write and the graph tools and holds neither Edit nor Bash
- [ ] `harness guard` refuses a write by the drafter to any path but the current ticket's clarify or solution draft in `.harness-drafts/`, or, if the hook payload cannot tell the drafter from its parent, the solution stage records that and the restriction is held by the instructions and disclosed as such
- [ ] At clarify and at solution, once the draft exists, `harness run` yields a `spawn` of `seen-drafter` with its task text (the ticket file, the template, the briefs and records to read, and after a return the return's reason and the record it returns from) before it yields `advance`, proven by a RED over the fixture walk
- [ ] `advance --drafted-by <agent>` records the disclosure on the advance record, refuses a name not in `[agents] names`, and `run --summary` reports per stage who drafted it
- [ ] A draft carrying an open question still stops the run once at `question_open` with every question in one batch, and the drafter's draft after the answer is the one the gate reads, proven by a RED
- [ ] The orchestrating session's own output tokens at clarify and solution are reported by `harness budget` apart from the drafter's, and the workflow document and the skill say what the drafter does and what it does not decide

## Depends on

- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants
- [SEEN-112](SEEN-112-run-a-ticket-from-clarify-to-merge-in-one-go.md): Run a ticket from clarify to merge in one go, asking only what it cannot decide. `harness run` and `harness/loop.py` exist only on its branch until it merges, so this ticket branches from it as SEEN-141's proof run did

## Blocks

- The next proof run for SEEN-112's criterion 1, which needs an orchestrator that stays inside one slice's budget

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- The evidence: SEEN-141's journal on branch `claude/SEEN-141-hold-a-figure-in-a-tdd-record`, records 1 to 16, and the handoff record 16 carrying the orchestrator's 89,674 output tokens
- The code: `harness/loop.py` and `harness/agents.py` on SEEN-112's branch, and `harness budget`'s reading of `<session>/subagents/agent-*.jsonl` from SEEN-111
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
