"""What the harness refuses once it stops merely recording.

SEEN-086 made evidence addressable and ordered. This is where it starts to mean
something: a RED that did not fail is not a RED.
"""

from harness.errors import HarnessError
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence


class RedRuleTest(CommandTest):

    def setUp(self):
        super().setUp()
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())

    def red(self, *command):
        return self.run_harness('check', self.ticket_id, '--phase', 'red',
                                '--actor', 'claude:implementer', '--', *command)

    def test_a_red_that_passed_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'did not fail'):
            self.red('true')

    def test_the_run_is_still_recorded_even_though_the_claim_is_refused(self):
        before = len(self.records())
        with self.assertRaises(HarnessError):
            self.red('true')
        after = self.records()
        self.assertEqual(len(after), before + 1, 'the run happened; the journal keeps it')
        self.assertEqual(after[-1]['data']['phase'], 'red')
        self.assertEqual(after[-1]['data']['exit_code'], 0)

    def test_a_red_that_failed_is_accepted(self):
        record = self.red('sh', '-c', 'echo expected 250, received 0; exit 1')
        self.assertEqual(record['data']['exit_code'], 1)

    def test_a_red_that_could_not_start_proves_nothing(self):
        with self.assertRaisesRegex(HarnessError, 'did not fail'):
            self.red('this-command-does-not-exist')

    def test_a_red_that_timed_out_proves_nothing(self):
        with self.assertRaisesRegex(HarnessError, 'did not fail'):
            self.run_harness('check', self.ticket_id, '--phase', 'red',
                             '--actor', 'claude:implementer', '--timeout', '1',
                             '--', 'sh', '-c', 'sleep 5')

    def test_a_green_that_failed_is_recorded_without_complaint(self):
        record = self.run_harness('check', self.ticket_id, '--phase', 'green',
                                  '--actor', 'claude:implementer', '--', 'false')
        self.assertEqual(record['data']['exit_code'], 1,
                         'only a red makes a claim about failing')


class CitedRedTest(CommandTest):

    def setUp(self):
        super().setUp()
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())

    def test_a_slice_citing_a_red_that_passed_is_refused(self):
        """A red recorded before the rule existed can still be cited, so the gate checks too."""
        from harness import journal
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        records = journal.read(folder)
        journal.append(folder, records, kind='check', stage='tdd', attempt=1,
                       actor='claude:implementer', head='0' * 40, ticket=self.ticket_id,
                       data=dict(phase='red', exit_code=0, command=['true'], duration_ms=1,
                                 output='', output_sha256='0' * 64, output_truncated=False,
                                 before='x', after='x'))
        self.run_harness('check', self.ticket_id, '--phase', 'green',
                         '--actor', 'claude:implementer', '--', 'true')
        self.run_harness('check', self.ticket_id, '--phase', 'regression',
                         '--actor', 'claude:implementer', '--', 'true')
        self.write('packages/core/coverage/coverage-summary.json',
                   '{"total": {"lines": {"total": 10, "covered": 9, "skipped": 0, "pct": 90.0}}}')
        self.run_harness('coverage', self.ticket_id, '--actor', 'claude:implementer', '--', 'true')
        red, green, regression = [r['sequence'] for r in self.records()[-4:-1]]
        with self.assertRaisesRegex(HarnessError, 'did not fail'):
            self.submit('tdd', dict(mode='code',
                                    slices=[dict(behaviour='x', failure_reason='y',
                                                 red=red, green=green)],
                                    regression=regression, coverage_delta=None))


