"""The review triage: three passes, cheapest first, and what each one settles.

Pass one runs no model at all, so its tests are about the journal and the tree.
Pass two runs against a stub transport, as every decision test does: no test here
calls the API. Pass three is not run by the harness, which runs no model; what is
tested is the task text the record hands the session to give its subagent.
"""

import json
import unittest

from harness import cli, jev, triage
from harness.errors import HarnessError
from harness.tests.test_decisions import noul, score
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence

TICKET_CRITERIA = ['Something observable happens']


def triage_stub(criterion=0.95, depth=(0.2, 0.8), must_read=0.9, matches=0.9, billing=0.1):
    """A transport answering every triage question, keyed the way triage asks them.

    The keys carry a suffix, `criterion_evidenced#1` and
    `reviewer_must_read#harness/x.py`, because one request carries the same
    question once per criterion and once per file. Answering by prefix is what
    lets one stub serve a ticket with any number of either.

    The stage questions are answered too, because getting a ticket to the review
    stage passes three gates on the way, and `sent` records every request so a
    test can assert that the triage itself made none.
    """
    sent = []

    def transport(endpoint, payload, credential, timeout):
        sent.append(dict(endpoint=endpoint, payload=payload))
        replies = {}
        for key, question in payload['questions'].items():
            name = key.partition('#')[0]
            if name == 'criterion_evidenced':
                replies[key] = noul(criterion)
            elif name == 'reviewer_must_read':
                replies[key] = noul(must_read)
            elif name == 'diff_matches_solution':
                replies[key] = noul(matches)
            elif name == 'review_depth':
                replies[key] = score(list(depth))
            elif name == 'touches_billing_or_policy_gate':
                replies[key] = noul(billing)
            elif question['type'] == 'score':
                replies[key] = score([0.2, 0.7, 0.1])
            else:
                replies[key] = noul(0.93)
        return {'model': 'jev-1.13.0', 'answers': replies,
                'usage': {'input_tokens': 900, 'output_tokens': 40}}

    transport.sent = sent
    return transport


class TriageTest(CommandTest):
    """A ticket worked to the review stage, with one file changed on the branch."""

    def setUp(self):
        super().setUp()
        self.write('.env.local', 'JEV_API_KEY=stub-credential\n')
        jev.TRANSPORT = triage_stub()
        self.start()

    def reach_review(self, solution=None, coverage_delta=0.0):
        """Everything up to the review stage, with the checks a triage reads."""
        self.submit('clarify', clarify_evidence(acceptance=TICKET_CRITERIA))
        self.submit('solution', solution if solution is not None else solution_evidence(
            changes=['harness/thing.py: the behaviour'],
            slices=[dict(name='The behaviour', points=1,
                         files=['harness/thing.py', 'harness/tests/test_thing.py'],
                         red='The behaviour is absent')]))
        self.write('harness/thing.py', 'def thing():\n    return 1\n')
        self.write('harness/tests/test_thing.py', 'def test_thing():\n    assert True\n')
        red = self.run_check('red', exit_code=1)
        green = self.run_check('green')
        regression = self.run_check('regression')
        self.record_coverage(coverage_delta)
        self.submit('tdd', dict(mode='code', regression=regression['sequence'],
                                coverage_delta=coverage_delta,
                                slices=[dict(behaviour='The behaviour',
                                             failure_reason='It was absent',
                                             red=red['sequence'], green=green['sequence'])]))

    def run_check(self, phase, exit_code=0):
        return self.run_harness('check', self.ticket_id, '--phase', phase,
                                '--actor', 'claude:implementer', '--',
                                'sh', '-c', f'exit {exit_code}')

    def record_coverage(self, delta):
        """A coverage check, written straight into the journal.

        The real command runs vitest, which no harness test has. What a triage
        reads is the recorded phase, the package and the delta, so those are what
        the fixture writes.
        """
        from harness import journal
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        records = journal.read(folder)
        return journal.append(folder, records, kind='check', stage='tdd', attempt=1,
                              actor='claude:implementer', head=self.git('rev-parse', 'HEAD'),
                              ticket=self.ticket_id,
                              data=dict(command=['pnpm', 'test'], phase='coverage', exit_code=0,
                                        duration_ms=1, output='', output_sha256='0' * 64,
                                        output_truncated=False, before='a', after='b',
                                        package='@seen/core', lines=80.0, baseline=80.0 - delta,
                                        delta=delta))

    def triage(self, *args):
        """Run the triage, with the requests the stage gates made cleared first.

        Reaching the review stage passes three gates, each of which is a request.
        What a triage test asks about is the request the triage itself made, or
        did not make, so the earlier ones are cleared rather than counted.
        """
        jev.TRANSPORT.sent.clear()
        return self.run_harness('review', 'triage', self.ticket_id,
                                '--actor', 'claude:implementer', *args)


