"""Figures derived from what was recorded, never from what anyone remembers."""

import json
import unittest

from pathlib import Path

from harness import kpi, report
from harness.errors import HarnessError
from harness.tests.test_delivery import DeliveryWalk

PROJECT = Path(__file__).resolve().parents[2]


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
               evidence=dict(mode='code', slices=[dict(name='One', points=1, files=['a'], red='x'),
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
               evidence=dict(mode='code', slices=[dict(red=4, green=5), dict(red=7, green=8)])),
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
               evidence=dict(mode='code', slices=[dict(red=4, green=5)]), decisions=[]),
        record(7, 'return', 'review', minute=25, from_stage='review', to_stage='tdd',
               to_attempt=2, reason='not right'),
        record(8, 'check', 'tdd', attempt=2, minute=30, phase='red', exit_code=1, command=['t']),
        record(9, 'check', 'tdd', attempt=2, minute=32, phase='green', exit_code=0, command=['t']),
        record(10, 'check', 'tdd', attempt=2, minute=33, phase='coverage', exit_code=0,
               command=['c'], package='@seen/core', lines=91.0, baseline=90.0, delta=1.0),
        record(11, 'advance', 'tdd', attempt=2, minute=40, from_stage='tdd', to_stage='review',
               evidence=dict(mode='code', slices=[dict(red=8, green=9)]), decisions=[]),
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


def journal_with_a_route():
    """Two slices, routed, worked in one session, with a handoff closing each.

    One session, so its figures are cumulative and a slice costs the difference
    between the two handoffs. That is the case this repository's own tickets are
    in, and the one a division by slices got wrong.
    """
    session = 'aaaaaaaaaaaa'
    records = journal_worked_in_two_sessions()
    # Both handoffs in one session, so the second carries the running total.
    records[5] = record(6, 'handoff', 'tdd', minute=20, session=session,
                        pack='.harness-drafts/x.md', sha256='d' * 64, estimated_tokens=900,
                        slice=dict(position=1, total=2, done=1, declared=True, inferred=1),
                        figures=dict(session=session, output_tokens=40000, tool_calls=30))
    for position in (0, 1, 2, 3, 4):
        records[position] = dict(records[position], session=session)
    for position in range(6, len(records)):
        records[position] = dict(records[position], session=session)
    tail = records[6:]
    routed = route_record(6, session, 18, [
        dict(position=1, name='One', points=1, files=['a'], red='x',
             model='haiku', effort='low', source='jev', rule=None, reason=None,
             model_probability=0.7, effort_probability=0.6),
        dict(position=2, name='Two', points=1, files=['b'], red='y',
             model='opus', effort='high', source='rule', rule='money',
             reason='b is money arithmetic', model_probability=None, effort_probability=None),
    ])
    handoff_one = dict(records[5], sequence=7)
    rest = []
    for offset, item in enumerate(tail):
        rest.append(dict(item, sequence=8 + offset))
    second = record(8 + len(tail), 'handoff', 'tdd', minute=45, session=session,
                    pack='.harness-drafts/x.md', sha256='e' * 64, estimated_tokens=900,
                    slice=dict(position=2, total=2, done=2, declared=True, inferred=2),
                    figures=dict(session=session, output_tokens=95000, tool_calls=60))
    return records[:5] + [routed, handoff_one] + rest + [second]


class ExecutionFiguresTest(DeliveryWalk):
    """What each slice was routed to, what it ran on, and what it cost.

    From the journal and the price table and nothing else: a handoff record
    carries the session's own spending at the moment it stopped, so a slice
    costs the difference between the boundary that closed it and the one before.
    """

    def measure(self, **changes):
        from harness import thresholds
        arguments = dict(points=2, rules=thresholds.load(PROJECT))
        arguments.update(changes)
        return kpi.measure(journal_with_a_route(), 'SEEN-001', **arguments)

    def test_one_entry_per_routed_slice_with_its_model_and_effort(self):
        execution = self.measure()['execution']
        self.assertEqual([entry['model'] for entry in execution], ['haiku', 'opus'])
        self.assertEqual([entry['effort'] for entry in execution], ['low', 'high'])
        self.assertEqual([entry['source'] for entry in execution], ['jev', 'rule'])

    def test_a_slice_costs_the_tokens_between_its_boundary_and_the_one_before(self):
        execution = self.measure()['execution']
        self.assertEqual(execution[0]['output_tokens'], 40000)
        self.assertEqual(execution[1]['output_tokens'], 55000)

    def test_the_cost_is_the_routed_model_s_price_for_those_tokens(self):
        from harness import thresholds
        prices = thresholds.load(PROJECT)['routing']['prices']
        execution = self.measure()['execution']
        self.assertEqual(execution[0]['cost_cents'],
                         round(40000 * prices['haiku']['output'] / 1_000_000, 2))
        self.assertEqual(execution[1]['cost_cents'],
                         round(55000 * prices['opus']['output'] / 1_000_000, 2))

    def test_the_cost_says_what_it_covers(self):
        """Output tokens only, because that is all a handoff record carries."""
        entry = self.measure()['execution'][0]
        self.assertIn('output', entry['cost_basis'])

    def test_without_a_price_table_the_cost_is_null_and_the_tokens_are_not(self):
        execution = self.measure(rules=None)['execution']
        self.assertIsNone(execution[0]['cost_cents'])
        self.assertEqual(execution[0]['output_tokens'], 40000)

    def test_a_ticket_with_no_route_carries_no_execution(self):
        from harness import thresholds
        self.assertIsNone(kpi.measure(journal_worked_in_two_sessions(), 'SEEN-001', points=2,
                                      rules=thresholds.load(PROJECT))['execution'])

    def test_the_model_the_checks_actually_ran_under_is_carried_beside_the_route(self):
        """In shadow the two differ, and the difference is what SEEN-109 reads."""
        entry = self.measure()['execution'][0]
        self.assertIn('ran_on', entry)
