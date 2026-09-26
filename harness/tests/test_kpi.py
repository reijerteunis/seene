"""Figures derived from what was recorded, never from what anyone remembers."""

import json
import unittest

from pathlib import Path

from harness import kpi, report
from harness.errors import HarnessError
from harness.tests.test_delivery import DeliveryWalk

PROJECT = Path(__file__).resolve().parents[2]

# The Outcome section is prose, so its figures are words. Built rather than
# listed, because the first version stopped at thirty-nine and a ticket that
# reached forty-one findings raised KeyError inside its own guard.
_UNITS = ('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen '
          'fifteen sixteen seventeen eighteen nineteen twenty').split()
_TENS = ('twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety')
WORDS = {word: number for number, word in enumerate(_UNITS)}
for _index, _ten in enumerate(_TENS):
    WORDS[_ten] = (_index + 2) * 10
    for _unit in range(1, 10):
        WORDS[f'{_ten}-{_UNITS[_unit]}'] = (_index + 2) * 10 + _unit


def at(minute):
    """A timestamp minutes after ten, so a journal can span an hour or more."""
    hour, minute = 10 + minute // 60, minute % 60
    return f'2026-09-23T{hour:02d}:{minute:02d}:00+00:00'


def record(sequence, kind, stage, attempt=1, minute=0, actor='claude:implementer',
           session=None, **data):
    return dict(sequence=sequence, ticket='SEEN-001', timestamp=at(minute), harness_version='1',
                kind=kind, stage=stage, attempt=attempt, actor=actor, session=session,
                head='0' * 40, prev_hash=None, data=data)


def journal_worked_in_two_sessions():
    """Two slices planned, two proved, and two sessions that wrote the records."""
    first, second = 'aaaaaaaaaaaa', 'bbbbbbbbbbbb'
    return [
        record(1, 'start', 'clarify', minute=0, session=first, ticket_file='docs/tickets/x.md',
               ticket_snapshot='# x', base_commit='a' * 40),
        record(2, 'advance', 'clarify', minute=5, session=first, from_stage='clarify',
               to_stage='solution', evidence={}, decisions=[]),
        record(3, 'advance', 'solution', minute=10, session=first, from_stage='solution',
               to_stage='tdd', decisions=[],
               evidence=dict(mode='code', slices=[dict(position=1, name='One', points=1, files=['a'], red='x'),
                                                  dict(name='Two', points=1, files=['b'], red='y')])),
        record(4, 'check', 'tdd', minute=12, session=first, phase='red', exit_code=1, command=['t']),
        record(5, 'check', 'tdd', minute=14, session=first, phase='green', exit_code=0,
               command=['t']),
        record(6, 'handoff', 'tdd', minute=20, session=first, pack='.harness-drafts/x.md',
               sha256='d' * 64, estimated_tokens=900,
               figures=dict(session=first, output_tokens=41000, tool_calls=30)),
        record(7, 'check', 'tdd', minute=30, session=second, phase='red', exit_code=1,
               command=['t']),
        record(8, 'check', 'tdd', minute=32, session=second, phase='green', exit_code=0,
               command=['t']),
        record(9, 'check', 'tdd', minute=33, session=second, phase='coverage', exit_code=0,
               command=['c'], package='@seen/core', lines=91.0, baseline=90.0, delta=1.0),
        record(10, 'advance', 'tdd', minute=40, session=second, from_stage='tdd',
               to_stage='review', decisions=[],
               evidence=dict(mode='code', slices=[dict(position=1, red=4, green=5), dict(red=7, green=8)])),
        record(11, 'advance', 'review', minute=50, session=second, actor='codex:reviewer',
               from_stage='review', to_stage='deliver', decisions=[], evidence=dict(findings=[])),
        record(12, 'receipt', 'deliver', minute=60, session=second, from_stage='deliver',
               to_stage='delivered', commit='b' * 40, tree='c' * 64),
    ]


def journal_with_a_return():
    """start, clarify, solution, tdd, review, back to tdd, review again, deliver, receipt."""
    return [
        record(1, 'start', 'clarify', minute=0, ticket_file='docs/tickets/x.md',
               ticket_snapshot='# x', base_commit='a' * 40),
        record(2, 'advance', 'clarify', minute=5, from_stage='clarify', to_stage='solution',
               evidence={}, decisions=[]),
        record(3, 'advance', 'solution', minute=10, from_stage='solution', to_stage='tdd',
               evidence={}, decisions=[]),
        record(4, 'check', 'tdd', minute=12, phase='red', exit_code=1, command=['t']),
        record(5, 'check', 'tdd', minute=14, phase='green', exit_code=0, command=['t']),
        record(6, 'advance', 'tdd', minute=20, from_stage='tdd', to_stage='review',
               evidence=dict(mode='code', slices=[dict(position=1, red=4, green=5)]), decisions=[]),
        record(7, 'return', 'review', minute=25, from_stage='review', to_stage='tdd',
               to_attempt=2, reason='not right'),
        record(8, 'check', 'tdd', attempt=2, minute=30, phase='red', exit_code=1, command=['t']),
        record(9, 'check', 'tdd', attempt=2, minute=32, phase='green', exit_code=0, command=['t']),
        record(10, 'check', 'tdd', attempt=2, minute=33, phase='coverage', exit_code=0,
               command=['c'], package='@seen/core', lines=91.0, baseline=90.0, delta=1.0),
        record(11, 'advance', 'tdd', attempt=2, minute=40, from_stage='tdd', to_stage='review',
               evidence=dict(mode='code', slices=[dict(position=1, red=8, green=9)]), decisions=[]),
        record(12, 'advance', 'review', attempt=2, minute=50, actor='codex:reviewer',
               from_stage='review', to_stage='deliver', decisions=[],
               evidence=dict(findings=[
                   dict(id='R-01', severity='high', status='resolved'),
                   dict(id='R-02', severity='low', status='waived'),
               ])),
        record(13, 'receipt', 'deliver', attempt=2, minute=60, from_stage='deliver',
               to_stage='delivered', commit='b' * 40, tree='c' * 64),
    ]


