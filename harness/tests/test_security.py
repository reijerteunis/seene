"""The controls that cannot be skipped.

Each one sits at the single place it applies: the record writer, the source
tree, the git hook. A control with six call sites has six ways to be forgotten.
"""

import unittest
import json
import os

from harness import journal, secrets
from harness.errors import HarnessError
from harness.tests.test_lifecycle import CommandTest


class EnvironmentValueTest(CommandTest):
    """No record carries a credential, whatever kind of record it is."""

    def setUp(self):
        super().setUp()
        self.start()
        os.environ['SEEN_TEST_TOKEN'] = 'sk-live-4f2b9c1d8e7a6b5c'
        self.addCleanup(os.environ.pop, 'SEEN_TEST_TOKEN', None)

    def folder(self):
        return self.root / 'docs' / 'harness' / 'history' / self.ticket_id

    def test_a_record_carrying_an_environment_value_is_refused(self):
        records = journal.read(self.folder())
        with self.assertRaisesRegex(HarnessError, 'SEEN_TEST_TOKEN'):
            journal.append(self.folder(), records, kind='note', stage='clarify', attempt=1,
                           actor='claude:implementer', head='0' * 40, ticket=self.ticket_id,
                           data=dict(text='the token is sk-live-4f2b9c1d8e7a6b5c'))

    def test_the_refusal_names_the_variable_and_not_its_value(self):
        records = journal.read(self.folder())
        try:
            journal.append(self.folder(), records, kind='note', stage='clarify', attempt=1,
                           actor='claude:implementer', head='0' * 40, ticket=self.ticket_id,
                           data=dict(text='sk-live-4f2b9c1d8e7a6b5c'))
            self.fail('the record should have been refused')
        except HarnessError as error:
            self.assertIn('SEEN_TEST_TOKEN', str(error))
            self.assertNotIn('sk-live-4f2b9c1d8e7a6b5c', str(error),
                             'a refusal that prints the secret has leaked it')

    def test_nothing_was_written(self):
        before = len(list(self.folder().glob('*.json')))
        with self.assertRaises(HarnessError):
            journal.append(self.folder(), journal.read(self.folder()), kind='note',
                           stage='clarify', attempt=1, actor='claude:implementer',
                           head='0' * 40, ticket=self.ticket_id,
                           data=dict(text='sk-live-4f2b9c1d8e7a6b5c'))
        self.assertEqual(len(list(self.folder().glob('*.json'))), before)

    def test_a_path_shaped_variable_does_not_refuse_an_ordinary_record(self):
        """A journal record legitimately contains file paths, so PATH is skipped."""
        record = journal.append(self.folder(), journal.read(self.folder()), kind='note',
                                stage='clarify', attempt=1, actor='claude:implementer',
                                head='0' * 40, ticket=self.ticket_id,
                                data=dict(text=f'the home directory is {os.environ.get("HOME")}'))
        self.assertEqual(record['kind'], 'note')

    def test_a_short_variable_is_not_treated_as_a_credential(self):
        os.environ['SEEN_TEST_SHORT'] = 'red'
        self.addCleanup(os.environ.pop, 'SEEN_TEST_SHORT', None)
        record = journal.append(self.folder(), journal.read(self.folder()), kind='note',
                                stage='clarify', attempt=1, actor='claude:implementer',
                                head='0' * 40, ticket=self.ticket_id,
                                data=dict(text='the check was red'))
        self.assertEqual(record['kind'], 'note')


class MarketplaceHostTest(CommandTest):
    """No test may call a live marketplace, and the lint is what says so."""

    def test_a_live_host_in_a_test_file_is_found(self):
        live = "const base = 'https://api.bol.com/retailer';\n"  # harness-allow-marketplace-host
        self.write('packages/connectors/src/bol.test.ts', live)
        found = secrets.marketplace_hosts(self.root)
        self.assertEqual(len(found), 1)
        self.assertIn('api.bol.com', found[0]['host'])  # harness-allow-marketplace-host
        self.assertIn('bol.test.ts', found[0]['path'])

    def test_every_marketplace_is_covered(self):
        for index, host in enumerate(secrets.MARKETPLACE_HOSTS):
            self.write(f'packages/connectors/src/case{index}.test.ts', f"const url = '{host}';\n")
        self.assertEqual(len(secrets.marketplace_hosts(self.root)), len(secrets.MARKETPLACE_HOSTS))

    def test_a_fixture_name_is_not_a_live_call(self):
        self.write('packages/connectors/src/bol.test.ts',
                   "import orders from './fixtures/bol-orders.json';\n")
        self.assertEqual(secrets.marketplace_hosts(self.root), [])

    def test_source_files_are_not_linted_because_the_connector_must_name_its_api(self):
        source = "export const BASE = 'https://api.bol.com/retailer';\n"  # harness-allow-marketplace-host
        self.write('packages/connectors/src/bol.ts', source)
        self.assertEqual(secrets.marketplace_hosts(self.root), [])


class ShellUseTest(CommandTest):
    """Ticket text and payloads are data, and data never reaches a shell."""

    def test_no_harness_source_runs_a_shell(self):
        from harness.tests import helpers
        found = secrets.shell_use(helpers.HARNESS)
        self.assertEqual(found, [], f'harness source must not use a shell: {found}')


