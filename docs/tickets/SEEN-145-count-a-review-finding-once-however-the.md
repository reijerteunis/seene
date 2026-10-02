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
status: review
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
| Status | review |

## Description

`kpi.findings` counts a ticket's review findings through `calibration.latest_finding_records`, which keys each finding by its `id`, its claim and its file, most recent record wins, so that a ticket reviewed twice does not count the same finding twice. Claim and file were added by SEEN-109, but the `id` is still part of the key, so the dedupe still rests on a session typing the same identifier in every review record, and nothing asks it to. SEEN-107 showed what happens when it does not: its journal holds two review advances, one carrying nineteen findings as `F1`, `G1`, `H1` and so on, and a later one carrying all twenty-six under `R1-1`, `R2-1` and so on, because the session renamed them for readability between the two. The delivered `kpi.json` reports forty-five findings against a real twenty-six, in a ticket whose profile includes the only high-severity finding recorded so far. The number is wrong in the direction that flatters nobody and misleads everybody: it inflates the finding count of exactly the tickets that were reviewed most. Two candidate shapes, and the solution stage picks one on the evidence rather than this description pre-empting it: count only the review advance that was accepted, on the reading that a returned review's findings are superseded by the record that replaced them, which removes the dependence on `id` entirely and makes the final record the whole picture; or derive identity from what a finding says rather than from what it is called. The first is simpler and puts the burden on the final review record carrying every finding, which SEEN-107's did, but since SEEN-109 a return records findings of its own that a later advance need not repeat, so it has to say what becomes of those; the second keeps working when it does not. The decision that matters: a figure the reports divide on must not rest on a field a session is free to rename, and SEEN-109 reads the same findings to decide what counts as an escape.

## Acceptance criteria

- [x] kpi.findings counts a finding once when two review advances describe it under different ids, proven with a fixture of two records whose findings differ only in their identifiers
- [x] SEEN-107's own committed journal reports its real finding total rather than forty-five, proven by a test that reads that journal from docs/harness/history/ rather than a constructed one
- [x] (as amended) Every other journal in this repository reports exactly what it reported before, except SEEN-102, which moves from seven to its real four, proven over every journal present
- [x] What the count rests on after this change is written in kpi.findings, and the weekly and sprint reports carry the corrected figure

## Amendments

- **2 October 2026, Ruud: criterion 3 is amended.** Measured at clarify over all
  29 journals, identity by content (the same file, and the same claim or the same
  failure scenario, never the id) changes two figures: SEEN-107 from 45 to 26 and
  SEEN-102 from 7 to 4. SEEN-102's second review renumbered F1 to F3 as F2 to F4
  and added a new F1, so its 7 is the defect this ticket fixes and not a figure to
  preserve. Holding it at 7 would need the id kept as a tiebreak, which brings back
  the dependence the ticket removes. The test pins both corrected figures and every
  other journal unchanged.
- **2 October 2026, Ruud, after review round 3 (note 36).** The id may break a tie
  and nothing more: where a later finding matches two findings of one record
  equally well on what they say, the one at the same file reference with its line
  takes it, then the one under the same id, then the earlier. The order only
  chooses among matches the content found, so the id still never makes two
  findings one, which is what the first amendment's sentence protects.

## Outcome

A review finding's identity now rests on what it says and where, never on its id.
`calibration.finding_identities` joins two findings when they name the same
normalised file and carry the same claim or the same failure scenario, and the
join is transitive, which is what SEEN-107's G1 needs: its claim was reworded as
R2-1 while its failure scenario was carried byte for byte. Two findings listed in
one record are never joined, directly or through a third. The id joins findings
only when they carry neither text, which the review gate refuses and no committed
journal holds. Every finding that said a text stays an anchor for it, and a later
finding is offered to the anchors sharing more of its texts first, so two alike
findings of one record each reach their own copy in a later round (F1 of the
first review, 3 counted where the old key counted 2; RED record 22, GREEN record
23), and a finding carried forward joins the one it matches on both texts rather
than an earlier one matching on its claim alone (F1 of the second review, a high
finding counted as low; RED record 29, GREEN record 30). Between two findings of
one record that a later one matches equally well, the one at the same line takes
it, then the one under the same id, and journal order is the last resort (F1 of
the third review, decided by Ruud at note 36; RED record 37, GREEN record 38). The pairs of each later record are joined
strongest first across the whole record, so a weak match listed first no longer
takes the anchor an exact copy needed (F1 of the fourth review, where an escape
was counted twice; decided by Ruud at note 44; RED record 47, GREEN record 48).
Position is still the last resort, and one case is left as a residue: a later
finding whose claim matches one earlier finding and whose scenario matches
another, every pair tying, where the order of a list can move the count (F1 of
the fifth review, returned at record 54 and accepted by Ruud at note 55).
[SEEN-146](SEEN-146-assign-a-later-review-s-findings-by-maximum.md) replaces the
greedy join with a maximum assignment. The id orders
matches the content found and never makes one. `latest_finding_records` (and so `kpi.findings`) and
`calibration.escapes` both group by that identity; `finding_key` is deleted.

- Criterion 1: `FindingIdentityTest` holds a fixture of two review advances whose
  findings differ only in their ids and counts one (RED record 11, `2 != 1`).
- Criterion 2: the test reads SEEN-107's committed journal and counts 26, where it
  counted 45 (RED record 11, `45 != 26`).
- Criterion 3, as amended: every journal under `docs/harness/history/` is compared
  with a table pinned at clarify; only SEEN-107 (45 to 26) and SEEN-102 (7 to 4)
  move. Escape and unattributable counts are unchanged in every journal (note 5).
- Criterion 4: `kpi.findings`' docstring says what the count rests on and names
  the residue, SEEN-006's R-04, reworded in every field and still counted twice
  (6 where a reader says 5), and the crossing tie above. The weekly report for 2026-W39 and the sprint 0
  report carry the corrected figures, and regenerating them after GREEN record 48
  changed no byte (note 49).

Delivered `kpi.json` files are not rewritten; the receipt does not hash them and
the reports recompute from the journals (note 5). The regression and the coverage
measurement are the ones the last tdd advance cites, run after this section was
final so that they cover the tree delivered.

The first review (returned at record 21) passed with three low findings: F1 is
fixed as above, F2 corrected this section's citations, and F3, the status row in
`docs/tickets/README.md` that no slice named, is the procedure's own status mirror
and is left as it is. The second review (returned at record 28) found the
claim-only join, fixed as above, and the regression run before this section's
last edit, which is why the regression now runs after it. The third (returned at
record 35) found the tie between equal matches, and the fourth (record 43) the
order inside a record and the missing report evidence, each settled as above.
The fifth (record 54) found the crossing tie, named as a residue and split into
SEEN-146 by Ruud's decision at note 55. F3 of every round, the status row in
`docs/tickets/README.md`, is the procedure's status mirror; the same file also
carries SEEN-146's row, and `CLAUDE.md` its index row.

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
