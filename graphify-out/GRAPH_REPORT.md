# Graph Report - seene  (2026-09-23)

## Corpus Check
- 142 files · ~66,639 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .toml 1)

## Summary
- 382 nodes · 924 edges · 13 communities (8 shown, 5 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f9e65c95`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- require
- .evaluate
- .start
- Repository
- HarnessError
- doctor.py
- Seen: Claude Code entry point
- RecordTest
- DoctorTest
- DeliveryTest
- GraphTest
- graphify

## God Nodes (most connected - your core abstractions)
1. `require()` - 47 edges
2. `HarnessError` - 38 edges
3. `Repository` - 35 edges
4. `execute()` - 23 edges
5. `DoctorTest` - 20 edges
6. `RecordTest` - 19 edges
7. `CommandTest` - 18 edges
8. `DeliveryTest` - 18 edges
9. `clarify_evidence()` - 15 edges
10. `GraphTest` - 14 edges

## Surprising Connections (you probably didn't know these)
- `Working a ticket` --references--> `main()`  [INFERRED]
  CLAUDE.md → harness/cli.py
- `check()` --calls--> `phases_for()`  [EXTRACTED]
  harness/cli.py → harness/checks.py
- `ClarifyGateTest` --uses--> `HarnessError`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/errors.py
- `GateTest` --uses--> `Repository`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/repository.py
- `NonCodeGateTest` --uses--> `HarnessError`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/errors.py

## Import Cycles
- None detected.

## Communities (13 total, 5 thin omitted)

### Community 0 - "require"
Cohesion: 0.05
Nodes (81): argparse, datetime, Run one check and return the evidence to record., run(), advance(), build_parser(), check(), describe() (+73 more)

### Community 1 - ".evaluate"
Cohesion: 0.10
Nodes (10): advance_record(), check_record(), ClarifyGateTest, GateTest, NonCodeGateTest, What each stage gate proves before a ticket may leave its stage. The three…, RequiredFieldTest, ReviewGateTest (+2 more)

### Community 2 - ".start"
Cohesion: 0.11
Nodes (11): AdvanceTest, BranchTest, clarify_evidence(), CommandTest, DraftTest, NoteAndCheckTest, Runs commands in process, which is how the tests stay fast and readable., ReturnTest (+3 more)

### Community 3 - "Repository"
Cohesion: 0.08
Nodes (12): Every file in the project that git can see, ignored files excluded., Journal files git has seen change after the commit that created them. The hash…, Whether the remote already holds this commit as the tip of this branch., The working copy a harness command operates on., Refuse to operate from a subdirectory or from another repository., The branch, or None on a detached HEAD. Reporting commands use this, so…, Resolve a project-relative path that must exist inside the project., Every path git reports as changed, with renames resolved to both sides. (+4 more)

### Community 4 - "HarnessError"
Cohesion: 0.06
Nodes (36): Exception, harness, phases_for(), Running and recording a verification command. A check is a real subprocess in…, HarnessError, The one error type a harness command may fail with, and the check that raises…, A refusal a person can act on: what is wrong and, where possible, what to do., Asking graphify a question and keeping the answer in the journal. The harness… (+28 more)

### Community 5 - "doctor.py"
Cohesion: 0.15
Nodes (16): gitignore_problems(), journal_problems(), link_problems(), python_problems(), The self-check a session runs before it starts working. It reports problems…, Run every check and collect what is wrong., Journals whose chain, numbering or contents no longer verify., Records git has seen change after the commit that created them. The chain makes… (+8 more)

### Community 6 - "Seen: Claude Code entry point"
Cohesion: 0.29
Nodes (6): graphify, Ground rules, Index of docs/, Seen: Claude Code entry point, Tickets (92, 324 build points), Working a ticket

### Community 10 - "GraphTest"
Cohesion: 0.29
Nodes (3): CommandTest, GraphTest, A graphify on PATH that reports what it was asked, and nothing else.

## Knowledge Gaps
- **4 isolated node(s):** `graphify-mcp`, `Ground rules`, `Tickets (92, 324 build points)`, `graphify`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 100 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HarnessError` connect `HarnessError` to `require`, `.evaluate`, `.start`, `Repository`, `doctor.py`, `RecordTest`, `DoctorTest`, `DeliveryTest`?**
  _High betweenness centrality (0.383) - this node is a cross-community bridge._
- **Why does `Repository` connect `Repository` to `require`, `.evaluate`, `HarnessError`, `DoctorTest`, `DeliveryTest`, `GraphTest`?**
  _High betweenness centrality (0.172) - this node is a cross-community bridge._
- **Why does `require()` connect `require` to `Repository`, `HarnessError`, `doctor.py`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `HarnessError` (e.g. with `journal_problems()` and `Repository`) actually correct?**
  _`HarnessError` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `Repository` (e.g. with `HarnessError` and `DeliveryTest`) actually correct?**
  _`Repository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `execute()` (e.g. with `advance()` and `check()`) actually correct?**
  _`execute()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `DoctorTest` (e.g. with `HarnessError` and `Repository`) actually correct?**
  _`DoctorTest` has 2 INFERRED edges - model-reasoned connections that need verification._