class RefusalMessageTest(CommandTest):
    """A refusal has to say what happened, not what the rule is called."""

    def test_a_decision_that_did_not_clear_does_not_claim_it_cleared(self):
        from harness import cli
        answer = dict(question='clarified', type='noul', options=['yes', 'no'], source='jev',
                      model='jev-1.13.0', outcome='no', probabilities={'yes': 0.41, 'no': 0.59},
                      confidence=None, score=None, threshold=0.8, passed=False,
                      fallback_reason=None)
        try:
            cli.require_decisions_pass('clarify', [answer])
            self.fail('the advance should have been refused')
        except HarnessError as error:
            self.assertIn('did not clear', str(error))
            self.assertNotIn('clears its threshold', str(error))
            self.assertIn('0.41', str(error))

    def test_a_must_fix_that_cleared_says_it_cleared(self):
        from harness import cli
        answer = dict(question='must_fix', type='noul', options=['yes', 'no'], source='jev',
                      model='jev-1.13.0', outcome='yes', probabilities={'yes': 0.92, 'no': 0.08},
                      confidence=None, score=None, threshold=0.7, passed=True,
                      fallback_reason=None)
        with self.assertRaisesRegex(HarnessError, 'cleared its threshold'):
            cli.require_decisions_pass('review', [answer])


class CoverageTest(CommandTest):
    """Coverage on packages/core, measured by one fixed command and never allowed to fall."""

    def setUp(self):
        super().setUp()
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())

    def summary(self, percentage):
        """The shape vitest's json-summary reporter writes."""
        self.write('packages/core/coverage/coverage-summary.json',
                   f'{{"total": {{"lines": {{"total": 100, "covered": {int(percentage)}, '
                   f'"skipped": 0, "pct": {percentage}}}}}}}')

    def baseline(self, percentage):
        self.write('docs/harness/coverage.json',
                   f'{{"packages": {{"@seen/core": {{"lines": {percentage}}}}}}}')

    def measure(self):
        return self.run_harness('coverage', self.ticket_id, '--actor', 'claude:implementer',
                                '--', 'true')

    def test_a_first_measurement_has_no_baseline_and_is_not_a_regression(self):
        self.summary(72.5)
        record = self.measure()
        self.assertEqual(record['data']['phase'], 'coverage')
        self.assertEqual(record['data']['lines'], 72.5)
        self.assertIsNone(record['data']['baseline'])
        self.assertIsNone(record['data']['delta'])

    def test_a_rise_is_recorded_as_a_positive_delta(self):
        self.baseline(70.0)
        self.summary(74.0)
        self.assertEqual(self.measure()['data']['delta'], 4.0)

    def test_a_fall_is_recorded_rather_than_hidden(self):
        self.baseline(80.0)
        self.summary(71.0)
        self.assertEqual(self.measure()['data']['delta'], -9.0)

    def test_advance_from_tdd_is_refused_without_a_measurement(self):
        self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                         'claude:implementer', '--', 'sh', '-c', 'exit 1')
        self.run_harness('check', self.ticket_id, '--phase', 'green', '--actor',
                         'claude:implementer', '--', 'true')
        self.run_harness('check', self.ticket_id, '--phase', 'regression', '--actor',
                         'claude:implementer', '--', 'true')
        red, green, regression = [r['sequence'] for r in self.records()[-3:]]
        with self.assertRaisesRegex(HarnessError, 'coverage'):
            self.submit('tdd', dict(mode='code',
                                    slices=[dict(behaviour='x', failure_reason='y',
                                                 red=red, green=green)],
                                    regression=regression, coverage_delta=None))

    def test_advance_from_tdd_is_refused_when_coverage_fell(self):
        self.baseline(80.0)
        self.summary(71.0)
        self.measure()
        self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                         'claude:implementer', '--', 'sh', '-c', 'exit 1')
        self.run_harness('check', self.ticket_id, '--phase', 'green', '--actor',
                         'claude:implementer', '--', 'true')
        self.run_harness('check', self.ticket_id, '--phase', 'regression', '--actor',
                         'claude:implementer', '--', 'true')
        red, green, regression = [r['sequence'] for r in self.records()[-3:]]
        with self.assertRaisesRegex(HarnessError, '-9.0'):
            self.submit('tdd', dict(mode='code',
                                    slices=[dict(behaviour='x', failure_reason='y',
                                                 red=red, green=green)],
                                    regression=regression, coverage_delta=None))


