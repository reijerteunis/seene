---
id: SEEN-145
title: "Count a review finding once, however the record that carries it names it"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-091, SEEN-107, SEEN-109]
status: doing
priority: P1
---
# SEEN-145: Count a review finding once, however the record that carries it names it

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 1 point (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |

## Description

`kpi.findings` counts a ticket's review findings through `calibration.latest_finding_records`, which keys each finding by its `id`, its claim and its file, most recent record wins, so that a ticket reviewed twice does not count the same finding twice. Claim and file were added by SEEN-109, but the `id` is still part of the key, so the dedupe still rests on a session typing the same identifier in every review record, and nothing asks it to. SEEN-107 showed what happens when it does not: its journal holds two review advances, one carrying nineteen findings as `F1`, `G1`, `H1` and so on, and a later one carrying all twenty-six under `R1-1`, `R2-1` and so on, because the session renamed them for readability between the two. The delivered `kpi.json` reports forty-five findings against a real twenty-six, in a ticket whose profile includes the only high-severity finding recorded so far. The number is wrong in the direction that flatters nobody and misleads everybody: it inflates the finding count of exactly the tickets that were reviewed most. Two candidate shapes, and the solution stage picks one on the evidence rather than this description pre-empting it: count only the review advance that was accepted, on the reading that a returned review's findings are superseded by the record that replaced them, which removes the dependence on `id` entirely and makes the final record the whole picture; or derive identity from what a finding says rather than from what it is called. The first is simpler and puts the burden on the final review record carrying every finding, which SEEN-107's did, but since SEEN-109 a return records findings of its own that a later advance need not repeat, so it has to say what becomes of those; the second keeps working when it does not. The decision that matters: a figure the reports divide on must not rest on a field a session is free to rename, and SEEN-109 reads the same findings to decide what counts as an escape.

## Acceptance criteria

- [ ] kpi.findings counts a finding once when two review advances describe it under different ids, proven with a fixture of two records whose findings differ only in their identifiers
- [ ] SEEN-107's own committed journal reports its real finding total rather than forty-five, proven by a test that reads that journal from docs/harness/history/ rather than a constructed one
- [ ] Every other journal in this repository reports exactly what it reported before, proven over every journal present
- [ ] What the count rests on after this change is written in kpi.findings, and the weekly and sprint reports carry the corrected figure

## Depends on

- [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md): Collect harness KPIs per ticket and produce weekly and sprint reports
- [SEEN-107](SEEN-107-let-jev-settle-what-the-review-can-settle.md): Let Jev settle what the review can settle before a model reads the diff
- [SEEN-109](SEEN-109-calibrate-the-review-triage-and-the-routes-on.md): Calibrate the review triage and the routes on ten tickets before either saves a token

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