class SliceFiguresTest(DeliveryWalk):
    """Slices, sessions and what a slice cost, from the journal and nothing else."""

    def measure(self, records=None, **changes):
        arguments = dict(points=3, tokens=dict(output_tokens=90000))
        arguments.update(changes)
        return kpi.measure(records or journal_worked_in_two_sessions(), 'SEEN-001', **arguments)

    def test_it_counts_the_slices_planned_and_the_slices_proved(self):
        self.assertEqual(self.measure()['slices'], dict(planned=2, proven=2))

    def test_it_counts_the_sessions_that_wrote_the_journal(self):
        self.assertEqual(self.measure()['sessions'], 2)

    def test_output_tokens_per_slice_divides_by_the_slices_proved(self):
        self.assertEqual(self.measure()['output_tokens_per_slice'], 45000.0)

    def test_tokens_nobody_knows_give_a_figure_nobody_knows(self):
        self.assertIsNone(self.measure(tokens=None)['output_tokens_per_slice'])

    def test_a_journal_written_before_the_field_existed_counts_no_sessions(self):
        """Null, not one: a record without a session cannot say it was the same one."""
        self.assertIsNone(self.measure(journal_with_a_return())['sessions'])

    def test_a_ticket_with_no_plan_reports_no_planned_slices(self):
        figures = self.measure(journal_with_a_return())
        self.assertEqual(figures['slices']['planned'], 0)

    def test_slices_proved_are_counted_across_every_attempt(self):
        """A returned ticket proved slices in each attempt, and paid for each.

        Reading only the latest tdd record said this ticket proved one slice of
        the three it planned, and made the cost per slice three times too large.
        """
        figures = self.measure(journal_with_a_return())
        self.assertEqual(figures['slices']['proven'], 2)

    def test_the_cost_per_slice_divides_by_every_slice_worked(self):
        figures = self.measure(journal_with_a_return(), tokens=dict(output_tokens=90000))
        self.assertEqual(figures['output_tokens_per_slice'], 45000.0)

    def test_a_non_code_ticket_has_no_slices_at_all(self):
        """Null rather than zero: nothing was cut badly, there was nothing to cut."""
        records = [record for record in journal_with_a_return()
                   if not (record['kind'] == 'advance'
                           and record['data'].get('from_stage') == 'tdd')]
        self.assertIsNone(self.measure(records)['slices'])


class TicketFiguresTest(DeliveryWalk):

    def measure(self, records=None):
        return kpi.measure(records or journal_with_a_return(), 'SEEN-001', points=3)

    def test_cycle_time_runs_from_the_start_record_to_the_receipt(self):
        self.assertEqual(self.measure()['cycle_time_seconds'], 60 * 60)

    def test_a_stage_revisited_after_a_return_is_counted_twice(self):
        """Rework is time spent, so tdd counts both visits rather than the last."""
        stages = self.measure()['stage_seconds']
        self.assertEqual(stages['tdd'], (20 - 10) * 60 + (40 - 25) * 60)
        self.assertEqual(stages['clarify'], 5 * 60)

    def test_rework_counts_returns_and_reopens(self):
        self.assertEqual(self.measure()['rework'], 1)
        self.assertEqual(self.measure()['attempts'], 2)

    def test_findings_are_split_by_severity_and_a_waiver_is_not_a_fix(self):
        findings = self.measure()['findings']
        self.assertEqual(findings['by_severity'], {'high': 1, 'low': 1})
        self.assertEqual(findings['fixed'], 1)
        self.assertEqual(findings['waived'], 1)

    def test_red_before_green_holds_when_every_slice_cites_a_failing_red(self):
        self.assertTrue(self.measure()['red_before_green'])

    def test_a_slice_citing_a_red_that_passed_fails_the_measure(self):
        records = journal_with_a_return()
        records[7]['data']['exit_code'] = 0
        self.assertFalse(kpi.measure(records, 'SEEN-001', points=3)['red_before_green'])

    def test_coverage_comes_from_the_measurement_the_gate_required(self):
        coverage = self.measure()['coverage']
        self.assertEqual((coverage['lines'], coverage['delta']), (91.0, 1.0))

    def test_a_ticket_with_no_journal_is_measurable_and_honest_about_it(self):
        figures = kpi.measure([], 'SEEN-086', points=8, delivered_at='2026-09-23T12:00:00+00:00')
        self.assertEqual(figures['points'], 8)
        self.assertIsNone(figures['cycle_time_seconds'])
        self.assertIn('no journal', figures['note'])


