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
            'triage_shadow = true', f'triage_shadow = {"true" if on else "false"}'))

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
        self.set_shadow(False)
        jev.TRANSPORT = self.only_thing_is_worth_reading()
        self.reach_review()
        record = self.triage()

        task = record['data']['reviewer_task']
        self.assertIn('harness/thing.py', task)
        for path in record['data']['would_exclude']:
            self.assertNotIn(path, task,
                             f'{path} is outside the focus set, so the task must not name it')

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
        data = dict(review_depth='spot', shadow=True, excluded_share=0.42,
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

        self.assertEqual(figures['depth'], 'spot')
        self.assertTrue(figures['shadow'])
        self.assertEqual(figures['files'], 3)
        self.assertEqual(figures['focus'], 3)
        self.assertEqual(figures['excluded'], 2)
        self.assertEqual(figures['excluded_share'], 0.42)
        self.assertEqual(figures['record'], 3)

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
        opened, closed = kpi.review_window(self.journal())

        self.assertEqual(opened, '2026-09-23T10:20:00+00:00')
        self.assertEqual(closed, '2026-09-23T10:40:00+00:00')

    def test_there_is_no_window_without_a_triage(self):
        records = [entry for entry in self.journal() if entry['kind'] != 'triage']
        self.assertIsNone(kpi.review_window(records))


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


if __name__ == '__main__':
    unittest.main()
