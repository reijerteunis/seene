"""The route: which model and which effort implement each slice.

Rules first, and a rule is never Jev's to answer. A slice that changes an agent
action, touches billing or the policy gate, does money arithmetic in
packages/core, carries a migration or an RLS policy, or touches credentials goes
to the strongest model at high effort with no request made at all, which is what
these tests assert against a stub that records every request it receives.

Everything else is one request carrying both questions once per unruled slice,
keyed by position. No test here calls the API: a test that could reach Jev would
be a test that spends money and gives different answers on different days.
"""

import unittest
from pathlib import Path

from harness import jev
from harness.errors import HarnessError
from harness.tests.test_decisions import noul, score
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence

PROJECT = Path(__file__).resolve().parents[2]

# Jev answers a score by level index, and the levels are the question's options
# in order: haiku, sonnet, opus and low, medium, high.
SONNET = (0.1, 0.7, 0.2)
MEDIUM = (0.2, 0.6, 0.2)

MONEY = dict(name='Fee expectations', points=2,
             files=['packages/core/src/fees.ts', 'packages/core/src/fees.test.ts'],
             red='No fee expectation is computed for an order line')
MIGRATION = dict(name='The findings table', points=1,
                 files=['supabase/migrations/0007_findings.sql'],
                 red='The table does not exist')
CREDENTIALS = dict(name='The connection secret', points=1,
                   files=['packages/connectors/src/credentials.ts'],
                   red='A credential is read from the database')
PLAIN = dict(name='The status line', points=1,
             files=['apps/web/src/status.tsx'],
             red='The status line shows nothing')
SECOND_PLAIN = dict(name='The empty state', points=1,
                    files=['apps/web/src/empty.tsx'],
                    red='The empty state is not rendered')


def route_stub(model=SONNET, effort=MEDIUM, billing=0.1, must_fix=0.05, leave_out=()):
    """A transport answering the two route questions, keyed by slice position.

    `leave_out` names keys the reply drops, which is how a well-formed answer
    that left a question out is told from a transport that failed: the first is
    an absence for that slice alone and the second is an absence for all of them.
    """
    sent = []

    def transport(endpoint, payload, credential, timeout):
        sent.append(dict(endpoint=endpoint, payload=payload))
        replies = {}
        for key, question in payload['questions'].items():
            name = key.partition('#')[0]
            if key in leave_out:
                continue
            if name == 'implementation_model':
                replies[key] = score(list(model))
            elif name == 'implementation_effort':
                replies[key] = score(list(effort))
            elif name == 'touches_billing_or_policy_gate':
                replies[key] = noul(billing)
            elif name == 'must_fix':
                # A stage gate refuses a must_fix that clears its bar, so a stub
                # answering every noul at 0.9 cannot walk a ticket to delivered.
                replies[key] = noul(must_fix)
            elif question['type'] == 'score':
                replies[key] = score([0.2, 0.7, 0.1])
            else:
                replies[key] = noul(0.9)
        return {'model': 'jev-1.13.0', 'answers': replies,
                'usage': {'input_tokens': 600, 'output_tokens': 30}}

    transport.sent = sent
    return transport


class RouteTest(CommandTest):
    """A ticket worked to the tdd stage, which is where the route is decided."""

    def setUp(self):
        super().setUp()
        self.write('.env.local', 'JEV_API_KEY=stub-credential\n')
        self.use(route_stub())
        self.start()

    def use(self, transport):
        self.transport = transport
        jev.TRANSPORT = transport
        return transport

    def reach_tdd(self, slices, clarify=None, **solution):
        """Both planning gates passed, with the stage requests forgotten.

        The gates ask Jev too, so what the stub recorded on the way here would
        otherwise read as a request the route made.
        """
        self.submit('clarify', clarify or clarify_evidence())
        self.submit('solution', solution_evidence(slices=slices, **solution))
        del self.transport.sent[:]

    def route(self, actor='claude:implementer'):
        return self.run_harness('route', self.ticket_id, '--actor', actor)

    def execution(self, record):
        return record['data']['execution']


class RulesTest(RouteTest):
    """What no model is asked about, and why each one is a rule."""

    def test_a_money_slice_is_routed_by_rule_and_jev_is_not_asked(self):
        self.reach_tdd([MONEY])
        record = self.route()
        entry = self.execution(record)[0]
        self.assertEqual(entry['model'], 'opus')
        self.assertEqual(entry['effort'], 'high')
        self.assertEqual(entry['source'], 'rule')
        self.assertEqual(entry['rule'], 'money')
        self.assertEqual(self.transport.sent, [])

    def test_a_migration_slice_is_routed_by_rule(self):
        self.reach_tdd([MIGRATION])
        entry = self.execution(self.route())[0]
        self.assertEqual((entry['source'], entry['rule']), ('rule', 'migration'))
        self.assertEqual(self.transport.sent, [])

    def test_a_credentials_slice_is_routed_by_rule(self):
        self.reach_tdd([CREDENTIALS])
        entry = self.execution(self.route())[0]
        self.assertEqual((entry['source'], entry['rule']), ('rule', 'credentials'))
        self.assertEqual(self.transport.sent, [])

    def test_an_rls_policy_is_the_migration_rule(self):
        self.reach_tdd([dict(PLAIN, files=['supabase/policies/rls_findings.sql'])])
        entry = self.execution(self.route())[0]
        self.assertEqual(entry['source'], 'rule')
        self.assertEqual(self.transport.sent, [])

    def test_a_ticket_that_changes_an_agent_action_routes_every_slice_by_rule(self):
        # The declaration the solution gate demands of such a ticket, so the
        # fixture fails on the route and never on the gate before it.
        self.reach_tdd([PLAIN, SECOND_PLAIN],
                       clarify=clarify_evidence(changes_agent_action=True),
                       policy_gate_action=dict(reversibility='reversible',
                                               action_type='reply_message',
                                               euro_impact_estimator='none: no money moves'))
        entries = self.execution(self.route())
        self.assertEqual([entry['rule'] for entry in entries],
                         ['agent_action', 'agent_action'])
        self.assertEqual(self.transport.sent, [])

    def test_a_ticket_that_touches_billing_routes_every_slice_by_rule(self):
        self.use(route_stub(billing=0.9))
        self.reach_tdd([PLAIN])
        entry = self.execution(self.route())[0]
        self.assertEqual((entry['source'], entry['rule']), ('rule', 'billing'))
        self.assertEqual(self.transport.sent, [])

    def test_a_plan_named_migrations_routes_every_slice_by_rule(self):
        self.reach_tdd([PLAIN], migrations=['0007_findings.sql'])
        entry = self.execution(self.route())[0]
        self.assertEqual((entry['source'], entry['rule']), ('rule', 'migration'))
        self.assertEqual(self.transport.sent, [])

    def test_only_the_unruled_slice_reaches_the_request(self):
        self.reach_tdd([MONEY, PLAIN])
        record = self.route()
        ruled, asked = self.execution(record)
        self.assertEqual(ruled['source'], 'rule')
        self.assertEqual(asked['source'], 'jev')
        self.assertEqual(len(self.transport.sent), 1)
        keys = sorted(self.transport.sent[0]['payload']['questions'])
        self.assertEqual(keys, ['implementation_effort#2', 'implementation_model#2'])


