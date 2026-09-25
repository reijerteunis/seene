"""The window, the escapes and the two verdicts, by a rule written before them.

The figures these tests derive decide whether a narrowed review and a cheaper
model ever take effect, so what is asserted here is that the rule is applied as
written rather than that a number came out favourable.
"""

import json
import unittest

from harness import calibration, gates, journal as journal_module, report, thresholds
from harness.errors import HarnessError
from harness.tests.helpers import PROJECT, ProjectTest
from harness.tests.test_lifecycle import CommandTest
from harness.tests.test_triage import TriageTest


def at(day, minute=0):
    return f'2026-10-{day:02d}T10:{minute:02d}:00+00:00'


def record(sequence, kind, stage, day=1, minute=0, ticket='SEEN-001', attempt=1, **data):
    return dict(sequence=sequence, ticket=ticket, timestamp=at(day, minute), harness_version='2',
                kind=kind, stage=stage, attempt=attempt, actor='claude:implementer',
                session='a' * 12, head='0' * 40, prev_hash=None, data=data)


def triage_record(sequence, day=1, minute=10, would_exclude=(), answers=(), ticket='SEEN-001',
                  files=None):
    """A triage as SEEN-107 writes one: what it would have dropped, and its answers."""
    return record(sequence, 'triage', 'review', day=day, minute=minute, ticket=ticket,
                  fingerprint='f' * 64, code_fingerprint='c' * 64,
                  files=[dict(path=path, added=1, removed=0)
                         for path in (files if files is not None
                                      else ['harness/skipped.py', 'harness/read.py',
                                            'harness/a.py', 'harness/b.py', 'harness/other.py',
                                            '.claude/agents/seen-reviewer.md',
                                            '.claude/agents/x.md', '.codex/agents/x.toml'])],
                  criteria=[], deterministic=[], rules=[],
                  jev=dict(asked=True, model='jev-1.13.0', reason=None, answers=[]),
                  criteria_answers=[dict(key=f'criterion_evidenced#{position}',
                                         criterion=criterion, passed=passed,
                                         outcome='yes' if passed else 'no',
                                         probabilities={}, threshold=0.6)
                                    for position, criterion, passed in answers],
                  review_depth='spot', model_depth='spot', reviewer_model='sonnet',
                  focus=[], shadow=True, would_exclude=list(would_exclude),
                  excluded_share=0.4, always_read=[], reviewer_task='read it')


def review_advance(sequence, findings, day=1, minute=20, ticket='SEEN-001'):
    return record(sequence, 'advance', 'review', day=day, minute=minute, ticket=ticket,
                  from_stage='review', to_stage='deliver', decisions=[],
                  evidence=dict(reviewer='codex:reviewer', independence='subagent',
                                read=[], findings=findings, verdict='pass'))


def finding(identifier, severity, file=None):
    body = dict(id=identifier, severity=severity, claim='It breaks',
                failure_scenario='It breaks like this', status='resolved',
                resolution='Fixed')
    if file is not None:
        body['file'] = file
    return body


def route_record(sequence, execution, day=1, minute=5, ticket='SEEN-001', solution=3):
    return record(sequence, 'route', 'tdd', day=day, minute=minute, ticket=ticket,
                  solution=solution, shadow=True, strongest='opus',
                  tiers=['haiku', 'sonnet', 'opus'], rules=[],
                  jev=dict(asked=True, model='jev-1.13.0', reason=None, answers=[]),
                  execution=execution)


def slice_entry(position, model, source='jev', points=1, files=('harness/a.py',), name='A slice'):
    return dict(position=position, name=name, points=points, files=list(files), red='x',
                model=model, effort='high' if model == 'opus' else 'medium', source=source,
                rule=None, reason=None, model_probability=0.7, effort_probability=0.6,
                model_passed=True, model_threshold=0.5)


def journal(ticket='SEEN-001', day=1, triage=None, findings=(), returns=(), execution=None,
            answers=(), returned_findings=None, declared_empty=False):
    """A delivered ticket's journal: start, plan, route, triage, review, receipt."""
    records = [
        record(1, 'start', 'clarify', day=day, ticket=ticket, ticket_file='docs/tickets/x.md',
               ticket_snapshot='# x', base_commit='a' * 40),
        record(2, 'advance', 'clarify', day=day, minute=1, ticket=ticket, from_stage='clarify',
               to_stage='solution', evidence={}, decisions=[]),
        record(3, 'advance', 'solution', day=day, minute=2, ticket=ticket, from_stage='solution',
               to_stage='tdd', decisions=[],
               evidence=dict(mode='code',
                             slices=[dict(position=1, name='A slice', points=1,
                                          files=['harness/a.py'], red='x')])),
    ]
    if execution is not None:
        records.append(route_record(4, execution, day=day, ticket=ticket))
    records.append(triage_record(len(records) + 1, day=day,
                                 would_exclude=triage or (), answers=answers, ticket=ticket))
    if returned_findings is not None:
        records.append(record(len(records) + 1, 'return', 'review', day=day, minute=14,
                              ticket=ticket, from_stage='review', to_stage='tdd', to_attempt=2,
                              reason='The review found a defect', unmet_criteria=[],
                              findings=list(returned_findings)))
        records.append(triage_record(len(records) + 1, day=day, minute=16,
                                     would_exclude=triage or (), answers=answers, ticket=ticket))
    if declared_empty:
        records.append(record(len(records) + 1, 'return', 'review', day=day, minute=13,
                              ticket=ticket, from_stage='review', to_stage='tdd', to_attempt=2,
                              reason='Not about a defect', unmet_criteria=[], findings=[],
                              no_findings=True))
        records.append(triage_record(len(records) + 1, day=day, minute=16,
                                     would_exclude=triage or (), answers=answers, ticket=ticket))
    for position, unmet in enumerate(returns):
        records.append(record(len(records) + 1, 'return', 'review', day=day, minute=17 + position,
                              ticket=ticket, from_stage='review', to_stage='tdd', to_attempt=2,
                              reason='Sent back', unmet_criteria=list(unmet)))
    records.append(review_advance(len(records) + 1, list(findings), day=day, ticket=ticket))
    records.append(record(len(records) + 1, 'receipt', 'deliver', day=day, minute=30,
                          ticket=ticket, from_stage='deliver', to_stage='delivered',
                          commit='b' * 40, tree='c' * 64))
    return records


