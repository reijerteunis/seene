---
id: SEEN-092
title: "Sync the harness skill to Claude Code and Codex and retire the Seene leftovers"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086, SEEN-087, SEEN-088, SEEN-089, SEEN-090, SEEN-091]
status: done
---
# SEEN-092: Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

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

Write docs/harness/skill.md as the single maintained skill (the steps, commands, actor labels and limits of the Seen harness) and docs/harness/workflow.md from the harness design; make harness sync generate .claude/skills/seen-harness/SKILL.md and .agents/skills/seen-harness/SKILL.md and make doctor fail when the copies drift. Remove .claude/skills/seene-harness, .agents/skills/seene-harness and the .harness-drafts records of the previous project, update .claude/settings.json to the new command allowlist, and add the harness section and the harness ticket list to CLAUDE.md. The decision that matters: one source file for the skill, generated copies that are never edited by hand.

## Acceptance criteria

- [x] harness sync produces both skill copies from docs/harness/skill.md and doctor fails when either copy is edited by hand
- [x] The skill text is installed where both assistants find it, and says the same thing to each: one source file, two generated copies, neither edited by hand
- [x] No file under .claude/skills/seene-harness, .agents/skills/seene-harness or .harness-drafts/SEENE-* remains in the tree (already true: the Seene project was removed in SEEN-086's first commit and the history was rebuilt from a fresh root, so those paths have never existed here)
- [x] CLAUDE.md links docs/harness/workflow.md and lists the harness commands under Working a ticket
- [x] This ticket's own journal is the reference example: all five stages, verify-delivery, and its kpi.json committed, with docs/harness/skill.md pointing a new session at it (amended at clarify on 24 September 2026: a trivial ticket invented to be worked would leave a journal about nothing and a fake ticket in the backlog for ever)

## Outcome

Delivered on 24 September 2026, the last of the ten tickets that built the harness. This journal is
the worked example the skill points a new session at.

**One source, generated copies.** `docs/harness/skill.md` is maintained; `sync` writes
`.claude/skills/seen-harness/SKILL.md`, `.agents/skills/seen-harness/SKILL.md` and, when the directory
already exists, `~/.codex/skills/seen-harness/SKILL.md`, which is where Codex actually reads a skill.
That last path is outside any repository, so it cannot be committed or checked, and the ticket says so
rather than implying coverage it does not have. `doctor` reports drift in the committed copies and
repairs nothing, which is its stance everywhere.

**The skill is short on purpose**: the five stages with their commands, the three rules a session
cannot infer, and what the harness will refuse. A skill read before every ticket competes for the
context the ticket needs, so the reasoning stays in the workflow document.

**Two criteria were already true, and the ticket says why rather than claiming work.** No Seene
leftover exists, because the project was removed in SEEN-086's first commit and the history was
rebuilt from a fresh root. The command allowlist was added by SEEN-090.

**The dry run is this ticket** rather than an invented trivial one, which would have left a journal
about nothing and a fake entry in the backlog for ever.

**And the workflow document now describes what was built.** Ten tickets changed the harness in a day:
the command table gained `coverage`, `lint`, `discard`, `reopen`, `verify-merge`, `report` and `sync`;
the modules, the paths outside the fingerprint and the five conventions the work settled are all in it.
A document describing a harness nobody built is worse than no document.

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts
- [SEEN-087](SEEN-087-install-graphify-build-the-repo-graph-and-wire.md): Install graphify, build the repo graph and wire it into both assistants
- [SEEN-088](SEEN-088-integrate-jev-ai-typed-decisions-into-the.md): Integrate Jev AI typed decisions into the harness gates
- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce TDD and CI quality gates in the harness
- [SEEN-090](SEEN-090-add-harness-security-controls-secrets.md): Add harness security controls: secrets, permissions, injection, supply chain
- [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md): Collect harness KPIs per ticket and produce weekly and sprint reports

## Blocks

- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants
- [SEEN-106](SEEN-106-enforce-the-harness-with-hooks-in-both.md): Enforce the harness with hooks in both assistants, generated from one source
- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