class ReportTest(DeliveryWalk):

    def test_a_week_covers_only_receipts_inside_it(self):
        inside = dict(ticket='SEEN-001', delivered_at='2026-09-23T10:00:00+00:00', points=3)
        outside = dict(ticket='SEEN-002', delivered_at='2026-09-10T10:00:00+00:00', points=5)
        covered = report.within_week([inside, outside], '2026-09-23')
        self.assertEqual([entry['ticket'] for entry in covered], ['SEEN-001'])

    def test_the_totals_are_derived_from_the_tickets(self):
        totals = report.totals([
            dict(ticket='SEEN-001', points=3, cycle_time_seconds=3600, rework=1,
                 first_pass_ci=True, findings={'by_severity': {'high': 1}, 'fixed': 1, 'waived': 0}),
            dict(ticket='SEEN-002', points=5, cycle_time_seconds=7200, rework=0,
                 first_pass_ci=None, findings={'by_severity': {'low': 2}, 'fixed': 2, 'waived': 0}),
        ])
        self.assertEqual(totals['points_delivered'], 8)
        self.assertEqual(totals['median_cycle_time_seconds'], 5400)
        self.assertEqual(totals['rework_per_ticket'], 0.5)
        self.assertEqual(totals['findings_by_severity'], {'high': 1, 'low': 2})
        self.assertEqual(totals['first_pass_ci_rate'], 1.0, 'measured on the tickets that have it')
        self.assertEqual(totals['first_pass_ci_unknown'], 1)

    def test_a_fix_ticket_increments_escaped_defects_on_what_it_fixed(self):
        self.write('docs/tickets/SEEN-200-fix-the-thing.md',
                   '---\nid: SEEN-200\nfixes: SEEN-001\nstatus: done\n---\n# fix\n')
        self.assertEqual(report.escaped_defects(self.root, 'SEEN-001'), ['SEEN-200'])
        self.assertEqual(report.escaped_defects(self.root, 'SEEN-002'), [])

    def test_a_report_carrying_a_credential_is_refused(self):
        import os
        os.environ['SEEN_TEST_REPORT_TOKEN'] = 'sk-not-in-a-report-9f2b'
        self.addCleanup(os.environ.pop, 'SEEN_TEST_REPORT_TOKEN', None)
        with self.assertRaisesRegex(HarnessError, 'SEEN_TEST_REPORT_TOKEN'):
            report.write(self.root, 'test', 'a report mentioning sk-not-in-a-report-9f2b', {})

    def test_the_reports_directory_does_not_change_the_reviewed_tree(self):
        from harness.repository import Repository
        repository = Repository(self.root)
        before = repository.fingerprint()
        self.write('docs/harness/reports/2026-W39.md', '# a report\n')
        self.write('docs/harness/history/SEEN-001/kpi.json', '{"ticket": "SEEN-001"}')
        self.assertEqual(before, repository.fingerprint())


class RepeatedReviewTest(DeliveryWalk):
    """A review re-run lists its findings again; they are still the same findings."""

    def journal(self):
        records = journal_with_a_return()
        # A second review advance, as a returned ticket produces, listing the
        # first review's findings again alongside a new one.
        records.append(record(14, 'advance', 'review', attempt=3, minute=70,
                              actor='codex:reviewer', from_stage='review', to_stage='deliver',
                              decisions=[], evidence=dict(findings=[
                                  dict(id='R-01', severity='high', status='resolved'),
                                  dict(id='R-02', severity='low', status='waived'),
                                  dict(id='R-03', severity='medium', status='resolved'),
                              ])))
        return records

    def test_findings_are_counted_once_not_once_per_review(self):
        findings = kpi.measure(self.journal(), 'SEEN-001', points=3)['findings']
        self.assertEqual(findings['by_severity'], {'high': 1, 'low': 1, 'medium': 1})
        self.assertEqual(findings['fixed'], 2)
        self.assertEqual(findings['waived'], 1)

    def test_rework_per_ticket_is_reported_to_two_decimals(self):
        figures = report.totals([dict(ticket='a', points=1, rework=1, cycle_time_seconds=1),
                                 dict(ticket='b', points=1, rework=0, cycle_time_seconds=1),
                                 dict(ticket='c', points=1, rework=1, cycle_time_seconds=1)])
        self.assertEqual(figures['rework_per_ticket'], 0.67)


class SubagentAttributionTest(unittest.TestCase):
    """Whether a ticket was worked with the scout and the reviewer, from its journal.

    The fifth criterion of SEEN-105 compares the main session's cost on tickets
    worked that way against the SEEN-099 baseline, so the report has to be able to
    tell them apart, and the journal is the only place that knows.
    """

    def journal(self, briefs=1, independence='subagent', agent='seen-scout'):
        records = [record(1, 'start', 'clarify', minute=0, session='aaaaaaaaaaaa',
                          ticket_file='docs/tickets/x.md', ticket_snapshot='# x',
                          base_commit='a' * 40)]
        for number in range(briefs):
            records.append(record(2 + number, 'note', 'clarify', minute=2 + number,
                                  session='aaaaaaaaaaaa', text='a brief', agent=agent,
                                  words=120))
        if independence is not None:
            records.append(record(2 + briefs, 'advance', 'review', minute=30,
                                  session='aaaaaaaaaaaa', from_stage='review', to_stage='deliver',
                                  decisions=[],
                                  evidence=dict(independence=independence,
                                                reviewer='claude:reviewer', findings=[],
                                                verdict='pass')))
        return records

    def test_a_brief_from_the_reviewer_is_not_a_brief_from_the_scout(self):
        """F4: the report row is about the scout and the reviewer, not either one."""
        answer = kpi.subagents(self.journal(agent='seen-reviewer'))

        self.assertEqual(answer['agents'], ['seen-reviewer'])
        self.assertFalse(answer['both'])

    def test_a_brief_and_a_subagent_review_are_both_recorded(self):
        answer = kpi.subagents(self.journal())

        self.assertEqual(answer['briefs'], 1)
        self.assertEqual(answer['agents'], ['seen-scout'])
        self.assertEqual(answer['review'], 'subagent')
        self.assertTrue(answer['both'])

    def test_a_cross_tool_review_is_recorded_as_what_it_was(self):
        answer = kpi.subagents(self.journal(independence='independent'))

        self.assertEqual(answer['review'], 'independent')
        self.assertFalse(answer['both'])

    def test_a_review_with_no_brief_behind_it_is_not_both(self):
        answer = kpi.subagents(self.journal(briefs=0))

        self.assertEqual(answer['briefs'], 0)
        self.assertFalse(answer['both'])

    def test_a_journal_that_knows_neither_says_so_rather_than_false(self):
        """Nineteen journals were written before either agent existed."""
        self.assertIsNone(kpi.subagents(self.journal(briefs=0, independence=None)))

    def test_measure_carries_it_beside_the_other_figures(self):
        measured = kpi.measure(self.journal(), 'SEEN-001', points=3)

        self.assertTrue(measured['subagents']['both'])

    def test_a_ticket_with_no_journal_carries_the_absence(self):
        measured = kpi.measure([], 'SEEN-001', points=3)

        self.assertIsNone(measured['subagents'])


