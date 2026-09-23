"""Delivery against CI, and the merge against the receipt.

No test here talks to GitHub: both readers are module-level names the tests
replace, the same way the Jev transport is replaced.
"""

import json

from harness import github
from harness.errors import HarnessError
from harness.tests.test_delivery import DeliveryWalk


def runs(*states):
    """Check runs in the shape gh reports them."""
    return [dict(name=f'check {index}', status=status, conclusion=conclusion)
            for index, (status, conclusion) in enumerate(states, start=1)]


class DeliveryChecksTest(DeliveryWalk):

    def setUp(self):
        super().setUp()
        self.walk_to_deliver()
        self.commit_and_push()

    def with_checks(self, *states):
        github.CHECKS = lambda repository, commit: runs(*states)
        self.addCleanup(setattr, github, 'CHECKS', None)

    def test_a_delivery_passes_when_every_check_concluded_green(self):
        self.with_checks(('completed', 'success'), ('completed', 'skipped'))
        self.assertEqual(len(self.verify()['receipt_sha256']), 64)

    def test_a_failed_check_refuses_the_delivery_and_names_it(self):
        self.with_checks(('completed', 'success'), ('completed', 'failure'))
        with self.assertRaisesRegex(HarnessError, 'check 2'):
            self.verify()

    def test_a_check_still_running_refuses_the_delivery(self):
        self.with_checks(('completed', 'success'), ('in_progress', None))
        with self.assertRaisesRegex(HarnessError, 'still running'):
            self.verify()

    def test_a_commit_nobody_built_is_not_a_commit_that_passed(self):
        self.with_checks()
        with self.assertRaisesRegex(HarnessError, 'no checks'):
            self.verify()

    def test_gh_that_cannot_answer_refuses_rather_than_passes(self):
        def broken(repository, commit):
            raise HarnessError('gh: not authenticated')
        github.CHECKS = broken
        self.addCleanup(setattr, github, 'CHECKS', None)
        with self.assertRaisesRegex(HarnessError, 'not authenticated'):
            self.verify()


class MergeTest(DeliveryWalk):

    def setUp(self):
        super().setUp()
        self.walk_to_deliver()
        self.commit_and_push()
        github.CHECKS = lambda repository, commit: runs(('completed', 'success'))
        self.addCleanup(setattr, github, 'CHECKS', None)
        self.receipt = self.verify()
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'docs: record delivery receipt')
        self.git('push', '-q', 'origin', 'HEAD')
        self.with_body(f"The receipt is {self.receipt['receipt_sha256']}")

    def with_body(self, body):
        github.PULL_REQUEST = lambda repository: dict(number=1, body=body,
                                                      headRefName='claude/SEEN-001-a-ticket')
        self.addCleanup(setattr, github, 'PULL_REQUEST', None)

    def merge_check(self):
        return self.run_harness('verify-merge', self.ticket_id)

    def test_a_clean_delivery_is_ready_to_merge(self):
        result = self.merge_check()
        self.assertTrue(result['ready'])
        self.assertEqual(result['receipt_sha256'], self.receipt['receipt_sha256'])

    def test_a_source_change_after_the_receipt_refuses_the_merge(self):
        self.write('packages/core/src/late.ts', 'export const late = true;\n')
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'fix: a change nobody reviewed')
        with self.assertRaisesRegex(HarnessError, 'late.ts'):
            self.merge_check()

    def test_journal_and_bookkeeping_commits_after_the_receipt_are_fine(self):
        self.write('docs/harness/coverage.json', '{"packages": {"@seen/core": {"lines": 91.0}}}')
        self.write('graphify-out/graph.json', '{"nodes": [], "links": []}')
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'chore: bookkeeping')
        self.assertTrue(self.merge_check()['ready'])

    def test_a_pull_request_body_without_the_receipt_hash_refuses_the_merge(self):
        self.with_body('Looks good to me')
        with self.assertRaisesRegex(HarnessError, 'receipt'):
            self.merge_check()

    def test_the_command_appends_nothing_so_the_receipt_stays_last(self):
        before = self.run_harness('history', self.ticket_id)
        self.merge_check()
        after = self.run_harness('history', self.ticket_id)
        self.assertEqual(len(before), len(after))
        self.assertEqual(after[-1]['kind'], 'receipt')

    def test_a_ticket_that_has_not_delivered_cannot_be_merge_verified(self):
        other = 'SEEN-002'
        with self.assertRaisesRegex(HarnessError, 'receipt'):
            self.run_harness('verify-merge', other)


class SupersededRunTest(DeliveryWalk):
    """A commit can carry more than one run of the same check.

    GitHub shows the latest per name; so does this. Found when a delivery was
    refused by a failure from a run that had already been superseded by a green
    one on the same commit.
    """

    def setUp(self):
        super().setUp()
        self.walk_to_deliver()
        self.commit_and_push()

    def with_runs(self, *entries):
        github.CHECKS = lambda repository, commit: [
            dict(id=identifier, name=name, status='completed', conclusion=conclusion)
            for identifier, name, conclusion in entries]
        self.addCleanup(setattr, github, 'CHECKS', None)

    def test_a_superseded_failure_does_not_refuse_the_delivery(self):
        self.with_runs((1, 'ci', 'failure'), (2, 'ci', 'success'))
        self.assertEqual(len(self.verify()['receipt_sha256']), 64)

    def test_a_superseded_success_does_not_rescue_a_failing_check(self):
        self.with_runs((1, 'ci', 'success'), (2, 'ci', 'failure'))
        with self.assertRaisesRegex(HarnessError, 'ci'):
            self.verify()

    def test_each_check_name_is_judged_on_its_own_latest_run(self):
        self.with_runs((1, 'ci', 'failure'), (2, 'ci', 'success'),
                       (3, 'lint', 'failure'))
        with self.assertRaisesRegex(HarnessError, 'lint'):
            self.verify()
