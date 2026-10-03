"""The run: what the next action is, where it stops, and what it refuses.

Slice 1 of SEEN-112. Three properties, and the first is the cheap one: the loop
answers every stage of one ticket with argv a session can run, so an
end-to-end run is a sequence of commands a person can read rather than a model
improvising. The second is the one the ticket is really about: every stop is one
of the named ones, each says where it stopped and how to resume, and none is
retried, which in an append-only journal means at most one stop record per
reason and record. The third is the refusal: a ticket whose executor is `human`
is refused before its journal exists, because a run that started SEEN-110 would
arrive at a verification whose only way forward is to invent the fact the
criterion exists to establish.

Slice 2 adds the three things the run needs before it can be trusted with a whole
ticket: the single question batch, the merge that waits on a person, and the
summary a person reads at the end. All three are below, from QuestionBatchTest
onwards.

Attempt 3 turns the summary from a list of criteria into the run's own evidence
about itself: who worked each slice, on what, and what it cost. RunEvidenceTest,
at the end.
"""

import contextlib
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

from harness import cli, loop, routing, thresholds
from harness.errors import HarnessError
from harness.tests import helpers
from harness.tests.test_delivery import DeliveryWalk
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence
from harness.tests.test_session_cap import SessionEnvironment, plan

PROJECT = Path(__file__).resolve().parents[2]
# Every action's argv starts here: the entry point a session already runs.
ENTRY = ['python3', 'harness/run.py']
# Except the merge, which nothing in the harness does.
MERGE = ['gh', 'pr', 'merge']
# The worked example the ticket names, read from the real file rather than a
# fixture: what the refusal has to name is what this ticket actually says.
SEEN_110 = 'SEEN-110-verify-the-hooks-in-a-codex-session-and-close.md'


class RunMixin:
    """Asking the loop, and the properties every answer has."""

    def rules(self):
        return thresholds.load(self.root)

    def ask(self, *extra):
        return self.run_harness('run', self.ticket_id, '--actor', 'claude:implementer', *extra)

    def named(self, action):
        """The harness subcommand this action's argv runs."""
        return action['argv'][2]

    def assert_runnable(self, action):
        self.assertIn(action['kind'], loop.ACTIONS, action)
        if action['kind'] == 'merge':
            # The one action whose argv is not a harness command, because the
            # harness has no merge and never will: what merges a pull request is
            # gh, run by the person who authorised it.
            self.assertEqual(action['argv'][:3], MERGE, action)
        else:
            self.assertEqual(action['argv'][:2], ENTRY, action)
            self.assertIn(self.ticket_id, action['argv'], action)
        self.assertTrue(action['why'], action)
        self.assertEqual(list(action['stops']), list(loop.stops(self.rules())), action)
        if action['kind'] == 'stop':
            self.assertIn(action['reason'], loop.stops(self.rules()), action)
        return action

    def kinds(self):
        return [record['kind'] for record in self.records()]


class LoopTest(RunMixin, DeliveryWalk):
    """One ticket from clarify to the receipt, asking the loop at every step."""

    def test_the_loop_answers_every_stage_with_runnable_argv(self):
        answers = []

        def step():
            action = self.assert_runnable(self.ask())
            answers.append(action)
            return action

        # Nothing started yet: the run begins by starting the ticket.
        self.assertEqual(self.named(step()), 'start')
        self.start()

        # Each working stage is a draft to fill in and then its gate.
        self.assertEqual(self.named(step()), 'draft')
        self.run_harness('draft', self.ticket_id)
        self.assertEqual(self.named(step()), 'advance')
        self.submit('clarify', clarify_evidence())

        self.assertEqual(self.named(step()), 'draft')
        self.run_harness('draft', self.ticket_id)
        self.assertEqual(self.named(step()), 'advance')
        self.submit('solution', solution_evidence())

        # tdd: the plan is routed before a slice is worked, because the model a
        # slice runs on is never chosen inside the session that works it.
        self.assertEqual(self.named(step()), 'route')
        self.run_harness('route', self.ticket_id, '--actor', 'claude:implementer')

        spawn = step()
        self.assertEqual(spawn['kind'], 'spawn')
        self.assertEqual(spawn['agent'], 'seen-implementer')
        self.assertIn('Work slice 1', spawn['task'])
        self.assertEqual(self.named(spawn), 'check')
        self.assertIn('--agent', spawn['argv'])
        self.assertIn('seen-implementer', spawn['argv'])
        self.assertIn('--model', spawn['argv'])

        red = self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                               'claude:implementer', '--', 'sh', '-c',
                               'echo expected 1, got 0; exit 1')
        green = self.run_harness('check', self.ticket_id, '--phase', 'green', '--actor',
                                 'claude:implementer', '--', 'true')

        # The slice is proved, so what is left before the gate is the measurement
        # and the regression.
        self.assertEqual(self.named(step()), 'coverage')
        self.write('packages/core/coverage/coverage-summary.json',
                   '{"total": {"lines": {"total": 10, "covered": 9, "skipped": 0, "pct": 90.0}}}')
        self.run_harness('coverage', self.ticket_id, '--actor', 'claude:implementer', '--', 'true')

        regression = step()
        self.assertEqual(self.named(regression), 'check')
        self.assertIn('regression', regression['argv'])
        recorded = self.run_harness('check', self.ticket_id, '--phase', 'regression', '--actor',
                                    'claude:implementer', '--', 'true')

        self.assertEqual(self.named(step()), 'draft')
        self.run_harness('draft', self.ticket_id)
        self.assertEqual(self.named(step()), 'advance')
        self.submit('tdd', dict(mode='code',
                                slices=[dict(position=1,
                                             behaviour='The loop answers every stage',
                                             failure_reason='expected 1, got 0',
                                             red=red['sequence'], green=green['sequence'])],
                                regression=recorded['sequence'],
                                coverage_delta=None))

        # review: the cheapest pass first, which is the triage.
        triage = step()
        self.assertEqual(self.named(triage), 'review')
        self.assertIn('triage', triage['argv'])
        qa = self.run_harness('check', self.ticket_id, '--phase', 'qa', '--actor',
                              'codex:reviewer', '--', 'true')
        self.submit('review', dict(reviewer='codex:reviewer',
                                   independence='independent',
                                   read=['harness/loop.py'],
                                   acceptance_evidence=['The journal holds every stage'],
                                   findings=[],
                                   checks=[qa['sequence']],
                                   security_checklist=['No secret in the diff'],
                                   verdict='pass'),
                    actor='codex:reviewer')

        self.assertEqual(self.named(step()), 'draft')
        self.run_harness('draft', self.ticket_id)
        self.assertEqual(self.named(step()), 'verify-delivery')
        self.commit_and_push()
        self.verify()

        # The receipt is written and the merge is not the run's to take: the last
        # action is the check a person reads before merging by hand.
        self.assertEqual(self.named(step()), 'verify-merge')

        # No step of a run with nothing wrong is a stop, and no stop reason the
        # thresholds do not name can appear at all (assert_runnable checks the
        # vocabulary on every answer above).
        self.assertEqual([action for action in answers if action['kind'] == 'stop'], [])
        self.assertNotIn('stop', self.kinds())

    def test_asking_the_loop_never_makes_the_journal_longer_on_its_own(self):
        self.start()
        before = len(self.records())
        for _ in range(3):
            self.ask()
        self.assertEqual(len(self.records()), before)