def plant(root, ticket, day, **kwargs):
    """Write a journal to disk, chained the way journal.append chains one."""
    folder = root / 'docs' / 'harness' / 'history' / ticket
    folder.mkdir(parents=True, exist_ok=True)
    previous = None
    for entry in journal(ticket=ticket, day=day, **kwargs):
        path = folder / f'{entry["sequence"]:04d}.json'
        path.write_bytes(journal_module.serialise(dict(entry, prev_hash=previous)))
        previous = journal_module.digest(path)
    return folder


class EscapeTest(unittest.TestCase):
    """What counts as an escape, and what the rule refuses to count either way."""

    def test_a_blocking_finding_in_an_excluded_file_is_an_escape(self):
        found = calibration.escapes(journal(triage=['harness/skipped.py'],
                                            findings=[finding('F1', 'blocking',
                                                              'harness/skipped.py:12')]))
        self.assertEqual([entry['kind'] for entry in found['escapes']],
                         ['finding_in_excluded_file'])
        self.assertEqual(found['escapes'][0]['file'], 'harness/skipped.py')

    def test_a_finding_in_a_file_the_triage_kept_is_not_an_escape(self):
        found = calibration.escapes(journal(triage=['harness/skipped.py'],
                                            findings=[finding('F1', 'blocking',
                                                              'harness/read.py:3')]))
        self.assertEqual(found['escapes'], [])
        self.assertEqual(found['unattributable'], [])

    def test_a_medium_finding_in_an_excluded_file_is_not_an_escape(self):
        found = calibration.escapes(journal(triage=['harness/skipped.py'],
                                            findings=[finding('F1', 'medium',
                                                              'harness/skipped.py:12')]))
        self.assertEqual(found['escapes'], [])

    def test_a_high_finding_naming_no_file_is_unattributable(self):
        found = calibration.escapes(journal(triage=['harness/skipped.py'],
                                            findings=[finding('F1', 'high')]))
        self.assertEqual(found['escapes'], [])
        self.assertEqual([entry['id'] for entry in found['unattributable']], ['F1'])

    def test_a_criterion_the_triage_evidenced_and_the_review_found_unmet_is_an_escape(self):
        found = calibration.escapes(journal(answers=[(1, 'Something observable happens', True)],
                                            returns=[[1]]))
        self.assertEqual([entry['kind'] for entry in found['escapes']], ['unmet_criterion'])
        self.assertEqual(found['escapes'][0]['criterion'], 'Something observable happens')

    def test_a_criterion_the_triage_found_unevidenced_is_not_an_escape(self):
        """The triage said so itself and returned the ticket; it missed nothing."""
        found = calibration.escapes(journal(answers=[(1, 'Something observable happens', False)],
                                            returns=[[1]]))
        self.assertEqual(found['escapes'], [])
        self.assertEqual(found['unattributable'], [])

    def test_a_criterion_the_triage_never_answered_is_unattributable(self):
        found = calibration.escapes(journal(returns=[[1]]))
        self.assertEqual(found['escapes'], [])
        self.assertEqual([entry['position'] for entry in found['unattributable']], [1])

    def test_a_return_naming_no_criterion_is_unattributable(self):
        """F4 of the first review: nothing requires the flag, so a forgotten one

        would hide an escape in exactly the direction the rule forbids.
        """
        found = calibration.escapes(journal(answers=[(1, 'A criterion', True)], returns=[[]]))
        self.assertEqual(found['escapes'], [])
        self.assertEqual([entry['kind'] for entry in found['unattributable']], ['return'])

    def test_a_finding_in_a_dot_directory_the_triage_excluded_is_an_escape(self):
        """F1 of the first review: lstrip strips characters, not a prefix."""
        found = calibration.escapes(journal(triage=['.claude/agents/seen-reviewer.md'],
                                            findings=[finding('F1', 'blocking',
                                                              '.claude/agents/seen-reviewer.md:84')]))
        self.assertEqual([entry['kind'] for entry in found['escapes']],
                         ['finding_in_excluded_file'])
        self.assertEqual(found['escapes'][0]['file'], '.claude/agents/seen-reviewer.md')

    def test_a_finding_and_an_exclusion_written_with_a_leading_dot_slash_still_meet(self):
        found = calibration.escapes(journal(triage=['./harness/a.py'],
                                            findings=[finding('F1', 'high', 'harness/a.py:2')]))
        self.assertEqual(len(found['escapes']), 1)

    def test_a_finding_at_an_absolute_path_is_unattributable(self):
        """Nothing repository-relative can be compared with it, so it is placed nowhere."""
        found = calibration.escapes(journal(triage=['harness/a.py'],
                                            findings=[finding('F1', 'blocking',
                                                              '/Users/x/seene/harness/a.py:2')]))
        self.assertEqual(found['escapes'], [])
        self.assertEqual([entry['id'] for entry in found['unattributable']], ['F1'])


