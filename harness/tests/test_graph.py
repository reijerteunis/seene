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


class GraphTest(CommandTest):

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

    def test_an_impact_query_is_recorded_as_a_note(self):
        self.stub_graphify()
        record = self.graph('impact', '--about', 'stage gate')
        self.assertEqual(record['kind'], 'note')
        self.assertEqual(record['data']['mode'], 'impact')
        self.assertEqual(record['data']['exit_code'], 0)
        self.assertIn('affected', record['data']['command'])
        self.assertIn('stage gate', record['data']['command'])
        self.assertIn('verb: affected', record['data']['answer'])

    def test_the_record_names_the_graph_that_answered(self):
        self.stub_graphify()
        record = self.graph('impact', '--about', 'stage gate')
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
        with self.assertRaisesRegex(HarnessError, 'about'):
            self.graph('impact')

    def test_a_missing_graph_is_refused_rather_than_recorded_empty(self):
        self.stub_graphify()
        (self.root / 'graphify-out' / 'graph.json').unlink()
        with self.assertRaisesRegex(HarnessError, 'graph'):
            self.graph('impact', '--about', 'stage gate')

    def test_a_failed_query_is_still_recorded(self):
        self.stub_graphify(exit_code=2)
        record = self.graph('impact', '--about', 'nothing here')
        self.assertEqual(record['data']['exit_code'], 2,
                         'a failed query is a fact about the work')

    def test_the_graph_directory_does_not_change_the_reviewed_tree(self):
        from harness.repository import Repository
        repository = Repository(self.root)
        before = repository.fingerprint()
        self.write('graphify-out/graph.json', json.dumps({'nodes': [1], 'edges': []}))
        self.assertNotEqual(before, repository.fingerprint(),
                            'the graph is committed, so it is part of the tree under review')