def route_record(sequence, session, minute, execution):
    return record(sequence, 'route', 'tdd', minute=minute, session=session,
                  solution=3, shadow=True, strongest='opus',
                  tiers=['haiku', 'sonnet', 'opus'], rules=[],
                  jev=dict(asked=True, model='jev-1.13.0', reason=None, answers=[]),
                  execution=execution)


def journal_with_a_route(ran_under='claude-opus-5'):
    """Two slices, routed, each closed by its own handoff boundary.

    One session, so its figures are cumulative and a slice costs the difference
    between the boundary that closed it and the one before. The first handoff
    closes nothing: it is written after the plan is accepted and before any
    slice is worked, and the planning window belongs to no slice.
    """
    session = 'aaaaaaaaaaaa'

    def handoff(sequence, minute, done, position, output):
        return record(sequence, 'handoff', 'tdd', minute=minute, session=session,
                      pack='.harness-drafts/x.md', sha256='d' * 64, estimated_tokens=900,
                      slice=dict(position=position, total=2, done=done, declared=True,
                                 inferred=done),
                      figures=dict(session=session, output_tokens=output, tool_calls=done * 20))

    def check(sequence, minute, phase, exit_code, model=ran_under):
        return record(sequence, 'check', 'tdd', minute=minute, session=session, phase=phase,
                      exit_code=exit_code, command=['t'], model=model)

    return [
        record(1, 'start', 'clarify', minute=0, session=session, ticket_file='docs/tickets/x.md',
               ticket_snapshot='# x', base_commit='a' * 40),
        record(2, 'advance', 'clarify', minute=5, session=session, from_stage='clarify',
               to_stage='solution', evidence={}, decisions=[]),
        record(3, 'advance', 'solution', minute=10, session=session, from_stage='solution',
               to_stage='tdd', decisions=[],
               evidence=dict(mode='code', slices=[dict(position=1, name='One', points=1, files=['a'], red='x'),
                                                  dict(name='Two', points=2, files=['b'],
                                                       red='y')])),
        route_record(4, session, 12, [
            dict(position=1, name='One', points=1, files=['a'], red='x',
                 model='haiku', effort='low', source='jev', rule=None, reason=None,
                 model_probability=0.7, effort_probability=0.6),
            dict(position=2, name='Two', points=2, files=['b'], red='y',
                 model='opus', effort='high', source='rule', rule='money',
                 reason='b is money arithmetic', model_probability=None,
                 effort_probability=None),
        ]),
        # The planning window: 10,000 tokens spent before any slice was worked.
        handoff(5, 14, done=0, position=1, output=10000),
        check(6, 16, 'red', 1),
        check(7, 18, 'green', 0),
        handoff(8, 20, done=1, position=2, output=50000),
        check(9, 30, 'red', 1),
        check(10, 32, 'green', 0),
        record(11, 'check', 'tdd', minute=33, session=session, phase='coverage', exit_code=0,
               command=['c'], package='@seen/core', lines=91.0, baseline=90.0, delta=1.0),
        handoff(12, 35, done=2, position=None, output=95000),
        # The advance carries the session's figures, because the plan ends here
        # and no handoff follows the last slice.
        record(13, 'advance', 'tdd', minute=40, session=session, from_stage='tdd',
               to_stage='review', decisions=[],
               figures=dict(session=session, output_tokens=95000, tool_calls=40),
               evidence=dict(mode='code', slices=[dict(position=1, red=6, green=7), dict(red=9, green=10)])),
        record(14, 'advance', 'review', minute=50, session=session, actor='codex:reviewer',
               from_stage='review', to_stage='deliver', decisions=[], evidence=dict(findings=[])),
        record(15, 'receipt', 'deliver', minute=60, session=session, from_stage='deliver',
               to_stage='delivered', commit='b' * 40, tree='c' * 64),
    ]


