---
id: SEEN-111
title: "Close the four findings SEEN-108 carried, and the stray check they hid"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-108]
status: todo
---
# SEEN-111: Close the four findings SEEN-108 carried, and the stray check they hid

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

SEEN-108's third review returned six findings. Two were fixed in that ticket, the model declaration the implementer was never told to make and the window that charged a rework round to a slice; the other four were carried here by Ruud's decision, recorded in SEEN-108's journal at note 59 with the review's own evidence for each. They are not escaped defects: every one was found by the review before delivery and deferred deliberately, so this ticket's frontmatter does not name SEEN-108 in a `fixes` field and the escaped-defect count stays right.

The one that matters is the stray check. SEEN-105 added `agents.strays` so that an agent file with no source under `harness/agents/`, holding Edit, Write and Bash, cannot ship without review; SEEN-108 made `seen-implementer` a generated agent, which put its name in the set `strays` skips, and the two tests that guarded the check now pass through `drift` instead. Deleting `+ strays(root)` from `agents.drift` leaves both green, which is the definition of a test that passes with the behaviour removed. The fixtures need a name nobody generates, and `strays` needs a test that fails when it is gone.

The other three are small and each is a claim a reader can check: the sprint report tells its reader to run `report --calibration`, which does not exist until SEEN-109; the money rule is an fnmatch pattern that a slice naming a directory rather than a file slips past, on exactly the arithmetic the ground rules care most about; and SEEN-108's record 38 quotes a failure its cited RED does not contain, the third instance of that fault in one journal and the only one still uncorrected, which the append-only journal answers with a note beside it rather than an edit.

## Acceptance criteria

- [ ] The two stray fixtures in harness/tests/test_agents.py use an agent name no source generates, and a test fails when `+ strays(root)` is removed from `agents.drift`, proven by deleting it in the RED
- [ ] The rendered cost table says the routed counterfactual is compared by a command SEEN-109 adds, rather than by one a reader can run today, and the same sentence in harness/context.py and harness/report.py agree
- [ ] `[routing.rules] money` matches a slice whose files entry names `packages/core` or `packages/core/src` as well as one naming a file under them, proven with a fixture per form, and the same holds for the migration and credentials patterns where a directory is a legitimate way to name them
- [ ] A note in SEEN-108's journal corrects record 38, which quotes "AttributeError: 'dict' object has no attribute 'ran_on_tier'" where check 34 contains `KeyError: 'ran_on_tier'`, in the shape notes 42 and 52 already set
- [ ] `go_back` in harness/cli.py no longer assigns a local it does not use, which is a leftover from the sync that moved to the solution advance

## Depends on

- [SEEN-108](SEEN-108-route-each-slice-to-a-model-and-an-effort-at.md): Route each slice to a model and an effort at solution, by rule first and by Jev second

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- The findings, with the review's own evidence for each: SEEN-108's journal, note 59
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