class JevTest(RouteTest):
    """What the model is asked, and what is done with what comes back."""

    def test_an_unruled_slice_is_routed_by_jev_with_its_probabilities(self):
        self.reach_tdd([PLAIN])
        entry = self.execution(self.route())[0]
        self.assertEqual(entry['source'], 'jev')
        self.assertEqual(entry['model'], 'sonnet')
        self.assertEqual(entry['effort'], 'medium')
        self.assertEqual(entry['model_probability'], 0.7)
        self.assertEqual(entry['effort_probability'], 0.6)
        self.assertIsNone(entry['rule'])

    def test_one_request_carries_every_unruled_slice_keyed_by_position(self):
        self.reach_tdd([PLAIN, SECOND_PLAIN])
        self.route()
        self.assertEqual(len(self.transport.sent), 1)
        keys = sorted(self.transport.sent[0]['payload']['questions'])
        self.assertEqual(keys, ['implementation_effort#1', 'implementation_effort#2',
                                'implementation_model#1', 'implementation_model#2'])

    def test_the_question_carries_the_slice_it_is_about(self):
        self.reach_tdd([PLAIN])
        self.route()
        asked = self.transport.sent[0]['payload']['questions']['implementation_model#1']
        self.assertIn('The status line', asked['instructions'])
        self.assertIn('apps/web/src/status.tsx', asked['instructions'])
        self.assertIn(PLAIN['red'], asked['instructions'])

    def test_the_state_carries_what_the_ticket_already_settled(self):
        self.reach_tdd([PLAIN])
        self.route()
        state = self.transport.sent[0]['payload']['state']
        self.assertEqual(state['stage'], 'tdd')
        self.assertEqual(state['risk'], 'medium')
        self.assertEqual(state['returns'], 0)
        self.assertIn('approach', state['solution'])

    def test_a_slice_the_reply_left_out_goes_to_the_strongest_as_an_absence(self):
        self.use(route_stub(leave_out=('implementation_model#1',)))
        self.reach_tdd([PLAIN])
        entry = self.execution(self.route())[0]
        self.assertEqual(entry['source'], 'unavailable')
        self.assertEqual((entry['model'], entry['effort']), ('opus', 'high'))
        self.assertIn('implementation_model#1', entry['reason'])

    def test_no_credential_routes_every_slice_to_the_strongest(self):
        self.reach_tdd([PLAIN])
        (self.root / '.env.local').unlink()
        jev.TRANSPORT = None
        entry = self.execution(self.route())[0]
        self.assertEqual(entry['source'], 'unavailable')
        self.assertEqual((entry['model'], entry['effort']), ('opus', 'high'))
        self.assertIn('credential', entry['reason'])

    def test_a_transport_that_failed_is_an_absence_and_not_a_refusal(self):
        def broken(endpoint, payload, credential, timeout):
            raise OSError('the network is not here')

        self.reach_tdd([PLAIN])
        jev.TRANSPORT = broken
        record = self.route()
        self.assertEqual(self.execution(record)[0]['source'], 'unavailable')
        self.assertFalse(record['data']['jev']['asked'])


class RecordTest(RouteTest):
    """The record itself: where it may be written and what it names."""

    def test_the_record_names_the_solution_advance_it_routes(self):
        self.reach_tdd([PLAIN])
        record = self.route()
        self.assertEqual(record['kind'], 'route')
        self.assertEqual(record['stage'], 'tdd')
        solution = [item for item in self.records()
                    if item['kind'] == 'advance' and item['data']['from_stage'] == 'solution']
        self.assertEqual(record['data']['solution'], solution[-1]['sequence'])

    def test_the_record_carries_one_entry_per_planned_slice_in_order(self):
        self.reach_tdd([MONEY, PLAIN, SECOND_PLAIN])
        entries = self.execution(self.route())
        self.assertEqual([entry['position'] for entry in entries], [1, 2, 3])
        self.assertEqual([entry['name'] for entry in entries],
                         [MONEY['name'], PLAIN['name'], SECOND_PLAIN['name']])
        self.assertEqual(entries[0]['points'], MONEY['points'])
        self.assertEqual(entries[0]['files'], MONEY['files'])

    def test_the_record_carries_the_shadow_flag_it_was_written_under(self):
        self.reach_tdd([PLAIN])
        self.assertTrue(self.route()['data']['shadow'])

    def test_a_route_before_the_plan_is_refused(self):
        self.submit('clarify', clarify_evidence())
        with self.assertRaisesRegex(HarnessError, 'tdd'):
            self.route()

    def test_a_route_after_the_tdd_stage_is_refused(self):
        self.reach_tdd([PLAIN])
        self.run_harness('return', self.ticket_id, '--to', 'clarify',
                         '--reason', 'The plan was wrong', '--actor', 'claude:implementer')
        with self.assertRaisesRegex(HarnessError, 'tdd'):
            self.route()

    def test_a_non_code_ticket_has_no_slices_to_route(self):
        self.submit('clarify', clarify_evidence())
        self.submit('solution', dict(mode='non-code',
                                     approach='Register the developer account.',
                                     changes=['docs/tickets/SEEN-001: the outcome'],
                                     migrations=[],
                                     alternatives=['Waiting, rejected because the keys gate the work'],
                                     risks=['The registration is refused; mitigated by re-filing'],
                                     rollback='Nothing is built, so nothing is undone.',
                                     new_dependencies=[],
                                     tenant_tables=['none'],
                                     buyer_pii='none',
                                     policy_gate_action=None))
        with self.assertRaisesRegex(HarnessError, 'slice'):
            self.route()


