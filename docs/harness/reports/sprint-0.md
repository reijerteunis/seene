# Sprint 0: 68 of 154 points delivered

## What delivered

| Ticket | Points | Cycle time | Attempts | Rework | Findings | Coverage |
|---|---|---|---|---|---|---|
| SEEN-006 | 3 | 18m | 2 | 1 | 6 (6 closed, 0 open) | - |
| SEEN-086 | 8 | not measured | - | - | 0 (0 closed, 0 open) | - |
| SEEN-087 | 3 | 12m | 2 | 1 | 5 (5 closed, 0 open) | - |
| SEEN-088 | 3 | 37m | 4 | 3 | 9 (9 closed, 0 open) | - |
| SEEN-089 | 3 | 49m | 1 | 0 | 4 (4 closed, 0 open) | - |
| SEEN-090 | 3 | 1h 1m | 4 | 3 | 9 (9 closed, 0 open) | 0.0 |
| SEEN-091 | 3 | 33m | 3 | 2 | 6 (6 closed, 0 open) | 0.0 |
| SEEN-092 | 2 | 16m | 1 | 0 | 3 (3 closed, 0 open) | 0.0 |
| SEEN-093 | 2 | 4m | 1 | 0 | 2 (2 closed, 0 open) | - |
| SEEN-094 | 2 | 13m | 1 | 0 | 4 (4 closed, 0 open) | 0.0 |
| SEEN-095 | 1 | 26m | 2 | 1 | 3 (3 closed, 0 open) | 0.0 |
| SEEN-096 | 1 | 6h 39m | 1 | 0 | 3 (3 closed, 0 open) | 0.0 |
| SEEN-097 | 3 | 1h 5m | 3 | 2 | 8 (8 closed, 0 open) | 0.0 |
| SEEN-098 | 2 | 14m | 1 | 0 | 4 (4 closed, 0 open) | 0.0 |
| SEEN-099 | 1 | 9m | 1 | 0 | 2 (2 closed, 0 open) | 0.0 |
| SEEN-100 | 1 | 21m | 1 | 0 | 3 (3 closed, 0 open) | 0.0 |
| SEEN-101 | 1 | 7m | 1 | 0 | 3 (3 closed, 0 open) | 0.0 |
| SEEN-102 | - | 52m | 2 | 1 | 4 (4 closed, 0 open) | - |
| SEEN-103 | 1 | 16m | 1 | 0 | 3 (3 closed, 0 open) | 0.0 |
| SEEN-104 | 3 | 1h 9m | 3 | 2 | 7 (7 closed, 0 open) | 0.0 |
| SEEN-105 | 3 | 6h 19m | 5 | 4 | 26 (26 closed, 0 open) | 0.0 |
| SEEN-106 | 3 | 14h 6m | 16 | 15 | 20 (20 closed, 0 open) | 0.0 |
| SEEN-107 | 3 | 4h 43m | 11 | 10 | 26 (26 closed, 0 open) | 0.0 |
| SEEN-108 | 2 | 14h 7m | 14 | 13 | 5 (5 closed, 0 open) | 0.0 |
| SEEN-109 | 2 | 8h 1m | 9 | 8 | 26 (26 closed, 0 open) | 0.0 |
| SEEN-111 | 3 | 1h 23m | 1 | 0 | 2 (2 closed, 0 open) | 0.0 |
| SEEN-113 | 2 | 32h 5m | 8 | 7 | 21 (21 closed, 0 open) | 0.0 |
| SEEN-114 | 3 | 22h 6m | 16 | 15 | 34 (34 closed, 0 open) | 0.0 |
| SEEN-140 | 1 | 2h 2m | 7 | 6 | 8 (8 closed, 0 open) | 0.0 |

## Against the targets

| Measure | This report | Target |
|---|---|---|
| Median cycle time | 50m | under 2 days per ticket |
| Rework per ticket | 3.36 | under 0.5 over a sprint |
| First-pass CI | 100% | 80% |
| Points delivered | 68 | against plan |

## Findings

- blocking: 6
- high: 41
- low: 103
- medium: 106

## The review triage

In shadow: yes, by the threshold. [review] triage_shadow is true in harness/thresholds.toml


## The context budget

- One tool call per question. A second call answering the same question is a question that was not asked properly.
- A codegraph query names a symbol, not a directory. A directory is a repository-wide read wearing a tool's name.
- No repository-wide read when a graph can answer. grep over the tree is the last resort, not the first move.

| Measure | This report | Baseline |
|---|---|---|
| Output tokens per point | 207616.6 | 40581.5 |
| Output tokens per slice | 38686.3 | none: the baseline predates slices |
| Tool calls per point | 109.1 | 18.5 |
| Qualifying tickets | 13 | 27 points over 10 tickets |
| Output tokens per point, worked with the scout and the reviewer | not measured | 40581.5 |
| Tickets worked with both agents | 0 | none: the baseline predates them |

### Cost per point by the model the work ran on

| Model | Slices | Points | Points priced | Output tokens | Cost (EUR cents) | Cost per point |
|---|---|---|---|---|---|---|
| opus | 10 | 14 | 12 | 968669 | 7264 | 605.33 |
| unknown | 2 | 3 | 0 | 71653 | not measured | not measured |

Prices read on 2026-09-25, in EUR cents per million tokens, from `[routing.prices]`. Output tokens only: a handoff record carries the session's output tokens and tool calls and nothing about input, so the figure says what it covers rather than guessing at the rest. Cost per point is the cost divided by the points it could price, which is the fourth column and not the third: a slice whose boundary carried no token figure counts its points and not its cost, so a row where the two differ does not divide the way it reads. Rows are the model each slice actually ran on, which while `[routing] shadow` is true is the session's model and not the routed one; what the route would have cost is carried per slice in kpi.json as `routed_cost_cents`; `report --calibration`, which SEEN-109 added, compares the two beside the returns and the findings each slice was followed by. A row named `unknown` is slices whose session left no log to read a model from.

**The rule, recorded before the numbers.** Below the baseline, the tools paid for the context they occupy and stay. Above it, one is removed, graphify first, because codegraph and repowise can partly answer its questions. A rise removes them immediately rather than after five tickets. The call is the founder's.

**What it points to.** Remove one, graphify first: 207616.6 output tokens per point against a baseline of 40581.5. codegraph and repowise can partly answer its questions. The call is the founder's.

**The founder's call.** Not made here; it belongs in this report, written by Ruud beside the line above.

## Not measurable yet

- Eval pass rate for policy-gate action tickets: the eval set is SEEN-036 and no such ticket has been worked, so a figure here would be invented
- Escaped defects: counted from tickets whose frontmatter names an earlier one, and none has been written yet
- Cost in euros beyond output tokens: a handoff record carries the session's output tokens and tool calls and nothing about input, so the cost per slice in [routing.prices] covers the output side and says so, with the date the prices were read printed beside it