class NonCodeCoverageTest(CommandTest):
    """A ticket with no behaviour to prove owes no coverage figure.

    Its own setUp since SEEN-103, because the mode is declared at solution now
    and the two stages must agree.
    """

    def setUp(self):
        super().setUp()
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence(mode='non-code', tests_first=[]))

    def test_a_non_code_ticket_needs_no_coverage(self):
        self.submit('tdd', dict(mode='non-code', change_type='documentation',
                                reason='Prose only.', sources=[], checks=[]))

        self.assertEqual(self.run_harness('status', self.ticket_id)['stage'], 'review')


class BaselineTest(CommandTest):
    """The baseline moves only when a ticket delivers."""

    def test_delivery_writes_the_measured_figure_as_the_new_baseline(self):
        from harness import github
        from harness.tests import helpers
        import json as json_module
        helpers.add_remote(self.root)
        # Delivery now asks GitHub about the commit; this test is about the
        # baseline, so the answer is green and nothing reaches the network.
        github.CHECKS = lambda repository, commit: [
            dict(name='ci', status='completed', conclusion='success')]
        self.addCleanup(setattr, github, 'CHECKS', None)
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())
        self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                         'claude:implementer', '--', 'sh', '-c', 'exit 1')
        self.run_harness('check', self.ticket_id, '--phase', 'green', '--actor',
                         'claude:implementer', '--', 'true')
        self.run_harness('check', self.ticket_id, '--phase', 'regression', '--actor',
                         'claude:implementer', '--', 'true')
        self.write('packages/core/coverage/coverage-summary.json',
                   '{"total": {"lines": {"total": 10, "covered": 8, "skipped": 0, "pct": 83.5}}}')
        self.run_harness('coverage', self.ticket_id, '--actor', 'claude:implementer', '--', 'true')
        red, green, regression = [r['sequence'] for r in self.records()[-4:-1]]
        self.submit('tdd', dict(mode='code',
                                slices=[dict(behaviour='x', failure_reason='y',
                                             red=red, green=green)],
                                regression=regression, coverage_delta=None))
        self.run_harness('check', self.ticket_id, '--phase', 'qa', '--actor',
                         'codex:reviewer', '--', 'true')
        qa = self.records()[-1]['sequence']
        self.submit('review', dict(reviewer='codex:reviewer', independence='independent',
                                   read=['harness/journal.py'],
                                   acceptance_evidence=['covered'], findings=[], checks=[qa],
                                   security_checklist=['No secret in the diff'], verdict='pass'),
                    actor='codex:reviewer')
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'feat: the work')
        self.git('push', '-q', '-u', 'origin', 'HEAD')
        relative = f'.harness-drafts/{self.ticket_id}-deliver.json'
        self.write(relative, json_module.dumps(
            {'remote': 'origin', 'pull_request': 'https://github.test/seen/pull/1',
             'limits': ['none']}))
        self.run_harness('verify-delivery', self.ticket_id, '--file', relative,
                         '--actor', 'claude:implementer')

        stored = json_module.loads((self.root / 'docs' / 'harness' / 'coverage.json').read_text())
        self.assertEqual(stored['packages']['@seen/core']['lines'], 83.5)


class BaselineFingerprintTest(CommandTest):
    """The baseline is bookkeeping, not reviewed content.

    Delivery writes it, so counting it would mean the receipt could never survive
    the delivery that produced it, which is the circularity ADR 0002 resolves.
    """

    def test_the_coverage_baseline_does_not_change_the_reviewed_tree(self):
        from harness.repository import Repository
        repository = Repository(self.root)
        before = repository.fingerprint()
        self.write('docs/harness/coverage.json',
                   '{"packages": {"@seen/core": {"lines": 91.2}}}')
        self.assertEqual(before, repository.fingerprint())