class WindowTest(ProjectTest):
    """Which tickets the window counts, and which it names as excluded and why."""

    def setUp(self):
        super().setUp()
        self.rules = thresholds.load(self.root)

    def plant(self, ticket, day, **kwargs):
        plant(self.root, ticket, day, **kwargs)

    def test_a_ticket_that_built_the_thing_under_calibration_is_excluded_by_name(self):
        for excluded in self.rules['calibration']['excluded']:
            self.plant(excluded, 2)
        self.plant('SEEN-200', 2)
        section = calibration.evidence(self.root, self.rules)
        self.assertEqual([entry['ticket'] for entry in section['tickets']], ['SEEN-200'])
        self.assertEqual(sorted(entry['ticket'] for entry in section['excluded']),
                         sorted(self.rules['calibration']['excluded']))

    def test_a_ticket_started_before_the_rule_existed_is_excluded_with_its_date(self):
        rules = dict(self.rules, calibration=dict(self.rules['calibration'],
                                                  counted_from='2026-10-05T00:00:00+00:00'))
        self.plant('SEEN-200', 2)
        self.plant('SEEN-201', 6)
        section = calibration.evidence(self.root, rules)
        self.assertEqual([entry['ticket'] for entry in section['tickets']], ['SEEN-201'])
        self.assertEqual([entry['ticket'] for entry in section['excluded']], ['SEEN-200'])

    def test_the_window_is_the_most_recent_ten_counted_tickets(self):
        for day in range(1, 14):
            self.plant(f'SEEN-3{day:02d}', day)
        section = calibration.evidence(self.root, self.rules)
        self.assertEqual(len(section['tickets']), 13)
        self.assertEqual(len(section['triage']['window']), 10)
        self.assertEqual(section['triage']['window'][0], 'SEEN-304')


class TriageVerdictTest(unittest.TestCase):
    """Go-live or stay-shadow for the triage, stated by the rule and not by a reading."""

    def setUp(self):
        self.rules = thresholds.load(PROJECT)

    def rows(self, count, escapes_on=()):
        rows = []
        for index in range(count):
            ticket = f'SEEN-4{index:02d}'
            rows.append(dict(ticket=ticket,
                             escapes=[dict(kind='finding_in_excluded_file', id='F1',
                                           file='harness/a.py', severity='blocking',
                                           detail='left out')] if index in escapes_on else [],
                             unattributable=[]))
        return rows

    def test_nine_counted_tickets_state_stay_shadow_and_name_the_shortfall(self):
        verdict = calibration.verdict_triage(self.rows(9), self.rules)
        self.assertEqual(verdict['state'], 'stay_shadow')
        self.assertIn('9 of 10', verdict['reason'])

    def test_ten_clean_tickets_state_go_live(self):
        verdict = calibration.verdict_triage(self.rows(10), self.rules)
        self.assertEqual(verdict['state'], 'go_live')

    def test_one_escape_in_the_window_states_stay_shadow_and_names_it(self):
        verdict = calibration.verdict_triage(self.rows(10, escapes_on=[4]), self.rules)
        self.assertEqual(verdict['state'], 'stay_shadow')
        self.assertIn('SEEN-404', verdict['reason'])

    def test_an_escape_that_has_dropped_out_of_the_window_no_longer_holds_it(self):
        """The ticket's another ten: ten clean tickets after the escape."""
        verdict = calibration.verdict_triage(self.rows(21, escapes_on=[4]), self.rules)
        self.assertEqual(verdict['state'], 'go_live')


class RouteVerdictTest(unittest.TestCase):
    """The downgraded slices against the rest, on the charges the rule names."""

    def setUp(self):
        self.rules = thresholds.load(PROJECT)

    def test_a_slice_jev_sent_below_the_strongest_is_the_downgraded_group(self):
        rows = calibration.slice_rows('SEEN-500',
                                      journal(execution=[slice_entry(1, 'sonnet'),
                                                         slice_entry(2, 'opus')]),
                                      escaped=[], rules=self.rules)
        self.assertEqual([row['group'] for row in rows], ['downgraded', 'strongest'])

    def test_a_rule_routed_slice_is_in_the_strongest_group(self):
        rows = calibration.slice_rows('SEEN-500',
                                      journal(execution=[slice_entry(1, 'opus', source='rule')]),
                                      escaped=[], rules=self.rules)
        self.assertEqual(rows[0]['group'], 'strongest')

    def test_a_finding_is_charged_to_the_slice_whose_files_it_lands_in(self):
        rows = calibration.slice_rows(
            'SEEN-500',
            journal(execution=[slice_entry(1, 'sonnet', files=['harness/a.py']),
                               slice_entry(2, 'opus', files=['harness/b.py'])],
                    findings=[finding('F1', 'high', 'harness/b.py:4')]),
            escaped=[], rules=self.rules)
        self.assertEqual([row['findings'] for row in rows], [0, 1])

    def test_the_routes_go_live_when_the_downgraded_rate_is_at_or_below_the_rest(self):
        rows = [dict(group='downgraded', points=1, rework=0),
                dict(group='strongest', points=1, rework=1)]
        verdict = calibration.verdict_routes(rows, ['SEEN-%03d' % n for n in range(10)],
                                             self.rules)
        self.assertEqual(verdict['state'], 'go_live')

    def test_the_routes_stay_in_shadow_when_the_downgraded_rate_is_worse(self):
        rows = [dict(group='downgraded', points=1, rework=2),
                dict(group='strongest', points=1, rework=1)]
        verdict = calibration.verdict_routes(rows, ['SEEN-%03d' % n for n in range(10)],
                                             self.rules)
        self.assertEqual(verdict['state'], 'stay_shadow')

    def test_no_downgraded_slice_is_not_measurable_rather_than_a_pass(self):
        rows = [dict(group='strongest', points=1, rework=0)]
        verdict = calibration.verdict_routes(rows, ['SEEN-%03d' % n for n in range(10)],
                                             self.rules)
        self.assertEqual(verdict['state'], 'stay_shadow')
        self.assertIn('no slice', verdict['reason'])


