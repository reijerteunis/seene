"""Git access, and the fingerprint that decides whether evidence is still current."""

import unittest
from harness.errors import HarnessError
from harness.repository import Repository
from harness.tests.helpers import ProjectTest


class RepositoryTest(ProjectTest):

    def setUp(self):
        super().setUp()
        self.repository = Repository(self.root)

    def test_it_reports_the_branch_and_head(self):
        self.assertEqual(self.repository.branch(), 'claude/SEEN-001-a-ticket-to-work')
        self.assertEqual(len(self.repository.head()), 40)

    def test_it_refuses_a_path_outside_the_project(self):
        with self.assertRaisesRegex(HarnessError, 'inside'):
            self.repository.file_inside('../escape.md')

    def test_a_changed_file_changes_the_fingerprint(self):
        before = self.repository.fingerprint()
        self.write('docs/tickets/other.md', 'new work')
        self.assertNotEqual(before, self.repository.fingerprint())

    def test_the_journal_and_drafts_do_not_change_the_fingerprint(self):
        before = self.repository.fingerprint()
        self.write('docs/harness/history/SEEN-001/0001.json', '{}')
        self.write('.harness-drafts/SEEN-001-clarify.json', '{}')
        self.assertEqual(before, self.repository.fingerprint(),
                         'recording evidence about a tree must not change that tree')

    def test_a_committed_change_still_changes_the_fingerprint(self):
        before = self.repository.fingerprint()
        self.write('docs/tickets/other.md', 'new work')
        self.git('add', '-A')
        self.git('commit', '-m', 'feat: more')
        self.assertNotEqual(before, self.repository.fingerprint())

    def test_it_reports_whether_the_tree_is_clean(self):
        self.assertTrue(self.repository.is_clean())
        self.write('docs/tickets/other.md', 'new work')
        self.assertFalse(self.repository.is_clean())

    def test_it_finds_journal_records_that_were_committed_as_modifications(self):
        record = self.write('docs/harness/history/SEEN-001/0001.json', '{"sequence": 1}')
        self.git('add', '-A')
        self.git('commit', '-m', 'docs: record')
        self.assertEqual(self.repository.rewritten_history_records(), [])
        record.write_text('{"sequence": 1, "actor": "someone else"}')
        self.git('add', '-A')
        self.git('commit', '-m', 'docs: quietly change the record')
        self.assertEqual(self.repository.rewritten_history_records(),
                         ['docs/harness/history/SEEN-001/0001.json'])

    def test_it_refuses_to_run_from_a_subdirectory(self):
        with self.assertRaisesRegex(HarnessError, 'root'):
            Repository(self.root / 'docs').require_is_root()

if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
