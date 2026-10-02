---
id: SEEN-146
title: "Match a later review's findings as a whole, so the order they are listed in never changes a count"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-145]
status: review
priority: P2
---
# SEEN-146: Match a later review's findings as a whole, so the order they are listed in never changes a count

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | review |
| Priority | P2 (no committed journal has the shape; the figure it corrects is one a session can move by reordering a list) |

## Description

SEEN-145 made a review finding's identity rest on what it says: `calibration.finding_identities` joins two findings when they name the same file and carry the same claim or the same failure scenario, never two findings of one record. Within each later record it joins the (earlier finding, later finding) pairs greedily, strongest first: texts shared, then the same file reference with its line, then the same id, then position. Five reviews of SEEN-145 each found one more edge of that greed, and the fifth was left as a named residue by Ruud's decision (SEEN-145, note 55): when a later finding's claim matches one earlier finding and its failure scenario another, every pair ties, position decides, and the greedy join can strand a finding that a better assignment would have placed. Record 1 holds F1 (claim c1, scenario s1) and F2 (c2, s2) at one file and line; record 2 holds G1 (c1, s2) and G2 (c3, s1). Listed as [G1, G2], `kpi.findings` counts 3; listed as [G2, G1], it counts 2. The figure the reports divide on, and the escape count SEEN-109 decides on, should not move when a reviewer reorders a list.

The fix replaces the greedy pass with an assignment per record that maximises what is placed: the later record's findings on one side, the earlier identities on the other, an edge where the content matches and the identity holds no finding of this record yet, weighted by the same ranking, and a maximum-weight matching taken over the whole record. The transitive merge of two earlier identities through one later finding has to keep working, and the solution stage says how the matching and that merge compose.

## Acceptance criteria

- [x] The crossing case above counts 2 in both listing orders and with F1 and F2 swapped in record 1, proven by a test that runs every permutation of both records
- [x] For any two records of up to four findings each, built from a small alphabet of claims, scenarios and lines, the count does not depend on the order of the findings in either record, proven by a property test over the permutations
- [x] Every journal in this repository reports what it reported after SEEN-145, proven by SEEN-145's pinned table unchanged, and every case in FindingIdentityTest stays green
- [x] SEEN-145's residue sentence in `kpi.findings` and in `finding_identities` is removed, and the docstring says what the assignment maximises

## Outcome

A later review's findings are now joined to the earlier identities as a whole,
never one pair at a time, so the order a reviewer lists either record in moves
no count. `calibration.finding_identities` builds, per record, each earlier
identity and the findings of the record it matched, at the strength of the
strongest pair under SEEN-145's ranking (texts shared, then the same file
reference with its line, then the same id). Over each connected component of
those matches, `_best_joins` searches every way to give each identity at most
one finding and takes the one with the most joins, then the largest summed
strength field by field, then, where two still tie, the one whose pairs come
first by what they say, each finding serialised with its keys sorted. Position
is never read. The transitive merge is chosen by the same search: a finding may
take more than one identity where none of them shares a record with it or with
each other, the refusal `join` makes, rather than in a second pass after the
matching. A component of more than `SEARCH_CAP` (2**16) choices takes a greedy
join ranked by strength and then by content, which reads no position either;
the largest component in any committed journal at solution had 2 choices.

- The crossing case (F1 (c1, s1), F2 (c2, s2) against G1 (c1, s2), G2 (c3, s1))
  counts 2 in all four orders of the two records, where the greedy join counted
  3 for [G1, G2]. RED record 10, GREEN record 11.
- A property test draws 400 pairs of records of one to four findings each from
  a fixed seed (146) over claims a to c, scenarios x to z and two lines, and
  counts every permutation of both: none moves. Against SEEN-145's greedy join,
  25 of the 400 pairs moved.
- FindingIdentityTest.PINNED is unchanged and every FindingIdentityTest case is
  green; SEEN-145's own journal, which PINNED does not list, still reports 16
  findings, no escapes and none unattributable, the figures measured at clarify.
- The crossing-tie residue is gone from `kpi.findings`' docstring and from the
  per-record comment in `finding_identities`, whose docstring now says what is
  maximised and in what order, how the merge composes and what the cap does.
  The one residue left is SEEN-006's R-04, a finding reworded in every field.

The first review passed with two low findings, fixed before delivery at
Ruud's choice (return record 18, RED record 19, GREEN record 20). F1: a
paragraph of the `finding_identities` docstring still said the finding at the
same line and then under the same id takes a tie, which SEEN-145's greedy pass
did; it now says the line and the id are the last two fields of a join's
strength, weighed after the number of joins and the texts shared. F2: the
property test never drew two findings sharing an id, so a second one draws 400
pairs from seed 1462 with ids sampled from one alphabet for both records, 335
of them sharing an id across the two, and none counts differently by order.

The regression is the whole harness suite, and the tdd advance cites the run
and the coverage measurement taken on this tree.

## Depends on

- [SEEN-145](SEEN-145-count-a-review-finding-once-however-the.md): Count a review finding once, however the record that carries it names it

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- The code: `finding_identities` in `harness/calibration.py`, read by `latest_finding_records`, `kpi.findings` and `calibration.escapes`
- The evidence: SEEN-145's journal, review returns at records 21, 28, 35, 43 and 54, and the decisions at notes 36, 44 and 55
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
