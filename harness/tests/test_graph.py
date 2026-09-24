"""The graph command: a thin wrapper that records what graphify answered.

The harness does not traverse the graph itself. It runs one graphify verb, keeps
the answer in the journal with the hash of the graph that produced it, and stays
out of the way.
"""

import json
import os
import stat

from harness.errors import HarnessError
from harness.tests.test_lifecycle import CommandTest

STUB = """#!/bin/sh
echo "verb: $1"
echo "args: $@"
exit %d
"""


class GraphFixture(CommandTest):
    """Stubs and helpers. No tests of its own, so nothing is run twice."""

    def setUp(self):
        super().setUp()
        self.start()
        self.write('graphify-out/graph.json', json.dumps({'nodes': [], 'edges': []}))

    def stub_graphify(self, exit_code=0):
        """A graphify on PATH that reports what it was asked, and nothing else."""
        binaries = self.root / '.harness-drafts' / 'bin'
        binaries.mkdir(parents=True, exist_ok=True)
        stub = binaries / 'graphify'
        stub.write_text(STUB % exit_code)
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
        os.environ['PATH'] = f'{binaries}{os.pathsep}{os.environ["PATH"]}'
        self.addCleanup(lambda: os.environ.__setitem__(
            'PATH', os.environ['PATH'].replace(f'{binaries}{os.pathsep}', '')))

    def graph(self, *args):
        return self.run_harness('graph', self.ticket_id, *args,
                                '--actor', 'claude:implementer')


class GraphTest(GraphFixture):
    """The recording mechanics, exercised through the graphify modes."""

    def test_a_query_is_recorded_as_a_note(self):
        self.stub_graphify()
        record = self.graph('prs')
        self.assertEqual(record['kind'], 'note')
        self.assertEqual(record['data']['mode'], 'prs')
        self.assertEqual(record['data']['exit_code'], 0)
        self.assertIn('verb: prs', record['data']['answer'])

    def test_the_record_names_the_graph_that_answered(self):
        self.stub_graphify()
        record = self.graph('prs')
        self.assertEqual(len(record['data']['graph_sha256']), 64)

    def test_a_path_query_carries_both_ends(self):
        self.stub_graphify()
        record = self.graph('path', '--from', 'advance', '--to', 'journal.append')
        self.assertEqual(record['data']['mode'], 'path')
        self.assertIn('advance', record['data']['command'])
        self.assertIn('journal.append', record['data']['command'])

    def test_prs_needs_no_subject(self):
        self.stub_graphify()
        self.assertEqual(self.graph('prs')['data']['mode'], 'prs')

    def test_an_unknown_mode_names_the_ones_that_work(self):
        self.stub_graphify()
        with self.assertRaisesRegex(HarnessError, 'impact'):
            self.graph('god-nodes', '--about', 'x')

    def test_a_query_without_its_subject_is_refused(self):
        self.stub_graphify()
        with self.assertRaisesRegex(HarnessError, 'from'):
            self.graph('path')

    def test_a_missing_graph_is_refused_rather_than_recorded_empty(self):
        self.stub_graphify()
        (self.root / 'graphify-out' / 'graph.json').unlink()
        with self.assertRaisesRegex(HarnessError, 'graph'):
            self.graph('prs')

    def test_a_failed_query_is_still_recorded(self):
        self.stub_graphify(exit_code=2)
        record = self.graph('prs')
        self.assertEqual(record['data']['exit_code'], 2,
                         'a failed query is a fact about the work')

    def test_the_graph_does_not_change_the_reviewed_tree(self):
        """The graph is derived from the tree, not evidence about it.

        The post-commit hook rewrites it in the background after every commit,
        so counting it would make delivery refuse a ticket for a change the tool
        made rather than a person.
        """
        from harness.repository import Repository
        repository = Repository(self.root)
        before = repository.fingerprint()
        self.write('graphify-out/graph.json', json.dumps({'nodes': [1], 'edges': []}))
        self.write('graphify-out/GRAPH_REPORT.md', '# rebuilt\n')
        self.assertEqual(before, repository.fingerprint())


CODEGRAPH_STUB = """#!/bin/sh
if [ "$1" = "sync" ]; then
  echo "synced"
  exit 0
fi
if [ "$1" = "status" ]; then
  echo "  Nodes:     962"
  echo "  Edges:     2,583"
  exit 0
fi
echo "codegraph: $@"
exit %d
"""


class RoutingTest(GraphFixture):
    """Which tool answers which question.

    codegraph indexes symbols, so it answers impact and explain. graphify knows
    files, commits and pull requests, so it keeps path and prs. Installing
    codegraph established the one thing that shapes this: there is no standing
    daemon, the watcher belongs to the MCP server an assistant starts, so a
    shell command syncs before it asks. Recorded in this ticket's journal at
    record 13.
    """

    def stub_codegraph(self, exit_code=0):
        binaries = self.root / '.harness-drafts' / 'bin'
        binaries.mkdir(parents=True, exist_ok=True)
        stub = binaries / 'codegraph'
        stub.write_text(CODEGRAPH_STUB % exit_code)
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
        (self.root / '.codegraph').mkdir(exist_ok=True)
        os.environ['PATH'] = f'{binaries}{os.pathsep}{os.environ["PATH"]}'
        self.addCleanup(lambda: os.environ.__setitem__(
            'PATH', os.environ['PATH'].replace(f'{binaries}{os.pathsep}', '')))

    def test_impact_asks_codegraph(self):
        self.stub_codegraph()
        record = self.graph('impact', '--about', 'state_for')

        self.assertEqual(record['data']['source'], 'codegraph')
        self.assertEqual(record['data']['command'][0], 'codegraph')
        self.assertIn('state_for', record['data']['command'])

    def test_explain_asks_codegraph(self):
        self.stub_codegraph()
        record = self.graph('explain', '--about', 'state_for')

        self.assertEqual(record['data']['source'], 'codegraph')

    def test_path_and_prs_stay_with_graphify(self):
        """A guard, not a change: graphify knows files and pull requests."""
        self.stub_graphify()
        self.stub_codegraph()

        self.assertEqual(self.graph('path', '--from', 'a', '--to', 'b')['data']['source'],
                         'graphify')
        self.assertEqual(self.graph('prs')['data']['source'], 'graphify')

    def test_a_codegraph_query_syncs_first_and_records_that_it_did(self):
        """Without the MCP server running, the index is as old as the last sync."""
        self.stub_codegraph()
        record = self.graph('impact', '--about', 'state_for')

        self.assertTrue(record['data']['synced'])

    def test_the_record_fingerprints_the_index_that_answered(self):
        self.stub_codegraph()
        record = self.graph('impact', '--about', 'state_for')

        self.assertEqual(record['data']['index'], {'nodes': 962, 'edges': 2583})

    def test_impact_still_refuses_without_its_subject(self):
        self.stub_codegraph()
        with self.assertRaisesRegex(HarnessError, 'about'):
            self.graph('impact')

    def test_a_missing_index_is_refused_rather_than_answered_from_nothing(self):
        self.stub_codegraph()
        (self.root / '.codegraph').rmdir()
        with self.assertRaisesRegex(HarnessError, 'codegraph'):
            self.graph('impact', '--about', 'state_for')