class EffectiveShadowTest(ProjectTest):
    """The one question a triage asks: which shadow am I in, and what put me there."""

    def setUp(self):
        super().setUp()
        self.rules = thresholds.load(self.root)

    def plant(self, ticket, day, **kwargs):
        plant(self.root, ticket, day, **kwargs)

    def test_the_threshold_alone_keeps_the_triage_in_shadow(self):
        answer = calibration.effective_shadow(self.root, self.rules)
        self.assertTrue(answer['shadow'])
        self.assertIn('triage_shadow', answer['reason'])

    def live(self):
        """The switch and the decision it names, which is what going live takes."""
        return dict(self.rules, review=dict(self.rules['review'], triage_shadow=False),
                    calibration=dict(self.rules['calibration'],
                                     went_live=dict(ticket='SEEN-601', record=4,
                                                    on='2026-11-01')))

    def test_with_the_threshold_off_and_ten_clean_tickets_the_triage_is_live(self):
        for day in range(1, 11):
            self.plant(f'SEEN-6{day:02d}', day)
        answer = calibration.effective_shadow(self.root, self.live())
        self.assertFalse(answer['shadow'])

    def test_an_escape_after_go_live_returns_the_triage_to_shadow(self):
        rules = self.live()
        for day in range(1, 11):
            self.plant(f'SEEN-6{day:02d}', day)
        self.plant('SEEN-620', 11, triage=['harness/skipped.py'],
                   findings=[finding('F1', 'blocking', 'harness/skipped.py:2')])
        answer = calibration.effective_shadow(self.root, rules)
        self.assertTrue(answer['shadow'])
        self.assertIn('SEEN-620', answer['reason'])


class FindingFileTest(unittest.TestCase):
    """A finding nobody can place is a silent pass in favour of the narrowing."""

    severities = ['low', 'medium', 'high', 'blocking']

    def test_a_blocking_finding_with_no_file_is_refused(self):
        with self.assertRaises(HarnessError) as raised:
            gates.check_findings([finding('F1', 'blocking')], self.severities)
        self.assertIn('file', str(raised.exception))

    def test_a_high_finding_with_no_file_is_refused(self):
        with self.assertRaises(HarnessError):
            gates.check_findings([finding('F1', 'high')], self.severities)

    def test_a_medium_finding_needs_no_file(self):
        gates.check_findings([finding('F1', 'medium')], self.severities)

    def test_a_blocking_finding_naming_its_file_is_accepted(self):
        gates.check_findings([finding('F1', 'blocking', 'harness/a.py:12')], self.severities)


class CalibrationRulesTest(ProjectTest):
    """The rule is fatal when half-written, like every other rule in the file."""

    def test_the_loader_demands_every_calibration_key(self):
        path = self.root / 'harness' / 'thresholds.toml'
        text = path.read_text()
        self.assertIn('[calibration]', text)
        path.write_text(text.replace('window = 10', ''))
        with self.assertRaises(HarnessError) as raised:
            thresholds.load(self.root)
        self.assertIn('calibration.window', str(raised.exception))




class ReportTest(CommandTest):
    """The evidence per ticket and per slice, with the rule printed beside it."""

    def setUp(self):
        super().setUp()
        self.rules = thresholds.load(self.root)

    def plant_window(self, count=10, **kwargs):
        for day in range(1, count + 1):
            plant(self.root, f'SEEN-7{day:02d}', day,
                  execution=[slice_entry(1, 'sonnet'), slice_entry(2, 'opus', files=['harness/b.py'])],
                  **kwargs)

    def report(self):
        written = self.run_harness('report', '--calibration')
        return ((self.root / written['report']).read_text(),
                json.loads((self.root / written['data']).read_text()))

    def test_the_report_states_a_verdict_for_the_triage_and_for_the_routes(self):
        self.plant_window()
        markdown, payload = self.report()
        self.assertEqual(payload['triage']['state'], 'go_live')
        self.assertIn(payload['routes']['state'], ('go_live', 'stay_shadow'))
        self.assertIn('The rule, recorded before the numbers', markdown)

    def test_the_report_names_the_tickets_it_excluded_and_why(self):
        self.plant_window()
        plant(self.root, 'SEEN-107', 1)
        markdown, payload = self.report()
        excluded = {entry['ticket']: entry['reason'] for entry in payload['excluded']}
        self.assertIn('SEEN-107', excluded)
        self.assertIn('SEEN-107', markdown)

    def test_the_report_shows_the_excluded_files_and_the_escapes_per_ticket(self):
        self.plant_window(triage=['harness/skipped.py'],
                          findings=[finding('F1', 'blocking', 'harness/skipped.py:2')])
        markdown, payload = self.report()
        self.assertEqual(payload['triage']['state'], 'stay_shadow')
        self.assertTrue(all(entry['escapes'] for entry in payload['tickets']))
        self.assertIn('harness/skipped.py', markdown)

    def test_the_report_shows_each_slice_s_route_against_what_followed(self):
        self.plant_window(findings=[finding('F1', 'high', 'harness/b.py:7')])
        markdown, payload = self.report()
        rows = [row for row in payload['slices'] if row['ticket'] == 'SEEN-701']
        self.assertEqual([row['model'] for row in rows], ['sonnet', 'opus'])
        self.assertEqual([row['findings'] for row in rows], [0, 1])
        self.assertIn('| sonnet at medium |', markdown)

    def test_below_the_window_the_report_concludes_nothing(self):
        self.plant_window(count=3)
        markdown, payload = self.report()
        self.assertEqual(payload['triage']['state'], 'stay_shadow')
        self.assertIn('3 of 10', payload['triage']['reason'])

    def test_the_weekly_report_names_the_escape_that_returned_the_triage_to_shadow(self):
        """F2 of the first review: the only test for this line exercised the branch

        that cannot see an escape, so deleting the escape branch left it green.
        """
        path = self.root / 'harness' / 'thresholds.toml'
        text = path.read_text().replace('triage_shadow = true', 'triage_shadow = false')
        path.write_text(text.replace(
            'went_live = {}',
            'went_live = { ticket = "SEEN-701", record = 4, on = "2026-11-01" }'))
        self.plant_window(triage=['harness/skipped.py'],
                          findings=[finding('F1', 'blocking', 'harness/skipped.py:2')])
        written = self.run_harness('report', '--week', '--date', '2026-10-05')
        markdown = (self.root / written['report']).read_text()
        payload = json.loads((self.root / written['data']).read_text())
        self.assertIn('The review triage', markdown)
        self.assertIn('Returned to shadow by the calibration rule', markdown)
        self.assertIn('SEEN-701', markdown)
        self.assertTrue(payload['review_triage_shadow']['shadow'])
        self.assertEqual(payload['review_triage_shadow']['source'], 'calibration')

    def test_the_weekly_report_says_when_the_threshold_alone_holds_the_shadow(self):
        self.plant_window()
        written = self.run_harness('report', '--week', '--date', '2026-10-05')
        markdown = (self.root / written['report']).read_text()
        self.assertIn('triage_shadow', markdown)


