"""Figures derived from what was recorded, never from what anyone remembers."""

import json

from harness import kpi, report
from harness.errors import HarnessError
from harness.tests.test_delivery import DeliveryWalk


def at(minute):
    """A timestamp minutes after ten, so a journal can span an hour or more."""
    hour, minute = 10 + minute // 60, minute % 60
    return f'2026-09-23T{hour:02d}:{minute:02d}:00+00:00'


def record(sequence, kind, stage, attempt=1, minute=0, actor='claude:implementer', **data):
    return dict(sequence=sequence, ticket='SEEN-001', timestamp=at(minute), harness_version='1',
                kind=kind, stage=stage, attempt=attempt, actor=actor, head='0' * 40,
                prev_hash=None, data=data)


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