class StopTest(RunMixin, CommandTest):
    """Every named stop says where it stopped, and none is retried."""

    def setUp(self):
        super().setUp()
        self.start()

    def test_every_named_stop_reports_its_stage_its_record_and_one_resume_command(self):
        for reason in loop.stops(self.rules()):
            with self.subTest(reason=reason):
                action = self.assert_runnable(self.ask('--stop', reason))
                self.assertEqual(action['kind'], 'stop')
                self.assertEqual(action['reason'], reason)
                self.assertEqual(action['stage'], 'clarify')
                # The record that made it stop, never the stop itself.
                self.assertEqual(action['record'], 1)
                self.assertEqual(action['resume'][:2], ENTRY)
                self.assertIn(self.ticket_id, action['resume'])
                self.assertTrue(action['why'])

    def test_a_stop_that_stands_is_reported_again_and_recorded_once(self):
        first = self.ask('--stop', 'check_failed')
        self.assertTrue(first['recorded'])
        before = len(self.records())
        second = self.ask('--stop', 'check_failed')
        self.assertFalse(second['recorded'])
        self.assertEqual(second['sequence'], first['sequence'])
        self.assertEqual(second['record'], first['record'])
        self.assertEqual(second['resume'], first['resume'])
        self.assertEqual(len(self.records()), before)
        self.assertEqual(self.kinds().count('stop'), 1)

    def test_a_stop_reason_the_thresholds_do_not_name_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'stop'):
            self.ask('--stop', 'it_felt_wrong')
        self.assertNotIn('stop', self.kinds())

    def test_a_failed_check_stops_the_run_on_the_journal_alone(self):
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())
        self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                         'claude:implementer', '--', 'sh', '-c', 'echo not yet; exit 1')
        # A red that fails is the red doing its job, so the run carries on.
        self.assertNotEqual(self.ask()['kind'], 'stop')
        green = self.run_harness('check', self.ticket_id, '--phase', 'green', '--actor',
                                 'claude:implementer', '--', 'sh', '-c', 'echo still red; exit 3')
        action = self.ask()
        self.assertEqual(action['kind'], 'stop')
        self.assertEqual(action['reason'], 'check_failed')
        self.assertEqual(action['record'], green['sequence'])
        self.assertEqual(self.kinds().count('stop'), 1)
        self.ask()
        self.assertEqual(self.kinds().count('stop'), 1)

    def test_a_second_return_under_one_plan_stops_the_run(self):
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())
        self.run_harness('return', self.ticket_id, '--to', 'clarify', '--reason',
                         'The scope named the wrong marketplace', '--actor', 'claude:implementer')
        self.assertNotEqual(self.ask()['kind'], 'stop')
        self.submit('clarify', clarify_evidence())
        second = self.run_harness('return', self.ticket_id, '--to', 'clarify', '--reason',
                                  'And the scope is still wrong', '--actor', 'claude:implementer')
        action = self.ask()
        self.assertEqual(action['kind'], 'stop')
        self.assertEqual(action['reason'], 'second_return')
        self.assertEqual(action['record'], second['sequence'])
        self.assertEqual(self.kinds().count('stop'), 1)