class TriageShadowTest(TriageTest):
    """The one thing that happens without a person: the return to shadow."""

    def loosen(self, ticket='SEEN-801', record=4):
        """Go live the way the founder must: the switch and the decision it names."""
        path = self.root / 'harness' / 'thresholds.toml'
        text = path.read_text().replace('triage_shadow = true', 'triage_shadow = false')
        path.write_text(text.replace(
            'went_live = {}',
            f'went_live = {{ ticket = "{ticket}", record = {record}, on = "2026-11-01" }}'))

    def plant_window(self, count=10, **kwargs):
        for day in range(1, count + 1):
            plant(self.root, f'SEEN-8{day:02d}', day, **kwargs)
        self.git('add', '-A')
        self.git('-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'chore: window')

    def test_with_the_threshold_off_and_a_clean_window_the_triage_narrows(self):
        self.loosen()
        self.plant_window()
        self.reach_review()
        record = self.triage()
        self.assertFalse(record['data']['shadow'])
        self.assertEqual(record['data']['shadow_source'], 'calibration')

    def test_an_escape_in_the_window_puts_the_triage_back_in_shadow(self):
        self.loosen()
        self.plant_window(triage=['harness/skipped.py'],
                          findings=[finding('F1', 'blocking', 'harness/skipped.py:2')])
        self.reach_review()
        record = self.triage()
        self.assertTrue(record['data']['shadow'])
        self.assertEqual(record['data']['shadow_source'], 'calibration')
        self.assertIn('SEEN-801', record['data']['shadow_reason'])

    def test_the_threshold_alone_still_says_why_the_triage_is_in_shadow(self):
        self.reach_review()
        record = self.triage()
        self.assertTrue(record['data']['shadow'])
        self.assertEqual(record['data']['shadow_source'], 'threshold')
        self.assertIn('triage_shadow', record['data']['shadow_reason'])
class UnmetCriteriaTest(CommandTest):
    """F3 of the first review: the flag the second escape kind is read from."""

    def reach_tdd(self):
        from harness.tests.test_lifecycle import clarify_evidence, solution_evidence
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())

    def test_a_return_records_the_criteria_it_names(self):
        self.reach_tdd()
        record = self.run_harness('return', self.ticket_id, '--to', 'clarify',
                                  '--actor', 'claude:implementer',
                                  '--reason', 'Criterion 2 has nothing behind it',
                                  '--unmet', '2', '--unmet', '2', '--unmet', '1')
        self.assertEqual(record['data']['unmet_criteria'], [1, 2])

    def test_a_return_that_names_none_records_an_empty_list(self):
        self.reach_tdd()
        record = self.run_harness('return', self.ticket_id, '--to', 'clarify',
                                  '--actor', 'claude:implementer', '--reason', 'Replanning')
        self.assertEqual(record['data']['unmet_criteria'], [])

    def test_a_criterion_number_below_one_is_refused(self):
        self.reach_tdd()
        with self.assertRaisesRegex(HarnessError, 'counting from 1'):
            self.run_harness('return', self.ticket_id, '--to', 'clarify',
                             '--actor', 'claude:implementer', '--reason', 'Wrong number',
                             '--unmet', '0')


class TriageReturnTest(TriageTest):
    """The triage's own return names what it could see no evidence for.

    Without the numbers on it, F4's rule would read every one of them as a
    review that forgot the flag, which is the opposite of what happened: the
    triage caught the criterion itself, before any model read the diff.
    """

    def setUp(self):
        super().setUp()
        from harness import jev
        from harness.tests.test_triage import triage_stub
        jev.TRANSPORT = triage_stub(criterion=0.1)

    def test_the_triage_return_carries_the_unevidenced_criteria_by_number(self):
        self.reach_review()
        with self.assertRaises(HarnessError):
            self.triage()
        returned = self.records()[-1]
        self.assertEqual(returned['kind'], 'return')
        self.assertEqual(returned['data']['unmet_criteria'], [1])

    def test_the_calibration_reads_it_as_neither_an_escape_nor_unattributable(self):
        self.reach_review()
        with self.assertRaises(HarnessError):
            self.triage()
        found = calibration.escapes(self.records())
        self.assertEqual(found['escapes'], [])
        self.assertEqual(found['unattributable'], [])


class SecondReviewTest(ProjectTest):
    """The four findings of the second review, at note 25."""

    def setUp(self):
        super().setUp()
        self.rules = thresholds.load(self.root)

    def test_a_finding_is_charged_to_a_slice_whose_files_sit_in_a_dot_directory(self):
        """F1: the same character-stripping, one function below the one that was fixed."""
        rows = calibration.slice_rows(
            'SEEN-900',
            journal(execution=[slice_entry(1, 'sonnet', files=['.claude/agents/x.md']),
                               slice_entry(2, 'opus', files=['harness/b.py'])],
                    findings=[finding('F1', 'blocking', '.claude/agents/x.md:84')]),
            escaped=[], rules=self.rules)
        self.assertEqual([row['findings'] for row in rows], [1, 0])

    def test_a_slice_naming_a_directory_still_covers_the_files_under_it(self):
        rows = calibration.slice_rows(
            'SEEN-900',
            journal(execution=[slice_entry(1, 'sonnet', files=['.codex/'])],
                    findings=[finding('F1', 'high', '.codex/agents/x.toml:3')]),
            escaped=[], rules=self.rules)
        self.assertEqual(rows[0]['findings'], 1)

    def test_a_finding_that_returned_a_ticket_is_read_from_the_return(self):
        """F2: findings read only from the advance meant a returning round vanished."""
        records = journal(triage=['harness/skipped.py'],
                          returned_findings=[finding('F1', 'blocking', 'harness/skipped.py:2')])
        found = calibration.escapes(records)
        self.assertEqual([entry['kind'] for entry in found['escapes']],
                         ['finding_in_excluded_file'])

    def test_a_finding_carried_forward_into_the_passing_record_is_one_finding(self):
        carried = finding('F1', 'blocking', 'harness/skipped.py:2')
        records = journal(triage=['harness/skipped.py'], returned_findings=[carried],
                          findings=[dict(carried, status='resolved', resolution='Fixed')])
        self.assertEqual(len(calibration.latest_findings(records)), 1)
        self.assertEqual(len(calibration.escapes(records)['escapes']), 1)

    def test_two_findings_sharing_an_id_but_not_a_file_are_two_findings(self):
        records = journal(triage=['harness/skipped.py'],
                          returned_findings=[finding('F1', 'blocking', 'harness/skipped.py:2')],
                          findings=[finding('F1', 'high', 'harness/other.py:9')])
        self.assertEqual(len(calibration.latest_findings(records)), 2)