class ExecutionFiguresTest(DeliveryWalk):
    """What each slice was routed to, what it ran on, and what it cost.

    From the journal and the price table and nothing else. A handoff record
    carries the session's own spending at the moment it stopped, so a slice
    costs the difference between the boundary that closed it and the one before,
    and the boundary that closed it is the one whose `done` names it.
    """

    def measure(self, records=None, **changes):
        from harness import thresholds
        arguments = dict(points=3, rules=thresholds.load(PROJECT))
        arguments.update(changes)
        return kpi.measure(records or journal_with_a_route(), 'SEEN-001', **arguments)

    def prices(self):
        from harness import thresholds
        return thresholds.load(PROJECT)['routing']['prices']

    def test_one_entry_per_routed_slice_with_its_model_and_effort(self):
        execution = self.measure()['execution']
        self.assertEqual([entry['model'] for entry in execution], ['haiku', 'opus'])
        self.assertEqual([entry['effort'] for entry in execution], ['low', 'high'])
        self.assertEqual([entry['source'] for entry in execution], ['jev', 'rule'])

    def test_a_slice_is_charged_the_window_its_own_boundary_closed(self):
        """Keyed by `done` and not `position`.

        A handoff names the slice in front of you, so keying by position charges
        every slice the window before it and charges the planning window, which
        belongs to no slice, to slice 1.
        """
        execution = self.measure()['execution']
        self.assertEqual(execution[0]['output_tokens'], 40000)
        self.assertEqual(execution[1]['output_tokens'], 45000)

    def test_ran_on_is_the_model_the_greens_in_its_window_were_recorded_under(self):
        execution = self.measure()['execution']
        self.assertEqual([entry['ran_on'] for entry in execution],
                         ['claude-opus-5', 'claude-opus-5'])
        self.assertEqual([entry['ran_on_tier'] for entry in execution], ['opus', 'opus'])

    def test_the_cost_is_priced_at_the_model_the_work_ran_on(self):
        """In shadow a slice runs on the session's model, whatever it was routed to.

        Pricing the actual tokens at the routed model's price would put a
        counterfactual in the column SEEN-109 decides from, and show a saving
        that has not happened.
        """
        entry = self.measure()['execution'][0]
        self.assertEqual(entry['ran_on_tier'], 'opus')
        self.assertEqual(entry['cost_cents'],
                         round(40000 * self.prices()['opus']['output'] / 1_000_000, 2))

    def test_the_routed_price_is_carried_separately_as_the_counterfactual(self):
        entry = self.measure()['execution'][0]
        self.assertEqual(entry['routed_cost_cents'],
                         round(40000 * self.prices()['haiku']['output'] / 1_000_000, 2))
        self.assertNotEqual(entry['cost_cents'], entry['routed_cost_cents'])

    def test_the_cost_says_which_of_the_two_it_is(self):
        entry = self.measure()['execution'][0]
        self.assertIn('ran on', entry['cost_basis'])
        self.assertIn('output', entry['cost_basis'])

    def test_a_check_that_names_no_model_leaves_the_cost_unpriced(self):
        execution = self.measure(journal_with_a_route(ran_under=None))['execution']
        self.assertIsNone(execution[0]['ran_on'])
        self.assertIsNone(execution[0]['cost_cents'])
        self.assertEqual(execution[0]['output_tokens'], 40000)

    def test_without_a_price_table_the_cost_is_null_and_the_tokens_are_not(self):
        execution = self.measure(rules=None)['execution']
        self.assertIsNone(execution[0]['cost_cents'])
        self.assertEqual(execution[0]['output_tokens'], 40000)

    def test_a_ticket_with_no_route_carries_no_execution(self):
        from harness import thresholds
        self.assertIsNone(kpi.measure(journal_worked_in_two_sessions(), 'SEEN-001', points=2,
                                      rules=thresholds.load(PROJECT))['execution'])


class IntegerCentsTest(DeliveryWalk):
    """Amounts are cents as integers with a currency code, which is a ground rule.

    F7 of SEEN-108's first review: cost_cents returned fractional cents as a
    float, so a consumer reading it as the integer the table promises either
    truncates or fails on the type, and a long sum of rounded floats drifts from
    the sum of the printed rows.
    """

    def execution(self):
        from harness import thresholds
        return kpi.measure(journal_with_a_route(), 'SEEN-001', points=3,
                           rules=thresholds.load(PROJECT))['execution']

    def test_every_amount_is_a_whole_number_of_cents(self):
        for entry in self.execution():
            for field in ('cost_cents', 'routed_cost_cents'):
                value = entry[field]
                if value is not None:
                    self.assertIsInstance(value, int, f'{field} is {value!r}')

    def test_a_price_below_one_cent_rounds_rather_than_disappearing(self):
        from harness import thresholds
        prices = thresholds.load(PROJECT)['routing']['prices']
        self.assertEqual(kpi.cost_cents('haiku', 1000, prices), 0)
        self.assertEqual(kpi.cost_cents('haiku', 2000, prices), 1)


class LastSliceTest(DeliveryWalk):
    """F3: the slice no handoff follows.

    A handoff is written at a boundary, and the last slice has none after it, so
    the final slice of every ticket carried no tokens, no cost and no ran_on.
    The accepted tdd advance is that boundary, and it now records the session's
    figures the way a handoff does.
    """

    def journal(self):
        records = journal_with_a_route()
        # The procedure does not write a handoff after the last slice, so the
        # fixture must not either: that is the shape the defect lived in.
        return [record for record in records
                if not (record['kind'] == 'handoff'
                        and (record['data'].get('slice') or {}).get('done') == 2)]

    def measure(self):
        from harness import thresholds
        return kpi.measure(self.journal(), 'SEEN-001', points=3,
                           rules=thresholds.load(PROJECT))

    def test_the_last_slice_is_charged_the_window_the_tdd_advance_closed(self):
        execution = self.measure()['execution']
        self.assertEqual(execution[1]['output_tokens'], 45000)

    def test_the_last_slice_carries_the_model_it_ran_on(self):
        self.assertEqual(self.measure()['execution'][1]['ran_on'], 'claude-opus-5')


