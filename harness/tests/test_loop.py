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
"""

import contextlib
import io
from pathlib import Path
import unittest

from harness import cli, loop, thresholds
from harness.errors import HarnessError
from harness.tests import helpers
from harness.tests.test_delivery import DeliveryWalk
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence

PROJECT = Path(__file__).resolve().parents[2]
# Every action's argv starts here: the entry point a session already runs.
ENTRY = ['python3', 'harness/run.py']
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


if __name__ == '__main__':
    unittest.main()
