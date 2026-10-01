---
id: SEEN-140
title: "One answer to whether a slice's plan covers a path"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: []
fixes: SEEN-104
status: doing
priority: P0
---
# SEEN-140: One answer to whether a slice's plan covers a path

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 1 point (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |
| Priority | P0 (it blocks SEEN-114 at the review stage) |

## Description

Three places in the harness ask whether a slice's plan covers a changed path, and they do not agree. `harness/calibration.py` `_covers` answers it for the route verdict and reads a directory entry: a slice naming `packages` covers `packages/core/db/tables.ts`. `harness/guard.py` answers it for the PreToolUse guard with `if relative not in entry['files']`, and the triage's `_slice_files_check` in `harness/triage.py` answers it with `path not in named`; both compare exactly, so the same slice naming `packages` covers nothing inside it. One question, three readers, two answers, and the looser one is the one a session meets first.

SEEN-114 is what that cost, three ways in one ticket. Its slices named `apps` and `packages` because adopting a formatter rewrites every source file it is pointed at, twenty-six of them, and that is the honest way to say so. One implementer was refused the right to write `rules/fixtures/<slug>/violation.ts` and `packages/core/db/tables.ts` although its plan named `rules/fixtures` and `packages`, and wrote both through a shell, which the PreToolUse guard does not intercept; another met the same refusal, stopped and reported, so the two agents behaved differently because the guard did, not because they did. Then the triage returned the ticket three times saying it could see no evidence for two criteria, with `slice_files` failing in each round and naming about forty files as belonging to no slice: the criteria whose evidence lives in exactly those files are the two Jev would not answer yes for, at 0.36, 0.37 and 0.39 against a threshold it never approached, while every check that proves them was recorded and moved it by hundredths.

The fix is one shared reader rather than three, and it is small. `_covers` is already the right answer and already tested, so it moves to where all three can call it, and `guard.py` and `triage.py` call it. What the ticket must not do is widen it: a slice naming `packages` covering `packages/core/db/tables.ts` is the behaviour `gates.py` has had since SEEN-104, decided there and not here, and the point is that the other two stop disagreeing with it. The guard's refusal message keeps naming the files the slice listed, because a path is what a session can go and look at.

One thing the ticket has to answer rather than assume: whether a slice that names a directory should be allowed at all, or whether the solution gate should refuse a plan whose slices overlap. SEEN-114 would have been a different ticket with narrower slices, and record 107 of its journal argues that `apps` and `packages` was the true description of a formatter adoption. That question is noted and not settled here; this ticket makes the three readers agree, which is the defect, and leaves the policy to the founder.

## Acceptance criteria

- [ ] One function answers whether a slice's plan covers a path, called by `harness/gates.py`, `harness/guard.py` and `harness/triage.py`, with no second implementation of the comparison anywhere in `harness/`
- [ ] `harness guard <path>` allows a write to a file inside a directory the accepted slice names, and still refuses one outside every entry, with the refusal naming the entries
- [ ] The triage's `slice_files` check passes when every changed path is inside a directory the plan names, and still fails on a path no entry covers, with the failure naming it
- [ ] A test fails before the change for each of the two readers: one proving `harness guard` refused a path inside a named directory, one proving `slice_files` reported such a path as belonging to no slice
- [ ] The whole harness suite is green, and SEEN-114's `slice_files` check passes against its own journal and diff, which is the measurement this ticket is judged by

## Depends on

Nothing. The three readers all exist on `main`.

## Blocks

- SEEN-114: Turn every recurring finding into a rule the pre-commit hook runs in seconds. It is parked at the review stage with four slices proved and the triage returning it on this defect.

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- The evidence: SEEN-114's journal records 36 (the guard refusing a directory's contents), 52 and 103 (what it cost the tdd record), and 107 (the three triage rounds and the one cause under them)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