class DeterministicPassTest(TriageTest):
    """Pass one: what the harness can settle with no model at all."""

    def test_triage_is_refused_before_the_review_stage(self):
        with self.assertRaisesRegex(HarnessError, 'review'):
            self.triage()

    def test_the_deterministic_pass_names_every_check_it_ran(self):
        self.reach_review()
        record = self.triage()

        ran = {check['name']: check for check in record['data']['deterministic']}
        self.assertEqual(set(ran), set(triage.DETERMINISTIC))
        for check in ran.values():
            self.assertIn(check['outcome'], ('pass', 'fail', 'unavailable'))
            self.assertTrue(check['detail'].strip(), f'{check["name"]} recorded no detail')

    def test_a_red_that_failed_and_a_coverage_that_held_both_pass(self):
        self.reach_review()
        record = self.triage()
        ran = {check['name']: check for check in record['data']['deterministic']}

        self.assertEqual(ran['red_before_green']['outcome'], 'pass')
        self.assertEqual(ran['coverage']['outcome'], 'pass')
        self.assertEqual(ran['tests_added']['outcome'], 'pass')
        self.assertEqual(ran['slice_files']['outcome'], 'pass')
        self.assertEqual(ran['fingerprint']['outcome'], 'pass')
        self.assertEqual(record['data']['rules'], [],
                         'A clean pass one trips no rule, so nothing forces full depth')

    def test_coverage_that_fell_fails_the_check(self):
        """Asserted on the check rather than on a journey, because there is none.

        The tdd gate already refuses a fall, so no ticket reaches review with one
        through the commands. The check stays because the triage records the figure
        the reviewer reads either way, and a branch nothing can reach today is
        still a branch a journal written by some other path can land on.
        """
        records = [dict(sequence=1, kind='check', stage='tdd', attempt=1,
                        data=dict(phase='coverage', package='@seen/core', lines=80.0,
                                  baseline=81.5, delta=-1.5))]
        check = triage._coverage_check(records, 1)

        self.assertEqual(check['outcome'], 'fail')
        self.assertIn('-1.5', check['detail'])

    def test_a_first_coverage_measurement_is_not_a_regression(self):
        records = [dict(sequence=1, kind='check', stage='tdd', attempt=1,
                        data=dict(phase='coverage', package='@seen/core', lines=80.0,
                                  baseline=None, delta=None))]
        check = triage._coverage_check(records, 1)

        self.assertEqual(check['outcome'], 'pass')
        self.assertIn('no baseline', check['detail'])

    def test_a_tree_that_moved_after_the_tests_fails_the_fingerprint(self):
        self.reach_review()
        self.write('harness/thing.py', 'def thing():\n    return 99\n')
        ran = {check['name']: check for check in self.triage()['data']['deterministic']}

        self.assertEqual(ran['fingerprint']['outcome'], 'fail')
        self.assertIn('not the tests for this tree', ran['fingerprint']['detail'])

    def test_a_change_with_no_test_in_it_fails_tests_added(self):
        self.reach_review()
        (self.root / 'harness' / 'tests' / 'test_thing.py').unlink()
        ran = {check['name']: check for check in self.triage()['data']['deterministic']}
        self.assertEqual(ran['tests_added']['outcome'], 'fail')

    def test_a_file_no_slice_named_fails_the_slice_check_and_forces_full_depth(self):
        self.reach_review()
        self.write('harness/unplanned.py', 'def unplanned():\n    return 2\n')
        record = self.triage()

        ran = {check['name']: check for check in record['data']['deterministic']}
        self.assertEqual(ran['slice_files']['outcome'], 'fail')
        self.assertIn('harness/unplanned.py', ran['slice_files']['detail'])
        self.assertEqual(record['data']['review_depth'], 'full')

    def test_the_record_carries_the_fingerprint_it_read(self):
        self.reach_review()
        record = self.triage()
        self.assertEqual(len(record['data']['fingerprint']), 64)