class SliceBoundaryTest(RouteTest):
    """What the session that picks up the next slice is told to run it on."""

    def pack(self):
        self.run_harness('handoff', self.ticket_id, '--actor', 'claude:implementer')
        return (self.root / '.harness-drafts' / f'{self.ticket_id}-handoff.md').read_text()

    def test_the_pack_names_the_model_and_the_effort_of_the_slice_in_hand(self):
        self.reach_tdd([PLAIN, SECOND_PLAIN])
        self.route()
        text = self.pack()
        self.assertIn('sonnet', text)
        self.assertIn('medium', text)

    def test_the_pack_names_the_rule_when_a_rule_decided_it(self):
        self.reach_tdd([MONEY])
        self.route()
        self.assertIn('rule', self.pack())

    def test_a_pack_written_before_the_route_says_the_route_is_not_decided(self):
        self.reach_tdd([PLAIN])
        self.assertIn('No route', self.pack())


class GateTest(RouteTest):
    """A check recorded under a model the route did not choose.

    Refused only with shadow off, because in shadow every slice still runs on
    whatever model the session is and a gate that refused would be the change
    the shadow window exists to hold back.
    """

    def set_shadow(self, on):
        """The one line in the project's own thresholds, and only that line.

        Written precisely because `triage_shadow = true` ends in the same five
        words: a looser replacement would turn off the review triage's shadow
        as well and the test would be about two things.
        """
        path = self.root / 'harness' / 'thresholds.toml'
        text = path.read_text()
        wanted = f'\nshadow = {"true" if on else "false"}\n'
        for value in ('\nshadow = true\n', '\nshadow = false\n'):
            if value in text:
                path.write_text(text.replace(value, wanted))
                return
        raise AssertionError('no [routing] shadow line to set')

    def run_check(self, phase, exit_code=0, model=None):
        """A check, recorded under a model, which is what a session log gives.

        The tests have no session log, so what would be read from one is
        substituted here: it is the value that reaches the record either way.
        Declares an agent on every call: this class is about the model
        comparison alone, and SEEN-111's own gate, `_require_a_context_of_its_
        own`, is a separate refusal that these fixtures are not about.
        """
        from harness import sessions
        original = sessions.model
        sessions.model = lambda root, identity=None: model
        try:
            return self.run_harness('check', self.ticket_id, '--phase', phase,
                                    '--actor', 'claude:implementer', '--agent',
                                    'seen-implementer', '--', 'sh', '-c', f'exit {exit_code}')
        finally:
            sessions.model = original

    def record_coverage(self, delta=0.0, attempt=1):
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

    def prove(self, model=None):
        """One slice proved red then green, both recorded under one model."""
        red = self.run_check('red', exit_code=1, model=model)
        green = self.run_check('green', model=model)
        regression = self.run_check('regression', model=model)
        self.record_coverage()
        return dict(mode='code', regression=regression['sequence'], coverage_delta=0.0,
                    slices=[dict(position=1,
                                 behaviour='The status line shows the stage',
                                 failure_reason='AssertionError: the status line is empty',
                                 red=red['sequence'], green=green['sequence'])])

    def test_a_check_records_the_model_it_ran_under(self):
        self.reach_tdd([PLAIN])
        record = self.run_check('green', model='claude-opus-5')
        self.assertEqual(record['data']['model'], 'claude-opus-5')

    def test_a_check_with_no_session_log_records_no_model(self):
        self.reach_tdd([PLAIN])
        self.assertIsNone(self.run_check('green')['data']['model'])

    def test_a_green_under_another_model_is_refused_naming_both(self):
        self.use(route_stub(model=(0.1, 0.7, 0.2)))
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        evidence = self.prove(model='claude-opus-5')
        with self.assertRaises(HarnessError) as raised:
            self.submit('tdd', evidence)
        message = str(raised.exception)
        self.assertIn('sonnet', message)
        self.assertIn('claude-opus-5', message)

    def test_the_routed_model_advances(self):
        self.use(route_stub(model=(0.1, 0.2, 0.7)))
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        record = self.submit('tdd', self.prove(model='claude-opus-5'))
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_in_shadow_the_same_mismatch_advances(self):
        self.reach_tdd([PLAIN])
        self.route()
        record = self.submit('tdd', self.prove(model='claude-opus-5'))
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_a_check_that_names_no_model_is_not_refused(self):
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        record = self.submit('tdd', self.prove(model=None))
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_an_unrouted_ticket_is_not_refused(self):
        self.reach_tdd([PLAIN])
        self.set_shadow(False)
        record = self.submit('tdd', self.prove(model='claude-haiku-4-5-20251001'))
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_a_tier_whose_model_id_is_unknown_is_not_refused(self):
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        path = self.root / 'harness' / 'thresholds.toml'
        path.write_text(path.read_text().replace('sonnet = "claude-sonnet-5"', 'sonnet = ""'))
        record = self.submit('tdd', self.prove(model='claude-opus-5'))
        self.assertEqual(record['data']['to_stage'], 'review')


class ImplementerCopyTest(RouteTest):
    """The agent the slice is worked by, and the keys its copies carry.

    They were generated per slice once, on the reasoning that the file was the
    only place a routed effort could go. That made a generated file depend on
    the state of a ticket, which was wrong on a detached HEAD, after a replan,
    the moment a green landed and after the receipt, and is why this ticket
    could not merge; record 121 removed it and record 130 amended criterion 3 to
    say the effort is recorded rather than applied. What is left here is that
    both copies exist and carry the keys each assistant reads. That the values
    never vary is FixedCopiesTest, and this docstring says so because F5 of the
    ninth review found the abandoned design still documented as current in the
    tests that were about it.
    """

    def setUp(self):
        super().setUp()
        for name in ('seen-scout', 'seen-reviewer', 'seen-implementer'):
            self.write(f'harness/agents/{name}.md', f'# {name}\n\nStand-in body.\n')

    def frontmatter(self):
        self.run_harness('sync')
        return (self.root / '.claude/agents/seen-implementer.md').read_text().split('---\n')[1]

    def codex(self):
        import tomllib
        self.run_harness('sync')
        return tomllib.loads(
            (self.root / '.codex/agents/seen-implementer.toml').read_text())

    def test_both_questions_are_asked_by_the_route_and_by_no_stage(self):
        for name in ('implementation_model', 'implementation_effort'):
            self.assertIsNone(jev.QUESTIONS[name]['stage'])
            self.assertNotIn(name, jev.questions_for('solution'))
            self.assertNotIn(name, jev.questions_for('tdd'))

    def test_the_options_are_the_tiers_and_the_efforts_in_order(self):
        self.assertEqual(jev.QUESTIONS['implementation_model']['options'],
                         ('haiku', 'sonnet', 'opus'))
        self.assertEqual(jev.QUESTIONS['implementation_effort']['options'],
                         ('low', 'medium', 'high'))

    def test_each_option_carries_a_criterion(self):
        for name in ('implementation_model', 'implementation_effort'):
            question = jev.QUESTIONS[name]
            self.assertEqual(len(question['criteria']), len(question['options']))


