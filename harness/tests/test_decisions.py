"""The decision layer: typed questions, recorded with their probabilities.

Jev answers questions about the procedure, never about the product. Every test
here runs against a stub transport: no test calls the API.
"""

import json
import os

from harness import cli, jev
from harness.errors import HarnessError
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence


def stub(answer, score=None):
    """A transport that answers in the shape the question asked for.

    One canned body per question type, because a real answer to a score question
    is never yes or no, and a stub that ignores the type tests nothing.
    """
    sent = []

    def transport(endpoint, payload, credential, timeout):
        sent.append(dict(endpoint=endpoint, payload=payload, credential=credential))
        if payload['type'] == 'score':
            return score or SCORE
        return answer

    transport.sent = sent
    return transport


NOUL = {'answer': 'yes', 'probabilities': {'yes': 0.93, 'no': 0.07}, 'model': 'typesafe/jev-1.13'}
SCORE = {'answer': 'medium', 'probabilities': {'low': 0.2, 'medium': 0.7, 'high': 0.1},
         'model': 'typesafe/jev-1.13'}


class QuestionTest(CommandTest):

    credentialled = True

    def setUp(self):
        super().setUp()
        if self.credentialled:
            self.write('.env.local', 'JEV_API_KEY=stub-credential\n')
        self.start()

    def decide(self, question, *args, **named):
        return self.run_harness('decide', self.ticket_id, '--question', question,
                                '--actor', 'claude:implementer', *args, **named)


class AnswerTest(QuestionTest):

    def test_an_answer_becomes_a_decision_record(self):
        jev.TRANSPORT = stub(NOUL)
        record = self.decide('clarified')
        self.assertEqual(record['kind'], 'decision')
        data = record['data']
        self.assertEqual(data['question'], 'clarified')
        self.assertEqual(data['source'], 'jev')
        self.assertEqual(data['model'], 'typesafe/jev-1.13')
        self.assertEqual(data['outcome'], 'yes')
        self.assertEqual(data['probabilities']['yes'], 0.93)
        self.assertEqual(data['threshold'], 0.8)
        self.assertTrue(data['passed'])

    def test_a_score_question_carries_every_option(self):
        jev.TRANSPORT = stub(SCORE)
        data = self.decide('risk')['data']
        self.assertEqual(data['type'], 'score')
        self.assertEqual(sorted(data['probabilities']), ['high', 'low', 'medium'])
        self.assertEqual(data['outcome'], 'medium')

    def test_a_probability_below_the_threshold_does_not_pass(self):
        jev.TRANSPORT = stub({'answer': 'yes', 'probabilities': {'yes': 0.6, 'no': 0.4},
                              'model': 'typesafe/jev-1.13'})
        self.assertFalse(self.decide('clarified')['data']['passed'])

    def test_the_record_carries_the_state_that_was_judged(self):
        transport = stub(NOUL)
        jev.TRANSPORT = transport
        self.decide('clarified')
        payload = transport.sent[0]['payload']
        self.assertEqual(payload['model'], 'typesafe/jev-1.13')
        self.assertIn('clarified', json.dumps(payload))

    def test_an_unknown_question_names_the_ones_that_exist(self):
        jev.TRANSPORT = stub(NOUL)
        with self.assertRaisesRegex(HarnessError, 'clarified'):
            self.decide('is_it_friday')

    def test_the_threshold_comes_from_the_threshold_file(self):
        path = self.root / 'harness' / 'thresholds.toml'
        path.write_text(path.read_text().replace('clarified = 0.8', 'clarified = 0.95'))
        jev.TRANSPORT = stub(NOUL)
        data = self.decide('clarified')['data']
        self.assertEqual(data['threshold'], 0.95)
        self.assertFalse(data['passed'], '0.93 does not clear 0.95')


class FallbackTest(QuestionTest):

    credentialled = False

    def test_without_a_credential_the_human_answers(self):
        jev.TRANSPORT = None
        data = self.decide('clarified', '--answer', 'yes', '--confidence', '1.0')['data']
        self.assertEqual(data['source'], 'human')
        self.assertEqual(data['outcome'], 'yes')
        self.assertIsNone(data['model'])
        self.assertTrue(data['passed'])

    def test_without_a_credential_and_without_an_answer_it_says_what_to_run(self):
        jev.TRANSPORT = None
        with self.assertRaisesRegex(HarnessError, '--answer'):
            self.decide('clarified')

    def test_a_failing_api_falls_back_rather_than_failing_the_command(self):
        self.write('.env.local', 'JEV_API_KEY=stub-credential\n')

        def broken(endpoint, payload, credential, timeout):
            raise OSError('connection reset')
        jev.TRANSPORT = broken
        data = self.decide('clarified', '--answer', 'no', '--confidence', '0.9')['data']
        self.assertEqual(data['source'], 'human')
        self.assertIn('connection reset', data['fallback_reason'])

    def test_a_human_answer_outside_the_options_is_refused(self):
        jev.TRANSPORT = None
        with self.assertRaisesRegex(HarnessError, 'low'):
            self.decide('risk', '--answer', 'catastrophic', '--confidence', '1.0')


