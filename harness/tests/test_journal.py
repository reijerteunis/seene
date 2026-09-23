"""The journal: what a record is, and what makes a chain of them trustworthy."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from harness import journal
from harness.errors import HarnessError


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class RecordTest(unittest.TestCase):

    def setUp(self):
        self.folder = Path(tempfile.mkdtemp()) / 'SEEN-086'

    def append(self, kind='note', stage='clarify', attempt=1, data=None):
        records = journal.read(self.folder)
        return journal.append(self.folder, records, kind=kind, stage=stage, attempt=attempt,
                              actor='claude:implementer', head='0' * 40, ticket='SEEN-086',
                              data={} if data is None else data)

    def test_first_record_is_numbered_one_and_chains_to_nothing(self):
        record = self.append(kind='start')
        self.assertEqual(record['sequence'], 1)
        self.assertIsNone(record['prev_hash'])
        self.assertTrue((self.folder / '0001.json').is_file())

    def test_record_carries_the_full_envelope(self):
        record = self.append(kind='start', data={'ticket_file': 'docs/tickets/x.md'})
        self.assertEqual(list(record), ['sequence', 'ticket', 'timestamp', 'harness_version',
                                        'kind', 'stage', 'attempt', 'actor', 'head',
                                        'prev_hash', 'data'])
        self.assertEqual(record['harness_version'], journal.HARNESS_VERSION)

    def test_prev_hash_is_the_sha256_of_the_previous_file_as_it_sits_on_disk(self):
        self.append(kind='start')
        second = self.append()
        self.assertEqual(second['prev_hash'], digest(self.folder / '0001.json'))

    def test_a_record_file_ends_with_one_newline_and_is_indented(self):
        self.append(kind='start')
        text = (self.folder / '0001.json').read_text()
        self.assertTrue(text.endswith('}\n'))
        self.assertFalse(text.endswith('\n\n'))
        self.assertIn('\n  "ticket": "SEEN-086"', text)

    def test_reading_returns_every_record_in_order(self):
        self.append(kind='start')
        self.append()
        self.append(kind='advance', stage='clarify')
        self.assertEqual([record['sequence'] for record in journal.read(self.folder)], [1, 2, 3])

    def test_reading_an_absent_journal_is_not_an_error(self):
        self.assertEqual(journal.read(self.folder), [])

    def test_an_edited_record_breaks_the_chain(self):
        self.append(kind='start')
        self.append()
        path = self.folder / '0001.json'
        record = json.loads(path.read_text())
        record['actor'] = 'codex:reviewer'
        path.write_text(json.dumps(record, indent=2) + '\n')
        with self.assertRaisesRegex(HarnessError, 'chain'):
            journal.read(self.folder)

    def test_reformatting_a_record_breaks_the_chain(self):
        self.append(kind='start')
        self.append()
        path = self.folder / '0001.json'
        path.write_text(json.dumps(json.loads(path.read_text())) + '\n')
        with self.assertRaisesRegex(HarnessError, 'chain'):
            journal.read(self.folder)

    def test_a_removed_record_is_detected_as_a_gap(self):
        self.append(kind='start')
        self.append()
        self.append()
        (self.folder / '0002.json').unlink()
        with self.assertRaisesRegex(HarnessError, 'missing'):
            journal.read(self.folder)

    def test_a_stray_file_beside_the_records_is_refused(self):
        self.append(kind='start')
        (self.folder / '0001.json.bak').write_text('{}')
        with self.assertRaisesRegex(HarnessError, '0001.json.bak'):
            journal.read(self.folder)

    def test_the_kpi_file_and_attachments_are_allowed_beside_the_records(self):
        self.append(kind='start')
        (self.folder / 'kpi.json').write_text('{}')
        (self.folder / 'attachments').mkdir()
        (self.folder / 'attachments' / 'bol-response.json').write_text('{}')
        self.assertEqual(len(journal.read(self.folder)), 1)

    def test_an_existing_record_is_never_overwritten(self):
        self.append(kind='start')
        records = journal.read(self.folder)
        (self.folder / '0002.json').write_text('{}')
        with self.assertRaises(Exception):
            journal.append(self.folder, records, kind='note', stage='clarify', attempt=1,
                           actor='claude:implementer', head='0' * 40, ticket='SEEN-086', data={})

    def test_an_unknown_kind_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'kind'):
            self.append(kind='approve')

    def test_state_reports_the_stage_and_attempt_of_the_last_record(self):
        self.append(kind='start')
        self.append(kind='return', stage='solution', attempt=2)
        self.assertEqual(journal.state(journal.read(self.folder)),
                         dict(stage='solution', attempt=2, records=2))


if __name__ == '__main__':
    unittest.main()
