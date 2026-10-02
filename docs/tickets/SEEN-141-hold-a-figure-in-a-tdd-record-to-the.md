---
id: SEEN-141
title: "Hold a figure in a tdd record to the check it cites"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-114]
status: todo
priority: P1
---
# SEEN-141: Hold a figure in a tdd record to the check it cites

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P1 (five findings on one ticket, and the doctor warning it leaves behind is live on main) |

## Description

A tdd record's `failure_reason` is prose, and the numbers in it are read by every later reader as the measurement the cited check took. Five findings on SEEN-114 were one defect in that prose: a figure the record it cites does not contain. The reviews caught every one, which is the expensive way to catch it, and the fifth left `doctor` warning on `main` that `harness/outcome-figure-names-its-record` has recurred five times with no rule written.

The instances, because they are the specification. `102` where the cited red ran 58 tests. `716` where it ran 723. `158` where it ran 174. `58 staged paths` where the check's output prints 34 files and 46 modules and no path count at all. `eleven modules of packages/core/db` where git has returned nine since the commit that created the directory, in an amended acceptance criterion. In every case the failing counts and the failing test names were right and only the denominator was wrong, which is why six reviews and four replays went past some of them: the prose reads as though somebody had checked.

The gate already does this comparison one layer out. `cited_check` holds a record's `red` and `green` to the checks they name, and refuses a citation whose check did not fail or does not belong to this attempt. What it does not read is the sentence beside the citation. The check's own output is in the journal, `Ran 1564 tests` and `FAILED (failures=2, errors=29)` in so many words, so the figure and its source are both already recorded and nothing new has to be measured: the rule is a comparison between two things the record already holds.

Scope, narrowly, because the general problem is unbounded. A number in prose can be anything, and a rule that tried to check every one would refuse a record for saying "the three shapes a schedule is written in". This rule reads the figures that name a size of a test run, which is the shape every one of the five instances took: a count adjacent to the word `tests`, or the `N of M` form the records use, written in digits, with or without thousands separators, or in number words, because this journal's prose says "four of its sixty-seven" as readily as "729 tests". Each such figure must appear in the output of the check that entry cites. Nothing else in the prose is this rule's business, and the ticket says so rather than leaving a reader to discover it.

One decision the solution stage owns rather than this description. The alternative design is structural: each slice entry gains a field carrying the total, read out of the cited check by the harness rather than typed by a session, and the prose is then free to say anything because the figure lives beside it. That is strictly safer and it is a template change, so every journal written before it has a record shape the gate must still accept. Weigh it against the parsing rule and record which, with the reason.

The rule also has to end up in `rules/registry.toml`, or the loop it closes cannot close. `report.rule_loop` reads a candidate as written when the registry carries its id, so `harness/tdd-record-count-matches-check` naming a gate nobody registered would leave `doctor` warning for ever about a rule that exists. SEEN-114 settled the shape for a check that is the harness's own: an entry with a citation and a fixture, and a branch in `rules._run_harness` that runs the check over the fixture tree. The fixture here is a journal rather than a source file, which is new, and its violation is a tdd record whose prose names a total its cited check does not print.

Worth saying what this ticket is not. It does not touch the Outcome or the ticket file: three of the five instances were there, and a rule that read a ticket's prose would be a rule that refuses a sentence for being a sentence. What makes the tdd record tractable is that it is JSON, its figures are about one named check, and that check's output is beside it.

## Acceptance criteria

- [ ] The tdd gate refuses a record whose `failure_reason` names a test total the check that entry cites does not print, and the refusal names the entry, the figure and the check
- [ ] A total written in number words is read as well as one written in digits, with the `N of M` form the records use covered, and a figure the output does carry is accepted whichever form it is written in
- [ ] `rules/registry.toml` carries `harness/tdd-record-count-matches-check` with a citation and a fixture, and `harness rules --fixtures` proves it by running the check over a journal fixture whose record disagrees with its check
- [ ] `harness report --week` stops listing `harness/outcome-figure-names-its-record` as a candidate recurring with no rule written, and `doctor` stops warning about it, with the connection between the candidate and this rule id recorded rather than assumed
- [ ] A RED per criterion: a tdd record carrying each of SEEN-114's five real instances is refused, and the same record with the figure corrected is accepted
- [ ] The whole harness suite is green, and every tdd record already in `docs/harness/history/` still passes the gate it was accepted under, or the ones that do not are listed with the reason

## Depends on

- SEEN-114: Turn every recurring finding into a rule the pre-commit hook runs in seconds. It built the registry, `_run_harness`, the rule loop and the doctor warning this rule registers itself with, and it is the ticket whose five findings are the specification.

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- The evidence: SEEN-114's journal, where the five instances are findings F2, F13, F14, F15 and F29, and records 231, 324 and 343 carry what each one was and what it cost. Record 343 is also the correction of one of them, which is the shape of the defect at its clearest: a claim measured at the repository root about an import that resolves from its own package.
- The gate that already does this one layer out: `cited_check` in `harness/gates.py`
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.

## Not an escaped defect

The frontmatter names no `fixes`, deliberately. Every one of the five instances was found by a review before the ticket delivered, so none of them escaped, and `report.escaped_defects` counts a ticket whose frontmatter names an earlier one. Writing `fixes: SEEN-114` here would record five escapes that did not happen and move a KPI by inventing them. What this ticket fixes is the cost of catching them that way: five findings, four replays and six review rounds, which the rule would have taken in seconds.