class DeliveredCostTest(unittest.TestCase):
    """F2 of SEEN-108's second review: criterion 4 names kpi.json, and delivery writes it.

    Every other test of the cost per slice calls kpi.measure directly, so the one
    line in delivery.verify that hands it the price table was guarded by nothing
    and could be deleted with the whole suite green. This walks a ticket to
    delivered through a real route and a real session log, and reads the figure
    out of the file, which is the shape DeliveredFiguresTest already uses for the
    reviewer's own tokens: asserting that two words appear in the source is not a
    guard, as G2 of SEEN-107's third review found.
    """

    SESSION = 'seen-108-delivered-cost'

    def log(self, root, model='claude-opus-5'):
        """A session log for this walk, because a cost without tokens is null.

        The name is the session id `sessions.figures` will look for, which is
        what makes the handoff figures and the check's model real here.
        """
        import os
        import shutil
        from harness import cost
        previous = os.environ.get('CLAUDE_CODE_SESSION_ID')
        os.environ['CLAUDE_CODE_SESSION_ID'] = self.SESSION
        self.addCleanup(lambda: os.environ.__setitem__('CLAUDE_CODE_SESSION_ID', previous)
                        if previous else os.environ.pop('CLAUDE_CODE_SESSION_ID', None))
        directory = cost.log_directory(root)
        directory.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, directory, True)
        (directory / f'{self.SESSION}.jsonl').write_text('\n'.join(
            json.dumps(dict(timestamp='2026-09-25T00:00:00+00:00',
                            isSidechain=False,
                            message=dict(model=model,
                                         usage=dict(input_tokens=1, output_tokens=20000,
                                                    cache_read_input_tokens=0,
                                                    cache_creation_input_tokens=0))))
            for _ in range(2)) + '\n')

    def test_the_delivered_file_carries_a_cost_for_each_routed_slice(self):
        from harness import jev
        from harness.tests.test_delivery import DeliveryWalk
        from harness.tests.test_lifecycle import clarify_evidence, solution_evidence
        from harness.tests.test_routing import route_stub

        class Walk(DeliveryWalk):
            def runTest(self):                              # pragma: no cover - never run
                pass

        walk = Walk()
        walk.setUp()
        try:
            self.log(walk.root)
            walk.write('.env.local', 'JEV_API_KEY=stub-credential\n')
            jev.TRANSPORT = route_stub(model=(0.1, 0.7, 0.2))
            walk.start()
            walk.submit('clarify', clarify_evidence())
            walk.submit('solution', solution_evidence())
            walk.run_harness('route', walk.ticket_id, '--actor', 'claude:implementer')
            walk.run_harness('check', walk.ticket_id, '--phase', 'red', '--actor',
                             'claude:implementer', '--', 'sh', '-c',
                             'echo expected 1, got 0; exit 1')
            walk.run_harness('check', walk.ticket_id, '--phase', 'green', '--actor',
                             'claude:implementer', '--', 'true')
            walk.run_harness('check', walk.ticket_id, '--phase', 'regression', '--actor',
                             'claude:implementer', '--', 'true')
            walk.write('packages/core/coverage/coverage-summary.json',
                       '{"total": {"lines": {"total": 10, "covered": 9, "skipped": 0, '
                       '"pct": 90.0}}}')
            walk.run_harness('coverage', walk.ticket_id, '--actor', 'claude:implementer',
                             '--', 'true')
            walk.submit('tdd', dict(mode='code',
                                    slices=[dict(position=1, behaviour='The harness records a delivery',
                                                 failure_reason='expected 1, got 0',
                                                 red=5, green=6)],
                                    regression=7, coverage_delta=None))
            walk.run_harness('check', walk.ticket_id, '--phase', 'qa', '--actor',
                             'codex:reviewer', '--', 'true')
            walk.submit('review', dict(reviewer='codex:reviewer', independence='independent',
                                       read=['harness/journal.py'],
                                       acceptance_evidence=['The journal holds every stage'],
                                       findings=[], checks=[], security_checklist=[],
                                       verdict='pass'),
                        actor='codex:reviewer')
            walk.commit_and_push()
            walk.verify()
            folder = walk.root / 'docs' / 'harness' / 'history' / walk.ticket_id
            figures = json.loads((folder / 'kpi.json').read_text())
        finally:
            jev.TRANSPORT = None
            walk.doCleanups()

        self.assertIsNotNone(figures['execution'], 'the walk must route, or this proves nothing')
        entry = figures['execution'][0]
        self.assertIsNotNone(entry['output_tokens'], 'the walk must spend, or the cost is null')
        self.assertIsNotNone(entry['ran_on_tier'])
        self.assertIsNotNone(entry['cost_cents'])


def journal_with_rework(rework_tokens=105000):
    """The same two-slice ticket, returned once and proved again.

    The shape F2 of the third review is about: a second accepted tdd advance
    after a return, with no plan slice left for it to close.
    """
    session = 'aaaaaaaaaaaa'
    # Everything through the first accepted tdd advance, which is record 13.
    records = list(journal_with_a_route())[:13]
    return records + [
        record(14, 'return', 'review', minute=70, session=session,
               from_stage='review', to_stage='tdd', to_attempt=2, reason='a finding'),
        record(15, 'check', 'tdd', attempt=2, minute=75, session=session, phase='red',
               exit_code=1, command=['t'], model='claude-opus-5'),
        record(16, 'check', 'tdd', attempt=2, minute=80, session=session, phase='green',
               exit_code=0, command=['t'], model='claude-opus-5'),
        record(17, 'advance', 'tdd', attempt=2, minute=85, session=session,
               from_stage='tdd', to_stage='review', decisions=[],
               figures=dict(session=session, output_tokens=95000 + rework_tokens,
                            tool_calls=70),
               evidence=dict(mode='code', slices=[dict(position=1, red=15, green=16)])),
    ]


