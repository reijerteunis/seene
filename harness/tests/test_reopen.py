"""Voiding a receipt before the work is merged.

A receipt is final when the work is merged, not when it is written. Until then a
ticket can be reopened, and the journal says so rather than hiding it.
"""

import unittest
import hashlib
import json

from harness.errors import HarnessError
from harness.tests import helpers
from harness.tests.test_delivery import DeliveryWalk


class ReopenTest(DeliveryWalk):

    def deliver(self):
        self.walk_to_deliver()
        self.commit_and_push()
        return self.verify()

    def reopen(self, reason='The transport could never have reached its API'):
        return self.run_harness('reopen', self.ticket_id, '--reason', reason,
                                '--actor', 'claude:implementer')

    def test_a_delivered_ticket_returns_to_tdd_on_the_next_attempt(self):
        receipt = self.deliver()
        record = self.reopen()
        self.assertEqual(record['kind'], 'reopen')
        self.assertEqual(record['data']['to_stage'], 'tdd')
        self.assertEqual(record['data']['to_attempt'], 2)
        status = self.run_harness('status', self.ticket_id)
        self.assertEqual((status['stage'], status['attempt']), ('tdd', 2))
        self.assertEqual(record['data']['voided_receipt'], receipt['receipt_sha256'])

    def test_the_record_carries_the_reason_and_the_commit_it_voided(self):
        receipt = self.deliver()
        record = self.reopen('The API contract turned out to be different')
        self.assertIn('contract', record['data']['reason'])
        self.assertEqual(record['data']['voided_commit'], receipt['record']['data']['commit'])

    def test_the_receipt_itself_is_untouched(self):
        receipt = self.deliver()
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        path = folder / f'{receipt["record"]["sequence"]:04d}.json'
        before = path.read_bytes()
        self.reopen()
        self.assertEqual(path.read_bytes(), before, 'a receipt is voided, never edited')
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), receipt['receipt_sha256'])

    def test_the_chain_still_verifies_across_a_reopen(self):
        self.deliver()
        self.reopen()
        self.assertTrue(self.run_harness('doctor')['ok'])
        kinds = [record['kind'] for record in self.run_harness('history', self.ticket_id)]
        self.assertEqual(kinds[-2:], ['receipt', 'reopen'])

    def test_a_ticket_that_is_not_delivered_may_not_be_reopened(self):
        self.walk_to_deliver()
        with self.assertRaisesRegex(HarnessError, 'deliver'):
            self.reopen()

    def test_a_merged_ticket_may_not_be_reopened(self):
        self.deliver()
        branch = self.git('symbolic-ref', '--short', 'HEAD')
        self.git('checkout', '-q', 'main')
        self.git('merge', '-q', '--no-ff', '-m', 'merge the ticket', branch)
        self.git('push', '-q', 'origin', 'main')
        self.git('checkout', '-q', branch)
        with self.assertRaisesRegex(HarnessError, 'merged'):
            self.reopen()

    def test_a_reopened_ticket_can_be_delivered_again(self):
        first = self.deliver()
        self.reopen()
        self.write('docs/tickets/fix.md', 'the correction')
        self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                         'claude:implementer', '--', 'sh', '-c', 'echo still wrong; exit 1')
        self.run_harness('check', self.ticket_id, '--phase', 'green', '--actor',
                         'claude:implementer', '--', 'true')
        self.run_harness('check', self.ticket_id, '--phase', 'regression', '--actor',
                         'claude:implementer', '--', 'true')
        self.write('packages/core/coverage/coverage-summary.json',
                   '{"total": {"lines": {"total": 10, "covered": 9, "skipped": 0, "pct": 90.0}}}')
        self.run_harness('coverage', self.ticket_id, '--actor', 'claude:implementer', '--', 'true')
        records = self.run_harness('history', self.ticket_id)
        red, green, regression = [r['sequence'] for r in records[-4:-1]]
        self.submit('tdd', dict(mode='code',
                                slices=[dict(position=1, behaviour='The correction',
                                             failure_reason='still wrong', red=red, green=green)],
                                regression=regression, coverage_delta=None))
        self.run_harness('check', self.ticket_id, '--phase', 'qa', '--actor', 'codex:reviewer',
                         '--', 'true')
        qa = self.run_harness('history', self.ticket_id)[-1]['sequence']
        self.submit('review', dict(reviewer='codex:reviewer', independence='independent',
                                   read=['harness/journal.py'],
                                   acceptance_evidence=['The correction is covered'],
                                   findings=[], checks=[qa],
                                   security_checklist=['No secret in the diff'], verdict='pass'),
                    actor='codex:reviewer')
        self.commit_and_push('fix: the correction')
        second = self.verify()
        self.assertNotEqual(second['receipt_sha256'], first['receipt_sha256'])
        self.assertEqual(self.run_harness('status', self.ticket_id)['stage'], 'delivered')

if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
