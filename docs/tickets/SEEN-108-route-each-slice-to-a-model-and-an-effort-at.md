---
id: SEEN-108
title: "Route each slice to a model and an effort at solution, by rule first and by Jev second"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-104, SEEN-105, SEEN-098]
status: review
---
# SEEN-108: Route each slice to a model and an effort at solution, by rule first and by Jev second

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | review |

## Description

Every slice runs on the session's model at the session's effort today, whatever the slice is. After the solution record is accepted, harness route <ticket> decides per slice which model and which effort implement it. Rules first, in a [routing] section of harness/thresholds.toml: a slice that changes an agent action, touches billing or the policy gate, money arithmetic in packages/core (detectors, matching, fee expectations), a migration or an RLS policy, or credentials goes to the strongest model at high effort, and Jev is not asked. Every other slice is a Jev choice: implementation_model over haiku, sonnet and opus and implementation_effort over low, medium and high, with the slice (points, files, the RED), the approach, the risk score from clarify, repowise's change-risk percentile, whether the pattern already exists in the repository (the codegraph and repowise answers on record), new dependencies, the marketplaces touched and the ticket's returns so far as state, and the criteria per option written into the question. The route lands in the solution record as execution (slice, model, effort, source rule or jev, probability) and in the handoff pack; the implementer subagent is spawned with it (Claude Code: the per-invocation model and the agent's effort; Codex: model and model_reasoning_effort in the agent TOML harness sync writes for that slice), and the tdd gate refuses a check recorded under a model other than the route's, reading the model from the session log the cost KPI already reads. The reviewer's model is a rule too: the strongest model at full depth, one tier down at spot depth. The decision that matters: the route is chosen where the information is, at solution with the slice plan and the risk answers on record, and never inside the session that would benefit from a stronger model.

## Acceptance criteria

- [x] (as amended) harness route <ticket> writes an execution entry per slice with model, effort, source and probability into a route record naming the accepted solution record it routes, the handoff pack carries the entry for the slice in hand, and a route is read only for the plan it routed
- [x] A slice matching a routing rule (agent action, billing or policy gate, money arithmetic in packages/core, migration or RLS, credentials) is routed to the strongest model at high effort without a Jev call, proven with a fixture
- [x] (as amended twice) The implementer subagent is spawned with the routed model in Claude Code and with the routed model and effort in Codex, from the spawn instruction the route record carries, and a check recorded under a different model is refused by the tdd gate naming both models, reading the model the subagent declares when it declares one and the session log otherwise
- [x] kpi.json carries model, effort, output tokens and cost per slice, and harness report --sprint shows cost per point by model beside the tokens per point it already shows
- [x] docs/harness/skill.md says the route is read from the handoff pack and never chosen inside the session, and sync regenerates both copies

## Outcome

Worked in one session by the digest `710e96458c5b`: 12 attempts, 11 returns,
15 slices proved against four planned, counting the tdd advance
this section was written for. Ten of the returns came from a review and each
found something real; one came from the review triage before any model read the
diff, which is what SEEN-107 was built to do; two were this ticket's own, to take
a review's findings. The counts are read from the journal rather than recalled,
because the first version of this section was recalled, went stale within two
commits and said four findings were outstanding that were fixed on this branch.
The fourth review found that, and it is the reason this paragraph says where its
numbers come from.

**What it delivers.** `harness route <ticket>` decides per slice which model and
which effort implement it, at the tdd stage with the plan and the risk answers on
record. Rules run first over the slice's own files and are never Jev's to answer;
what no rule settles is one request carrying `implementation_model` and
`implementation_effort` once per slice, and a slice nobody could answer for goes
to the strongest model rather than the cheapest. The route lands in a `route`
record, the handoff pack names what the slice in hand runs on, `sync` writes it
into `seen-implementer`'s copies for both assistants, and `kpi.json` carries what
each slice was routed to, what it ran on and what it cost. `[routing] shadow` is
true, so nothing here yet changes what a slice runs on: SEEN-109's window
decides.

**What the criteria could not be given as written.** Two were amended, each on a
decision recorded before the amendment and each because the criterion named a
mechanism the harness forbids. Criterion 1 asked for the entry to be written into
the solution record, which an append-only journal cannot do: the route record
names that record instead, and a route is read only for the plan it routed, which
was the half nothing yet delivered. The triage found it, scoring the criterion as
worded 0.44 against a bar of 0.6 and returning the ticket before a reviewer was
spawned. Criterion 3 asked the gate to read the model from the session log, and a
subagent's model is not in it: a Claude Code subagent inherits
`CLAUDE_CODE_SESSION_ID`, so its checks resolve to the parent's transcript, and
of 15,631 entries in this project's logs after three subagent runs none carries
`isSidechain` true. The implementer declares its model instead, which is a
disclosure and not a proof, the same position SEEN-105 took for the reviewer's
session id. The decisions are at records 41 and 50 with the options offered.

**What the reviews found that the tests did not.** Forty-one findings over eight
reviews, falling nine, six, six, five, two, three, five, five. Three were the
same fault in different clothes: a figure attributed to the wrong thing. The
tokens of a slice were keyed by the handoff's `position` rather than its `done`,
so every slice was charged the window before it and the planning window was
charged to slice 1; the fix left the last slice charged to nobody; the fix for
that let slice 4 swallow all four review rounds, 253,085 output tokens against a
two-point slice. Three more were a generator that could not answer: it raised on
a damaged journal and took `doctor`'s report down with it, it read the branch
where a `pull_request` checkout has none, and it fell back while the committed
copies held the old plan's model. Two were mine in the plainest sense: the
`failure_reason` field, which asks for the runner's words, was filled three times
from what this session had been reading, and a correcting note written after the
first was not enough to stop the second or the third. Records 42, 52 and 70 correct all three, and the corrections are listed below.

**What it cost, on its own figures.** Slice 1 68,043 output tokens, slice 2
23,659, slice 3 45,545, slice 4 unknown because no figure was recorded at the
boundary that closed it. Routed opus, opus, haiku and sonnet; run on opus
throughout, because in shadow a slice runs on whatever the session is. Slice 3 is
the number the whole ticket is about: routed haiku at a counterfactual 18 cents,
run on opus at 342, an eighteenfold gap that the first version of the cost table
would have credited to haiku as a saving nothing on haiku ever earned.

**What is carried.** Nothing. Four findings of the third review were carried to a
follow-up, SEEN-111, and then fixed here instead, because the review gate refuses
a delivery with open findings and says not to relabel one; SEEN-111 was withdrawn
in the same commit that closed them. Every finding of all eight reviews is closed
in this ticket, and none of them is an escaped defect, because every one was
found by a review before delivery rather than after it.

**What the sixth review found, which is the pattern in one sentence.** Note 83
asked the next ticket that touched `harness/templates/tdd.json` to put the
reading of the position field into the template's own prose. One attempt later
this ticket touched that file, made the field mandatory, shipped a literal `1`
where every other field ships instruction, and so taught a rework round the one
value that is wrong for it: the mistake record 82 made, turned into the default.
Advice written to a future ticket by the ticket still holding the file is advice
to nobody.

**What the design cost, and what finally changed it.** The implementer's
generated copies were built to vary with the slice in hand, because Claude Code
documents no per-invocation override for the effort and the file was the only
place a routed effort could go. A file whose correct content depends on the
state of a ticket was then wrong on a detached HEAD, wrong after a replan, wrong
the moment a green landed and wrong after the receipt, where doctor reported
drift on the commit being merged and verify-merge refused with no way to
re-sync: four findings across four reviews, each patched separately, one design
behind all of them. The copies are fixed now, at the strongest tier and high
effort, and the routed model reaches the implementer through the spawn
instruction. The effort is carried and reported rather than applied in Claude
Code, which is what the second amendment to criterion 3 says and what record 121
decided.

**What the journal owns.** Four corrections, at records 42, 52, 70 and 83, and a
fifth thing worth naming beside them: the fingerprint check refused the sixth
and seventh triages, because this session wrote the outcome after the final
regression and ran those checks with the fixes unstaged. SEEN-107 passed that
check eleven times on the same code, so it was the order of work and not the
check; note 87 records it and check 85 stands in its place. The order the
harness reads is outcome, commit, then the final checks, and this section was
written that way on the ninth attempt. Three
are the same fault: the `failure_reason` field asks for the runner's words and
was filled from what the session had been reading, at records 23, 46 and 38. The
fourth is record 82 naming a plan position for a rework round that spans three
slices' files, one attempt after adding the field so that nothing would be
guessed. Record 70 has a slip of its own, citing 70 where it means 64. None of
them changes a slice's proof; all of them are what an append-only journal does
instead of an edit.

**What is not closed.** The gate refuses a mismatch only when `[routing] shadow`
is false, and nothing has run under that yet. `ran_on` is null for slice 1,
whose green predates checks recording a model at all, and for any slice whose
boundary carried no figures. The Codex agent keys `model` and
`model_reasoning_effort` are unverified against a Codex release, because no Codex
session has ever run on this repository, which is the position SEEN-105 recorded
and this ticket does not improve on.

## Amendments

- **25 September 2026, Ruud: criterion 1 is amended.** The entry per slice is
  written into a `route` record of its own, which names the sequence of the
  accepted solution advance it routes, rather than into the solution record
  itself. The journal is append-only and every record is sealed by the next
  record's `prev_hash`, so writing into an accepted record is either a rewrite of
  evidence or a second record claiming to be the first; that is the decision in
  docs/adr/0001-journal-integrity-file-bytes-and-git-as-notary.md, and it is the
  same call SEEN-104 made for `handoff` and SEEN-107 for `triage`. The ticket's
  own description already said the route is decided after the solution record is
  accepted, so the two halves could not both be true. Raised by the review triage
  at record 24, which scored the criterion as worded 0.44 against a bar of 0.6
  and returned the ticket to tdd before any model read the diff; the reasoning
  was recorded in advance in the clarify record at record 4, and the decision
  itself, with the three options put to him and the one he chose, is at record
  41. What the criterion
  asks for is delivered in substance: one entry per slice with model, effort,
  source and probability, carried in the handoff pack. Only its location moves.

- **25 September 2026, Ruud: criterion 3 is amended.** The gate reads the model
  the implementer declares when it declares one, and the session log otherwise.
  The criterion asked for the log alone, and a subagent's model is not in it: a
  Claude Code subagent inherits CLAUDE_CODE_SESSION_ID, so its checks resolve to
  the parent's transcript, and of the 15,631 entries in this project's logs after
  one scout run and two reviewer runs, none carries `isSidechain` true and every
  model entry reads claude-opus-5. Left as written, the gate would refuse a slice
  that ran exactly as routed and name a remedy the session cannot carry out.
  Raised as F1 of the second review at note 49, verified by that reviewer from
  inside its own subagent; the decision, with the three options put to him and
  the one he chose, is at record 50. A declaration is a disclosure and not a
  proof, which is the position SEEN-105 already took for the reviewer's session
  id, and the record carries both values so that what was observed and what was
  claimed are told apart.

- **25 September 2026, Ruud: criterion 3 is amended a second time.** The
  generated agent copies no longer vary by slice, so in Claude Code the routed
  model reaches the implementer through the per-invocation override the spawn
  instruction names, and the routed effort is carried and reported but not
  applied there, because Claude Code documents `effort` only as a frontmatter
  key and documents no per-invocation override for it. In Codex both still
  reach it, through the agent TOML. The reason is F3 of the eighth review at
  note 120: a file whose correct content depends on which slice is in hand has
  no correct content once no slice is, so after the receipt `doctor` reported
  drift on the commit being merged and `verify-merge` refused, and the copies
  could not be re-synced without changing a tree the receipt attests. Four
  findings across four reviews were symptoms of the same thing. The decision,
  with the three options put to him and the one he chose, is at record 121.

## Depends on

- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack
- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants
- [SEEN-098](SEEN-098-add-repowise-and-carry-risk-into-the-gate.md): Add repowise and carry its risk answer into the gate

## Blocks

- [SEEN-109](SEEN-109-calibrate-the-review-triage-and-the-routes-on.md): Calibrate the review triage and the routes on ten tickets before either saves a token

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
