# The calibration window

The window is the most recent 10 counted tickets. A ticket counts when it was started after 2026-09-25T20:08:27+00:00, when it has delivered, and when it is not one of the tickets that built the thing under calibration.

**What an escape is, recorded before the first one.** A finding at high or blocking severity in a file the triage would have excluded, or a criterion the triage answered evidenced that the review found unmet. A finding at low or medium severity is never an escape: the saving is that such a finding is not looked for. A high or blocking finding naming no file, and a criterion the triage never answered, are reported as unattributable and counted neither way, because counting them as no escape would be a silent pass in favour of the narrowing being measured.

## The triage

**The rule.** With no escape in the most recent ten counted tickets, and nothing in them that could not be placed, spot depth can go live. It takes two lines: the founder sets [review] triage_shadow to false and fills [calibration] went_live with the ticket and the record number of the decision, which doctor checks exists. Evidence nobody can place holds the verdict rather than passing it, because counted neither way cannot mean counted as clean. Spot depth stays live until the first escape, which returns the triage to shadow with nobody editing a file, for another ten tickets.

**Where the switch stands.** The triage is in shadow: [review] triage_shadow is true.

**The verdict: stay-shadow.** 0 of 10 counted tickets carry a triage, so the evidence is reported and nothing is concluded from it

| Ticket | Findings | Would have excluded | Share of the diff | Escapes | Unattributable | Escaped defects |
|---|---|---|---|---|---|---|

What this table cannot see, recorded here rather than left to be discovered: once spot depth is live a reviewer no longer reads the files the narrowing drops, so a defect in one of them can only become a finding if the reviewer reads beyond its focus set. The escaped-defects column is shown for that reason and is not an escape by the definition above, which is the ticket's own two kinds. Whether a defect found after delivery should return the triage to shadow by itself is a question for the founder, raised by F5 of SEEN-109's first review and not settled by it.

## The routes

**The rule.** Each routed slice is charged the returns of its ticket, the findings at high or blocking severity landing in the files it planned to change, and its ticket's escaped defects. A return sends the whole ticket back and no record says which slice caused it, so every slice of the plan carries it, and an escaped defect is charged the same way; findings are the only per-slice measure, so a per-slice rate is evidence about a group and never about a cause. The slices Jev routed below the strongest tier are one group and every other slice, rule-routed ones included, is the other. The routes go live when the downgraded group's rework per point is at or below the other group's over the window; with no slice in either group there is nothing to compare and the verdict stays shadow.

**The verdict: stay-shadow.** 0 of 10 counted tickets carry a route, so the evidence is reported and nothing is concluded from it

| Group | Slices | Points | Rework charged | Rework per point |
|---|---|---|---|---|
| downgraded | 0 | 0 | 0 | not measurable |
| strongest | 0 | 0 | 0 | not measurable |

## Not in the window

- SEEN-006: Started 2026-09-23T19:07:47.301078+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-087: Started 2026-09-23T15:59:17.417788+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-088: Started 2026-09-23T18:26:11.873304+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-089: Started 2026-09-23T19:05:41.774586+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-090: Started 2026-09-23T20:45:59.536037+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-091: Started 2026-09-23T21:48:35.067922+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-092: Started 2026-09-23T22:23:53.048198+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-093: Started 2026-09-23T18:51:10.588159+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-094: Started 2026-09-23T20:22:59.297667+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-095: Started 2026-09-23T22:46:42.388587+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-096: Started 2026-09-23T23:18:38.879940+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-097: Started 2026-09-24T07:57:45.840548+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-098: Started 2026-09-24T06:00:15.192701+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-099: Started 2026-09-24T06:17:34.246014+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-100: Started 2026-09-24T05:09:42.707437+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-101: Started 2026-09-24T05:38:24.317121+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-102: Started 2026-09-24T06:47:31.399695+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-103: Started 2026-09-24T07:10:14.454720+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-104: Started 2026-09-24T10:16:01.932804+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-105: Started 2026-09-24T11:36:57.839797+00:00, before the calibration rule existed at 2026-09-25T20:08:27+00:00
- SEEN-107: Built the triage, the routes or this window, so it was not worked under them
- SEEN-108: Built the triage, the routes or this window, so it was not worked under them
- SEEN-109: Built the triage, the routes or this window, so it was not worked under them

**The rule, recorded before the numbers.** Both rules above are `[calibration]` in `harness/thresholds.toml`, committed before the first ticket this report counts was started. Neither verdict flips a switch. Going live is the founder's, and for the triage it is two lines in that file: `[review] triage_shadow` goes false and `[calibration] went_live` names the ticket and the record number of the decision, which `doctor` checks exists and CI runs. The return to shadow is the one thing that happens without a person, because an escape in the window makes the verdict stay-shadow and the triage reads the verdict.