class ChangedFilesTest(TriageTest):
    """The per-file facts pass two is given, gathered without a model."""

    def test_every_changed_file_carries_the_facts_the_question_needs(self):
        self.reach_review()
        files = {entry['path']: entry for entry in self.triage()['data']['files']}

        self.assertIn('harness/thing.py', files)
        entry = files['harness/thing.py']
        for key in ('hunks', 'added', 'removed', 'package', 'risk_percentile',
                    'coverage_delta', 'named_in_solution'):
            self.assertIn(key, entry)
        self.assertTrue(entry['named_in_solution'])
        self.assertGreater(entry['added'], 0)

    def test_a_file_outside_the_plan_is_marked_as_unnamed(self):
        self.reach_review()
        self.write('harness/unplanned.py', 'def unplanned():\n    return 2\n')
        files = {entry['path']: entry for entry in self.triage()['data']['files']}
        self.assertFalse(files['harness/unplanned.py']['named_in_solution'])


class DepthByRuleTest(TriageTest):
    """The three rules that are never Jev's to answer."""

    def assert_full_by_rule(self, record, rule):
        self.assertEqual(record['data']['review_depth'], 'full')
        self.assertIn(rule, ' '.join(record['data']['rules']))
        self.assertEqual(record['data']['jev']['asked'], False)
        self.assertEqual(jev.TRANSPORT.sent, [],
                         'A ticket whose depth is set by rule must not be put to the model')

    def test_a_migration_gets_full_depth_with_jev_not_asked(self):
        self.reach_review(solution=solution_evidence(
            migrations=['0003_add_triage.sql: a column'],
            changes=['harness/thing.py: the behaviour'],
            slices=[dict(name='The behaviour', points=1,
                         files=['harness/thing.py', 'harness/tests/test_thing.py'],
                         red='The behaviour is absent')]))
        self.assert_full_by_rule(self.triage(), 'migration')

    def test_an_agent_action_gets_full_depth_with_jev_not_asked(self):
        self.submit('clarify', clarify_evidence(acceptance=TICKET_CRITERIA,
                                                changes_agent_action=True))
        self.submit('solution', solution_evidence(
            changes=['harness/thing.py: the behaviour'],
            slices=[dict(name='The behaviour', points=1,
                         files=['harness/thing.py', 'harness/tests/test_thing.py'],
                         red='The behaviour is absent')],
            policy_gate_action=dict(reversibility='reversible', action_type='message',
                                    euro_impact_estimator='zero')))
        self.write('harness/thing.py', 'def thing():\n    return 1\n')
        self.write('harness/tests/test_thing.py', 'def test_thing():\n    assert True\n')
        red = self.run_check('red', exit_code=1)
        green = self.run_check('green')
        regression = self.run_check('regression')
        self.record_coverage(0.0)
        self.submit('tdd', dict(mode='code', regression=regression['sequence'],
                                coverage_delta=0.0,
                                slices=[dict(behaviour='The behaviour',
                                             failure_reason='It was absent',
                                             red=red['sequence'], green=green['sequence'])]))
        self.assert_full_by_rule(self.triage(), 'agent action')

    def test_billing_or_the_policy_gate_gets_full_depth_with_jev_not_asked(self):
        jev.TRANSPORT = triage_stub(billing=0.99)
        self.reach_review()
        self.assert_full_by_rule(self.triage(), 'billing')


class RecordTest(TriageTest):
    """The triage record itself: a kind of its own, at the review stage."""

    def test_the_triage_record_is_its_own_kind(self):
        self.reach_review()
        record = self.triage()
        self.assertEqual(record['kind'], 'triage')
        self.assertEqual(record['stage'], 'review')
        self.assertEqual(record['attempt'], 1)

    def test_a_triage_record_does_not_move_the_ticket(self):
        self.reach_review()
        self.triage()
        self.assertEqual(self.run_harness('status', self.ticket_id)['stage'], 'review')

    def test_triage_is_refused_on_another_ticket_s_branch(self):
        self.reach_review()
        self.git('checkout', '-q', '-b', 'claude/SEEN-002-something-else')
        with self.assertRaisesRegex(HarnessError, 'branch'):
            self.triage()


if __name__ == '__main__':
    unittest.main()
