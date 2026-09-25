"""Delivery: the stage gate that writes the receipt, and what it refuses."""

import json

from harness.errors import HarnessError
from harness.tests import helpers
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence


class DeliveryWalk(CommandTest):
    """The walk to a delivered ticket, without the tests.

    Separated so other files can reuse the walk without inheriting, and running,
    every delivery test with it.
    """

    def setUp(self):
        super().setUp()
        self.remote = helpers.add_remote(self.root)
        self._stub_github()

    def _stub_github(self):
        """No test reaches GitHub. Green by default; a test that cares says otherwise."""
        from harness import github
        github.CHECKS = lambda repository, commit: [
            dict(name='Harness tests (Python 3.12)', status='completed', conclusion='success')]
        github.PULL_REQUEST = lambda repository: dict(
            number=1, body='receipt pending', headRefName='claude/SEEN-001-a-ticket-to-work')
        self.addCleanup(setattr, github, 'CHECKS', None)
        self.addCleanup(setattr, github, 'PULL_REQUEST', None)

    def walk_to_deliver(self):
        """Take a ticket through every stage, with real recorded checks."""
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())
        self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                         'claude:implementer', '--', 'sh', '-c', 'echo expected 1, got 0; exit 1')
        self.run_harness('check', self.ticket_id, '--phase', 'green', '--actor',
                         'claude:implementer', '--', 'true')
        self.run_harness('check', self.ticket_id, '--phase', 'regression', '--actor',
                         'claude:implementer', '--', 'true')
        # The coverage gate wants a measurement for the attempt; the summary is a
        # fixture here, because what is under test is delivery, not vitest.
        self.write('packages/core/coverage/coverage-summary.json',
                   '{"total": {"lines": {"total": 10, "covered": 9, "skipped": 0, "pct": 90.0}}}')
        self.run_harness('coverage', self.ticket_id, '--actor', 'claude:implementer', '--', 'true')
        red, green, regression = 4, 5, 6
        self.submit('tdd', dict(mode='code',
                                slices=[dict(position=1, behaviour='The harness records a delivery',
                                             failure_reason='expected 1, got 0',
                                             red=red, green=green)],
                                regression=regression,
                                coverage_delta=None))
        self.run_harness('check', self.ticket_id, '--phase', 'qa', '--actor',
                         'codex:reviewer', '--', 'true')
        self.submit('review', dict(reviewer='codex:reviewer',
                                   independence='independent',
                                   read=['harness/journal.py'],
                                   acceptance_evidence=['The journal holds every stage'],
                                   findings=[],
                                   checks=[9],
                                   security_checklist=['No secret in the diff'],
                                   verdict='pass'),
                    actor='codex:reviewer')

    def deliver_evidence(self, **changes):
        data = dict(remote='origin', pull_request='https://github.test/seen/pull/1',
                    limits=['The CI check lands with SEEN-089'])
        data.update(changes)
        return data

    def commit_and_push(self, message='docs: the journal so far'):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', message)
        self.git('push', '-q', '-u', 'origin', 'HEAD')

    def verify(self, **changes):
        relative = f'.harness-drafts/{self.ticket_id}-deliver.json'
        self.write(relative, json.dumps(self.deliver_evidence(**changes)))
        return self.run_harness('verify-delivery', self.ticket_id, '--file', relative,
                                '--actor', 'claude:implementer')


class DeliveryTest(DeliveryWalk):

    def test_a_delivered_ticket_has_a_receipt_and_a_terminal_stage(self):
        self.walk_to_deliver()
        self.commit_and_push()
        result = self.verify()
        self.assertEqual(len(result['receipt_sha256']), 64)
        self.assertEqual(result['record']['data']['to_stage'], 'delivered')
        self.assertEqual(self.run_harness('status', self.ticket_id)['stage'], 'delivered')

    def test_the_receipt_hash_is_the_sha256_of_the_receipt_file(self):
        self.walk_to_deliver()
        self.commit_and_push()
        result = self.verify()
        import hashlib
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        path = folder / f'{result["record"]["sequence"]:04d}.json'
        self.assertEqual(result['receipt_sha256'],
                         hashlib.sha256(path.read_bytes()).hexdigest())

    def test_the_receipt_survives_the_journal_commit_that_carries_it(self):
        self.walk_to_deliver()
        self.commit_and_push()
        before = self.verify()['record']['data']['tree']
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'docs(SEEN-001): record delivery receipt')
        from harness.repository import Repository
        self.assertEqual(Repository(self.root).fingerprint(), before,
                         'committing the receipt must not invalidate the receipt')

    def test_delivery_is_refused_before_the_ticket_reaches_deliver(self):
        self.start()
        with self.assertRaisesRegex(HarnessError, 'deliver'):
            self.verify()

    def test_delivery_is_refused_when_the_tree_changed_after_review(self):
        self.walk_to_deliver()
        self.commit_and_push()
        self.write('docs/tickets/late-edit.md', 'changed after review')
        with self.assertRaisesRegex(HarnessError, 'changed'):
            self.verify()

    def test_delivery_is_refused_when_the_commit_is_not_on_the_remote(self):
        self.walk_to_deliver()
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'docs: not pushed')
        with self.assertRaisesRegex(HarnessError, 'remote'):
            self.verify()

    def test_delivery_is_refused_when_a_record_is_not_committed(self):
        self.walk_to_deliver()
        self.commit_and_push()
        self.write('.harness-drafts/note.md', 'One more thought.')
        self.run_harness('note', self.ticket_id, '--file', '.harness-drafts/note.md',
                         '--actor', 'claude:implementer')
        with self.assertRaisesRegex(HarnessError, 'Commit and push the journal'):
            self.verify()

    def test_a_delivered_ticket_takes_no_further_records(self):
        self.walk_to_deliver()
        self.commit_and_push()
        self.verify()
        self.write('.harness-drafts/note.md', 'An afterthought.')
        with self.assertRaisesRegex(HarnessError, 'follow-up'):
            self.run_harness('note', self.ticket_id, '--file', '.harness-drafts/note.md',
                             '--actor', 'claude:implementer')

    def test_the_whole_journal_verifies_after_delivery(self):
        self.walk_to_deliver()
        self.commit_and_push()
        self.verify()
        kinds = [record['kind'] for record in self.run_harness('history', self.ticket_id)]
        self.assertEqual(kinds, ['start', 'advance', 'advance', 'check', 'check', 'check',
                                 'check', 'advance', 'check', 'advance', 'receipt'])
