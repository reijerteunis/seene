# Graph Report - seene  (2026-09-23)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 371 nodes · 926 edges · 12 communities (7 shown, 5 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 38 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5d799d93`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10

## God Nodes (most connected - your core abstractions)
1. `require()` - 49 edges
2. `HarnessError` - 43 edges
3. `Repository` - 38 edges
4. `execute()` - 23 edges
5. `CommandTest` - 20 edges
6. `DoctorTest` - 20 edges
7. `RecordTest` - 19 edges
8. `DeliveryTest` - 18 edges
9. `GraphTest` - 16 edges
10. `clarify_evidence()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `ClarifyGateTest` --uses--> `HarnessError`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/errors.py
- `GateTest` --uses--> `Repository`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/repository.py
- `NonCodeGateTest` --uses--> `HarnessError`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/errors.py
- `RequiredFieldTest` --uses--> `HarnessError`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/errors.py
- `ReviewGateTest` --uses--> `HarnessError`  [INFERRED]
  harness/tests/test_stage_gates.py → harness/errors.py

## Import Cycles
- None detected.

## Communities (12 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (66): argparse, datetime, phases_for(), Running and recording a verification command. A check is a real subprocess in…, Run one check and return the evidence to record., run(), advance(), build_parser() (+58 more)

### Community 1 - "Community 1"
Cohesion: 0.10
Nodes (10): advance_record(), check_record(), ClarifyGateTest, GateTest, NonCodeGateTest, What each stage gate proves before a ticket may leave its stage. The three…, RequiredFieldTest, ReviewGateTest (+2 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (11): AdvanceTest, BranchTest, clarify_evidence(), CommandTest, DraftTest, NoteAndCheckTest, Runs commands in process, which is how the tests stay fast and readable., ReturnTest (+3 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (14): Git access, and the fingerprint that decides whether evidence is still current.…, Every file in the project that git can see, ignored files excluded., Journal files git has seen change after the commit that created them. The hash…, Whether the remote already holds this commit as the tip of this branch., The working copy a harness command operates on., Refuse to operate from a subdirectory or from another repository., The branch, or None on a detached HEAD. Reporting commands use this, so…, Resolve a project-relative path that must exist inside the project. (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (20): Entry point: python3 harness/run.py <command>., harness_tests, add_remote(), make_project(), ProjectTest, A throwaway project to run harness commands against. Tests never touch the…, A git repository shaped like Seen: a ticket, the harness files, one commit., Base class giving each test its own project and ticket. (+12 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (23): Exception, harness, gitignore_problems(), journal_problems(), link_problems(), python_problems(), The self-check a session runs before it starts working. It reports problems…, Run every check and collect what is wrong. (+15 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (23): _evidence(), cited_check(), _clarify(), evaluate(), _filled(), latest_evidence(), load_template(), _non_code() (+15 more)

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HarnessError` connect `Community 5` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 10`?**
  _High betweenness centrality (0.451) - this node is a cross-community bridge._
- **Why does `Repository` connect `Community 3` to `Community 0`, `Community 1`, `Community 4`, `Community 5`, `Community 8`, `Community 9`, `Community 10`?**
  _High betweenness centrality (0.174) - this node is a cross-community bridge._
- **Why does `require()` connect `Community 0` to `Community 3`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `HarnessError` (e.g. with `list_tickets()` and `main()`) actually correct?**
  _`HarnessError` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `Repository` (e.g. with `HarnessError` and `DeliveryTest`) actually correct?**
  _`Repository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `execute()` (e.g. with `advance()` and `check()`) actually correct?**
  _`execute()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05754385964912281 - nodes in this community are weakly interconnected._