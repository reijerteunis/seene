# Sprint 0: 37 of 81 points delivered

## What delivered

| Ticket | Points | Cycle time | Attempts | Rework | Findings | Coverage |
|---|---|---|---|---|---|---|
| SEEN-006 | 3 | 18m | 2 | 1 | 5 (5 fixed, 0 waived) | - |
| SEEN-086 | 5 | not measured | - | - | 0 (0 fixed, 0 waived) | - |
| SEEN-087 | 3 | 12m | 2 | 1 | 5 (5 fixed, 0 waived) | - |
| SEEN-088 | 3 | 37m | 4 | 3 | 9 (9 fixed, 0 waived) | - |
| SEEN-089 | 5 | 49m | 1 | 0 | 4 (4 fixed, 0 waived) | - |
| SEEN-090 | 3 | 1h 1m | 4 | 3 | 9 (9 fixed, 0 waived) | 0.0 |
| SEEN-091 | 3 | 33m | 3 | 2 | 6 (6 fixed, 0 waived) | 0.0 |
| SEEN-092 | 2 | 16m | 1 | 0 | 3 (3 fixed, 0 waived) | 0.0 |
| SEEN-093 | 2 | 4m | 1 | 0 | 2 (2 fixed, 0 waived) | - |
| SEEN-094 | 2 | 13m | 1 | 0 | 4 (4 fixed, 0 waived) | 0.0 |
| SEEN-095 | 1 | 26m | 2 | 1 | 3 (3 fixed, 0 waived) | 0.0 |
| SEEN-096 | 1 | 6h 39m | 1 | 0 | 3 (3 fixed, 0 waived) | 0.0 |
| SEEN-098 | 2 | 14m | 1 | 0 | 4 (4 fixed, 0 waived) | 0.0 |
| SEEN-100 | 1 | 21m | 1 | 0 | 3 (3 fixed, 0 waived) | 0.0 |
| SEEN-101 | 1 | 7m | 1 | 0 | 3 (3 fixed, 0 waived) | 0.0 |

## Against the targets

| Measure | This report | Target |
|---|---|---|
| Median cycle time | 20m | under 2 days per ticket |
| Rework per ticket | 0.79 | under 0.5 over a sprint |
| First-pass CI | 100% | 80% |
| Points delivered | 37 | against plan |

## Findings

- blocking: 2
- high: 18
- low: 16
- medium: 27

## The context budget

- One tool call per question. A second call answering the same question is a question that was not asked properly.
- A codegraph query names a symbol, not a directory. A directory is a repository-wide read wearing a tool's name.
- No repository-wide read when a graph can answer. grep over the tree is the last resort, not the first move.

| Measure | This report | Baseline |
|---|---|---|
| Output tokens per point | not measured | 40581.5 |
| Tool calls per point | not measured | 18.5 |
| Qualifying tickets | 0 | 27 points over 10 tickets |

**The rule, recorded before the numbers.** Below the baseline, the tools paid for the context they occupy and stay. Above it, one is removed, graphify first, because codegraph and repowise can partly answer its questions. A rise removes them immediately rather than after five tickets. The call is the founder's.

**What it points to.** Nothing yet. The context budget comparison: 0 of 5 qualifying tickets have delivered, so the figures are reported and nothing is concluded from them

## Not measurable yet

- Eval pass rate for policy-gate action tickets: the eval set is SEEN-036 and no such ticket has been worked, so a figure here would be invented
- Escaped defects: counted from tickets whose frontmatter names an earlier one, and none has been written yet
- Cost in euros: the session logs carry tokens, and a price per token is stale the day it is written, so only tokens are reported
- The context budget comparison: 0 of 5 qualifying tickets have delivered, so the figures are reported and nothing is concluded from them