class GoLiveDecisionTest(ProjectTest):
    """F3: going live must name the record the decision is in, or it is an edit."""

    def setUp(self):
        super().setUp()
        self.rules = thresholds.load(self.root)

    def live(self, **went_live):
        return dict(self.rules,
                    review=dict(self.rules['review'], triage_shadow=False),
                    calibration=dict(self.rules['calibration'], went_live=went_live))

    def test_the_threshold_off_with_no_decision_named_stays_in_shadow(self):
        answer = calibration.effective_shadow(self.root, self.live())
        self.assertTrue(answer['shadow'])
        self.assertIn('went_live', answer['reason'])

    def test_a_decision_naming_a_record_that_does_not_exist_stays_in_shadow(self):
        answer = calibration.effective_shadow(self.root,
                                              self.live(ticket='SEEN-900', record=4, on='2026-11-01'))
        self.assertTrue(answer['shadow'])
        self.assertIn('SEEN-900', answer['reason'])

    def test_a_decision_naming_a_record_that_exists_goes_live(self):
        plant(self.root, 'SEEN-900', 1)
        answer = calibration.effective_shadow(self.root,
                                              self.live(ticket='SEEN-900', record=4, on='2026-11-01'))
        self.assertFalse(answer['shadow'])
        self.assertIn('SEEN-900', answer['reason'])

    def test_doctor_reports_a_switch_flipped_with_no_decision_on_the_record(self):
        path = self.root / 'harness' / 'thresholds.toml'
        path.write_text(path.read_text().replace('triage_shadow = true', 'triage_shadow = false'))
        from harness import doctor
        from harness.repository import Repository
        found = doctor.report(Repository(self.root), thresholds.load(self.root))
        self.assertFalse(found['ok'])
        self.assertTrue(any('went_live' in problem for problem in found['problems']))


class ReturningFindingsTest(CommandTest):
    """A review that returns a ticket records what it found, or the window cannot read it."""

    def reach_tdd(self):
        from harness.tests.test_lifecycle import clarify_evidence, solution_evidence
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())

    def send_back(self, findings):
        relative = f'.harness-drafts/{self.ticket_id}-findings.json'
        self.write(relative, json.dumps(findings))
        return self.run_harness('return', self.ticket_id, '--to', 'clarify',
                                '--actor', 'claude:reviewer', '--reason', 'A defect',
                                '--findings', relative)

    def test_the_return_carries_the_findings_it_names(self):
        self.reach_tdd()
        record = self.send_back([dict(finding('F1', 'blocking', 'harness/a.py:2'),
                                      status='open', resolution='')])
        self.assertEqual([entry['id'] for entry in record['data']['findings']], ['F1'])

    def test_a_returning_finding_needs_no_resolution(self):
        self.reach_tdd()
        record = self.send_back([dict(id='F1', severity='medium', claim='It breaks',
                                      failure_scenario='Like this', status='open',
                                      resolution='')])
        self.assertEqual(record['data']['findings'][0]['status'], 'open')

    def test_a_returning_blocking_finding_still_has_to_name_its_file(self):
        self.reach_tdd()
        with self.assertRaisesRegex(HarnessError, 'names no file'):
            self.send_back([dict(id='F1', severity='blocking', claim='It breaks',
                                 failure_scenario='Like this', status='open', resolution='')])

    def test_a_return_with_no_findings_file_records_an_empty_list(self):
        self.reach_tdd()
        record = self.run_harness('return', self.ticket_id, '--to', 'clarify',
                                  '--actor', 'claude:implementer', '--reason', 'Replanning')
        self.assertEqual(record['data']['findings'], [])


