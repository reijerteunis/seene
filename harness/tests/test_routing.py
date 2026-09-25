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

from harness import jev
from harness.errors import HarnessError
from harness.tests.test_decisions import noul, score
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence

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


def route_stub(model=SONNET, effort=MEDIUM, billing=0.1, leave_out=()):
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
        """
        from harness import sessions
        original = sessions.model
        sessions.model = lambda root, identity=None: model
        try:
            return self.run_harness('check', self.ticket_id, '--phase', phase,
                                    '--actor', 'claude:implementer', '--',
                                    'sh', '-c', f'exit {exit_code}')
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
                    slices=[dict(behaviour='The status line shows the stage',
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
    """The agent the slice is worked by, carrying the route it was given.

    Generated per slice rather than once, because Claude Code documents no
    per-invocation effort override: the file is the only place a routed effort
    can be put, so the file follows the slice in hand.
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

    def test_the_copies_carry_the_route_of_the_slice_in_hand(self):
        self.use(route_stub(model=(0.1, 0.7, 0.2), effort=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        self.assertIn('model: sonnet', self.frontmatter())
        self.assertIn('effort: low', self.frontmatter())
        self.assertEqual(self.codex()['model'], 'sonnet')
        self.assertEqual(self.codex()['model_reasoning_effort'], 'low')

    def test_the_copies_follow_the_slice_boundary(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([MONEY, PLAIN])
        self.route()
        # Slice 1 is a rule, so the strongest; slice 2 is Jev's, so haiku.
        self.assertIn('model: opus', self.frontmatter())
        self.run_harness('handoff', self.ticket_id, '--actor', 'claude:implementer',
                         '--slice-done', '1')
        self.assertIn('model: haiku', self.frontmatter())

    def test_a_plan_worked_through_falls_back_to_the_strongest(self):
        self.use(route_stub(model=(0.7, 0.2, 0.1)))
        self.reach_tdd([PLAIN])
        self.route()
        self.run_harness('handoff', self.ticket_id, '--actor', 'claude:implementer',
                         '--slice-done', '1')
        self.assertIn('model: opus', self.frontmatter())

    def test_route_writes_the_copies_so_doctor_is_not_left_behind(self):
        from harness import doctor as doctoring
        from harness.repository import Repository
        self.use(route_stub(model=(0.1, 0.7, 0.2)))
        self.reach_tdd([PLAIN])
        self.run_harness('sync')
        self.route()
        self.assertEqual(doctoring.report(Repository(self.root), {})['problems'], [])


class QuestionTest(CommandTest):
    """The two questions, registered the way the triage's four are."""

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

    def test_a_broken_chain_leaves_the_copies_at_the_strongest(self):
        from harness import agents
        self.start()
        record = self.root / 'docs' / 'harness' / 'history' / self.ticket_id / '0001.json'
        record.write_text(record.read_text().replace('"attempt": 1', '"attempt": 2'))
        self.assertEqual(agents.routed(self.root), ('opus', 'high'))

    def test_doctor_still_reports_the_broken_chain(self):
        from harness import doctor as doctoring
        from harness.repository import Repository
        self.start()
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        (folder / 'notes.txt').write_text('a stray file\n')
        problems = doctoring.report(Repository(self.root), {})['problems']
        self.assertTrue(any('notes.txt' in problem for problem in problems), problems)
