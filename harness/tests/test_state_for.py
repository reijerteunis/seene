"""Which ticket a gate is judging against, and whether it admits which one.

SEEN-096 was split three ways, its file was renamed, and every judgement after
that read the snapshot taken before the split: a ticket asking for three tools,
against a record describing one. The score said the record was two thirds short,
which it was, of a ticket that no longer existed.
"""

import json
import unittest

from harness import cli
from harness.errors import HarnessError
from harness.tests.helpers import ProjectTest


class StateForTest(ProjectTest):

    def journal(self, ticket_file, snapshot='# The ticket as it was\n'):
        """Record 1 as start writes it, with the pieces state_for reads."""
        return [dict(sequence=1, ticket='SEEN-001', kind='start', stage='clarify', attempt=1,
                     data=dict(ticket_file=ticket_file, ticket_id='SEEN-001',
                               ticket_snapshot=snapshot)),
                dict(sequence=2, ticket='SEEN-001', kind='advance', stage='clarify', attempt=1,
                     data=dict(evidence={'scope': 'something'}))]

    def state(self, records):
        return cli.state_for(records, dict(stage='clarify', attempt=1), root=self.root)

    def test_the_recorded_path_is_read_when_it_is_there(self):
        state = self.state(self.journal(self.ticket_file))

        self.assertIn('A ticket to work', state['ticket_text'])
        self.assertEqual(state['ticket_source'], 'recorded path')

    def test_a_renamed_ticket_is_found_by_its_id(self):
        """The rename SEEN-096 made, and the silent fallback it exposed."""
        renamed = 'docs/tickets/SEEN-001-renamed-during-clarify.md'
        (self.root / self.ticket_file).rename(self.root / renamed)

        state = self.state(self.journal(self.ticket_file))

        self.assertIn('A ticket to work', state['ticket_text'])
        self.assertEqual(state['ticket_source'], 'found by id')

    def test_the_snapshot_is_used_only_when_no_ticket_matches_and_says_so(self):
        (self.root / self.ticket_file).unlink()

        state = self.state(self.journal(self.ticket_file, snapshot='# Gone\n'))

        self.assertEqual(state['ticket_text'], '# Gone\n')
        self.assertEqual(state['ticket_source'], 'snapshot in record 1')

    def test_two_files_for_one_id_is_a_refusal_naming_both(self):
        """A duplicated id is a mistake worth seeing, not a choice to make.

        Only when the id is what is being resolved by. A recorded path that is
        still there is unambiguous whatever else shares the id.
        """
        (self.root / self.ticket_file).rename(self.root / 'docs/tickets/SEEN-001-renamed.md')
        self.write('docs/tickets/SEEN-001-a-second-file.md', '# Also SEEN-001\n')

        with self.assertRaises(HarnessError) as refused:
            self.state(self.journal(self.ticket_file))

        self.assertIn('renamed', str(refused.exception))
        self.assertIn('a-second-file', str(refused.exception))

    def test_a_shared_id_is_no_obstacle_while_the_recorded_path_is_there(self):
        self.write('docs/tickets/SEEN-001-a-second-file.md', '# Also SEEN-001\n')

        state = self.state(self.journal(self.ticket_file))

        self.assertEqual(state['ticket_source'], 'recorded path')

    def test_a_longer_id_is_not_a_match_for_a_shorter_one(self):
        """SEEN-10 must not glob up SEEN-100."""
        self.write('docs/tickets/SEEN-0011-a-different-ticket.md', '# SEEN-0011\n')
        (self.root / self.ticket_file).rename(
            self.root / 'docs/tickets/SEEN-001-renamed.md')

        state = self.state(self.journal(self.ticket_file))

        self.assertIn('A ticket to work', state['ticket_text'])

    def test_the_id_falls_back_to_the_record_when_record_1_has_no_ticket_id(self):
        """Every journal so far carries ticket_id, but the envelope is the promise."""
        records = self.journal(self.ticket_file)
        del records[0]['data']['ticket_id']
        (self.root / self.ticket_file).rename(self.root / 'docs/tickets/SEEN-001-renamed.md')

        state = self.state(records)

        self.assertEqual(state['ticket_source'], 'found by id')


if __name__ == '__main__':
    unittest.main()