class HumanExecutorTest(unittest.TestCase):
    """SEEN-110, the ticket a run must refuse before it writes anything."""

    ticket_id = 'SEEN-110'

    def setUp(self):
        self.root, stub = helpers.make_project(self.ticket_id)
        (self.root / stub).unlink()
        self.relative = f'docs/tickets/{SEEN_110}'
        self.text = (PROJECT / self.relative).read_text()
        (self.root / self.relative).write_text(self.text)
        helpers.git(self.root, 'add', '-A')
        helpers.git(self.root, 'commit', '-q', '-m', 'docs: the ticket as it stands')

    def argv(self):
        return ['--root', str(self.root), 'run', self.ticket_id, '--actor', 'claude:implementer']

    def refusal(self):
        with self.assertRaises(HarnessError) as caught:
            cli.execute(cli.parse(self.argv()))
        return str(caught.exception)

    def test_the_run_exits_non_zero_and_says_the_executor_is_human(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = cli.main(self.argv())
        self.assertNotEqual(code, 0)
        self.assertIn('human', stderr.getvalue())

    def test_the_refusal_names_the_criteria_that_wait_on_an_interactive_session(self):
        message = self.refusal()
        self.assertIn('is recorded as a verification in the journal', message)
        self.assertIn('is settled from that session', message)
        self.assertIn('If the session contradicts what SEEN-106 generated', message)

    def test_the_refusal_leaves_out_the_criteria_a_session_could_settle(self):
        message = self.refusal()
        self.assertNotIn('The tdd gate refuses a regression check', message)
        self.assertNotIn("harness command list names every command", message)

    def test_a_refused_ticket_gets_no_journal_at_all(self):
        self.refusal()
        self.assertFalse((self.root / 'docs' / 'harness' / 'history' / self.ticket_id).exists())

    def test_a_ticket_a_session_can_work_is_not_refused(self):
        """The refusal is about the executor and not about the word human.

        A code ticket mentioning a person in its criteria is worked, or the
        refusal would be a keyword search standing in for a decision.
        """
        root, relative = helpers.make_project('SEEN-001')
        text = (root / relative).read_text().replace(
            '- [ ] Something observable happens',
            '- [ ] A person verifies the figure in an interactive session')
        (root / relative).write_text(text)
        helpers.git(root, 'add', '-A')
        helpers.git(root, 'commit', '-q', '-m', 'docs: a criterion naming a person')
        action = cli.execute(cli.parse(['--root', str(root), 'run', 'SEEN-001',
                                        '--actor', 'claude:implementer']))
        self.assertEqual(action['argv'][2], 'start')


class QuestionBatchTest(RunMixin, CommandTest):
    """Every question a record leaves open, asked once and in one batch.

    Slice 2. Two properties: the batch, because a run that asked its questions one
    at a time would stop as many times over one record and spend a person's
    attention on each; and the resume, because what makes the run continue is the
    answer being recorded rather than the loop deciding it liked it. What only the
    work can settle is not asked at all: it belongs in the record's decisions with
    the observation that will settle it, which is SEEN-100's distinction, and the
    record's own two lists are what makes it rather than a classifier here.
    """

    QUESTIONS = ['Which marketplace does the first pilot run on?',
                 'Who signs the DPA before the pilot starts?']
    # An unknowable in the record's own words: named, with what will settle it.
    ONLY_THE_WORK = ('Whether gh answers within the timeout on a cold machine, settled by the '
                     'first real merge')

    def setUp(self):
        super().setUp()
        self.start()

    def draft(self, questions, answers=()):
        """The clarify draft as a session would leave it, open questions and all."""
        data = clarify_evidence(open_questions=list(questions),
                                decisions=['Recorded by the harness itself, per SEEN-086',
                                           self.ONLY_THE_WORK, *answers])
        self.write(f'.harness-drafts/{self.ticket_id}-clarify.json', json.dumps(data))
        return data

    def answer(self, text='Bol, and Ruud signs it. Both answered on 27 September 2026.'):
        self.write(f'.harness-drafts/{self.ticket_id}-answers.md', text)
        return self.run_harness('note', self.ticket_id, '--file',
                                f'.harness-drafts/{self.ticket_id}-answers.md',
                                '--actor', 'claude:implementer')

    def test_every_open_question_is_asked_at_once_in_one_ask(self):
        self.draft(self.QUESTIONS)
        action = self.assert_runnable(self.ask())
        self.assertEqual(action['kind'], 'ask')
        self.assertEqual(action['questions'], self.QUESTIONS)
        # Where the answer goes: on record as a note, not into the loop's head.
        self.assertEqual(self.named(action), 'note')
        # What only the work can settle is not in the batch, and the ask says
        # where it belongs instead.
        self.assertNotIn(self.ONLY_THE_WORK, action['questions'])
        self.assertIn('decisions', action['why'])

    def test_the_ask_leaves_one_question_open_stop_pointing_at_the_record(self):
        self.draft(self.QUESTIONS)
        action = self.ask()
        self.assertEqual(action['stop']['reason'], 'question_open')
        self.assertEqual(action['stop']['record'], 1)
        self.assertTrue(action['stop']['recorded'])
        stopped = self.records()[-1]
        self.assertEqual(stopped['kind'], 'stop')
        # The stop carries the batch, which is what makes a later question a
        # second batch rather than the same one asked twice.
        self.assertEqual(stopped['data']['questions'], self.QUESTIONS)
        self.ask()
        self.assertEqual(self.kinds().count('stop'), 1)

    def test_the_run_continues_once_a_note_answers_the_batch(self):
        self.draft(self.QUESTIONS)
        self.assertEqual(self.ask()['kind'], 'ask')
        self.answer()
        answered = self.draft([], answers=['Bol first, on Ruud\'s call of 27 September 2026'])
        action = self.assert_runnable(self.ask())
        self.assertNotEqual(action['kind'], 'stop')
        self.assertEqual(self.named(action), 'advance')
        # And the gate is what judges the answer: `clarified` clears, the record
        # is accepted, and nothing here decided that for itself.
        self.assertEqual(self.submit('clarify', answered)['data']['to_stage'], 'solution')

    def test_a_second_batch_is_counted_from_the_stop_records_as_a_defect(self):
        self.draft(self.QUESTIONS)
        self.ask()
        self.answer()
        later = 'And who pays for the Amazon developer account?'
        self.draft([*self.QUESTIONS, later])
        second = self.ask()
        self.assertEqual(second['kind'], 'ask')
        # Only what the first batch did not carry: a question already asked and
        # answered is not asked again.
        self.assertEqual(second['questions'], [later])
        summary = self.run_harness('run', self.ticket_id, '--summary')
        self.assertEqual(summary['question_batches'],
                         [record['sequence'] for record in self.records()
                          if record['kind'] == 'stop'])
        defect = next(entry for entry in summary['defects']
                      if entry['defect'] == 'second_question_batch')
        self.assertEqual(defect['records'], summary['question_batches'])


class MergeAuthorisationTest(RunMixin, DeliveryWalk):
    """The merge waits on a person, and the run never takes it.

    Slice 2. The receipt says what was built and verify-merge says it is still
    what is about to merge; neither says anybody wanted it merged. That is the
    authorisation record, and the loop offers the merge only once one exists.
    """

    def deliver(self):
        """A delivered ticket whose pull request carries its receipt hash."""
        self.walk_to_deliver()
        self.commit_and_push()
        delivered = self.verify()
        from harness import github
        github.PULL_REQUEST = lambda repository: dict(
            number=1, body=f'Receipt: {delivered["receipt_sha256"]}',
            headRefName=f'claude/{self.ticket_id}-a-ticket-to-work')
        return delivered

    def authorise(self, by='Ruud'):
        return self.run_harness('authorise', self.ticket_id, '--merge', '--by', by,
                                '--actor', 'claude:implementer')

    def test_a_green_verify_merge_stops_the_run_and_offers_no_merge(self):
        delivered = self.deliver()
        action = self.assert_runnable(self.ask())
        self.assertEqual(action['kind'], 'stop')
        self.assertEqual(action['reason'], 'awaiting_authorisation')
        self.assertEqual(action['stage'], 'delivered')
        # One command resumes it, and it is the authorisation.
        self.assertEqual(self.named(action), 'authorise')
        self.assertIn('--merge', action['resume'])
        # The receipt stays the last record, which is what verify-merge itself
        # requires, so the run's ordinary end is reported and not written.
        self.assertFalse(action['recorded'])
        self.assertEqual(self.records()[-1]['kind'], 'receipt')
        self.assertEqual(self.records()[-1]['sequence'], delivered['record']['sequence'])

    def test_the_merge_is_offered_only_after_an_authorisation_record(self):
        self.deliver()
        self.assertEqual(self.ask()['kind'], 'stop')
        authorised = self.authorise()
        self.assertEqual(authorised['kind'], 'authorisation')
        self.assertEqual(authorised['data']['scope'], 'merge')
        self.assertEqual(authorised['data']['by'], 'Ruud')
        # When is the record's own timestamp, and what was authorised is named.
        self.assertTrue(authorised['timestamp'])
        self.assertEqual(authorised['data']['tip'], self.git('rev-parse', 'HEAD'))
        action = self.assert_runnable(self.ask())
        self.assertEqual(action['kind'], 'merge')
        self.assertEqual(action['authorisation'], authorised['sequence'])
        self.assertEqual(action['by'], 'Ruud')

    def test_the_loop_never_merges_anything_itself(self):
        self.deliver()
        self.ask()
        self.authorise()
        head, before = self.git('rev-parse', 'HEAD'), len(self.records())
        action = self.ask()
        self.ask()
        # The argv is handed over, not run: the branch and the journal are
        # exactly where they were before the loop was asked twice.
        self.assertEqual(action['argv'][:3], MERGE)
        self.assertEqual(self.git('rev-parse', 'HEAD'), head)
        self.assertEqual(len(self.records()), before)

    def test_a_branch_that_moved_after_the_authorisation_is_not_offered_for_merge(self):
        self.deliver()
        self.ask()
        self.authorise()
        self.write('after.md', 'A commit nobody authorised.')
        self.commit_and_push('docs: after the authorisation')
        action = self.assert_runnable(self.ask())
        self.assertNotEqual(action['kind'], 'merge')
        self.assertEqual(self.named(action), 'reopen')

    def test_a_merge_cannot_be_authorised_before_there_is_a_receipt(self):
        self.walk_to_deliver()
        with self.assertRaisesRegex(HarnessError, 'deliver'):
            self.authorise()
        self.assertNotIn('authorisation', self.kinds())


class SummaryTest(RunMixin, CommandTest):
    """Every criterion, its box as the ticket file has it, and what it waits on.

    Slice 2. The summary is the one thing a run produces that a person reads
    rather than executes, so it asserts nothing of its own: the box state is the
    ticket file's and what an unmet criterion waits on is the journal's.
    """

    CRITERIA = ['Something observable happens', 'And something else is measured']
    CHECKS = ['The journal holds one record per stage',
              'The second is measured by the run that delivers it']

    def setUp(self):
        super().setUp()
        self.start()
        path = self.root / self.ticket_file
        path.write_text(path.read_text().replace(
            f'- [ ] {self.CRITERIA[0]}',
            f'- [x] {self.CRITERIA[0]}\n- [ ] {self.CRITERIA[1]}'))

    def summary(self):
        return self.run_harness('run', self.ticket_id, '--summary')

    def test_every_criterion_is_listed_with_its_box_state_from_the_ticket_file(self):
        summary = self.summary()
        self.assertEqual([entry['criterion'] for entry in summary['criteria']], self.CRITERIA)
        self.assertEqual([entry['met'] for entry in summary['criteria']], [True, False])
        self.assertEqual([entry['box'] for entry in summary['criteria']], ['x', ' '])
        self.assertEqual((summary['met'], summary['unmet']), (1, 1))

    def test_every_unmet_criterion_says_what_it_waits_on_from_the_journal(self):
        clarified = self.submit('clarify', clarify_evidence(acceptance=self.CHECKS))
        met, unmet = self.summary()['criteria']
        self.assertIsNone(met['waiting_on'])
        # The stage it stands at, and the check the clarify record restated for
        # it, by record number: read from the journal rather than asserted.
        self.assertIn('solution', unmet['waiting_on'])
        self.assertIn(self.CHECKS[1], unmet['waiting_on'])
        self.assertEqual(unmet['check'], self.CHECKS[1])
        self.assertEqual(unmet['check_record'], clarified['sequence'])

    def test_the_summary_takes_no_actor_and_writes_nothing(self):
        before = len(self.records())
        self.assertEqual(self.summary()['ticket'], self.ticket_id)
        self.assertEqual(len(self.records()), before)


class NamedConditionsTest(RunMixin, CommandTest):
    """The criterion's five conditions, and which of them the loop finds itself.

    Attempt 2 of SEEN-112, and the distinction the triage could not see: the six
    reasons in `[run] stops` are a vocabulary, while the criterion names five
    conditions. StopTest proves the vocabulary, that each reason reports its
    stage, its record and one resume command, and that none is recorded twice. It
    does not prove that a condition ends the run when it occurs, and a condition
    a session has to remember to declare is weaker evidence than one a later
    reader finds in the records: two sessions reading the same journal would
    otherwise disagree about whether the run had ended.

    So each of the five is classified here, and the classification is the loop's
    own rather than this file's. Four are detected, from the journal or from what
    verify-delivery already reads. One is declared, for one reason only: a gate
    that refuses raises and writes nothing, so there is no record for a later
    reader to find, and the declaration is then held to the vocabulary.
    """

    def clarify_draft(self, **changes):
        """A clarify draft a session has written, so the next action is the gate."""
        relative = f'.harness-drafts/{self.ticket_id}-clarify.json'
        self.write(relative, json.dumps(clarify_evidence(**changes)))
        return relative

    def decided(self, question='clarified', answer='yes', confidence=0.52):
        """One typed answer on record, with the confidence it came with.

        0.52 against a bar of 0.8 is the shape of SEEN-112's own record 20, where
        criterion_evidenced was answered no at 0.52: an answer somebody made, kept
        with its probability, and below the bar the stage applies to it.
        """
        return self.run_harness('decide', self.ticket_id, '--question', question,
                                '--answer', answer, '--confidence', str(confidence),
                                '--actor', 'claude:implementer')

    def test_each_of_the_five_conditions_is_either_detected_or_declared_exactly_once(self):
        conditions = [reason for reason in loop.stops(self.rules())
                      if reason != 'awaiting_authorisation']
        # Five conditions, and the ordinary end of a run is not one of them: it is
        # a stop that is not a failure.
        self.assertEqual(len(conditions), 5, conditions)
        self.assertEqual(sorted(conditions), sorted([*loop.DETECTED, *loop.DECLARED]),
                         'Every condition the criterion names must be one the run detects or one '
                         'a session declares, and the loop must say which')
        self.assertEqual(set(loop.DETECTED) & set(loop.DECLARED), set())
        self.assertNotIn('awaiting_authorisation', [*loop.DETECTED, *loop.DECLARED])
        # And the one that is only declared is the one with nothing to detect,
        # which the gate refusal test below is the evidence for.
        self.assertEqual(tuple(loop.DECLARED), ('gate_refused',))

    def test_a_recorded_answer_below_its_bar_stops_the_run_at_question_open(self):
        self.start()
        self.clarify_draft()
        self.assertEqual(self.named(self.ask()), 'advance')
        decision = self.decided()
        self.assertIs(decision['data']['passed'], False)
        action = self.assert_runnable(self.ask())
        self.assertEqual(
            action['kind'], 'stop',
            'A Jev question that does not clear is one of the five conditions the criterion '
            'names, and the answer on record cannot pass the gate it blocks, so offering '
            f'{action["argv"][2]} again is retrying a decision: {action["argv"]}')
        self.assertEqual(action['reason'], 'question_open')
        self.assertEqual(action['stage'], 'clarify')
        # It points at the decision record itself, which is where a reader sees
        # the probability and the bar it did not clear.
        self.assertEqual(action['record'], decision['sequence'])

    def test_the_stop_names_the_question_to_answer_again_and_is_recorded_once(self):
        self.start()
        self.clarify_draft()
        self.decided()
        action = self.ask()
        # One command, and it is the question put again: a note alone leaves the
        # answer on record below its bar, so the advance would refuse identically.
        self.assertEqual(self.named(action), 'decide')
        self.assertIn('--question', action['resume'])
        self.assertIn('clarified', action['resume'])
        self.assertTrue(action['recorded'])
        written = self.records()[-1]
        self.assertEqual(written['kind'], 'stop')
        self.assertEqual(written['data']['question'], 'clarified')
        self.assertEqual(written['data']['resume'], action['resume'])
        self.assertEqual(written['data']['record'], action['record'])
        # Asked again it reports the same halt and writes nothing.
        again = self.ask()
        self.assertFalse(again['recorded'])
        self.assertEqual(again['sequence'], written['sequence'])
        self.assertEqual(self.kinds().count('stop'), 1)

    def test_an_answer_that_clears_its_bar_is_not_a_stop(self):
        self.start()
        self.clarify_draft()
        self.decided(confidence=0.9)
        action = self.assert_runnable(self.ask())
        self.assertNotEqual(action['kind'], 'stop')
        self.assertEqual(self.named(action), 'advance')
        self.assertNotIn('stop', self.kinds())

    def test_an_answer_below_its_bar_on_a_question_this_stage_does_not_block_on_is_not_a_stop(self):
        """The stage decides which questions block, and one reader decides it.

        `risk` routes rather than blocks, so a low confidence in it is not a halt:
        which way a question reads is cli.BLOCKING's, and the loop reads that
        rather than keeping a second copy of it.
        """
        self.start()
        self.clarify_draft()
        self.decided(question='risk', answer='low', confidence=0.3)
        self.assertNotEqual(self.ask()['kind'], 'stop')
        self.assertNotIn('stop', self.kinds())

    def test_a_gate_that_refuses_writes_no_record_so_the_session_declares_the_stop(self):
        self.start()
        before = len(self.records())
        with self.assertRaisesRegex(HarnessError, 'acceptance'):
            self.submit('clarify', clarify_evidence(acceptance=[]))
        # Nothing for a later reader to find: the refusal is a raised error and an
        # unwritten record, which is why this condition is the declared one.
        self.assertEqual(len(self.records()), before)
        self.assertNotEqual(self.ask()['kind'], 'stop')
        action = self.assert_runnable(self.ask('--stop', 'gate_refused'))
        self.assertEqual(action['reason'], 'gate_refused')
        self.assertEqual(action['stage'], 'clarify')
        self.assertEqual(action['record'], before)
        # One runnable resume argv, and it is the same gate over the same draft.
        self.assertEqual(self.named(action), 'advance')
        self.assertIn(f'.harness-drafts/{self.ticket_id}-clarify.json', action['resume'])
        self.assertEqual(self.records()[-1]['data']['resume'], action['resume'])
        # And the declaration is held to the vocabulary: a reason nobody named is
        # not a stop just because a session said so.
        with self.assertRaisesRegex(HarnessError, 'stop'):
            self.ask('--stop', 'the_gate_looked_cross')
        self.assertEqual(self.kinds().count('stop'), 1)


class RedCITest(RunMixin, DeliveryWalk):
    """Red CI on the commit the receipt would attest, read and not declared.

    Attempt 2 of SEEN-112. What CI says about a commit is what verify-delivery
    already reads, so the run reads it one step earlier and stops at a named stop
    rather than at a command that refuses. Only a completed check with a failing
    conclusion is red: a pending check, a commit with no checks and a gh that
    cannot answer are each verify-delivery's own refusal to explain in its own
    words, and none of them is this stop.
    """

    def failing(self, conclusion='failure'):
        from harness import github
        github.CHECKS = lambda repository, commit: [
            dict(name='Harness tests (Python 3.12)', status='completed', conclusion=conclusion)]

    def test_red_ci_stops_the_run_before_the_receipt_and_nobody_declares_it(self):
        self.walk_to_deliver()
        self.commit_and_push()
        self.failing()
        reviewed = self.records()[-1]['sequence']
        action = self.assert_runnable(self.ask())
        self.assertEqual(
            action['kind'], 'stop',
            'Red CI is one of the five conditions the criterion names, and it is readable from '
            f'what verify-delivery already reads, so the run must not offer {action["argv"][2]} '
            'and wait for a session to declare the stop')
        self.assertEqual(action['reason'], 'ci_red')
        self.assertEqual(action['stage'], 'deliver')
        # The record it stopped on, never the stop itself.
        self.assertEqual(action['record'], reviewed)
        # The check that is red is named, and the resume is the verification that
        # writes the receipt once it is green.
        self.assertIn('Harness tests (Python 3.12)', action['why'])
        self.assertEqual(self.named(action), 'verify-delivery')
        written = self.records()[-1]
        self.assertEqual(written['kind'], 'stop')
        self.assertEqual(written['data']['record'], reviewed)
        self.assertEqual(written['data']['checks'], ['Harness tests (Python 3.12) (failure)'])
        self.assertEqual(written['data']['why'], action['why'])
        self.assertNotIn('receipt', self.kinds())
        self.ask()
        self.assertEqual(self.kinds().count('stop'), 1)

    def test_ci_that_has_not_finished_is_not_this_stop(self):
        self.walk_to_deliver()
        from harness import github
        github.CHECKS = lambda repository, commit: [
            dict(name='Harness tests (Python 3.12)', status='in_progress', conclusion=None)]
        self.assertNotEqual(self.ask()['kind'], 'stop')
        self.assertNotIn('stop', self.kinds())

    def test_a_gh_that_cannot_answer_is_not_this_stop(self):
        self.walk_to_deliver()

        def cannot(repository, commit):
            raise HarnessError('gh is not installed, so this delivery cannot be verified')

        from harness import github
        github.CHECKS = cannot
        self.assertNotEqual(self.ask()['kind'], 'stop')
        self.assertNotIn('stop', self.kinds())

    def test_a_skipped_check_is_green_and_not_red(self):
        self.walk_to_deliver()
        self.commit_and_push()
        self.failing(conclusion='skipped')
        self.assertNotEqual(self.ask()['kind'], 'stop')
        self.assertNotIn('stop', self.kinds())


class RunEvidenceTest(RunMixin, SessionEnvironment):
    """What a run says about itself: who worked each slice, on what, at what cost.

    Attempt 3 of SEEN-112, and criterion 1 as record 31 amended it. Two of the
    three things that criterion now rests on were facts of this ticket's own
    journal that nothing read: that each slice was handed to an implementer with
    a context of its own, and that each ran on the model it was routed to. Both
    were true, and both were true only as prose in a note; prose about a run is
    the run's own account of itself rather than evidence about it. So the summary
    reports them per slice from the journal and nowhere else, beside what the
    session and its subagents spent, which is `harness budget`'s figure and not a
    second reading of the same logs.
    """

    COVERAGE = '{"total": {"lines": {"total": 10, "covered": 9, "skipped": 0, "pct": 90.0}}}'

    def setUp(self):
        super().setUp()
        from harness import cost
        self.addCleanup(setattr, cost, 'LOGS', cost.LOGS)
        cost.LOGS = Path(tempfile.mkdtemp())
        self.keep_the_routes_in_shadow()
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence(slices=plan(count=2)))
        self.route = self.run_harness('route', self.ticket_id, '--actor', 'claude:implementer')

    def keep_the_routes_in_shadow(self):
        """Pinned rather than inherited, because one slice below runs off its route.

        In shadow the tdd gate reports a model mismatch and refuses nothing, which
        is exactly the window in which the summary is the only thing that would
        show one. With `[routing] shadow` off that gate refuses the slice and this
        fixture could not exist, so the flag is set here rather than read.
        """
        path = self.root / 'harness' / 'thresholds.toml'
        text = re.sub(r'(?m)^shadow = false$', 'shadow = true', path.read_text())
        self.assertIn('\nshadow = true\n', text)
        path.write_text(text)

    def routed(self, position):
        """What the route record decided for one slice, read from the record itself."""
        return self.route['data']['execution'][position - 1]

    def prove(self, model=None, agent=None):
        """One slice's RED and its GREEN, declaring what its session was asked to."""
        declaration = []
        if model is not None:
            declaration += ['--model', model]
        if agent is not None:
            declaration += ['--agent', agent]
        red = self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                               'claude:implementer', *declaration, '--', 'sh', '-c',
                               'echo expected 1, got 0; exit 1')
        green = self.run_harness('check', self.ticket_id, '--phase', 'green', '--actor',
                                 'claude:implementer', *declaration, '--', 'true')
        return red['sequence'], green['sequence']

    def walk_the_slices(self, second=None):
        """Both slices proved, then cited: the citation is where a check meets a slice."""
        proved = [self.prove(model='opus', agent='seen-implementer'),
                  self.prove(**(second if second is not None else dict(model='opus')))]
        self.write('packages/core/coverage/coverage-summary.json', self.COVERAGE)
        self.run_harness('coverage', self.ticket_id, '--actor', 'claude:implementer', '--', 'true')
        regression = self.run_harness('check', self.ticket_id, '--phase', 'regression',
                                      '--actor', 'claude:implementer', '--', 'true')
        return self.submit('tdd', dict(
            mode='code',
            slices=[dict(position=position,
                         behaviour=f'Slice {position} does its part',
                         failure_reason='expected 1, got 0', red=red, green=green)
                    for position, (red, green) in enumerate(proved, start=1)],
            regression=regression['sequence'], coverage_delta=None))

    def write_log(self, output_tokens, tool_calls=0):
        """This session's own log, of the shape the assistant writes and no other."""
        from harness import cost
        directory = cost.log_directory(self.root)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f'{self.session}.jsonl').write_text(json.dumps(dict(
            message=dict(usage=dict(output_tokens=output_tokens),
                         content=[dict(type='tool_use')] * tool_calls))) + '\n')

    def write_subagent_log(self, agent_id, agent_type, output_tokens, tool_calls=0):
        """A subagent's transcript beside the parent's, which is the only place the
        split between the two exists to read."""
        from harness import cost
        directory = cost.log_directory(self.root) / self.session / 'subagents'
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f'agent-{agent_id}.jsonl').write_text(json.dumps(dict(
            message=dict(usage=dict(output_tokens=output_tokens),
                         content=[dict(type='tool_use')] * tool_calls))) + '\n')
        (directory / f'agent-{agent_id}.meta.json').write_text(
            json.dumps(dict(agentType=agent_type)))

    def summary(self):
        return self.run_harness('run', self.ticket_id, '--summary')

    def test_each_slice_says_whether_it_was_delegated_and_to_which_agent(self):
        self.walk_the_slices()
        first, second = self.summary()['slices']
        self.assertEqual((first['position'], second['position']), (1, 2))
        self.assertTrue(first['delegated'])
        self.assertEqual(first['agent'], 'seen-implementer')
        self.assertEqual([check['phase'] for check in first['checks']], ['red', 'green'])
        self.assertEqual([check['agent'] for check in first['checks']],
                         ['seen-implementer', 'seen-implementer'])
        # Recorded in the orchestrating session's own context: neither cited check
        # declares an agent, and only the declaration could ever say so, because a
        # Claude Code subagent inherits its parent's session id.
        self.assertFalse(second['delegated'])
        self.assertIsNone(second['agent'])

    def test_a_slice_nothing_has_proved_yet_says_nobody_knows_rather_than_no(self):
        # The rule cost.py applies to tokens and sessions.py to a missing log: an
        # absence and a no must not read alike. The route is on record before the
        # first slice is worked, so that much is reported either way.
        entries = self.summary()['slices']
        self.assertEqual([entry['position'] for entry in entries], [1, 2])
        for entry in entries:
            self.assertEqual(entry['checks'], [])
            self.assertIsNone(entry['delegated'])
            self.assertIsNone(entry['agent'])
            self.assertIsNone(entry['as_routed'])
            self.assertEqual(entry['routed']['model'], self.routed(entry['position'])['model'])
            self.assertEqual(entry['routed']['effort'], self.routed(entry['position'])['effort'])

    def test_each_slice_reports_what_it_ran_on_beside_what_the_route_decided(self):
        strongest = routing.strongest(self.rules())
        self.walk_the_slices(second=dict(model='sonnet', agent='seen-implementer'))
        first, second = self.summary()['slices']
        self.assertEqual(first['declared_model'], strongest)
        self.assertEqual(first['routed']['model'], strongest)
        self.assertTrue(first['as_routed'])
        # A slice that ran on something else is visible rather than asserted. In
        # shadow the tdd gate reports this and refuses nothing, so the summary is
        # the only place it is said.
        self.assertEqual(second['declared_model'], 'sonnet')
        self.assertEqual(second['routed']['model'], strongest)
        self.assertFalse(second['as_routed'])
        self.assertEqual([check['declared_model'] for check in second['checks']],
                         ['sonnet', 'sonnet'])

    def test_the_summary_reports_the_session_and_the_subagents_spending_apart(self):
        self.write_log(1200, tool_calls=4)
        self.write_subagent_log('a', 'seen-implementer', 700, tool_calls=3)
        spending = self.summary()['spending']
        self.assertEqual(spending['output_tokens'], 1200)
        self.assertEqual(spending['tool_calls'], 4)
        # A delegated slice's cost is a different session's, told apart from this
        # one's rather than folded into it.
        self.assertEqual(spending['subagents']['output_tokens'], 700)
        self.assertEqual([entry['agent'] for entry in spending['subagents']['agents']],
                         ['seen-implementer'])
        # harness budget's own figures: one reader, so the summary and the command
        # a session runs mid-slice cannot disagree about what the slice cost.
        budget = self.run_harness('budget', self.ticket_id)
        self.assertEqual(spending,
                         {key: value for key, value in budget.items() if key != 'ticket'})

    def test_a_machine_with_no_session_log_is_null_rather_than_zero(self):
        spending = self.summary()['spending']
        self.assertIsNone(spending['output_tokens'])
        self.assertIn('null is not zero', spending['unavailable'])

    def test_the_summary_is_still_read_only_and_takes_no_actor(self):
        self.walk_the_slices()
        before = len(self.records())
        self.assertEqual(self.summary()['ticket'], self.ticket_id)
        self.assertEqual(len(self.records()), before)