class DamagedJournalTest(CommandTest):
    """What the implementer's copies do when the journal cannot be read.

    doctor reports a broken chain and a stray file beside the records. It
    regenerates the agent copies to compare them, so a generator that raised on
    a damaged journal would take the report down with it and hand the person a
    traceback where the problem list belongs.
    """

    def test_doctor_still_reports_the_broken_chain(self):
        from harness import doctor as doctoring
        from harness.repository import Repository
        self.start()
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        (folder / 'notes.txt').write_text('a stray file\n')
        problems = doctoring.report(Repository(self.root), {})['problems']
        self.assertTrue(any('notes.txt' in problem for problem in problems), problems)


class StalePlanTest(RouteTest):
    """A route is read only for the plan it routed.

    The record names the solution advance it routes, and the amendment to
    criterion 1 is that the name is used rather than only stored. Matching a
    slice by position alone survives a return to solution: the plan changes,
    nobody routes it again, and the pack hands the next session a model chosen
    for a slice that no longer exists.
    """

    def replan(self, slices):
        """Back to solution, a different plan accepted, and no new route."""
        self.run_harness('return', self.ticket_id, '--to', 'solution',
                         '--reason', 'The plan was wrong', '--actor', 'claude:implementer')
        self.submit('solution', solution_evidence(slices=slices))

    def test_a_route_from_a_replaced_plan_is_not_read(self):
        from harness import journal, routing
        self.reach_tdd([PLAIN])
        self.route()
        self.replan([MONEY, SECOND_PLAIN])
        records = journal.read(self.root / 'docs' / 'harness' / 'history' / self.ticket_id)
        self.assertIsNone(routing.for_slice(records, 1))

    def test_the_pack_says_the_new_plan_has_no_route_yet(self):
        self.reach_tdd([PLAIN])
        self.route()
        self.replan([MONEY, SECOND_PLAIN])
        self.run_harness('handoff', self.ticket_id, '--actor', 'claude:implementer')
        pack = (self.root / '.harness-drafts' / f'{self.ticket_id}-handoff.md').read_text()
        self.assertIn('No route', pack)

    def test_routing_the_new_plan_again_is_read(self):
        from harness import journal, routing
        self.reach_tdd([PLAIN])
        self.route()
        self.replan([MONEY, SECOND_PLAIN])
        self.route()
        records = journal.read(self.root / 'docs' / 'harness' / 'history' / self.ticket_id)
        entry = routing.for_slice(records, 1)
        self.assertEqual((entry['source'], entry['rule']), ('rule', 'money'))

    def task(self, position=1):
        return self.route()['data']['execution'][position - 1]['implementer_task']

    def test_the_entry_carries_a_task_naming_the_model_and_the_effort(self):
        self.use(route_stub(model=(0.1, 0.7, 0.2), effort=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        task = self.task()
        self.assertIn('sonnet', task)
        self.assertIn('low', task)
        self.assertIn('seen-implementer', task)

    def test_the_task_names_the_slice_and_what_its_red_must_demonstrate(self):
        self.reach_tdd([PLAIN])
        task = self.task()
        self.assertIn(PLAIN['name'], task)
        self.assertIn(PLAIN['red'], task)
        self.assertIn('apps/web/src/status.tsx', task)

    def test_the_task_says_how_each_assistant_is_given_the_model(self):
        self.reach_tdd([PLAIN])
        task = self.task()
        self.assertIn('Claude Code', task)
        self.assertIn('Codex', task)

    def test_a_rule_routed_slice_says_which_rule_sent_it_there(self):
        self.reach_tdd([MONEY])
        self.assertIn('money', self.task())


class DeclaredModelTest(GateTest):
    """What a subagent can say about itself, because the log cannot say it.

    A Claude Code subagent inherits CLAUDE_CODE_SESSION_ID, so a check it runs
    resolves to its parent's transcript and records the parent's model. F1 of
    this ticket's second review. A declaration is a disclosure and not a proof,
    which is the position SEEN-105 already took for the reviewer's session id.
    """

    def declared_check(self, phase, exit_code=0, model=None, declared=None):
        """Declares an agent on every call: this class is about `--model`, and
        SEEN-111's separate context-of-its-own refusal is not what these
        fixtures test.
        """
        from harness import sessions
        original = sessions.model
        sessions.model = lambda root, identity=None: model
        try:
            arguments = ['check', self.ticket_id, '--phase', phase,
                         '--actor', 'claude:implementer', '--agent', 'seen-implementer']
            if declared is not None:
                arguments += ['--model', declared]
            return self.run_harness(*arguments, '--', 'sh', '-c', f'exit {exit_code}')
        finally:
            sessions.model = original

    def test_a_check_records_what_was_declared_beside_what_was_observed(self):
        self.reach_tdd([PLAIN])
        record = self.declared_check('green', model='claude-opus-5', declared='haiku')
        self.assertEqual(record['data']['model'], 'claude-opus-5')
        self.assertEqual(record['data']['model_declared'], 'haiku')

    def test_a_check_that_declares_nothing_says_so(self):
        self.reach_tdd([PLAIN])
        self.assertIsNone(
            self.declared_check('green', model='claude-opus-5')['data']['model_declared'])

    def test_an_unknown_tier_is_refused_rather_than_recorded(self):
        self.reach_tdd([PLAIN])
        with self.assertRaisesRegex(HarnessError, 'haiku'):
            self.declared_check('green', declared='gpt-4')

    def prove_declared(self, model=None, declared=None):
        red = self.declared_check('red', exit_code=1, model=model, declared=declared)
        green = self.declared_check('green', model=model, declared=declared)
        regression = self.declared_check('regression', model=model, declared=declared)
        self.record_coverage()
        return dict(mode='code', regression=regression['sequence'], coverage_delta=0.0,
                    slices=[dict(position=1,
                                 behaviour='The status line shows the stage',
                                 failure_reason='AssertionError: the status line is empty',
                                 red=red['sequence'], green=green['sequence'])])

    def test_the_declaration_is_what_the_gate_compares(self):
        """The subagent ran on the routed model; the log says the parent's."""
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        record = self.submit('tdd', self.prove_declared(model='claude-opus-5',
                                                        declared='haiku'))
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_a_declaration_that_disagrees_with_the_route_is_refused(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        with self.assertRaises(HarnessError) as raised:
            self.submit('tdd', self.prove_declared(model='claude-haiku-4-5-20251001',
                                                   declared='opus'))
        message = str(raised.exception)
        self.assertIn('haiku', message)
        self.assertIn('opus', message)
        self.assertIn('declared', message)


class ContextOfItsOwnTest(RouteTest):
    """A slice held to a context of its own, and not only to its route's model.

    SEEN-111: a slice recorded in the orchestrating session's own context,
    with neither its RED nor its GREEN declaring an agent, is refused once
    `[routing] shadow` is off. One of the two declaring an agent is a
    delegated slice and is not refused.

    Extends `RouteTest` and not `GateTest`: `GateTest` carries its own tests
    of `_require_the_routed_model`, proved with no `--agent` at all, and
    inheriting them here would run every one of them again under this
    ticket's new refusal, which is a second thing under test and not this
    one. `set_shadow` and `record_coverage` are copied rather than shared for
    the same reason `GateTest` itself is not reused.
    """

    def set_shadow(self, on):
        """The one line in the project's own thresholds, and only that line.

        Written precisely because `triage_shadow = true` ends in the same five
        words: a looser replacement would turn off the review triage's shadow
        as well and the test would be about two things.
        """
        path = self.root / 'harness' / 'thresholds.toml'
        text = path.read_text()
        wanted = f'\nshadow = {"true" if on else "false"}\n'
        for value in ('\nshadow = true\n', '\nshadow = false\n'):
            if value in text:
                path.write_text(text.replace(value, wanted))
                return
        raise AssertionError('no [routing] shadow line to set')

    def record_coverage(self, delta=0.0, attempt=1):
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

    def declared_check(self, phase, exit_code=0, model=None, declared=None, agent=None):
        from harness import sessions
        original = sessions.model
        sessions.model = lambda root, identity=None: model
        try:
            arguments = ['check', self.ticket_id, '--phase', phase,
                         '--actor', 'claude:implementer']
            if declared is not None:
                arguments += ['--model', declared]
            if agent is not None:
                arguments += ['--agent', agent]
            return self.run_harness(*arguments, '--', 'sh', '-c', f'exit {exit_code}')
        finally:
            sessions.model = original

    def prove_context(self, model='claude-opus-5', declared='opus', red_agent=None,
                      green_agent=None):
        red = self.declared_check('red', exit_code=1, model=model, declared=declared,
                                  agent=red_agent)
        green = self.declared_check('green', model=model, declared=declared, agent=green_agent)
        regression = self.declared_check('regression', model=model, declared=declared)
        self.record_coverage()
        evidence = dict(mode='code', regression=regression['sequence'], coverage_delta=0.0,
                        slices=[dict(position=1,
                                     behaviour='The status line shows the stage',
                                     failure_reason='AssertionError: the status line is empty',
                                     red=red['sequence'], green=green['sequence'])])
        return evidence, red, green

    def test_neither_check_declaring_an_agent_is_refused_without_a_context_of_its_own(self):
        self.use(route_stub(model=(0.1, 0.2, 0.7)))
        self.reach_tdd([PLAIN])
        route_record = self.route()
        self.set_shadow(False)
        evidence, red, green = self.prove_context()
        with self.assertRaises(HarnessError) as raised:
            self.submit('tdd', evidence)
        message = str(raised.exception)
        self.assertIn('Slice 1', message)
        self.assertIn(str(route_record['sequence']), message)
        self.assertIn(str(red['sequence']), message)
        self.assertIn(str(green['sequence']), message)

    def test_the_red_declaring_an_agent_is_a_delegated_slice_and_advances(self):
        self.use(route_stub(model=(0.1, 0.2, 0.7)))
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        evidence, red, green = self.prove_context(red_agent='seen-implementer')
        record = self.submit('tdd', evidence)
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_the_green_declaring_an_agent_is_a_delegated_slice_and_advances(self):
        self.use(route_stub(model=(0.1, 0.2, 0.7)))
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        evidence, red, green = self.prove_context(green_agent='seen-implementer')
        record = self.submit('tdd', evidence)
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_in_shadow_neither_declaring_an_agent_is_not_refused(self):
        self.reach_tdd([PLAIN])
        self.route()
        evidence, red, green = self.prove_context()
        record = self.submit('tdd', evidence)
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_an_unrouted_ticket_is_not_refused_for_lacking_a_context_of_its_own(self):
        self.reach_tdd([PLAIN])
        self.set_shadow(False)
        evidence, red, green = self.prove_context()
        record = self.submit('tdd', evidence)
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_an_unknown_agent_is_refused_rather_than_recorded(self):
        self.reach_tdd([PLAIN])
        with self.assertRaisesRegex(HarnessError, 'seen-scout'):
            self.declared_check('green', agent='not-an-agent')


class DeclarationIsInstructedTest(RouteTest):
    """The declaration is only worth having if something asks for it.

    F1 of the third review: --model existed in the parser and in a fixture, and
    in nothing a subagent reads, so the declaration the amended criterion 3
    rests on was never made and the gate fell back to the log, which reports the
    parent's model. The gate's half landed and the instruction half did not.
    """

    def test_the_spawn_text_gives_the_check_command_with_the_tier_in_it(self):
        self.use(route_stub(model=(0.1, 0.7, 0.2)))
        self.reach_tdd([PLAIN])
        task = self.route()['data']['execution'][0]['implementer_task']
        self.assertIn('--model sonnet', task)

    def test_a_rule_routed_slice_gets_its_own_tier_in_the_command(self):
        self.reach_tdd([MONEY])
        self.assertIn('--model opus',
                      self.route()['data']['execution'][0]['implementer_task'])

    def test_the_implementer_s_own_instructions_name_the_flag(self):
        from harness import agents
        source = (PROJECT / agents.source_of(agents.IMPLEMENTER)).read_text()
        self.assertIn('--model', source)

    def test_the_generated_copies_carry_the_instruction_too(self):
        from harness import agents
        for relative in (agents.claude_copy(agents.IMPLEMENTER),
                         agents.codex_copy(agents.IMPLEMENTER)):
            self.assertIn('--model', (PROJECT / relative).read_text(),
                          f'{relative} does not tell the implementer to declare its model')


class DirectoryNamedSliceTest(RouteTest):
    """A rule a plan's wording cannot dodge.

    F6 of the third review: the patterns were fnmatch globs under a directory,
    so a slice whose files entry named `packages/core` rather than a file in it
    went to Jev like any other and could come back haiku at low effort for fee
    expectations, which the ground rules call the most expensive thing here to
    get wrong.
    """

    def rule_for(self, files):
        self.reach_tdd([dict(PLAIN, files=files)])
        return self.route()['data']['execution'][0]

    def test_a_slice_naming_the_core_package_is_the_money_rule(self):
        self.assertEqual(self.rule_for(['packages/core'])['rule'], 'money')

    def test_a_slice_naming_the_source_directory_is_too(self):
        self.assertEqual(self.rule_for(['packages/core/src'])['rule'], 'money')

    def test_a_slice_naming_a_migrations_directory_is_the_migration_rule(self):
        self.assertEqual(self.rule_for(['supabase/migrations'])['rule'], 'migration')

    def test_a_neighbour_of_the_core_package_is_not_the_money_rule(self):
        """`packages/core-utils` is a different package, not money arithmetic."""
        entry = self.rule_for(['packages/core-utils/src/format.ts'])
        self.assertEqual(entry['source'], 'jev')


class SlicePositionTest(GateTest):
    """Which route a proved slice is held to.

    F1 of the fourth review: the gate read the slice's index in the tdd record
    and a route is keyed by plan position, so a rework attempt proving one slice
    read plan slice 1's route. The tdd record names the position now, and an
    older record that cannot is not refused on a mapping it never had.
    """

    def record_mutation(self, score=80.0):
        """The measurement the tdd gate asks of a slice naming packages/core/src, SEEN-116.

        Written beside the coverage record, which is where the gate reads it
        from. The plan's money slice names fees.ts, so this is what lets the
        advance these tests expect reach the route comparison they are about.
        """
        from harness import journal
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        records = journal.read(folder)
        return journal.append(folder, records, kind='check', stage='tdd', attempt=1,
                              actor='claude:implementer', head=self.git('rev-parse', 'HEAD'),
                              ticket=self.ticket_id,
                              data=dict(command=['pnpm', 'mutation'], phase='mutation',
                                        exit_code=0, duration_ms=1, output='',
                                        output_sha256='0' * 64, output_truncated=False,
                                        before='a', after='b', score=score, floor=70,
                                        files=['packages/core/src/fees.ts'], killed=8,
                                        survived=2, mutants=10, reason=None))

    def plan(self):
        return [dict(PLAIN, name='The status line'), dict(MONEY, name='Fee expectations')]

    def rework_of(self, position, declared, model='claude-opus-5'):
        """One slice proved on its own, the way a rework attempt proves one."""
        red = self.declared_check('red', exit_code=1, model=model, declared=declared)
        green = self.declared_check('green', model=model, declared=declared)
        regression = self.declared_check('regression', model=model, declared=declared)
        self.record_coverage()
        self.record_mutation()
        return dict(mode='code', regression=regression['sequence'], coverage_delta=0.0,
                    slices=[dict(position=position,
                                 behaviour='The reworked behaviour',
                                 failure_reason='AssertionError: the reworked behaviour is '
                                                'absent',
                                 red=red['sequence'], green=green['sequence'])])

    def declared_check(self, phase, exit_code=0, model=None, declared=None):
        """Declares an agent on every call, for the same reason `GateTest.run_check` does:
        this class is about which route a slice's position is held to, not about
        SEEN-111's separate context-of-its-own refusal.
        """
        from harness import sessions
        original = sessions.model
        sessions.model = lambda root, identity=None: model
        try:
            arguments = ['check', self.ticket_id, '--phase', phase,
                         '--actor', 'claude:implementer', '--agent', 'seen-implementer']
            if declared is not None:
                arguments += ['--model', declared]
            return self.run_harness(*arguments, '--', 'sh', '-c', f'exit {exit_code}')
        finally:
            sessions.model = original

    def test_a_rework_of_slice_two_is_held_to_slice_two_s_route(self):
        """Slice 1 is Jev's haiku, slice 2 is the money rule's opus."""
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd(self.plan())
        self.route()
        self.set_shadow(False)
        record = self.submit('tdd', self.rework_of(2, declared='opus'))
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_a_rework_declaring_the_wrong_slice_s_model_is_refused(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd(self.plan())
        self.route()
        self.set_shadow(False)
        with self.assertRaises(HarnessError) as raised:
            self.submit('tdd', self.rework_of(2, declared='haiku'))
        self.assertIn('Slice 2', str(raised.exception))

    def test_a_declared_absence_is_held_to_the_strictest_route_in_the_plan(self):
        """A round that belongs to no single slice answers to every one of them.

        This asserted that an omitted field was not refused until F2 of the
        fifth review found that omitting it was a way past the refusal nobody
        could tell from a record written before the field existed. It then
        asserted that the declared absence was held to no route at all, and the
        same review found that too: with the plan's file union granted for its
        scope, a null declaration bought the evidence and paid nothing for the
        route, so it was cheaper than the truth. Slice 2 here is the money rule's
        opus, and a rework round worked on haiku may have touched it.
        """
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd(self.plan())
        self.route()
        self.set_shadow(False)
        with self.assertRaises(HarnessError) as raised:
            self.submit('tdd', self.rework_of(None, declared='haiku'))
        self.assertIn('no single slice', str(raised.exception))

    def test_a_declared_absence_at_the_strictest_route_advances(self):
        """The way through, and there is one: the strongest tier the plan routed.

        A floor and not an equality, so the round is not refused for being
        stronger than slice 1's haiku. Without this test the rule above could be
        one no honest record could satisfy.
        """
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd(self.plan())
        self.route()
        self.set_shadow(False)
        record = self.submit('tdd', self.rework_of(None, declared='opus'))
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_a_position_outside_the_plan_is_refused(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd(self.plan())
        self.route()
        with self.assertRaisesRegex(HarnessError, '2 slices'):
            self.submit('tdd', self.rework_of(3, declared='opus'))


class RouteBelowItsBarTest(RouteTest):
    """F5: a route that did not clear its own threshold says so."""

    def test_the_entry_carries_whether_the_answer_cleared_its_bar(self):
        self.use(route_stub(model=(0.3, 0.46, 0.24)))
        self.reach_tdd([PLAIN])
        entry = self.route()['data']['execution'][0]
        self.assertEqual(entry['model'], 'sonnet')
        self.assertFalse(entry['model_passed'])
        self.assertEqual(entry['model_threshold'], 0.5)

    def test_a_route_that_cleared_its_bar_says_that_too(self):
        self.use(route_stub(model=(0.1, 0.7, 0.2)))
        self.reach_tdd([PLAIN])
        self.assertTrue(self.route()['data']['execution'][0]['model_passed'])

    def test_a_rule_routed_slice_has_no_bar_to_clear(self):
        self.reach_tdd([MONEY])
        self.assertIsNone(self.route()['data']['execution'][0]['model_passed'])


class PositionIsDeclaredTest(GateTest):
    """F2 of the fifth review: the route comparison is not skipped by omission.

    The field was optional so that a record written before it existed would not
    be refused, and that made leaving it out a way past the refusal
    indistinguishable from the case it was built for. It is declared now: an
    integer the plan has, or null for a round that belongs to no single slice,
    which is a claim on the record rather than a gap in it.
    """

    def evidence(self, slice_entry):
        red = self.run_check('red', exit_code=1, model='claude-opus-5')
        green = self.run_check('green', model='claude-opus-5')
        regression = self.run_check('regression', model='claude-opus-5')
        self.record_coverage()
        return dict(mode='code', regression=regression['sequence'], coverage_delta=0.0,
                    slices=[dict(slice_entry, red=red['sequence'], green=green['sequence'])])

    def base(self):
        return dict(behaviour='The status line shows the stage',
                    failure_reason='AssertionError: the status line is empty')

    def test_a_slice_that_names_no_position_at_all_is_refused(self):
        self.reach_tdd([PLAIN])
        self.route()
        with self.assertRaisesRegex(HarnessError, 'position'):
            self.submit('tdd', self.evidence(self.base()))

    def test_a_slice_may_declare_no_position_by_saying_so(self):
        """A rework round spanning slices belongs to none of them, and says null."""
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        record = self.submit('tdd', self.evidence(dict(self.base(), position=None)))
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_a_declared_position_is_still_held_to_its_route(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        with self.assertRaisesRegex(HarnessError, 'Slice 1'):
            self.submit('tdd', self.evidence(dict(self.base(), position=1)))

class FixedCopiesTest(RouteTest):
    """The copies say the same thing whatever the ticket is doing.

    Generated per slice, they were wrong on a detached HEAD, wrong after a
    replan, wrong the moment a green landed and wrong after the receipt, where
    doctor reported drift on the commit being merged and verify-merge refused
    with no way to re-sync: F1 of the first review, F4 of the second, F1 of the
    seventh and F3 of the eighth, one design behind all four. They carry the
    strongest tier at high effort now, from thresholds.toml and nothing else,
    and the routed model reaches the implementer through the spawn instruction.
    Decided at record 121.
    """

    def setUp(self):
        super().setUp()
        for name in ('seen-scout', 'seen-reviewer', 'seen-implementer'):
            self.write(f'harness/agents/{name}.md', f'# {name}\n\nStand-in body.\n')

    def copy(self):
        self.run_harness('sync')
        return (self.root / '.claude/agents/seen-implementer.md').read_text()

    def problems(self):
        from harness import doctor as doctoring
        from harness.repository import Repository
        return doctoring.report(Repository(self.root), {})['problems']

    def test_the_copies_carry_the_strongest_tier_at_high_effort(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        self.assertIn('model: opus', self.copy())
        self.assertIn('effort: high', self.copy())

    def test_a_slice_boundary_does_not_change_them(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([MONEY, PLAIN])
        self.route()
        before = self.copy()
        self.run_harness('handoff', self.ticket_id, '--actor', 'claude:implementer',
                         '--slice-done', '1')
        self.assertEqual(self.copy(), before)
        self.assertEqual(self.problems(), [])

    def test_a_new_plan_does_not_change_them(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        before = self.copy()
        self.run_harness('return', self.ticket_id, '--to', 'solution',
                         '--reason', 'The plan was wrong', '--actor', 'claude:implementer')
        self.submit('solution', solution_evidence(slices=[MONEY, SECOND_PLAIN]))
        self.assertEqual(self.copy(), before)
        self.assertEqual(self.problems(), [])

    def test_doctor_is_clean_on_a_detached_head(self):
        """Which is what actions/checkout gives on every pull_request event."""
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        self.run_harness('sync')
        self.git('add', '-A')
        self.git('-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'the slice')
        self.git('checkout', '-q', '--detach', 'HEAD')
        self.assertEqual(self.problems(), [])

    def test_doctor_is_clean_once_the_ticket_has_delivered(self):
        """The state F3 of the eighth review found: no slice is in hand at all."""
        from harness import journal
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        self.run_harness('sync')
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        journal.append(folder, journal.read(folder), kind='receipt', stage='deliver', attempt=1,
                       actor='claude:implementer', head=self.git('rev-parse', 'HEAD'),
                       ticket=self.ticket_id,
                       data=dict(from_stage='deliver', to_stage='delivered',
                                 commit='b' * 40, tree='c' * 64))
        # A delivered ticket says review until it merges, which doctor checks
        # separately; without it the fixture fails on its own paperwork rather
        # than on the drift it is about.
        ticket = self.root / self.ticket_file
        ticket.write_text(ticket.read_text().replace('status: doing', 'status: review'))
        self.git('add', '-A')
        self.git('-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'delivered')
        self.git('checkout', '-q', '--detach', 'HEAD')
        self.assertEqual(self.problems(), [],
                         'the commit being merged must not report drift')


class CarriedNotAppliedTest(RouteTest):
    """What the spawn instruction may promise about the effort, which is nothing.

    F1 of the ninth review: record 121's fix took the route out of the Codex
    agent TOML as well as the Claude Code copy, and three places still said the
    TOML carried it. The route decides the effort and nothing applies it, on
    either assistant; record 130 amends criterion 3 to say so rather than have
    the code described as doing more.
    """

    def task(self):
        self.use(route_stub(model=(0.1, 0.7, 0.2), effort=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        return self.route()['data']['execution'][0]['implementer_task']

    def test_the_spawn_text_does_not_send_a_codex_session_to_the_toml(self):
        task = self.task()
        self.assertNotIn('model_reasoning_effort', task)
        self.assertNotIn('.codex/agents/seen-implementer.toml', task)

    def test_it_still_names_the_model_for_both_assistants(self):
        task = self.task()
        self.assertIn('--model sonnet', task)
        self.assertIn('Claude Code', task)
        self.assertIn('Codex', task)

    def test_it_says_the_effort_is_recorded_rather_than_applied(self):
        self.assertRegex(self.task(), r'(?is)recorded\b.*rather than applied')

    def test_neither_generated_copy_carries_a_routed_effort(self):
        import tomllib
        self.use(route_stub(model=(0.7, 0.2, 0.1), effort=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        for name in ('seen-scout', 'seen-reviewer', 'seen-implementer'):
            self.write(f'harness/agents/{name}.md', f'# {name}\n\nStand-in body.\n')
        self.run_harness('sync')
        codex = tomllib.loads(
            (self.root / '.codex/agents/seen-implementer.toml').read_text())
        self.assertEqual(codex['model'], 'opus')
        self.assertEqual(codex['model_reasoning_effort'], 'high')


class RouteRecordIsCurrentTest(RouteTest):
    """F4: a route record that predates the fields the skill says it carries.

    The only one in this repository was written before implementer_task and
    model_passed existed, so criterion 3's spawn instruction had no instance on
    the branch delivering it, and nothing indexed the keys so nothing noticed.
    """

    def test_every_entry_carries_the_keys_a_reader_is_told_to_find(self):
        self.reach_tdd([MONEY, PLAIN])
        for entry in self.route()['data']['execution']:
            for key in ('implementer_task', 'model_passed', 'model_threshold'):
                self.assertIn(key, entry, f'slice {entry["position"]} is missing {key}')



class RuleTrippedByTheWorkTest(SlicePositionTest):
    """F3 of the ninth review: a rule a plan can miss by not naming a file.

    The rules match a slice's declared files, and a plan that does not foresee
    packages/core sends money arithmetic into the Jev request like any other
    slice. On this ticket slice_files diverged by 22 files across eight triages,
    so a plan understating its change is the normal case rather than the odd
    one. The route cannot know before the work exists; the tdd gate can, because
    by then the diff does.
    """

    def evidence(self, position=1, declared='haiku'):
        """Checks that declare the routed model, so the rule is what is under test.

        Without the declaration the model comparison refuses first and the test
        passes on the wrong refusal, which is what its first version did.
        """
        red = self.declared_check('red', exit_code=1, model='claude-opus-5', declared=declared)
        green = self.declared_check('green', model='claude-opus-5', declared=declared)
        regression = self.declared_check('regression', model='claude-opus-5', declared=declared)
        self.record_coverage()
        self.record_mutation()
        return dict(mode='code', regression=regression['sequence'], coverage_delta=0.0,
                    slices=[dict(position=position, behaviour='The behaviour',
                                 failure_reason='AssertionError: it was absent',
                                 red=red['sequence'], green=green['sequence'])])

    def test_money_written_under_a_jev_route_is_refused(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        self.write('packages/core/src/fees.ts', 'export const fee = 1;\n')
        with self.assertRaises(HarnessError) as raised:
            self.submit('tdd', self.evidence())
        message = str(raised.exception)
        self.assertIn('money', message)
        self.assertIn('packages/core/src/fees.ts', message)

    def test_the_same_work_under_a_rule_route_advances(self):
        self.reach_tdd([MONEY])
        self.route()
        self.set_shadow(False)
        self.write('packages/core/src/fees.ts', 'export const fee = 1;\n')
        record = self.submit('tdd', self.evidence(declared='opus'))
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_work_that_trips_no_rule_advances(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        self.set_shadow(False)
        self.write('apps/web/src/status.tsx', 'export const status = 1;\n')
        record = self.submit('tdd', self.evidence())
        self.assertEqual(record['data']['to_stage'], 'review')

    def test_in_shadow_it_is_not_refused(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        self.write('packages/core/src/fees.ts', 'export const fee = 1;\n')
        record = self.submit('tdd', self.evidence())
        self.assertEqual(record['data']['to_stage'], 'review')



class DescriptionSaysWhatIsNotAppliedTest(unittest.TestCase):
    """The ticket says the routed effort is applied by nothing, where a reader meets it.

    Criterion 3 was amended three times, each time to match what had been built,
    and the sequence amended it into a sentence whose subject was a thing
    nothing does: the review triage scored it 0.26 against a bar of 0.6 and
    returned the ticket before a reviewer was spawned. The criterion asks for
    what the code does now, and the gap goes in the description, which is read
    before the criteria. This holds it there.
    """

    TICKET = 'SEEN-108'

    def description(self):
        path = next((PROJECT / 'docs' / 'tickets').glob(f'{self.TICKET}-*.md'))
        text = path.read_text()
        start = text.index('## Description')
        return ' '.join(text[start:text.index('\n## ', start + 1)].split())

    def test_it_says_nothing_applies_the_routed_effort(self):
        self.assertRegex(self.description(), r'(?i)nothing applies it')

    def test_it_does_not_still_promise_the_agent_s_effort(self):
        """The sentence that promised Claude Code's effort and the Codex TOML."""
        self.assertNotRegex(self.description(), r"(?i)the per-invocation model and the agent's "
                                                r"effort")
        self.assertNotRegex(self.description(), r'(?i)model_reasoning_effort in the agent TOML')

    def test_it_says_why_the_effort_is_left_to_a_later_ticket(self):
        self.assertRegex(self.description(), r'(?i)per-slice agent file')


if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
