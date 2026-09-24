---
id: SEEN-107
title: "Let Jev settle what the review can settle before a model reads the diff"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-105, SEEN-098, SEEN-104]
status: doing
---
# SEEN-107: Let Jev settle what the review can settle before a model reads the diff

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

The review is the most expensive read in the procedure: a model reads the whole diff, the journal and the criteria, and Jev only scores the findings it wrote. Turn the review into three passes, cheapest first, so the model reads only what the cheaper passes could not settle. Pass one runs no model: the checks the harness already has (coverage, lint, gitleaks, the fingerprint, files inside the accepted slice) plus the ones the journal makes possible (a RED recorded as failing for the stated reason, tests added, an acceptance_evidence entry for every criterion, the pull request body's required parts). Pass two is one Jev request with the journal and the diff excerpts as state: criterion_evidenced per acceptance criterion (noul: does the cited check record, test name or hunk satisfy it), diff_matches_solution (noul: are the files and the mechanism the ones the solution record named), reviewer_must_read per file (noul, with the hunk size, the package, repowise's change-risk percentile, the coverage delta and whether the solution record named the file as state), and review_depth (choice: spot, full). Pass three is the reviewer subagent from SEEN-105 reading only the focus set at that depth, its findings scored by severity and must_fix as today. Three things stay rules, never Jev: a ticket that changes an agent action, touches billing or the policy gate, or carries a migration always gets full depth; a criterion Jev marks unevidenced returns the ticket to tdd with the criterion named before any model reads anything; and nothing here takes effect until SEEN-109's shadow window says it saves more than it misses. The decision that matters: Jev cannot execute a test or read the repository, so every answer it gives is only as good as the state the harness puts in front of it, which is why pass one exists and why the state is excerpts the journal already holds, not the tree.

## Acceptance criteria

- [ ] harness review triage <ticket> runs the deterministic pass and one Jev request and writes a triage record carrying the per-criterion answers, diff_matches_solution, reviewer_must_read per file, review_depth and the focus set, each with its probability
- [ ] A criterion answered unevidenced below the threshold returns the ticket to tdd naming the criterion, before the reviewer subagent is spawned, proven with a fixture
- [ ] A ticket that changes an agent action, touches billing or the policy gate, or carries a migration gets full depth by rule with Jev not asked, proven with a fixture
- [ ] The reviewer subagent's task carries only the focus set at the chosen depth, and the review gate refuses a review record whose recorded read list is smaller than the focus set
- [ ] In shadow mode the reviewer still reads everything and the triage record stores what would have been excluded; kpi.json carries the reviewer's output tokens and the excluded share of the diff

## Depends on

- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants
- [SEEN-098](SEEN-098-add-repowise-and-carry-risk-into-the-gate.md): Add repowise and carry its risk answer into the gate
- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack

## Blocks

- [SEEN-109](SEEN-109-calibrate-the-review-triage-and-the-routes-on.md): Calibrate the review triage and the routes on ten tickets before either saves a token

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
