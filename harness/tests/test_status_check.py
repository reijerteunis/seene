import unittest
"""A ticket's status, against the journal beside it.

Two tickets sat at doing for hours after they had delivered and merged, because
both mark-done commits were lost in a rebase and nothing compared the two.
"""

from harness import doctor, journal
from harness.repository import Repository
from harness.tests.test_lifecycle import CommandTest


class StatusAgainstJournalTest(CommandTest):

    def ticket(self, identifier, status):
        self.write(f'docs/tickets/{identifier}-a-thing.md',
                   f'---\nid: {identifier}\nestimate: 2\nstatus: {status}\n---\n# {identifier}\n')

    def journal_for(self, identifier, stage='tdd', receipt_commit=None):
        folder = self.root / 'docs' / 'harness' / 'history' / identifier
        records = journal.read(folder)
        records = [journal.append(folder, records, kind='start', stage='clarify', attempt=1,
                                  actor='claude:implementer', head='0' * 40, ticket=identifier,
                                  data=dict(ticket_file='docs/tickets/x.md', ticket_snapshot='x',
                                            base_commit='0' * 40))]
        if receipt_commit:
            journal.append(folder, records, kind='receipt', stage='deliver', attempt=1,
                           actor='claude:implementer', head=receipt_commit, ticket=identifier,
                           data=dict(from_stage='deliver', to_stage='delivered',
                                     commit=receipt_commit, tree='t' * 64))
        else:
            journal.append(folder, records, kind='advance', stage='clarify', attempt=1,
                           actor='claude:implementer', head='0' * 40, ticket=identifier,
                           data=dict(from_stage='clarify', to_stage=stage, evidence={},
                                     decisions=[]))

    def problems(self):
        return doctor.status_problems(Repository(self.root))

    def merged_commit(self):
        """A commit that is on main, which is what a merged receipt attests."""
        return self.git('rev-parse', 'main')

    def test_a_merged_receipt_with_a_status_of_doing_is_reported(self):
        self.ticket('SEEN-300', 'doing')
        self.journal_for('SEEN-300', receipt_commit=self.merged_commit())

        found = self.problems()

        self.assertTrue(any('SEEN-300' in problem and 'doing' in problem for problem in found),
                        found)

    def test_a_merged_receipt_with_a_status_of_done_passes(self):
        self.ticket('SEEN-301', 'done')
        self.journal_for('SEEN-301', receipt_commit=self.merged_commit())

        self.assertEqual([p for p in self.problems() if 'SEEN-301' in p], [])

    def test_a_delivered_receipt_not_yet_merged_may_say_review(self):
        """The normal state between writing a receipt and pressing merge."""
        self.ticket('SEEN-302', 'review')
        self.journal_for('SEEN-302', receipt_commit='f' * 40)

        self.assertEqual([p for p in self.problems() if 'SEEN-302' in p], [])

    def test_a_working_stage_that_says_done_is_reported(self):
        self.ticket('SEEN-303', 'done')
        self.journal_for('SEEN-303', stage='tdd')

        self.assertTrue(any('SEEN-303' in problem for problem in self.problems()))

    def test_a_working_stage_that_says_todo_is_reported(self):
        self.ticket('SEEN-304', 'todo')
        self.journal_for('SEEN-304', stage='solution')

        self.assertTrue(any('SEEN-304' in problem for problem in self.problems()))

    def test_a_working_stage_that_says_doing_passes(self):
        self.ticket('SEEN-305', 'doing')
        self.journal_for('SEEN-305', stage='tdd')

        self.assertEqual([p for p in self.problems() if 'SEEN-305' in p], [])

    def test_an_unstarted_ticket_is_not_reported(self):
        """Eighty tickets are todo with no journal; saying so every run is noise."""
        self.ticket('SEEN-306', 'todo')

        self.assertEqual([p for p in self.problems() if 'SEEN-306' in p], [])

    def test_the_bootstrap_may_be_done_with_no_journal(self):
        self.ticket(doctor.BOOTSTRAP, 'done')

        self.assertEqual([p for p in self.problems() if doctor.BOOTSTRAP in p], [])

    def test_any_other_ticket_done_with_no_journal_is_reported(self):
        self.ticket('SEEN-307', 'done')

        self.assertTrue(any('SEEN-307' in problem for problem in self.problems()))

    def test_the_check_repairs_nothing(self):
        self.ticket('SEEN-308', 'doing')
        self.journal_for('SEEN-308', receipt_commit=self.merged_commit())

        self.problems()

        text = (self.root / 'docs' / 'tickets' / 'SEEN-308-a-thing.md').read_text()
        self.assertIn('status: doing', text, 'a self-check reports, never repairs')

if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