class RegressionOrderTest(RunMixin, SessionEnvironment):
    """When a regression counts: after the work it covers, and never before it.

    Attempt 6, and the break the rebase onto SEEN-113 exposed. `_regression` read
    `handoff.accepted_greens`, which SEEN-113 removed along with the counting
    defect it carried, so every run that reached the tdd stage with its plan
    complete raised AttributeError instead of naming an action. What the reader
    needs back is not the greens but the record a regression has to follow, and
    the property that decides it is asserted here rather than left to the walk in
    LoopTest, which only ever records its checks in order: a regression recorded
    before the green it is supposed to cover is not this run's regression, and
    the loop asks for another one.
    """

    COVERAGE = '{"total": {"lines": {"total": 10, "covered": 9, "skipped": 0, "pct": 90.0}}}'

    def setUp(self):
        super().setUp()
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence(slices=plan(count=1)))
        self.run_harness('route', self.ticket_id, '--actor', 'claude:implementer')

    def check(self, phase, *command):
        return self.run_harness('check', self.ticket_id, '--phase', phase, '--actor',
                                'claude:implementer', '--', *(command or ('true',)))

    def prove(self):
        """The one slice of the plan, proved: a RED that fails and a GREEN that passes."""
        self.check('red', 'sh', '-c', 'echo expected 1, got 0; exit 1')
        return self.check('green')

    def measure(self):
        """The coverage the loop asks for before it asks for the regression."""
        self.write('packages/core/coverage/coverage-summary.json', self.COVERAGE)
        self.run_harness('coverage', self.ticket_id, '--actor', 'claude:implementer', '--', 'true')

    def test_the_regression_is_what_the_loop_asks_for_once_the_plan_is_proved(self):
        self.prove()
        self.measure()
        action = self.assert_runnable(self.ask())
        self.assertEqual(self.named(action), 'check')
        self.assertIn('regression', action['argv'])

    def test_a_regression_recorded_before_the_green_it_covers_does_not_count(self):
        self.check('red', 'sh', '-c', 'echo expected 1, got 0; exit 1')
        stale = self.check('regression')
        green = self.check('green')
        self.assertLess(stale['sequence'], green['sequence'])
        self.measure()
        # The suite ran over code the slice had not written yet, so it says
        # nothing about it and the loop asks for the regression again.
        action = self.assert_runnable(self.ask())
        self.assertEqual(self.named(action), 'check')
        self.assertIn('regression', action['argv'])

    def test_a_regression_recorded_after_the_green_is_the_one_the_gate_reads(self):
        self.check('red', 'sh', '-c', 'echo expected 1, got 0; exit 1')
        self.check('regression')
        self.check('green')
        self.measure()
        self.check('regression')
        # The tdd evidence is drafted next, which is the run saying the checks
        # before the gate are all in hand.
        self.assertEqual(self.named(self.assert_runnable(self.ask())), 'draft')


if __name__ == '__main__':
    unittest.main()
