# Graph Report - seene  (2026-09-23)

## Corpus Check
- 152 files · ~68,295 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .toml 1)

## Summary
- 399 nodes · 939 edges · 16 communities (11 shown, 5 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8feba5f7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- .evaluate
- .start
- Repository
- helpers.py
- doctor.py
- Seen: Claude Code entry point
- RecordTest
- DoctorTest
- DeliveryTest
- GraphTest
- graphify
- require
- SEEN-087: Install graphify, build the repo graph and wire it into both assistants
- SEEN-089: Enforce TDD and CI quality gates in the harness

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
- `ClarifyGateTest` --uses--> `HarnessError`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/errors.py
- `GateTest` --uses--> `Repository`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/repository.py
- `NonCodeGateTest` --uses--> `HarnessError`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/errors.py
- `RequiredFieldTest` --uses--> `HarnessError`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/errors.py

## Import Cycles
- None detected.

## Communities (16 total, 5 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.06
Nodes (50): argparse, phases_for(), Running and recording a verification command. A check is a real subprocess in…, Run one check and return the evidence to record., run(), advance(), build_parser(), check() (+42 more)

### Community 1 - ".evaluate"
Cohesion: 0.10
Nodes (10): advance_record(), check_record(), ClarifyGateTest, GateTest, NonCodeGateTest, What each stage gate proves before a ticket may leave its stage. The three…, RequiredFieldTest, ReviewGateTest (+2 more)

### Community 2 - ".start"
Cohesion: 0.10
Nodes (13): Delivery: the stage gate that writes the receipt, and what it refuses., AdvanceTest, BranchTest, clarify_evidence(), CommandTest, DraftTest, NoteAndCheckTest, One ticket from start to delivered, through the commands a session runs. (+5 more)

### Community 3 - "Repository"
Cohesion: 0.08
Nodes (12): Every file in the project that git can see, ignored files excluded., Journal files git has seen change after the commit that created them. The hash…, Whether the remote already holds this commit as the tip of this branch., The working copy a harness command operates on., Refuse to operate from a subdirectory or from another repository., The branch, or None on a detached HEAD. Reporting commands use this, so…, Resolve a project-relative path that must exist inside the project., Every path git reports as changed, with renames resolved to both sides. (+4 more)

### Community 4 - "helpers.py"
Cohesion: 0.09
Nodes (15): harness_tests, add_remote(), make_project(), ProjectTest, A throwaway project to run harness commands against. Tests never touch the…, A git repository shaped like Seen: a ticket, the harness files, one commit., Base class giving each test its own project and ticket., A bare repository to push to, so delivery can be verified without a network. (+7 more)

### Community 5 - "doctor.py"
Cohesion: 0.17
Nodes (14): gitignore_problems(), journal_problems(), link_problems(), python_problems(), The self-check a session runs before it starts working. It reports problems…, Run every check and collect what is wrong., Journals whose chain, numbering or contents no longer verify., Records git has seen change after the commit that created them. The chain makes… (+6 more)

### Community 6 - "Seen: Claude Code entry point"
Cohesion: 0.29
Nodes (6): graphify, Ground rules, Index of docs/, Seen: Claude Code entry point, Tickets (92, 324 build points), Working a ticket

### Community 10 - "GraphTest"
Cohesion: 0.26
Nodes (4): CommandTest, GraphTest, A graphify on PATH that reports what it was asked, and nothing else., The graph is derived from the tree, not evidence about it. The post-commit hook…

### Community 13 - "require"
Cohesion: 0.07
Nodes (52): datetime, Exception, harness, Read a stage evidence file, which must live where drafts live. Anywhere else it…, read_evidence(), _evidence(), Delivery: the deliver stage's own gate, and the receipt it writes. There is no…, Every record must already be in the history that was pushed. The receipt is the… (+44 more)

### Community 14 - "SEEN-087: Install graphify, build the repo graph and wire it into both assistants"
Cohesion: 0.25
Nodes (7): Acceptance criteria, Blocks, Clarified, Context, Depends on, Description, SEEN-087: Install graphify, build the repo graph and wire it into both assistants

### Community 15 - "SEEN-089: Enforce TDD and CI quality gates in the harness"
Cohesion: 0.25
Nodes (7): Acceptance criteria, Blocks, Carried in from SEEN-087, Context, Depends on, Description, SEEN-089: Enforce TDD and CI quality gates in the harness

## Knowledge Gaps
- **16 isolated node(s):** `Description`, `Acceptance criteria`, `Carried in from SEEN-087`, `Depends on`, `Blocks` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 115 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HarnessError` connect `require` to `cli.py`, `.evaluate`, `.start`, `Repository`, `doctor.py`, `RecordTest`, `DoctorTest`, `DeliveryTest`?**
  _High betweenness centrality (0.352) - this node is a cross-community bridge._
- **Why does `Repository` connect `Repository` to `cli.py`, `.evaluate`, `.start`, `DoctorTest`, `DeliveryTest`, `GraphTest`, `require`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Why does `require()` connect `require` to `cli.py`, `Repository`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `HarnessError` (e.g. with `journal_problems()` and `Repository`) actually correct?**
  _`HarnessError` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `Repository` (e.g. with `HarnessError` and `DeliveryTest`) actually correct?**
  _`Repository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `execute()` (e.g. with `advance()` and `check()`) actually correct?**
  _`execute()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `DoctorTest` (e.g. with `HarnessError` and `Repository`) actually correct?**
  _`DoctorTest` has 2 INFERRED edges - model-reasoned connections that need verification._