class ReworkWindowTest(DeliveryWalk):
    """F2 of the third review: what a rework round's tokens are charged to.

    Nothing, which is the honest answer: they belong to no slice of the plan.
    What must not happen is a window keyed past the end of the plan, whose
    tokens are silently dropped from a table that then makes a reworked route
    look cheaper than it was.
    """

    def windows(self):
        return kpi.slice_windows(journal_with_rework())

    def test_no_window_is_keyed_past_the_end_of_the_plan(self):
        self.assertEqual(sorted(self.windows()), [1, 2])

    def test_the_advance_closes_nothing_when_a_handoff_already_closed_the_plan(self):
        """This fixture ends its plan at a handoff, so the advance has nothing left.

        The advance is the boundary only for a last slice no handoff followed,
        which is what LastSliceTest covers; here it must not open a window of
        its own for the rework that comes after it.
        """
        window = self.windows()[2]
        self.assertEqual(window['closed'], 12, 'the handoff that declared done=2 closed it')
        self.assertEqual(window['spent'], 45000)

    def test_the_ticket_still_counts_what_the_rework_spent(self):
        """The slices do not carry it; the ticket's own token figure does."""
        from harness import thresholds
        measured = kpi.measure(journal_with_rework(), 'SEEN-001', points=3,
                               rules=thresholds.load(PROJECT),
                               tokens=dict(output_tokens=200000))
        charged = sum(entry['output_tokens'] or 0 for entry in measured['execution'])
        self.assertEqual(charged, 85000)
        self.assertEqual(measured['tokens']['output_tokens'], 200000)


def journal_with_a_compaction():
    """The same two-slice ticket, compacted once inside each slice.

    The shape F3 of SEEN-106's review is about. PreCompact writes a handoff
    record mid-slice through `handoff --auto`, so that record carries `auto` true
    and whatever `done` current_slice inferred at the moment the context filled:
    0 while slice 1 is still being worked, 1 once slice 1 is proved and slice 2 is
    in hand. Neither is a boundary anybody declared, and the figures each carries
    are a fragment of the slice it interrupted.

    One session, so the figures are cumulative and a slice costs the difference
    between the boundary that closed it and the one before. The numbers are far
    apart on purpose: 40,000 for slice 1 and 45,000 for slice 2 against the 8,000
    and 37,000 a reader gets by treating a compaction as a boundary.
    """
    session = 'aaaaaaaaaaaa'

    def handoff(sequence, minute, done, position, output, auto=False):
        return record(sequence, 'handoff', 'tdd', minute=minute, session=session,
                      pack='.harness-drafts/x.md', sha256='d' * 64, estimated_tokens=900,
                      auto=auto,
                      slice=dict(position=position, total=2, done=done, declared=not auto,
                                 inferred=done),
                      figures=dict(session=session, output_tokens=output, tool_calls=done * 20))

    def check(sequence, minute, phase, exit_code):
        return record(sequence, 'check', 'tdd', minute=minute, session=session, phase=phase,
                      exit_code=exit_code, command=['t'], model='claude-opus-5')

    return [
        record(1, 'start', 'clarify', minute=0, session=session, ticket_file='docs/tickets/x.md',
               ticket_snapshot='# x', base_commit='a' * 40),
        record(2, 'advance', 'clarify', minute=5, session=session, from_stage='clarify',
               to_stage='solution', evidence={}, decisions=[]),
        record(3, 'advance', 'solution', minute=10, session=session, from_stage='solution',
               to_stage='tdd', decisions=[],
               evidence=dict(mode='code',
                             slices=[dict(position=1, name='One', points=1, files=['a'], red='x'),
                                     dict(name='Two', points=2, files=['b'], red='y')])),
        # The planning window: 10,000 tokens spent before any slice was worked.
        handoff(4, 14, done=0, position=1, output=10000),
        check(5, 16, 'red', 1),
        # A compaction inside slice 1, which no session declared: done=0, so it
        # keys no window, and the 20,000 it carries are slice 1's own spending.
        handoff(6, 17, done=0, position=1, output=30000, auto=True),
        check(7, 18, 'green', 0),
        handoff(8, 20, done=1, position=2, output=50000),
        check(9, 30, 'red', 1),
        # A compaction inside slice 2, carrying the done=1 current_slice infers
        # from a proved slice 1: the record that overwrites slice 1's window.
        handoff(10, 31, done=1, position=2, output=58000, auto=True),
        check(11, 32, 'green', 0),
        handoff(12, 35, done=2, position=None, output=95000),
        record(13, 'advance', 'tdd', minute=40, session=session, from_stage='tdd',
               to_stage='review', decisions=[],
               figures=dict(session=session, output_tokens=95000, tool_calls=40),
               evidence=dict(mode='code',
                             slices=[dict(position=1, red=5, green=7), dict(red=9, green=11)])),
    ]


class CompactionWindowTest(DeliveryWalk):
    """F3 of SEEN-106's review: a compaction is not a slice boundary.

    A pack written by a compaction says where the work stands, which is what the
    pack is for; it does not say a slice ended. Reading it as a boundary keys a
    window a session already keyed and overwrites that slice's figures with a
    fragment of the next slice's spending, and a compaction inside the first
    slice moves the open cursor so that slice is charged only what came after it.
    Those figures are what SEEN-109's calibration decides the routes on.
    """

    def windows(self):
        return kpi.slice_windows(journal_with_a_compaction())

    def test_slice_one_keeps_the_figures_of_the_boundary_a_session_declared(self):
        """The declared boundary at record 8, not the compaction at record 10.

        Overwritten, windows[1] reads 8,000 and closes at 10: the tokens spent
        between the declared boundary and the compaction that interrupted slice 2.
        """
        window = self.windows()[1]
        self.assertEqual(window['closed'], 8, 'the handoff that declared done=1 closed slice 1')
        self.assertEqual(window['spent'], 40000)

    def test_a_compaction_inside_a_slice_does_not_move_where_that_slice_opened(self):
        """The open cursor stays where the declared boundary put it.

        Slice 2 runs from record 8 to record 12 whatever happened in between, so
        it costs 45,000 and not the 37,000 left after the compaction at record 10
        has taken the first 8,000 of it away.
        """
        window = self.windows()[2]
        self.assertEqual(window['opened'], 8)
        self.assertEqual(window['spent'], 45000)

    def test_no_window_is_keyed_by_a_record_a_compaction_wrote(self):
        closed = {window['closed'] for window in self.windows().values()}
        self.assertEqual(closed & {6, 10}, set(),
                         'records 6 and 10 were written by a compaction, not by a session '
                         'declaring a boundary')

    def test_the_slice_figures_the_calibration_reads_carry_the_declared_window(self):
        """output_tokens, cost_cents and routed_cost_cents per slice, which is
        what SEEN-109 compares a route against."""
        from harness import thresholds
        records = journal_with_a_compaction()
        records.append(route_record(14, 'aaaaaaaaaaaa', 11, [
            dict(position=1, name='One', points=1, files=['a'], red='x',
                 model='haiku', effort='low', source='jev', rule=None, reason=None,
                 model_probability=0.7, effort_probability=0.6),
            dict(position=2, name='Two', points=2, files=['b'], red='y',
                 model='opus', effort='high', source='rule', rule='money',
                 reason='b is money arithmetic', model_probability=None,
                 effort_probability=None),
        ]))
        measured = kpi.measure(records, 'SEEN-001', points=3, rules=thresholds.load(PROJECT))
        self.assertEqual([entry['output_tokens'] for entry in measured['execution']],
                         [40000, 45000])
        for entry in measured['execution']:
            self.assertIsNotNone(entry['cost_cents'])
            self.assertIsNotNone(entry['routed_cost_cents'])


