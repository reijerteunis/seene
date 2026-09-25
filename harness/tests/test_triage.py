"""The review triage: three passes, cheapest first, and what each one settles.

Pass one runs no model at all, so its tests are about the journal and the tree.
Pass two runs against a stub transport, as every decision test does: no test here
calls the API. Pass three is not run by the harness, which runs no model; what is
tested is the task text the record hands the session to give its subagent.
"""

import json
import pathlib
import shutil
import unittest

from harness import cli, jev, kpi, triage
from harness.errors import HarnessError
from harness.tests.test_decisions import noul, score
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence

TICKET_CRITERIA = ['Something observable happens']


def triage_stub(criterion=0.95, depth=(0.2, 0.8), must_read=0.9, matches=0.9,
                billing=0.1, must_fix=0.05):
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
            elif name == 'must_fix':
                replies[key] = noul(must_fix)
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
            slices=[dict(position=1, name='The behaviour', points=1,
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
                                slices=[dict(position=1, behaviour='The behaviour',
                                             failure_reason='It was absent',
                                             red=red['sequence'], green=green['sequence'])]))

    def run_check(self, phase, exit_code=0):
        return self.run_harness('check', self.ticket_id, '--phase', phase,
                                '--actor', 'claude:implementer', '--',
                                'sh', '-c', f'exit {exit_code}')

    def record_coverage(self, delta, attempt=1):
        """A coverage check, written straight into the journal.

        The real command runs vitest, which no harness test has. What a triage
        reads is the recorded phase, the package and the delta, so those are what
        the fixture writes.
        """
        from harness import journal
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        records = journal.read(folder)
        return journal.append(folder, records, kind='check', stage='tdd', attempt=attempt,
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
            slices=[dict(position=1, name='The behaviour', points=1,
                         files=['harness/thing.py', 'harness/tests/test_thing.py'],
                         red='The behaviour is absent')]))
        self.assert_full_by_rule(self.triage(), 'migration')

    def test_an_agent_action_gets_full_depth_with_jev_not_asked(self):
        self.submit('clarify', clarify_evidence(acceptance=TICKET_CRITERIA,
                                                changes_agent_action=True))
        self.submit('solution', solution_evidence(
            changes=['harness/thing.py: the behaviour'],
            slices=[dict(position=1, name='The behaviour', points=1,
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
                                slices=[dict(position=1, behaviour='The behaviour',
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


class ThreeCriteriaTest(TriageTest):
    """A ticket with more than one criterion, so per-criterion means something."""

    criteria = ['The first observable thing happens',
                'The second observable thing happens',
                'The third observable thing happens']

    def setUp(self):
        super().setUp()
        path = self.root / self.ticket_file
        body = path.read_text().split('## Acceptance criteria')[0]
        path.write_text(body + '## Acceptance criteria\n\n'
                        + ''.join(f'- [ ] {text}\n' for text in self.criteria))

    def reach_review(self, solution=None, coverage_delta=0.0):
        """The clarify record restates all three, so pass one has nothing to say.

        The solution record names thresholds.toml because the tests below vary it,
        and a file a ticket changes without naming fails slice_files and forces
        full depth, which is the behaviour under test in another class and noise
        in this one.
        """
        self.submit('clarify', clarify_evidence(acceptance=list(self.criteria)))
        self.submit('solution', solution if solution is not None else solution_evidence(
            changes=['harness/thing.py: the behaviour',
                     'harness/thresholds.toml: the settings these tests vary'],
            slices=[dict(position=1, name='The behaviour', points=1,
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
                                slices=[dict(position=1, behaviour='The behaviour',
                                             failure_reason='It was absent',
                                             red=red['sequence'], green=green['sequence'])]))


class OneRequestTest(ThreeCriteriaTest):
    """Pass two is one request, and it carries every question the triage asks."""

    def test_the_triage_asks_exactly_one_request(self):
        self.reach_review()
        self.triage()
        self.assertEqual(len(jev.TRANSPORT.sent), 1,
                         'Pass two is one request; a second is a question that was not asked '
                         'properly the first time')

    def test_the_request_carries_one_question_per_criterion_and_one_per_file(self):
        self.reach_review()
        record = self.triage()

        asked = set(jev.TRANSPORT.sent[0]['payload']['questions'])
        paths = [entry['path'] for entry in record['data']['files']]
        expected = ({f'criterion_evidenced#{position}'
                     for position in range(1, len(self.criteria) + 1)}
                    | {f'reviewer_must_read#{path}' for path in paths}
                    | {'diff_matches_solution', 'review_depth'})
        self.assertEqual(asked, expected)

    def test_each_question_carries_the_subject_it_is_asked_about(self):
        self.reach_review()
        self.triage()
        questions = jev.TRANSPORT.sent[0]['payload']['questions']

        self.assertIn(self.criteria[1], questions['criterion_evidenced#2']['instructions'])
        self.assertIn('harness/thing.py',
                      questions['reviewer_must_read#harness/thing.py']['instructions'])

    def test_the_state_carries_the_journal_and_the_diff_rather_than_the_tree(self):
        self.reach_review()
        self.triage()
        state = jev.TRANSPORT.sent[0]['payload']['state']

        self.assertEqual(state['criteria'], self.criteria)
        self.assertEqual([entry['name'] for entry in state['deterministic']],
                         list(triage.DETERMINISTIC))
        self.assertTrue(state['solution']['slices'])
        self.assertTrue(state['journal'])


class AnswersTest(ThreeCriteriaTest):
    """What the record keeps of pass two."""

    def test_every_criterion_gets_an_answer_with_its_probability(self):
        self.reach_review()
        answers = self.triage()['data']['criteria_answers']

        self.assertEqual([answer['criterion'] for answer in answers], self.criteria)
        for answer in answers:
            self.assertEqual(answer['question'], 'criterion_evidenced')
            self.assertEqual(answer['outcome'], 'yes')
            self.assertEqual(answer['probabilities']['yes'], 0.95)
            self.assertEqual(answer['threshold'], 0.6)
            self.assertIs(answer['passed'], True)

    def test_diff_matches_solution_and_review_depth_are_kept_with_their_probabilities(self):
        self.reach_review()
        answers = self.triage()['data']['jev']['answers']
        by_key = {answer['key']: answer for answer in answers}

        self.assertEqual(by_key['diff_matches_solution']['probabilities']['yes'], 0.9)
        self.assertEqual(by_key['review_depth']['outcome'], 'full')
        self.assertEqual(by_key['review_depth']['options'], ['spot', 'full'])

    def test_every_changed_file_gets_a_reviewer_must_read_answer(self):
        self.reach_review()
        record = self.triage()
        by_key = {answer['key']: answer for answer in record['data']['jev']['answers']}

        for entry in record['data']['files']:
            answer = by_key[f'reviewer_must_read#{entry["path"]}']
            self.assertEqual(answer['probabilities']['yes'], 0.9)

    def test_the_record_says_the_model_was_asked(self):
        self.reach_review()
        asked = self.triage()['data']['jev']
        self.assertTrue(asked['asked'])
        self.assertEqual(asked['model'], 'jev-1.13.0')


class UnevidencedCriterionTest(ThreeCriteriaTest):
    """The one answer that sends a ticket back before any model reads the diff."""

    def low_on_the_second(self):
        """A stub answering the second criterion below its threshold and no other."""
        base = triage_stub()

        def transport(endpoint, payload, credential, timeout):
            body = base(endpoint, payload, credential, timeout)
            if 'criterion_evidenced#2' in body['answers']:
                body['answers']['criterion_evidenced#2'] = noul(0.1)
            return body

        transport.sent = base.sent
        return transport

    def test_an_unevidenced_criterion_returns_the_ticket_to_tdd_naming_it(self):
        self.reach_review()
        jev.TRANSPORT = self.low_on_the_second()
        with self.assertRaisesRegex(HarnessError, self.criteria[1]):
            self.triage()

        self.assertEqual(self.run_harness('status', self.ticket_id)['stage'], 'tdd')
        kinds = [record['kind'] for record in self.records()]
        self.assertEqual(kinds[-2:], ['triage', 'return'],
                         'The triage is recorded because it happened, and the return follows it')

    def test_the_return_names_the_criterion_and_the_attempt_it_opens(self):
        self.reach_review()
        jev.TRANSPORT = self.low_on_the_second()
        with self.assertRaises(HarnessError):
            self.triage()

        returned = self.records()[-1]['data']
        self.assertEqual(returned['from_stage'], 'review')
        self.assertEqual(returned['to_stage'], 'tdd')
        self.assertEqual(returned['to_attempt'], 2)
        self.assertIn(self.criteria[1], returned['reason'])
        self.assertNotIn(self.criteria[0], returned['reason'])

    def test_a_criterion_nobody_could_answer_does_not_return_the_ticket(self):
        self.reach_review()

        def broken(endpoint, payload, credential, timeout):
            raise OSError('the API is unreachable')

        broken.sent = jev.TRANSPORT.sent
        jev.TRANSPORT = broken
        record = self.triage()

        self.assertEqual(self.run_harness('status', self.ticket_id)['stage'], 'review')
        for answer in record['data']['criteria_answers']:
            self.assertEqual(answer['source'], 'unavailable')
            self.assertIsNone(answer['passed'])
        self.assertEqual(record['data']['review_depth'], 'full',
                         'A judgement nobody made never narrows a review')


class FocusSetTest(ThreeCriteriaTest):
    """What the reviewer is asked to read, and what shadow mode does to it."""

    def set_shadow(self, on):
        path = self.root / 'harness' / 'thresholds.toml'
        path.write_text(path.read_text().replace(
            'triage_shadow = true', f'triage_shadow = {"true" if on else "false"}').replace(
            # Going live takes two lines from SEEN-109: the switch, and the
            # record its decision is in. A test that flips one and not the
            # other is a repository doctor refuses.
            'went_live = {}',
            'went_live = {}' if on
            else '''went_live = { ticket = "SEEN-001", record = 1, on = "2026-09-25" }'''))

    def test_full_depth_puts_every_changed_file_in_focus(self):
        self.reach_review()
        record = self.triage()

        self.assertEqual(record['data']['review_depth'], 'full')
        self.assertEqual(sorted(record['data']['focus']),
                         sorted(entry['path'] for entry in record['data']['files']))
        self.assertEqual(record['data']['would_exclude'], [])

    def test_spot_depth_drops_the_files_the_model_would_not_read(self):
        self.set_shadow(False)
        jev.TRANSPORT = self.only_thing_is_worth_reading()
        self.reach_review()
        record = self.triage()

        self.assertEqual(record['data']['review_depth'], 'spot')
        self.assertEqual(record['data']['focus'], ['harness/thing.py'])
        self.assertIn('harness/tests/test_thing.py', record['data']['would_exclude'])
        self.assertGreater(record['data']['excluded_share'], 0.0)

    def test_shadow_keeps_every_file_in_focus_and_records_what_it_would_have_dropped(self):
        self.set_shadow(True)
        jev.TRANSPORT = self.only_thing_is_worth_reading()
        self.reach_review()
        record = self.triage()

        self.assertTrue(record['data']['shadow'])
        self.assertEqual(record['data']['review_depth'], 'spot')
        self.assertEqual(sorted(record['data']['focus']),
                         sorted(entry['path'] for entry in record['data']['files']))
        self.assertIn('harness/tests/test_thing.py', record['data']['would_exclude'])
        self.assertGreater(record['data']['excluded_share'], 0.0)

    def test_a_focus_set_is_never_empty(self):
        self.set_shadow(False)
        jev.TRANSPORT = triage_stub(depth=(0.9, 0.1), must_read=0.01)
        self.reach_review()
        record = self.triage()

        self.assertEqual(record['data']['review_depth'], 'spot')
        self.assertEqual(len(record['data']['focus']), 1,
                         'A review that reads nothing is not a review, so the file the model '
                         'was least unsure about stays')

    def test_a_depth_the_model_is_undecided_about_is_full(self):
        self.set_shadow(False)
        jev.TRANSPORT = triage_stub(depth=(0.5, 0.5))
        self.reach_review()

        self.assertEqual(self.triage()['data']['review_depth'], 'full')

    def only_thing_is_worth_reading(self):
        """A stub asking for a spot review of one file out of the three."""
        base = triage_stub(depth=(0.9, 0.1))

        def transport(endpoint, payload, credential, timeout):
            body = base(endpoint, payload, credential, timeout)
            for key in body['answers']:
                if key.startswith('reviewer_must_read#'):
                    body['answers'][key] = noul(
                        0.95 if key.endswith('harness/thing.py') else 0.05)
            return body

        transport.sent = base.sent
        return transport


def review_evidence(read, **changes):
    """A review record in the shape the gate demands, with what it read."""
    data = dict(reviewer='codex:reviewer',
                independence='independent',
                acceptance_evidence=['Every criterion is proven by the recorded checks'],
                read=list(read),
                findings=[],
                checks=[],
                security_checklist=[],
                verdict='pass')
    data.update(changes)
    return data


class ReviewerTaskTest(FocusSetTest):
    """Pass three is text: the task the session hands its subagent."""

    def test_the_task_names_every_file_in_the_focus_set_and_no_other(self):
        """Asserted on the diff section, which is the part `no others` governs.

        The ticket file and the journal are named above it whatever the depth,
        because they are what a review is against and no focus set can hold them:
        H1 of the fourth review, which this test predates.
        """
        self.set_shadow(False)
        jev.TRANSPORT = self.only_thing_is_worth_reading()
        self.reach_review()
        record = self.triage()

        of_the_diff = record['data']['reviewer_task'].split('Of the diff')[1]
        self.assertIn('harness/thing.py', of_the_diff)
        for path in record['data']['would_exclude']:
            self.assertNotIn(path, of_the_diff.split('Already settled')[0],
                             f'{path} is outside the focus set, so the task must not list it '
                             'among the files to read')

    def test_the_task_names_the_depth_and_the_record_the_focus_set_came_from(self):
        self.reach_review()
        record = self.triage()

        task = record['data']['reviewer_task']
        self.assertIn(record['data']['review_depth'], task)
        self.assertIn(str(record['sequence']), task)
        self.assertIn(self.ticket_id, task)

    def test_in_shadow_the_task_names_every_changed_file(self):
        self.set_shadow(True)
        jev.TRANSPORT = self.only_thing_is_worth_reading()
        self.reach_review()
        record = self.triage()

        for entry in record['data']['files']:
            self.assertIn(entry['path'], record['data']['reviewer_task'])


class FocusSetGateTest(FocusSetTest):
    """The gate that makes the focus set worth computing."""

    def advance_review(self, read):
        return self.submit('review', review_evidence(read), actor='codex:reviewer')

    def test_a_read_list_short_of_the_focus_set_is_refused(self):
        self.reach_review()
        record = self.triage()
        focus = record['data']['focus']

        with self.assertRaisesRegex(HarnessError, focus[-1].replace('.', r'\.')):
            self.advance_review(focus[:-1])

    def test_a_read_list_that_covers_the_focus_set_is_accepted(self):
        self.reach_review()
        record = self.triage()

        advanced = self.advance_review(record['data']['focus'])
        self.assertEqual(advanced['data']['to_stage'], 'deliver')

    def test_reading_more_than_the_focus_set_is_never_refused(self):
        self.set_shadow(False)
        jev.TRANSPORT = self.only_thing_is_worth_reading()
        self.reach_review()
        record = self.triage()
        everything = [entry['path'] for entry in record['data']['files']]

        self.assertLess(len(record['data']['focus']), len(everything))
        self.advance_review(everything)

    def test_a_review_with_no_triage_at_all_is_unaffected(self):
        self.reach_review()
        self.advance_review(['harness/thing.py'])


class TriageFiguresTest(unittest.TestCase):
    """What kpi.json keeps of a triage, derived and never typed."""

    def journal(self, **changes):
        from harness.tests.test_kpi import record
        data = dict(review_depth='full', model_depth='spot', shadow=True, excluded_share=0.42,
                    files=[dict(path='a'), dict(path='b'), dict(path='c')],
                    focus=['a', 'b', 'c'], would_exclude=['b', 'c'],
                    jev=dict(asked=True, model='jev-1.13.0', answers=[]))
        data.update(changes)
        return [record(1, 'start', 'clarify', minute=0, ticket_file='docs/tickets/x.md',
                       ticket_snapshot='# x'),
                record(2, 'advance', 'tdd', minute=10, from_stage='tdd', to_stage='review',
                       evidence={}, decisions=[]),
                record(3, 'triage', 'review', minute=20, **data),
                record(4, 'advance', 'review', minute=40, from_stage='review',
                       to_stage='deliver', evidence={}, decisions=[])]

    def test_the_figures_carry_the_depth_the_counts_and_the_excluded_share(self):
        figures = kpi.measure(self.journal(), 'SEEN-001')['review_triage']

        self.assertEqual(figures['depth'], 'full')
        self.assertTrue(figures['shadow'])
        self.assertEqual(figures['files'], 3)
        self.assertEqual(figures['focus'], 3)
        self.assertEqual(figures['excluded'], 2)
        self.assertEqual(figures['excluded_share'], 0.42)
        self.assertEqual(figures['record'], 3)

    def test_the_row_says_which_depth_its_excluded_share_was_measured_at(self):
        """N1: the field went in at attempt 10 with no test, found by mutation.

        The share is measured at the depth the model chose and the focus set is
        the one the rules enforced, so a row carrying only one of the two cannot
        say whether the saving it reports was ever available. SEEN-109 divides on
        this row and reshapes it, and nothing failed when the field was deleted.
        """
        figures = kpi.measure(self.journal(), 'SEEN-001')['review_triage']

        self.assertEqual(figures['model_depth'], 'spot')
        self.assertNotEqual(figures['model_depth'], figures['depth'],
                            'A rule forced full depth here, so the share is what spot would '
                            'have dropped and not what this review saved')

    def test_a_row_whose_two_depths_agree_reports_a_saving_that_was_available(self):
        figures = kpi.measure(self.journal(review_depth='spot'),
                              'SEEN-001')['review_triage']

        self.assertEqual(figures['depth'], 'spot')
        self.assertEqual(figures['model_depth'], 'spot')

    def test_the_reviewer_s_output_tokens_are_carried_when_they_are_known(self):
        figures = kpi.measure(self.journal(), 'SEEN-001',
                              reviewer_tokens=dict(output_tokens=7200))['review_triage']

        self.assertEqual(figures['reviewer_output_tokens'], 7200)

    def test_they_are_null_rather_than_zero_when_no_log_was_read(self):
        figures = kpi.measure(self.journal(), 'SEEN-001')['review_triage']
        self.assertIsNone(figures['reviewer_output_tokens'])

    def test_a_journal_with_no_triage_has_none_rather_than_a_hollow_section(self):
        records = [entry for entry in self.journal() if entry['kind'] != 'triage']
        self.assertIsNone(kpi.measure(records, 'SEEN-001')['review_triage'])

    def test_the_window_runs_from_the_triage_to_the_review_advance(self):
        self.assertEqual(kpi.review_windows(self.journal()),
                         [('2026-09-23T10:20:00+00:00', '2026-09-23T10:40:00+00:00')])

    def test_there_is_no_window_without_a_triage(self):
        records = [entry for entry in self.journal() if entry['kind'] != 'triage']
        self.assertEqual(kpi.review_windows(records), [])


class SidechainTokensTest(unittest.TestCase):
    """The reviewer's own cost, read from the log rather than declared."""

    def setUp(self):
        import tempfile
        from harness import cost
        self.root = pathlib.Path(tempfile.mkdtemp())
        self.directory = cost.log_directory(self.root)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.directory, True)

    def write_log(self, entries):
        (self.directory / 'session.jsonl').write_text(
            ''.join(json.dumps(entry) + '\n' for entry in entries))

    def entry(self, stamp, output, sidechain):
        return dict(timestamp=stamp, isSidechain=sidechain,
                    message=dict(usage=dict(input_tokens=10, output_tokens=output,
                                            cache_read_input_tokens=0,
                                            cache_creation_input_tokens=0)))

    def test_only_the_subagent_s_own_entries_are_counted(self):
        from harness import cost
        self.write_log([self.entry('2026-09-23T10:25:00+00:00', 500, True),
                        self.entry('2026-09-23T10:26:00+00:00', 700, True),
                        self.entry('2026-09-23T10:27:00+00:00', 9000, False)])

        totals = cost.tokens_between(self.root, '2026-09-23T10:20:00+00:00',
                                     '2026-09-23T10:40:00+00:00', sidechain=True)
        self.assertEqual(totals['output_tokens'], 1200)

    def test_the_window_still_applies(self):
        from harness import cost
        self.write_log([self.entry('2026-09-23T10:25:00+00:00', 500, True),
                        self.entry('2026-09-23T11:99:00+00:00', 700, True)])

        totals = cost.tokens_between(self.root, '2026-09-23T10:20:00+00:00',
                                     '2026-09-23T10:40:00+00:00', sidechain=True)
        self.assertEqual(totals['output_tokens'], 500)

    def test_a_log_with_no_subagent_entry_reads_null_rather_than_zero(self):
        from harness import cost
        self.write_log([self.entry('2026-09-23T10:25:00+00:00', 9000, False)])

        self.assertIsNone(cost.tokens_between(self.root, '2026-09-23T10:20:00+00:00',
                                              '2026-09-23T10:40:00+00:00', sidechain=True))

    def test_counting_both_is_still_what_a_bare_call_does(self):
        from harness import cost
        self.write_log([self.entry('2026-09-23T10:25:00+00:00', 500, True),
                        self.entry('2026-09-23T10:27:00+00:00', 9000, False)])

        totals = cost.tokens_between(self.root, '2026-09-23T10:20:00+00:00',
                                     '2026-09-23T10:40:00+00:00')
        self.assertEqual(totals['output_tokens'], 9500)


class GeneratedCopiesTest(TriageTest):
    """Files sync writes are named by naming their source.

    Found by running the triage on SEEN-107's own branch: the four copies sync
    generates were flagged as changed but named by no slice, while the solution
    record named both sources. A copy has no review surface of its own, because
    doctor refuses one that does not match what its source would generate, so
    counting it as unplanned forces full depth on every harness ticket that runs
    sync and leaves SEEN-109 nothing to calibrate.
    """

    def touch_the_copies(self):
        from harness import agents, skills
        written = []
        for relative in list(skills.COMMITTED) + [agents.claude_copy(agents.REVIEWER),
                                                  agents.codex_copy(agents.REVIEWER)]:
            path = self.root / relative
            path.write_text(path.read_text() + '\n')
            written.append(str(relative))
        return written

    def test_a_generated_copy_does_not_fail_the_slice_check(self):
        self.reach_review()
        self.touch_the_copies()
        record = self.triage()

        ran = {check['name']: check for check in record['data']['deterministic']}
        self.assertEqual(ran['slice_files']['outcome'], 'pass')
        # Not `rules == []`: writing the copies moved the tree after the tests
        # ran, which the fingerprint check is right to catch. What must not be
        # in the rules is this check.
        self.assertNotIn('slice_files', ' '.join(record['data']['rules']))

    def test_a_generated_copy_is_still_a_changed_file_the_reviewer_can_be_sent_to(self):
        """Excluded from the check, not from the diff: it did change."""
        self.reach_review()
        written = self.touch_the_copies()
        paths = {entry['path'] for entry in self.triage()['data']['files']}

        for relative in written:
            self.assertIn(relative, paths)

    def test_a_file_nothing_generates_still_fails(self):
        self.reach_review()
        self.touch_the_copies()
        self.write('harness/unplanned.py', 'def unplanned():\n    return 2\n')
        ran = {check['name']: check
               for check in self.triage()['data']['deterministic']}

        self.assertEqual(ran['slice_files']['outcome'], 'fail')
        self.assertIn('harness/unplanned.py', ran['slice_files']['detail'])


class PartialAnswerTest(ThreeCriteriaTest):
    """F1: a reply that left one question out must not cost the rest.

    A transport failure is already an absence on every key. A well-formed reply
    missing one key was not: `_ask_api` refused it, `ask_batch` re-raised, and the
    triage record was never written at all, which also left the review gate with
    no focus set to hold the reviewer to.
    """

    def stub_that_drops(self, dropped):
        base = triage_stub()

        def transport(endpoint, payload, credential, timeout):
            body = base(endpoint, payload, credential, timeout)
            body['answers'].pop(dropped, None)
            return body

        transport.sent = base.sent
        return transport

    def test_the_triage_is_still_recorded_when_one_answer_is_missing(self):
        self.reach_review()
        jev.TRANSPORT = self.stub_that_drops('criterion_evidenced#2')
        record = self.triage()

        self.assertEqual(record['kind'], 'triage')
        answered = {answer['key']: answer for answer in record['data']['jev']['answers']}
        self.assertEqual(answered['criterion_evidenced#2']['source'], 'unavailable')
        self.assertIn('criterion_evidenced#2',
                      answered['criterion_evidenced#2']['fallback_reason'])
        self.assertEqual(answered['criterion_evidenced#1']['source'], 'jev')

    def test_a_missing_answer_does_not_return_the_ticket(self):
        self.reach_review()
        jev.TRANSPORT = self.stub_that_drops('criterion_evidenced#2')
        self.triage()

        self.assertEqual(self.run_harness('status', self.ticket_id)['stage'], 'review')

    def test_a_missing_review_depth_leaves_the_review_at_full(self):
        self.set_shadow(False)
        jev.TRANSPORT = self.stub_that_drops('review_depth')
        self.reach_review()

        self.assertEqual(self.triage()['data']['review_depth'], 'full')

    def set_shadow(self, on):
        path = self.root / 'harness' / 'thresholds.toml'
        path.write_text(path.read_text().replace(
            'triage_shadow = true', f'triage_shadow = {"true" if on else "false"}').replace(
            # Going live takes two lines from SEEN-109: the switch, and the
            # record its decision is in. A test that flips one and not the
            # other is a repository doctor refuses.
            'went_live = {}',
            'went_live = {}' if on
            else '''went_live = { ticket = "SEEN-001", record = 1, on = "2026-09-25" }'''))

    def test_a_stage_gate_still_refuses_a_reply_that_left_its_question_out(self):
        """The other half of must_answer: a stage needs a judgement."""
        from harness import thresholds

        def drops_clarified(endpoint, payload, credential, timeout):
            return {'model': 'jev-1.13.0',
                    'answers': {key: score([0.2, 0.7, 0.1])
                                for key in payload['questions'] if key != 'clarified'}}

        jev.TRANSPORT = drops_clarified
        with self.assertRaisesRegex(HarnessError, 'clarified'):
            jev.ask_many(self.root, thresholds.load(self.root), ['clarified', 'risk'], {})


class StaleTriageTest(FocusSetTest):
    """F4: the focus set is a floor, and a floor under a diff that has moved is none."""

    def advance_review(self, read):
        return self.submit('review', review_evidence(read), actor='codex:reviewer')

    def test_a_file_added_after_the_triage_refuses_the_advance(self):
        self.reach_review()
        record = self.triage()
        self.write('harness/afterwards.py', 'def afterwards():\n    return 3\n')

        with self.assertRaisesRegex(HarnessError, 'moved'):
            self.advance_review(record['data']['focus'])

    def test_the_ticket_file_moving_does_not_refuse_the_advance(self):
        """The procedure writes it between the triage and the advance, every time."""
        self.reach_review()
        record = self.triage()
        path = self.root / self.ticket_file
        path.write_text(path.read_text() + '\n## Outcome\n\nWhat happened.\n')

        self.advance_review(record['data']['focus'])

    def test_a_generated_copy_moving_does_not_refuse_the_advance(self):
        self.reach_review()
        record = self.triage()
        from harness import skills
        copy = self.root / skills.COMMITTED[0]
        copy.write_text(copy.read_text() + '\n')

        self.advance_review(record['data']['focus'])

    def test_the_triage_records_the_code_fingerprint_the_gate_compares(self):
        self.reach_review()
        data = self.triage()['data']

        self.assertEqual(len(data['code_fingerprint']), 64)
        self.assertNotEqual(data['code_fingerprint'], data['fingerprint'],
                            'The ticket file is in the tree, so leaving it out must change it')


class DeliveredFiguresTest(unittest.TestCase):
    """F3 of the second review: criterion 5 names kpi.json, and delivery writes it.

    G2 of the third review: this used to assert that two words appeared in the
    source of delivery.verify, and the comment above the call carries both, so it
    passed with the behaviour removed. It walks a ticket to delivered now, through
    a real triage, with a subagent entry in the log inside the review window and
    an implementer entry outside it, and reads the figure out of the file.
    """

    def test_the_delivered_kpi_file_carries_the_reviewer_s_own_tokens(self):
        from harness import journal
        from harness.tests.test_delivery import DeliveryWalk

        class Walk(DeliveryWalk):
            """The same walk, with the triage the procedure now runs before a review."""

            def runTest(self):                              # pragma: no cover - never run
                pass

            def walk_to_review(self):
                self.start()
                self.submit('clarify', clarify_evidence())
                self.submit('solution', solution_evidence())
                self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                                 'claude:implementer', '--', 'sh', '-c',
                                 'echo expected 1, got 0; exit 1')
                self.run_harness('check', self.ticket_id, '--phase', 'green', '--actor',
                                 'claude:implementer', '--', 'true')
                self.run_harness('check', self.ticket_id, '--phase', 'regression', '--actor',
                                 'claude:implementer', '--', 'true')
                self.write('packages/core/coverage/coverage-summary.json',
                           '{"total": {"lines": {"total": 10, "covered": 9, "skipped": 0, '
                           '"pct": 90.0}}}')
                self.run_harness('coverage', self.ticket_id, '--actor', 'claude:implementer',
                                 '--', 'true')
                self.submit('tdd', dict(mode='code',
                                        slices=[dict(position=1, behaviour='The harness records a delivery',
                                                     failure_reason='expected 1, got 0',
                                                     red=4, green=5)],
                                        regression=6,
                                        coverage_delta=None))

        walk = Walk()
        walk.setUp()
        try:
            walk.walk_to_review()
            triaged = walk.run_harness('review', 'triage', walk.ticket_id,
                                       '--actor', 'claude:implementer')
            self.write_log(walk.root, triaged['timestamp'])
            walk.run_harness('check', walk.ticket_id, '--phase', 'qa', '--actor',
                             'codex:reviewer', '--', 'true')
            walk.submit('review', dict(reviewer='codex:reviewer',
                                       independence='independent',
                                       read=list(triaged['data']['focus']),
                                       acceptance_evidence=['The journal holds every stage'],
                                       findings=[], checks=[], security_checklist=[],
                                       verdict='pass'),
                        actor='codex:reviewer')
            walk.commit_and_push()
            walk.verify()
            folder = walk.root / 'docs' / 'harness' / 'history' / walk.ticket_id
            figures = json.loads((folder / 'kpi.json').read_text())
            windows = kpi.review_windows(journal.read(folder))
        finally:
            walk.doCleanups()

        self.assertEqual(len(windows), 1)
        self.assertEqual(figures['review_triage']['reviewer_output_tokens'], 4321,
                         'The subagent entry inside the review window is the reviewer, and '
                         'the one before the triage is not')

    def write_log(self, root, opened):
        """One subagent entry inside the window, and one before it that is not."""
        from harness import cost
        directory = cost.log_directory(root)
        directory.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, directory, True)
        (directory / 'session.jsonl').write_text(
            json.dumps(self.entry('2000-01-01T00:00:00+00:00', 99999, True)) + '\n'
            + json.dumps(self.entry(opened, 4321, True)) + '\n'
            + json.dumps(self.entry(opened, 88888, False)) + '\n')

    def entry(self, stamp, output, sidechain):
        return dict(timestamp=stamp, isSidechain=sidechain,
                    message=dict(usage=dict(input_tokens=1, output_tokens=output,
                                            cache_read_input_tokens=0,
                                            cache_creation_input_tokens=0)))


class ReviewWindowsTest(unittest.TestCase):
    """G3: the window is the reviewer's, and the rework between two is not."""

    def journal(self):
        """Two review rounds, with a whole tdd attempt between them."""
        from harness.tests.test_kpi import record
        return [record(1, 'start', 'clarify', minute=0, ticket_file='docs/tickets/x.md',
                       ticket_snapshot='# x'),
                record(2, 'advance', 'tdd', minute=10, from_stage='tdd', to_stage='review',
                       evidence={}, decisions=[]),
                record(3, 'triage', 'review', minute=20, review_depth='full', focus=['a'],
                       would_exclude=[], excluded_share=0.0, files=[], shadow=True, jev={}),
                record(4, 'return', 'review', minute=30, from_stage='review', to_stage='tdd',
                       to_attempt=2, reason='a finding'),
                record(5, 'check', 'tdd', attempt=2, minute=40, phase='green', exit_code=0,
                       command=['t']),
                record(6, 'advance', 'tdd', attempt=2, minute=50, from_stage='tdd',
                       to_stage='review', evidence={}, decisions=[]),
                record(7, 'triage', 'review', attempt=2, minute=60, review_depth='full',
                       focus=['a'], would_exclude=[], excluded_share=0.0, files=[],
                       shadow=True, jev={}),
                record(8, 'advance', 'review', attempt=2, minute=70, from_stage='review',
                       to_stage='deliver', evidence={}, decisions=[])]

    def test_each_review_round_is_its_own_window(self):
        windows = kpi.review_windows(self.journal())

        self.assertEqual(windows, [('2026-09-23T10:20:00+00:00', '2026-09-23T10:30:00+00:00'),
                                   ('2026-09-23T11:00:00+00:00', '2026-09-23T11:10:00+00:00')])

    def test_the_rework_between_two_rounds_is_in_neither(self):
        """Where the scout runs, and from SEEN-108 the implementer subagent."""
        rework = '2026-09-23T10:40:00+00:00'
        for opened, closed in kpi.review_windows(self.journal()):
            self.assertFalse(opened <= rework <= closed,
                             'A tdd attempt is not the reviewer reading')

    def test_a_second_triage_in_one_round_closes_the_first_window(self):
        from harness.tests.test_kpi import record
        records = self.journal()[:3] + [
            record(4, 'triage', 'review', minute=35, review_depth='full', focus=['a'],
                   would_exclude=[], excluded_share=0.0, files=[], shadow=True, jev={}),
            record(5, 'advance', 'review', minute=45, from_stage='review', to_stage='deliver',
                   evidence={}, decisions=[])]

        self.assertEqual(len(kpi.review_windows(records)), 2,
                         'Two triages in one round are two reviewers, and both cost tokens')

    def test_a_journal_with_no_triage_has_no_window(self):
        records = [entry for entry in self.journal() if entry['kind'] != 'triage']
        self.assertEqual(kpi.review_windows(records), [])

    def test_a_round_still_open_runs_to_the_last_record(self):
        records = self.journal()[:3]
        self.assertEqual(kpi.review_windows(records),
                         [('2026-09-23T10:20:00+00:00', '2026-09-23T10:20:00+00:00')])


class UnreadableFileTest(FocusSetTest):
    """G1: a judgement nobody made must not take a file out of a review."""

    def stub_without(self, path):
        base = triage_stub(depth=(0.9, 0.1))

        def transport(endpoint, payload, credential, timeout):
            body = base(endpoint, payload, credential, timeout)
            for key in list(body['answers']):
                if key.startswith('reviewer_must_read#'):
                    body['answers'][key] = noul(0.95 if key.endswith('harness/thing.py') else 0.05)
            body['answers'].pop(f'reviewer_must_read#{path}', None)
            return body

        transport.sent = base.sent
        return transport

    def test_a_file_the_model_did_not_answer_for_stays_in_the_focus_set(self):
        self.set_shadow(False)
        jev.TRANSPORT = self.stub_without('harness/tests/test_thing.py')
        self.reach_review()
        record = self.triage()

        self.assertEqual(record['data']['review_depth'], 'spot')
        self.assertIn('harness/tests/test_thing.py', record['data']['focus'],
                      'An unanswered file is a doubt, and doubt resolves towards reading more')
        self.assertNotIn('harness/tests/test_thing.py', record['data']['would_exclude'])

    def test_a_file_the_model_answered_low_for_is_still_dropped(self):
        self.set_shadow(False)
        jev.TRANSPORT = self.stub_without('harness/tests/test_thing.py')
        self.reach_review()
        record = self.triage()

        self.assertIn(self.ticket_file, record['data']['would_exclude'],
                      'A file answered at 0.05 is a judgement, and it stands')


class TriageAcrossAttemptsTest(FocusSetTest):
    """G4: a ticket triaged once must not review a later attempt untriaged."""

    def advance_review(self, read):
        return self.submit('review', review_evidence(read), actor='codex:reviewer')

    def return_and_reach_review_again(self):
        self.run_harness('return', self.ticket_id, '--to', 'tdd', '--reason',
                         'A finding', '--actor', 'codex:reviewer')
        red = self.run_check('red', exit_code=1)
        green = self.run_check('green')
        regression = self.run_check('regression')
        self.record_coverage(0.0, attempt=2)
        self.submit('tdd', dict(mode='code', regression=regression['sequence'],
                                coverage_delta=0.0,
                                slices=[dict(position=1, behaviour='The correction',
                                             failure_reason='It was wrong',
                                             red=red['sequence'], green=green['sequence'])]))

    def test_a_review_after_a_return_is_refused_until_the_triage_is_run_again(self):
        self.reach_review()
        record = self.triage()
        self.return_and_reach_review_again()

        with self.assertRaisesRegex(HarnessError, 'triage'):
            self.advance_review(record['data']['focus'])

    def test_running_the_triage_again_clears_it(self):
        self.reach_review()
        self.triage()
        self.return_and_reach_review_again()
        fresh = self.triage()

        self.advance_review(fresh['data']['focus'])

    def test_a_ticket_that_never_triaged_is_still_unaffected(self):
        self.reach_review()
        self.advance_review(['harness/thing.py'])


class AlwaysReadTest(FocusSetTest):
    """H1: the two things a review is against are never in a focus set.

    The journal cannot be, because changed_files drops everything under
    FINGERPRINT_EXCLUDED, and the ticket file can be dropped from one at spot
    depth. A task that said "read these and no others" was telling the reviewer
    not to read the criteria or the evidence.
    """

    def test_the_task_names_the_ticket_file_and_the_journal_at_full_depth(self):
        self.reach_review()
        task = self.triage()['data']['reviewer_task']

        self.assertIn(self.ticket_file, task)
        self.assertIn(f'docs/harness/history/{self.ticket_id}/', task)

    def test_it_names_them_at_spot_depth_even_when_the_ticket_file_is_excluded(self):
        self.set_shadow(False)
        jev.TRANSPORT = self.only_thing_is_worth_reading()
        self.reach_review()
        record = self.triage()

        self.assertEqual(record['data']['review_depth'], 'spot')
        self.assertIn(self.ticket_file, record['data']['would_exclude'],
                      'The fixture must drop it, or this proves nothing')
        self.assertIn(self.ticket_file, record['data']['reviewer_task'])
        self.assertIn(f'docs/harness/history/{self.ticket_id}/',
                      record['data']['reviewer_task'])

    def test_the_record_says_what_must_be_read_whatever_the_depth(self):
        self.reach_review()
        always = self.triage()['data']['always_read']

        self.assertEqual(always, [self.ticket_file,
                                  f'docs/harness/history/{self.ticket_id}/'])

    def test_the_no_others_applies_to_the_diff_and_says_so(self):
        self.reach_review()
        task = self.triage()['data']['reviewer_task']

        self.assertIn('Of the diff', task)


class PartlySettledTest(FocusSetTest):
    """H2 and H3: a check that proves less than its name must not close a question."""

    def test_red_before_green_is_not_in_the_do_not_confirm_list(self):
        self.reach_review()
        task = self.triage()['data']['reviewer_task']

        settled = task.split('Already settled with no model')[1].split('\n')[0]
        self.assertNotIn('red_before_green', settled)
        self.assertIn('coverage', settled)

    def test_it_says_what_is_left_of_a_partly_settled_check(self):
        self.reach_review()
        task = self.triage()['data']['reviewer_task']

        self.assertIn('Partly settled', task)
        self.assertIn('red_before_green', task)
        self.assertIn('never that it failed for the reason', task)

    def test_acceptance_entries_is_partly_settled_too(self):
        self.reach_review()
        task = self.triage()['data']['reviewer_task']

        self.assertIn('acceptance_entries', task.split('Partly settled')[1])

    def test_the_red_check_detail_claims_only_what_it_proves(self):
        self.reach_review()
        ran = {check['name']: check for check in self.triage()['data']['deterministic']}

        detail = ran['red_before_green']['detail']
        self.assertEqual(ran['red_before_green']['outcome'], 'pass')
        self.assertIn('exited non-zero', detail)
        self.assertIn('for the reason the slice states', detail)

    def test_the_acceptance_check_detail_says_it_counts_rather_than_maps(self):
        self.reach_review()
        ran = {check['name']: check for check in self.triage()['data']['deterministic']}

        self.assertIn('Which check answers which criterion', ran['acceptance_entries']['detail'])

    def test_every_partly_settled_name_is_a_check_the_triage_runs(self):
        """A typo here would silently settle a check the reviewer should read."""
        self.assertTrue(set(triage.PARTLY_SETTLED) <= set(triage.DETERMINISTIC))


class FailedCheckStillAsksTest(ThreeCriteriaTest):
    """J1: only the three rules silence the request; a failed check does not.

    Pass one finding something wrong is the case where the criteria most need
    checking, and it was the one case nothing checked them. Every triage on this
    ticket's own branch carried jev.asked false for this reason, so pass two never
    ran once while the ticket that built it was being worked.
    """

    def unplanned_file(self):
        self.write('harness/unplanned.py', 'def unplanned():\n    return 2\n')

    def test_a_failed_check_forces_full_depth_and_still_asks(self):
        self.reach_review()
        self.unplanned_file()
        record = self.triage()

        ran = {check['name']: check for check in record['data']['deterministic']}
        self.assertEqual(ran['slice_files']['outcome'], 'fail')
        self.assertEqual(record['data']['review_depth'], 'full')
        self.assertTrue(record['data']['jev']['asked'],
                        'A failed check is why the reviewer reads everything, not a reason to '
                        'stop asking whether the criteria are evidenced')
        self.assertEqual(len(jev.TRANSPORT.sent), 1)

    def test_the_criteria_are_still_answered(self):
        self.reach_review()
        self.unplanned_file()
        answers = self.triage()['data']['criteria_answers']

        self.assertEqual(len(answers), len(self.criteria))
        for answer in answers:
            self.assertEqual(answer['source'], 'jev')

    def test_an_unevidenced_criterion_still_returns_the_ticket(self):
        self.reach_review()
        self.unplanned_file()
        base = triage_stub()

        def low_on_the_second(endpoint, payload, credential, timeout):
            body = base(endpoint, payload, credential, timeout)
            if 'criterion_evidenced#2' in body['answers']:
                body['answers']['criterion_evidenced#2'] = noul(0.1)
            return body

        low_on_the_second.sent = base.sent
        jev.TRANSPORT = low_on_the_second
        with self.assertRaisesRegex(HarnessError, self.criteria[1]):
            self.triage()

        self.assertEqual(self.run_harness('status', self.ticket_id)['stage'], 'tdd')

    def test_what_the_narrowing_would_have_dropped_is_still_measured(self):
        """The figure SEEN-109 divides on, which a skipped request left at zero."""
        self.reach_review()
        self.unplanned_file()
        jev.TRANSPORT = triage_stub(depth=(0.9, 0.1), must_read=0.05)
        record = self.triage()

        self.assertEqual(record['data']['review_depth'], 'full')
        self.assertEqual(record['data']['model_depth'], 'spot',
                         'What the rules enforced and what the model chose are two answers')
        self.assertTrue(record['data']['would_exclude'],
                        'Full depth by a failed check still records what spot would have dropped')
        self.assertGreater(record['data']['excluded_share'], 0.0)

    def test_a_depth_rule_does_still_silence_the_request(self):
        self.reach_review(solution=solution_evidence(
            migrations=['0003_add_triage.sql: a column'],
            changes=['harness/thing.py: the behaviour',
                     'harness/thresholds.toml: the settings these tests vary'],
            slices=[dict(position=1, name='The behaviour', points=1,
                         files=['harness/thing.py', 'harness/tests/test_thing.py'],
                         red='The behaviour is absent')]))
        record = self.triage()

        self.assertEqual(record['data']['jev']['asked'], False)
        self.assertEqual(jev.TRANSPORT.sent, [])
        self.assertEqual(record['data']['review_depth'], 'full')


class TestsAddedTest(FocusSetTest):
    """J2: a test path in the diff is not a test for the behaviour."""

    def test_tests_added_is_partly_settled(self):
        self.reach_review()
        task = self.triage()['data']['reviewer_task']

        self.assertIn('tests_added', task.split('Partly settled')[1])
        self.assertNotIn('tests_added',
                         task.split('Already settled with no model')[1].split('\n')[0])

    def test_its_detail_claims_only_that_a_test_path_changed(self):
        self.reach_review()
        ran = {check['name']: check for check in self.triage()['data']['deterministic']}

        self.assertIn('Whether the behaviour this slice adds has one', ran['tests_added']['detail'])


class RenamedTicketTest(FocusSetTest):
    """J3: SEEN-101's case, which procedure_paths and always_read did not follow."""

    def rename(self):
        old = self.root / self.ticket_file
        new = old.with_name(f'{self.ticket_id}-a-ticket-renamed-mid-flight.md')
        old.rename(new)
        self.git('add', '-A')
        return str(new.relative_to(self.root))

    def test_the_renamed_ticket_file_is_still_the_procedure_s_own(self):
        self.reach_review()
        renamed = self.rename()
        ran = {check['name']: check for check in self.triage()['data']['deterministic']}

        self.assertEqual(ran['slice_files']['outcome'], 'pass',
                         f'{renamed} is the ticket file under a new name, not an unplanned change')

    def test_the_task_points_at_the_ticket_as_it_stands(self):
        self.reach_review()
        renamed = self.rename()
        record = self.triage()

        self.assertEqual(record['data']['always_read'][0], renamed)
        self.assertIn(renamed, record['data']['reviewer_task'])
        self.assertTrue((self.root / renamed).is_file())


class AskedHonestlyTest(ThreeCriteriaTest):
    """K1: `asked` says whether pass two ran, and the reason says why not.

    Three cases reach the same empty answers: no credential, a transport that
    failed, and a reply nothing could be read from. The record said the same thing
    about all three, and SEEN-109 counts `asked` to find the triages pass two ran
    on.
    """

    def test_no_credential_is_recorded_as_no_request(self):
        (self.root / '.env.local').unlink()
        self.reach_review()
        asked = self.triage()['data']['jev']

        self.assertFalse(asked['asked'])
        self.assertIn('no request was made', asked['reason'])
        self.assertEqual(jev.TRANSPORT.sent, [])

    def test_a_transport_that_failed_says_the_request_was_made(self):
        self.reach_review()

        def broken(endpoint, payload, credential, timeout):
            raise OSError('the API is unreachable')

        broken.sent = jev.TRANSPORT.sent
        jev.TRANSPORT = broken
        asked = self.triage()['data']['jev']

        self.assertFalse(asked['asked'])
        self.assertIn('did not answer', asked['reason'])

    def test_a_request_that_answered_says_so_and_names_the_model(self):
        self.reach_review()
        asked = self.triage()['data']['jev']

        self.assertTrue(asked['asked'])
        self.assertIsNone(asked['reason'])
        self.assertEqual(asked['model'], 'jev-1.13.0')

    def test_a_rule_that_silenced_the_request_still_says_so_its_own_way(self):
        self.reach_review(solution=solution_evidence(
            migrations=['0003_add_triage.sql: a column'],
            changes=['harness/thing.py: the behaviour',
                     'harness/thresholds.toml: the settings these tests vary'],
            slices=[dict(position=1, name='The behaviour', points=1,
                         files=['harness/thing.py', 'harness/tests/test_thing.py'],
                         red='The behaviour is absent')]))
        asked = self.triage()['data']['jev']

        self.assertFalse(asked['asked'])
        self.assertIn('settled by rule', asked['reason'])


class PartlySettledIsDocumentedTest(unittest.TestCase):
    """K2: the canonical document and the code must name the same checks."""

    def test_the_workflow_names_every_partly_settled_check(self):
        from harness.tests.helpers import PROJECT

        paragraph = (PROJECT / 'docs' / 'harness' / 'workflow.md').read_text()
        for name in triage.PARTLY_SETTLED:
            self.assertIn(name, paragraph,
                          f'{name} passes on less than its name suggests and the document that '
                          'describes the harness does not say so')


class EveryAttemptsEvidenceTest(ThreeCriteriaTest):
    """L1: a returned ticket proved slices in each attempt, and Jev sees them all.

    Found by the triage firing on its own ticket at record 75. SEEN-107 proved its
    three planned slices in attempt 1 and one rework slice in each attempt after,
    and the state carried only the latest accepted tdd record, so two criteria came
    back unevidenced because the evidence for them was in a record Jev was never
    shown. The return was right about the state it was given, and the state was
    wrong. `kpi.slices` had already learned this: reading only the latest record
    said SEEN-104 proved one slice of the three it planned.
    """

    def prove_another_slice(self):
        """A return, then one more slice proved, the way rework goes."""
        self.run_harness('return', self.ticket_id, '--to', 'tdd', '--reason',
                         'A finding', '--actor', 'codex:reviewer')
        red = self.run_check('red', exit_code=1)
        green = self.run_check('green')
        regression = self.run_check('regression')
        self.record_coverage(0.0, attempt=2)
        self.submit('tdd', dict(mode='code', regression=regression['sequence'],
                                coverage_delta=0.0,
                                slices=[dict(position=1, behaviour='The correction',
                                             failure_reason='It was wrong',
                                             red=red['sequence'], green=green['sequence'])]))

    def test_the_state_carries_every_accepted_attempt_s_slices(self):
        self.reach_review()
        self.triage()
        self.prove_another_slice()
        self.triage()

        slices = jev.TRANSPORT.sent[-1]['payload']['state']['journal']['slices']
        behaviours = [entry['behaviour'] for entry in slices]
        self.assertIn('The behaviour', behaviours,
                      'The slice proved in attempt 1 is still what evidences its criterion')
        self.assertIn('The correction', behaviours)

    def test_each_slice_says_which_attempt_proved_it(self):
        self.reach_review()
        self.triage()
        self.prove_another_slice()
        self.triage()

        slices = jev.TRANSPORT.sent[-1]['payload']['state']['journal']['slices']
        self.assertEqual([entry['attempt'] for entry in slices], [1, 2])

    def test_a_ticket_with_no_rework_is_unchanged(self):
        self.reach_review()
        self.triage()

        slices = jev.TRANSPORT.sent[-1]['payload']['state']['journal']['slices']
        self.assertEqual(len(slices), 1)
        self.assertEqual(slices[0]['behaviour'], 'The behaviour')

    def test_the_excerpt_is_capped_so_a_long_ticket_cannot_blow_up_the_request(self):
        self.assertEqual(triage.MAX_SLICE_OUTPUTS, 8)


class SliceCapTest(unittest.TestCase):
    """M1 and M2: what a long ticket loses, and what it must not.

    The first cap kept the newest slices and dropped the oldest, which is the
    rework kept and the planned work dropped: past the bound the slices that
    evidence most criteria would have vanished, which is the input that produced
    the false unevidenced answers at record 75. Nothing caught it, because the
    only guard asserted the constant and no test built enough slices to reach the
    bound. These do.
    """

    def journal(self, slices):
        """One accepted tdd record per slice, each citing a red and a green."""
        from harness.tests.test_kpi import record
        records = [record(1, 'start', 'clarify', minute=0, ticket_file='docs/tickets/x.md',
                          ticket_snapshot='# x'),
                   record(2, 'advance', 'clarify', minute=1, from_stage='clarify',
                          to_stage='solution', evidence=dict(acceptance=['AC1']), decisions=[])]
        sequence = 3
        for position in range(slices):
            red, green = sequence, sequence + 1
            records.append(record(red, 'check', 'tdd', attempt=position + 1, minute=position * 10,
                                  phase='red', exit_code=1, command=['t'],
                                  output=f'failure {position}'))
            records.append(record(green, 'check', 'tdd', attempt=position + 1,
                                  minute=position * 10 + 1, phase='green', exit_code=0,
                                  command=['t'], output='ok'))
            records.append(record(green + 1, 'advance', 'tdd', attempt=position + 1,
                                  minute=position * 10 + 2, from_stage='tdd', to_stage='review',
                                  decisions=[],
                                  evidence=dict(slices=[dict(position=1, behaviour=f'slice {position}',
                                                             failure_reason=f'reason {position}',
                                                             red=red, green=green)])))
            sequence += 3
        return records

    def test_every_proved_slice_is_in_the_state_however_many_there_are(self):
        excerpts = triage.journal_excerpts(self.journal(20))

        self.assertEqual(excerpts['slices_proved'], 20)
        self.assertEqual([entry['behaviour'] for entry in excerpts['slices']],
                         [f'slice {position}' for position in range(20)],
                         'A slice that evidences a criterion cannot be dropped for being old')

    def test_the_oldest_slice_keeps_its_behaviour_and_the_reason_it_failed(self):
        oldest = triage.journal_excerpts(self.journal(20))['slices'][0]

        self.assertEqual(oldest['behaviour'], 'slice 0')
        self.assertEqual(oldest['failure_reason'], 'reason 0')
        self.assertEqual(oldest['red']['exit_code'], 1)
        self.assertEqual(oldest['red']['command'], ['t'])

    def test_what_the_cap_drops_is_the_runner_output_of_the_older_slices(self):
        excerpts = triage.journal_excerpts(self.journal(20))
        outputs = [entry['red']['output'] for entry in excerpts['slices']]

        self.assertEqual(outputs.count(None), 20 - triage.MAX_SLICE_OUTPUTS)
        self.assertIsNone(outputs[0], 'The oldest keeps its shape and loses its log')
        self.assertEqual(outputs[-1], 'failure 19', 'The newest keeps the log a reader needs')

    def test_a_ticket_inside_the_bound_keeps_every_output(self):
        excerpts = triage.journal_excerpts(self.journal(triage.MAX_SLICE_OUTPUTS))

        self.assertTrue(all(entry['red']['output'] for entry in excerpts['slices']))


class ReviewerModelTest(FocusSetTest):
    """The reviewer's model is a rule, and the depth is what decides it.

    A full review holds the whole diff, the journal and the criteria at once,
    which is the most expensive read in the procedure and the one where a missed
    defect costs most; a spot review reads a narrowed focus set. So full depth
    gets the strongest tier and spot depth one tier down. From SEEN-108.
    """

    def test_full_depth_reviews_on_the_strongest_model(self):
        self.reach_review()
        record = self.triage()

        self.assertEqual(record['data']['review_depth'], 'full')
        self.assertEqual(record['data']['reviewer_model'], 'opus')

    def test_spot_depth_reviews_one_tier_down(self):
        self.set_shadow(False)
        jev.TRANSPORT = self.only_thing_is_worth_reading()
        self.reach_review()
        record = self.triage()

        self.assertEqual(record['data']['review_depth'], 'spot')
        self.assertEqual(record['data']['reviewer_model'], 'sonnet')

    def test_the_task_names_the_model_to_run_the_reviewer_on(self):
        self.reach_review()
        task = self.triage()['data']['reviewer_task']

        self.assertRegex(task, r'(?i)opus')

if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