class LintExemptionTest(CommandTest):
    """A line may name a host when naming it is the point, and must say so."""

    def test_a_marked_line_is_not_reported(self):
        self.write('packages/connectors/src/bol.test.ts',
                   "// the lint must catch this: "
                   f"{'api' + '.bol.com'}  {secrets.ALLOW_MARKER}\n")
        self.assertEqual(secrets.marketplace_hosts(self.root), [])

    def test_an_unmarked_line_in_the_same_file_is_still_reported(self):
        self.write('packages/connectors/src/bol.test.ts',
                   f"const allowed = '{'api' + '.bol.com'}';  {secrets.ALLOW_MARKER}\n"
                   f"const sneaky = '{'api' + '.bol.com'}';\n")
        found = secrets.marketplace_hosts(self.root)
        self.assertEqual([entry['line'] for entry in found], [2])


class DiscardTest(CommandTest):
    """Removing a journal, which the harness could not do until now.

    It exists because people start tickets by mistake, and doing it by hand is
    worse than doing it through something that refuses the dangerous cases.
    """

    def setUp(self):
        super().setUp()
        self.start()

    def discard(self, *args):
        return self.run_harness('discard', self.ticket_id, '--reason', 'Started by mistake',
                                '--actor', 'human:implementer', *args)

    def test_it_refuses_without_the_ticket_typed_out(self):
        with self.assertRaisesRegex(HarnessError, 'confirm'):
            self.discard()

    def test_it_refuses_when_the_confirmation_does_not_match(self):
        with self.assertRaisesRegex(HarnessError, 'confirm'):
            self.discard('--confirm', 'SEEN-999')

    def test_it_refuses_once_a_record_is_committed(self):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'docs: the journal')
        with self.assertRaisesRegex(HarnessError, 'committed'):
            self.discard('--confirm', self.ticket_id)

    def test_it_writes_what_it_removed_before_removing_it(self):
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        self.assertTrue(folder.is_dir())

        result = self.discard('--confirm', self.ticket_id)

        self.assertFalse(folder.exists(), 'the journal is gone')
        log = (self.root / 'docs' / 'harness' / 'discarded.jsonl').read_text().strip().splitlines()
        entry = json.loads(log[-1])
        self.assertEqual(entry['ticket'], self.ticket_id)
        self.assertEqual(entry['actor'], 'human:implementer')
        self.assertIn('mistake', entry['reason'])
        self.assertEqual(len(entry['records']), 1)
        self.assertEqual(len(entry['records'][0]['sha256']), 64)
        self.assertEqual(result['removed'], 1)

    def test_the_decision_is_recorded_beside_the_removal(self):
        result = self.discard('--confirm', self.ticket_id)
        log = (self.root / 'docs' / 'harness' / 'discarded.jsonl').read_text().strip().splitlines()
        entry = json.loads(log[-1])
        self.assertEqual(entry['decision']['question'], 'is_destructive')
        self.assertIn(entry['decision']['source'], ('jev', 'human', 'unavailable'))
        self.assertEqual(result['ticket'], self.ticket_id)


class FalsePositiveTest(CommandTest):
    """A rule that refuses ordinary words is a rule people turn off.

    CI found this one: GITHUB_EVENT_NAME is pull_request on a pull request, and
    a delivery record legitimately contains those words.
    """

    def setUp(self):
        super().setUp()
        self.start()

    def folder(self):
        return self.root / 'docs' / 'harness' / 'history' / self.ticket_id

    def append(self, text):
        return journal.append(self.folder(), journal.read(self.folder()), kind='note',
                              stage='clarify', attempt=1, actor='claude:implementer',
                              head='0' * 40, ticket=self.ticket_id, data=dict(text=text))

    def test_an_ordinary_word_in_the_environment_does_not_refuse_a_record(self):
        os.environ['GITHUB_EVENT_NAME'] = 'pull_request'
        self.addCleanup(os.environ.pop, 'GITHUB_EVENT_NAME', None)
        self.assertEqual(self.append('opened as a pull_request')['kind'], 'note')

    def test_a_git_ref_in_the_environment_does_not_refuse_a_record(self):
        os.environ['GITHUB_REF'] = 'refs/pull/8/merge'
        self.addCleanup(os.environ.pop, 'GITHUB_REF', None)
        self.assertEqual(self.append('merged from refs/pull/8/merge')['kind'], 'note')

    def test_a_variable_named_like_a_credential_is_still_caught_however_short(self):
        os.environ['SOME_API_TOKEN'] = 'abc123def456'
        self.addCleanup(os.environ.pop, 'SOME_API_TOKEN', None)
        with self.assertRaisesRegex(HarnessError, 'SOME_API_TOKEN'):
            self.append('the token is abc123def456')

    def test_a_long_mixed_value_is_caught_whatever_it_is_called(self):
        os.environ['SEEN_TEST_OPAQUE'] = 'Xk29fJq8Lm4zPw7bTn5cRv3y'
        self.addCleanup(os.environ.pop, 'SEEN_TEST_OPAQUE', None)
        with self.assertRaisesRegex(HarnessError, 'SEEN_TEST_OPAQUE'):
            self.append('it was Xk29fJq8Lm4zPw7bTn5cRv3y')

if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