class SecrecyTest(QuestionTest):

    def test_no_decision_record_holds_the_credential_or_any_environment_value(self):
        os.environ['SEEN_TEST_SECRET'] = 'sk-do-not-record-me-4f2b'
        self.addCleanup(os.environ.pop, 'SEEN_TEST_SECRET', None)
        self.write('.env.local', 'JEV_API_KEY=credential-that-must-not-be-recorded\n')

        def echoing(endpoint, payload, credential, timeout):
            # An API that reflects the request, credentials and all.
            return {'answer': 'yes', 'probabilities': {'yes': 0.9, 'no': 0.1},
                    'model': 'typesafe/jev-1.13', 'echo': {'credential': credential,
                                                           'env': dict(os.environ)}}
        jev.TRANSPORT = echoing
        record = self.decide('clarified')
        written = json.dumps(record)
        self.assertNotIn('sk-do-not-record-me-4f2b', written)
        self.assertNotIn('SEEN_TEST_SECRET', written)
        self.assertNotIn('credential-that-must-not-be-recorded', written)

    def test_the_credential_is_read_from_the_env_file_before_the_environment(self):
        self.write('.env.local', 'JEV_API_KEY=from-the-file\n')
        os.environ['JEV_API_KEY'] = 'from-the-environment'
        self.addCleanup(os.environ.pop, 'JEV_API_KEY', None)
        self.assertEqual(jev.credential(self.root), 'from-the-file')

    def test_either_variable_name_works(self):
        (self.root / '.env.local').unlink()      # the file wins, so it must not be there
        os.environ.pop('JEV_API_KEY', None)
        os.environ['JEV_AI_API_KEY'] = 'from-the-other-name'
        self.addCleanup(os.environ.pop, 'JEV_AI_API_KEY', None)
        self.assertEqual(jev.credential(self.root), 'from-the-other-name')


class GateTest(QuestionTest):

    def test_advance_from_clarify_is_refused_below_the_threshold(self):
        jev.TRANSPORT = stub({'answer': 'no', 'probabilities': {'yes': 0.41, 'no': 0.59},
                              'model': 'typesafe/jev-1.13'})
        with self.assertRaisesRegex(HarnessError, 'clarified'):
            self.submit('clarify', clarify_evidence())

    def test_the_refusal_quotes_the_probability_it_judged_on(self):
        jev.TRANSPORT = stub({'answer': 'no', 'probabilities': {'yes': 0.41, 'no': 0.59},
                              'model': 'typesafe/jev-1.13'})
        try:
            self.submit('clarify', clarify_evidence())
            self.fail('the advance should have been refused')
        except HarnessError as error:
            self.assertIn('0.41', str(error))

    def test_a_clear_answer_lets_the_advance_through_and_is_recorded_beside_it(self):
        jev.TRANSPORT = stub(NOUL)
        record = self.submit('clarify', clarify_evidence())
        self.assertEqual(record['data']['to_stage'], 'solution')
        questions = [decision['question'] for decision in record['data']['decisions']]
        self.assertIn('clarified', questions)
        self.assertIn('risk', questions)

    def test_a_review_finding_nothing_to_fix_is_not_blocked(self):
        """must_fix is the one question that refuses when it passes.

        clarified and solution_complete must clear their bar to advance. must_fix
        is the opposite: a confident yes means something must be fixed, and that
        is what stops the ticket.
        """
        from harness import jev
        answer = dict(question='must_fix', type='noul', options=['yes', 'no'], source='human',
                      model=None, outcome='no', probabilities={'yes': 0.1, 'no': 0.9},
                      threshold=0.7, passed=False, fallback_reason=None)
        cli.require_decisions_pass('review', [answer])          # nothing to fix: proceed

        blocking = dict(answer, outcome='yes', probabilities={'yes': 0.92, 'no': 0.08},
                        passed=True)
        with self.assertRaisesRegex(HarnessError, 'must_fix'):
            cli.require_decisions_pass('review', [blocking])

    def test_a_clarify_question_refuses_the_other_way_round(self):
        answer = dict(question='clarified', type='noul', options=['yes', 'no'], source='jev',
                      model='typesafe/jev-1.13', outcome='no', probabilities={'yes': 0.3, 'no': 0.7},
                      threshold=0.8, passed=False, fallback_reason=None)
        with self.assertRaisesRegex(HarnessError, 'clarified'):
            cli.require_decisions_pass('clarify', [answer])

    def test_a_billing_or_policy_gate_ticket_needs_a_second_reviewer(self):
        jev.TRANSPORT = stub(NOUL)
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())
        draft = self.run_harness('draft', self.ticket_id, '--stage', 'review')
        self.assertIn('second_reviewer', json.loads((self.root / draft['draft']).read_text()))