class ThirdReviewTest(ProjectTest):
    """The findings of the third review, at note 36."""

    def setUp(self):
        super().setUp()
        self.rules = thresholds.load(self.root)

    def rows(self, count, unattributable_on=()):
        return [dict(ticket=f'SEEN-A{index:02d}', escapes=[],
                     unattributable=[dict(kind='return', reason='nothing can say')]
                     if index in unattributable_on else [])
                for index in range(count)]

    def test_a_window_carrying_anything_unattributable_cannot_state_go_live(self):
        """F1: counted neither way must mean the verdict waits, not that it passes."""
        verdict = calibration.verdict_triage(self.rows(10, unattributable_on=[3]), self.rules)
        self.assertEqual(verdict['state'], 'stay_shadow')
        self.assertIn('SEEN-A03', verdict['reason'])

    def test_a_clean_window_still_states_go_live(self):
        self.assertEqual(calibration.verdict_triage(self.rows(10), self.rules)['state'],
                         'go_live')

    def test_a_ticket_whose_receipt_was_voided_is_not_delivered(self):
        """F3: reopen voids the receipt, so the ticket is being worked again."""
        records = journal(ticket='SEEN-A10', day=1)
        records.append(record(len(records) + 1, 'reopen', 'deliver', day=1, minute=40,
                              ticket='SEEN-A10', voided_receipt=len(records),
                              voided_commit='b' * 40, reason='A defect was found'))
        self.assertIsNone(calibration.delivered_at(records))

    def test_the_routes_report_the_window_their_rates_came_from(self):
        """F4: a founder auditing the decision must recompute over the same list."""
        tickets = [f'SEEN-A{index:02d}' for index in range(13)]
        verdict = calibration.verdict_routes([dict(group='downgraded', points=1, rework=0)],
                                             tickets, self.rules)
        self.assertEqual(len(verdict['window']), self.rules['calibration']['window'])
        self.assertEqual(verdict['window'][0], 'SEEN-A03')

    def test_a_repeated_finding_is_charged_to_the_round_that_first_raised_it(self):
        """F5: the earliest round's triage is the one that would have dropped the file."""
        raised = finding('F1', 'blocking', 'harness/skipped.py:2')
        records = journal(triage=['harness/skipped.py'], returned_findings=[raised])
        # The second triage, the one before the passing round, excludes nothing.
        records[-3]['data']['would_exclude'] = []
        records[-2]['data']['evidence']['findings'] = [dict(raised, status='resolved',
                                                            resolution='Fixed')]
        found = calibration.escapes(records)
        self.assertEqual([entry['kind'] for entry in found['escapes']],
                         ['finding_in_excluded_file'])

    def test_a_damaged_journal_elsewhere_does_not_refuse_this_ticket(self):
        """F6: a stray file in one journal must not block every other review."""
        plant(self.root, 'SEEN-A20', 1)
        (self.root / 'docs' / 'harness' / 'history' / 'SEEN-A21').mkdir(parents=True)
        (self.root / 'docs' / 'harness' / 'history' / 'SEEN-A21' / '.DS_Store').write_text('x')
        section = calibration.evidence(self.root, self.rules)
        self.assertEqual([entry['ticket'] for entry in section['tickets']], ['SEEN-A20'])
        self.assertTrue(any(entry['ticket'] == 'SEEN-A21' and 'journal' in entry['reason']
                            for entry in section['excluded']))


class ReviewReturnDeclarationTest(CommandTest):
    """F1: a return from review says what it found, or says it found nothing."""

    def reach_tdd(self):
        from harness.tests.test_lifecycle import clarify_evidence, solution_evidence
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())

    def send_back(self, *extra, stage='review'):
        from harness import journal as journal_module
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        records = journal_module.read(folder)
        if stage == 'review':
            journal_module.append(folder, records, kind='advance', stage='tdd', attempt=1,
                                  actor='claude:implementer', head=self.git('rev-parse', 'HEAD'),
                                  ticket=self.ticket_id,
                                  data=dict(from_stage='tdd', to_stage='review', evidence={},
                                            decisions=[]))
        return self.run_harness('return', self.ticket_id, '--to', 'tdd',
                                '--actor', 'claude:reviewer', '--reason', 'Sent back', *extra)

    def test_a_return_from_review_declaring_nothing_is_refused(self):
        self.reach_tdd()
        with self.assertRaisesRegex(HarnessError, '--no-findings'):
            self.send_back()

    def test_a_return_from_review_that_declares_no_findings_is_accepted(self):
        self.reach_tdd()
        record = self.send_back('--no-findings')
        self.assertTrue(record['data']['no_findings'])

    def test_a_declared_empty_return_is_neither_an_escape_nor_unattributable(self):
        self.reach_tdd()
        self.send_back('--no-findings')
        from harness import journal as journal_module
        records = journal_module.read(self.root / 'docs' / 'harness' / 'history' / self.ticket_id)
        found = calibration.escapes(records)
        self.assertEqual(found['unattributable'], [])

    def test_a_return_from_an_earlier_stage_declares_nothing(self):
        self.reach_tdd()
        record = self.run_harness('return', self.ticket_id, '--to', 'clarify',
                                  '--actor', 'claude:implementer', '--reason', 'Replanning')
        self.assertEqual(record['data']['findings'], [])


class FourthReviewTest(ProjectTest):
    """The findings of the fourth review, at note 46."""

    def setUp(self):
        super().setUp()
        self.rules = thresholds.load(self.root)

    def placed(self, reference, would_exclude=('harness/skipped.py',), files=None):
        records = journal(triage=would_exclude,
                          findings=[finding('F1', 'blocking', reference)])
        for entry in records:
            if entry['kind'] == 'triage':
                entry['data']['files'] = [dict(path=path) for path in
                                          (files if files is not None
                                           else ['harness/skipped.py', 'harness/read.py'])]
        return calibration.escapes(records)

    def test_a_line_range_still_finds_the_file(self):
        """F1: a reviewer writes a hunk, and the tail is not all digits."""
        found = self.placed('harness/skipped.py:12-20')
        self.assertEqual([entry['kind'] for entry in found['escapes']],
                         ['finding_in_excluded_file'])

    def test_a_line_and_column_still_finds_the_file(self):
        found = self.placed('harness/skipped.py:58:5')
        self.assertEqual(len(found['escapes']), 1)

    def test_a_path_the_triage_never_saw_is_unattributable(self):
        """Not in would_exclude and not in the diff: placed nowhere, not placed outside."""
        found = self.placed('harness/typo.py:3')
        self.assertEqual(found['escapes'], [])
        self.assertEqual([entry['id'] for entry in found['unattributable']], ['F1'])

    def test_a_file_the_triage_read_is_neither(self):
        found = self.placed('harness/read.py:3')
        self.assertEqual(found['escapes'], [])
        self.assertEqual(found['unattributable'], [])

    def test_evidence_nobody_can_place_returns_a_live_triage_to_shadow(self):
        """F2: the triage reads the verdict, which is what four documents say."""
        rules = dict(self.rules, review=dict(self.rules['review'], triage_shadow=False),
                     calibration=dict(self.rules['calibration'],
                                      went_live=dict(ticket='SEEN-B01', record=4,
                                                     on='2026-11-01')))
        for day in range(1, 11):
            plant(self.root, f'SEEN-B{day:02d}', day)
        self.assertFalse(calibration.effective_shadow(self.root, rules)['shadow'])
        # One round that returned a ticket and declared nothing at all.
        plant(self.root, 'SEEN-B20', 11, returns=[[]], answers=[(1, 'A criterion', True)])
        answer = calibration.effective_shadow(self.root, rules)
        self.assertTrue(answer['shadow'])
        self.assertIn('could not be placed', answer['reason'])

    def test_a_short_window_does_not_return_a_live_triage_to_shadow(self):
        """A window that is not full is a reason to conclude nothing, not to override."""
        rules = dict(self.rules, review=dict(self.rules['review'], triage_shadow=False),
                     calibration=dict(self.rules['calibration'],
                                      went_live=dict(ticket='SEEN-B01', record=4,
                                                     on='2026-11-01')))
        plant(self.root, 'SEEN-B01', 1)
        self.assertFalse(calibration.effective_shadow(self.root, rules)['shadow'])

    def test_the_report_names_every_round_that_declared_it_found_nothing(self):
        """F3: a declaration is a claim by its author, so the report says who made it."""
        plant(self.root, 'SEEN-B30', 1, declared_empty=True)
        section = calibration.evidence(self.root, self.rules)
        entry = next(row for row in section['tickets'] if row['ticket'] == 'SEEN-B30')
        self.assertEqual([claim['actor'] for claim in entry['declared_empty']],
                         ['claude:implementer'])
        markdown = report.render_calibration(section, self.rules)
        self.assertIn('declared it found nothing', markdown)

    def test_the_printed_go_live_instruction_names_both_lines(self):
        """F4: the one-line instruction must not be able to come back quietly."""
        rows = [dict(ticket=f'SEEN-B{index:02d}', escapes=[], unattributable=[])
                for index in range(10)]
        reason = calibration.verdict_triage(rows, self.rules)['reason']
        self.assertIn('triage_shadow', reason)
        self.assertIn('went_live', reason)
        self.assertIn('triage_shadow', self.rules['calibration']['triage_rule'])
        self.assertIn('went_live', self.rules['calibration']['triage_rule'])
