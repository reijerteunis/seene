---
id: SEEN-110
title: "Verify the hooks in a Codex session and close what SEEN-106 declined"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: human
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-106]
status: todo
---
# SEEN-110: Verify the hooks in a Codex session and close what SEEN-106 declined

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | human, then Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

SEEN-106 built the hooks, generated both assistants' copies from one source and proved four of its five criteria with fixtures. Its fifth asked what an interactive Codex session does, and no session in this repository can answer that: `codex doctor` says nothing about hook discovery, and the schemas read out of the codex-cli binary settle the payload shapes while settling nothing about whether Codex loads a project-level `.codex/hooks.json` at all. SEEN-106 was split at record 44 rather than held open on an observation only a person can make, which is the SEEN-089 and SEEN-096 precedent: the id keeps what is proven and the rest opens as a new ticket.

This ticket carries that observation and the two improvements SEEN-106 declined as scope, each of which it declined in writing rather than by omission. The first is the ordering defect SEEN-106's own triage caught: regression check 34 ran against one tree and the triage read another, because the ticket's Outcome was written after the regression and the ticket file is inside the fingerprint. Nothing in the harness refuses that today, and the tdd gate is where it belongs, with its own RED. The second is smaller and is the other half of a finding SEEN-106 fixed only as far as its finding named: `CLAUDE.md` enumerates every harness command and omits `handoff`, `budget`, `route` and `review`.

If the Codex session shows that `/hooks` does not list the harness entries, the generated path moves to whatever that session shows Codex reads, and the move is recorded as a correction rather than the criterion dropped. If it shows Codex takes fewer events than `harness/hooks.json` gives it, `clients` is the one line that changes.

## Acceptance criteria

- [ ] A Codex session in this repository is recorded as a verification in the journal: the codex-cli version, what `/hooks` printed verbatim, and what a guarded edit to `packages/` returned, with the sources of every claim
- [ ] Whether anything reads `.agents/settings.json` is settled from that session, and the file is either confirmed read or removed, with the workflow document's Permissions row corrected either way
- [ ] The tdd gate refuses a regression check whose tree has moved since it ran, naming both fingerprints, proven by a RED that advances a ticket whose regression ran against an earlier tree
- [ ] CLAUDE.md's harness command list names every command `run.py --help` prints, and a test or a doctor check refuses the two lists differing
- [ ] If the session contradicts what SEEN-106 generated, the correction is made and recorded: the hook path if Codex reads another, or the `clients` line if Codex takes fewer events

## Depends on

- [SEEN-106](SEEN-106-enforce-the-harness-with-hooks-in-both.md): Enforce the harness with hooks in both assistants, generated from one source

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- SEEN-106's journal, `docs/harness/history/SEEN-106/`: record 20 for the codex-cli schema evidence, record 24 for the review that returned the ticket, record 37 for the triage that refused it at 0.13 on the criterion this ticket carries, record 42 for the two readings that led to the split
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