class StaleRouteTest(DeliveryWalk):
    """F2 of the fourth review: the KPI reads a route for the plan it routed.

    routing.for_slice refuses a route whose solution is not the accepted advance,
    and kpi.execution did not, so after a replan nobody routed again the KPI
    reported routes for slices that no longer exist.
    """

    def replanned(self):
        records = list(journal_with_a_route())
        return records + [
            record(16, 'return', 'review', minute=70, session='aaaaaaaaaaaa',
                   from_stage='review', to_stage='solution', to_attempt=2, reason='a finding'),
            record(17, 'advance', 'solution', minute=75, session='aaaaaaaaaaaa',
                   from_stage='solution', to_stage='tdd', decisions=[],
                   evidence=dict(mode='code',
                                 slices=[dict(position=1, name='Something else', points=1, files=['c'],
                                              red='z')])),
        ]

    def test_a_route_that_routed_a_replaced_plan_is_not_read(self):
        from harness import thresholds
        measured = kpi.measure(self.replanned(), 'SEEN-001', points=1,
                               rules=thresholds.load(PROJECT))
        self.assertIsNone(measured['execution'])

    def test_the_two_readers_agree_about_a_stale_route(self):
        from harness import routing
        records = self.replanned()
        self.assertIsNone(routing.for_slice(records, 1))
        self.assertIsNone(kpi.execution(records))


class OutcomeReconcilesTest(unittest.TestCase):
    """The Outcome's findings against the journal that is supposed to supply them.

    F4 of the fourth review and F2 of the seventh: the section was written from
    recall and said thirty-four where its own list summed to thirty-one. The
    first version of this test also compared the attempts, the returns and the
    slices against the journal, asserting the section was exactly one ahead of
    it, which is true when the section is written and false the moment the
    advance it anticipates is recorded: F1 of the eighth review, where the suite
    was red at HEAD and no delivered tree could have satisfied it. A guard
    against stale counts that is itself a ratchet is worse than none.

    What is checked here is what stays true as the journal grows: the total is
    the sum of the list beside it, the list has one figure per review it claims,
    and each figure is the count of findings in the reviewer note it refers to.
    Those hold whatever happens next, because the journal is append-only and an
    earlier note never changes. The moving counts are generated from the journal
    when the section is written and are not asserted here, because a number that
    must be one ahead of a growing list cannot be right for long.
    """

    TICKET = 'SEEN-108'

    def outcome(self):
        path = next((PROJECT / 'docs' / 'tickets').glob(f'{self.TICKET}-*.md'))
        text = path.read_text()
        start = text.index('## Outcome')
        return text[start:text.index('\n## ', start + 1)]

    def reviews(self):
        """Every reviewer note, in the order they were written."""
        from harness import journal
        records = journal.read(PROJECT / 'docs' / 'harness' / 'history' / self.TICKET)
        return [record for record in records
                if record['kind'] == 'note'
                and 'from the seen-reviewer subagent' in (record['data'].get('text') or '')]

    def stated(self):
        import re
        # To the full stop, not to the last comma: a greedy match ending in a
        # comma drops the final figure, which is the one most likely to be new.
        found = re.search(r'([A-Za-z-]+) findings over ([a-z-]+)\s*\n?reviews, falling ([^.]+)\.',
                          self.outcome(), re.IGNORECASE)
        self.assertIsNotNone(found, 'the outcome does not state its findings')
        return (WORDS[found.group(1).lower()], WORDS[found.group(2).lower()],
                [WORDS[word.strip().lower()] for word in found.group(3).split(',')
                 if word.strip().lower() in WORDS])

    def test_the_total_is_the_sum_of_the_list_beside_it(self):
        total, _, per_review = self.stated()
        self.assertEqual(sum(per_review), total, f'{per_review} sums to {sum(per_review)}')

    def test_the_list_has_one_figure_for_each_review_it_claims(self):
        _, reviews, per_review = self.stated()
        self.assertEqual(len(per_review), reviews)

    def test_each_figure_is_the_findings_in_the_review_it_refers_to(self):
        import re
        _, _, per_review = self.stated()
        notes = self.reviews()
        self.assertGreaterEqual(len(notes), len(per_review),
                                'the outcome claims more reviews than the journal holds')
        counted = [len(re.findall(r'^- \*\*F\d+,', note['data']['text'], re.MULTILINE))
                   for note in notes[:len(per_review)]]
        self.assertEqual(per_review, counted)


if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