class FifthReviewTest(ProjectTest):
    """The findings of the fifth review, at note 56."""

    def setUp(self):
        super().setUp()
        self.rules = thresholds.load(self.root)

    def unclaimed(self):
        """A ticket whose blocking finding lands in a file no slice named."""
        return journal(execution=[slice_entry(1, 'sonnet', files=['harness/a.py']),
                                  slice_entry(2, 'opus', files=['harness/b.py'])],
                       findings=[finding('F1', 'blocking', 'harness/unclaimed.py:12')])

    def test_a_finding_no_slice_can_be_compared_with_is_charged_to_every_slice(self):
        """F1: nothing says which slice caused it, which is what route_rule already
        says of a return and of an escaped defect."""
        rows = calibration.slice_rows('SEEN-C01', self.unclaimed(), escaped=[],
                                      rules=self.rules)
        self.assertEqual([row['unchargeable'] for row in rows], [1, 1])
        self.assertEqual([row['rework'] for row in rows], [1, 1])

    def test_a_finding_a_slice_owns_is_charged_to_that_slice_alone(self):
        rows = calibration.slice_rows(
            'SEEN-C01',
            journal(execution=[slice_entry(1, 'sonnet', files=['harness/a.py']),
                               slice_entry(2, 'opus', files=['harness/b.py'])],
                    findings=[finding('F1', 'blocking', 'harness/b.py:4')]),
            escaped=[], rules=self.rules)
        self.assertEqual([row['findings'] for row in rows], [0, 1])
        self.assertEqual([row['unchargeable'] for row in rows], [0, 0])

    def test_the_routes_cannot_state_go_live_while_a_finding_could_not_be_charged(self):
        rows = [dict(group='downgraded', points=1, rework=1, unchargeable=1, ticket='SEEN-C01'),
                dict(group='strongest', points=1, rework=1, unchargeable=1, ticket='SEEN-C01')]
        verdict = calibration.verdict_routes(rows, [f'SEEN-C{n:02d}' for n in range(10)],
                                             self.rules)
        self.assertEqual(verdict['state'], 'stay_shadow')
        self.assertIn('could not be charged', verdict['reason'])

    def test_the_routes_still_state_go_live_when_every_finding_was_charged(self):
        rows = [dict(group='downgraded', points=1, rework=0, unchargeable=0, ticket='SEEN-C01'),
                dict(group='strongest', points=1, rework=1, unchargeable=0, ticket='SEEN-C02')]
        verdict = calibration.verdict_routes(rows, [f'SEEN-C{n:02d}' for n in range(10)],
                                             self.rules)
        self.assertEqual(verdict['state'], 'go_live')

    def test_the_report_names_the_findings_no_slice_could_be_compared_with(self):
        plant(self.root, 'SEEN-C10', 1,
              execution=[slice_entry(1, 'sonnet', files=['harness/a.py'])],
              findings=[finding('F1', 'blocking', 'harness/unclaimed.py:12')])
        section = calibration.evidence(self.root, self.rules)
        markdown = report.render_calibration(section, self.rules)
        self.assertIn('could not be charged to a slice', markdown)
        self.assertIn('harness/unclaimed.py', markdown)

    def test_the_weekly_report_reads_a_returning_round_s_findings_too(self):
        """F2: two committed reports must not state different findings for one ticket."""
        from harness import kpi
        records = journal(returned_findings=[finding('F1', 'high', 'harness/a.py:2')])
        self.assertEqual(kpi.findings(records)['by_severity'], {'high': 1})

    def test_a_triage_that_recorded_no_files_places_an_unknown_path_nowhere(self):
        """F3: the fallback restored the merge the fourth review removed."""
        records = journal(triage=['harness/skipped.py'],
                          findings=[finding('F1', 'blocking', 'harness/nowhere.py:3')])
        for entry in records:
            if entry['kind'] == 'triage':
                entry['data']['files'] = []
        found = calibration.escapes(records)
        self.assertEqual(found['escapes'], [])
        self.assertEqual([entry['id'] for entry in found['unattributable']], ['F1'])

if __name__ == '__main__':
    unittest.main()
