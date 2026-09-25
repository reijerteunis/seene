"""The context budget, and the measurement that decides whether it paid.

Three MCP servers put three sets of tool schemas into every session before a
ticket is read. The budget says what that buys; the measurement says whether it
was worth it, against a baseline captured before any of them existed. The rule
for reading the number is written before the number exists, because a rule
chosen after seeing the figure is not a rule.
"""

import json
import unittest

from harness import context, cost, kpi, thresholds
from harness.tests.helpers import PROJECT, ProjectTest

BASELINE = {'totals': {'points': 27, 'output_tokens_per_point': 40581.5,
                       'tool_calls_per_point': 18.5}}


class BudgetRulesTest(unittest.TestCase):

    def setUp(self):
        self.rules = thresholds.load(PROJECT)['context']

    def test_the_three_rules_are_written_down(self):
        """A rule in a prompt is not a rule."""
        written = ' '.join(self.rules['rules']).lower()

        self.assertIn('one tool call per question', written)
        self.assertIn('symbol', written)
        self.assertIn('repository-wide read', written)

    def test_the_decision_rule_is_recorded_before_the_numbers_exist(self):
        self.assertIn('graphify', self.rules['decision_rule'].lower())

    def test_the_moment_the_tools_landed_decides_which_tickets_qualify(self):
        """A date would count the tickets that installed them, which it must not."""
        self.assertEqual(self.rules['tools_available_from'],
                         '2026-09-24T06:15:10.769645+00:00')

    def test_a_ticket_that_installed_a_tool_does_not_count_towards_it(self):
        since = '2026-09-24T06:15:10.769645+00:00'
        installing = dict(ticket='SEEN-098', points=2, output_tokens=1, tool_calls=1,
                          started='2026-09-24T06:00:15.192701+00:00')
        after = dict(ticket='SEEN-199', points=2, output_tokens=1, tool_calls=1,
                     started='2026-09-24T07:00:00.000000+00:00')

        counted = context.qualifying([installing, after], since)

        self.assertEqual([entry['ticket'] for entry in counted], ['SEEN-199'])

    def test_five_tickets_is_the_bar_the_ticket_set(self):
        self.assertEqual(self.rules['minimum_tickets'], 5)


class ToolCallsTest(ProjectTest):

    def log(self, entries):
        directory = cost.log_directory(self.root)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'session.jsonl').write_text(
            '\n'.join(json.dumps(entry) for entry in entries) + '\n')
        self.addCleanup(lambda: (directory / 'session.jsonl').unlink(missing_ok=True))

    def entry(self, stamp, blocks):
        return dict(timestamp=stamp, message=dict(role='assistant', content=blocks))

    def test_tool_use_blocks_inside_the_window_are_counted(self):
        self.log([self.entry('2026-09-24T10:00:00Z', [{'type': 'tool_use', 'name': 'Bash'},
                                                      {'type': 'text', 'text': 'hello'}]),
                  self.entry('2026-09-24T10:05:00Z', [{'type': 'tool_use', 'name': 'Read'}])])

        counted = cost.tool_calls_between(self.root, '2026-09-24T09:00:00Z',
                                          '2026-09-24T11:00:00Z')

        self.assertEqual(counted, 2)

    def test_blocks_outside_the_window_are_not(self):
        self.log([self.entry('2026-09-24T08:00:00Z', [{'type': 'tool_use', 'name': 'Bash'}]),
                  self.entry('2026-09-24T10:00:00Z', [{'type': 'tool_use', 'name': 'Read'}])])

        counted = cost.tool_calls_between(self.root, '2026-09-24T09:00:00Z',
                                          '2026-09-24T11:00:00Z')

        self.assertEqual(counted, 1)

    def test_no_logs_is_null_rather_than_zero(self):
        """Zero is a claim that nothing happened."""
        self.assertIsNone(cost.tool_calls_between(
            self.root / 'nowhere', '2026-09-24T09:00:00Z', '2026-09-24T11:00:00Z'))


class CachedFiguresTest(unittest.TestCase):
    """What the kpi.json beside a receipt claims to be."""

    def test_delivery_does_not_claim_to_cache_what_it_cannot_compute(self):
        """SEEN-099's rule, which SEEN-107 narrowed by one figure rather than broke.

        Points and the ticket's own tokens are still null at delivery and still
        filled by the report. The reviewer's tokens are the one exception, because
        criterion 5 of SEEN-107 names kpi.json and delivery is its only writer;
        they are null where there are no logs, so the file still reads the same on
        a machine that has none.
        """
        # Comment markers and wrapping removed first, so rewrapping the paragraph
        # does not fail a test about what it says.
        source = (PROJECT / 'harness' / 'delivery.py').read_text()
        prose = ' '.join(line.lstrip('# ') if line.lstrip().startswith('#') else line
                         for line in source.splitlines())

        self.assertIn("Points and the ticket's own tokens stay null here on purpose", prose)
        self.assertIn('harness report fills both', prose)

    def test_the_one_figure_delivery_reads_is_null_when_there_is_nothing_to_read(self):
        figures = kpi.measure([], 'SEEN-001', reviewer_tokens=None)
        self.assertIsNone(figures['review_triage'])


class ComparisonTest(unittest.TestCase):
    """What the report says about the figures, and when it refuses to say it."""

    def qualifying(self, count):
        return [dict(ticket=f'SEEN-{200 + n}', points=2, output_tokens=60000, tool_calls=20,
                     started='2026-09-25T09:00:00Z') for n in range(count)]

    def test_the_comparison_carries_both_rows_and_the_baseline(self):
        section = context.compare(self.qualifying(5), BASELINE, minimum=5)

        self.assertEqual(section['output_tokens_per_point'], 30000.0)
        self.assertEqual(section['tool_calls_per_point'], 10.0)
        self.assertEqual(section['baseline_output_tokens_per_point'], 40581.5)

    def test_below_the_baseline_the_tools_stay(self):
        section = context.compare(self.qualifying(5), BASELINE, minimum=5)

        self.assertIn('keep', section['conclusion'].lower())

    def test_above_the_baseline_graphify_goes_first(self):
        expensive = [dict(ticket='SEEN-300', points=1, output_tokens=90000, tool_calls=40,
                          started='2026-09-25T09:00:00Z')] * 5

        section = context.compare(expensive, BASELINE, minimum=5)

        self.assertIn('graphify', section['conclusion'].lower())

    def test_it_carries_output_tokens_per_slice_beside_per_point(self):
        tickets = [dict(ticket=f'SEEN-{200 + n}', points=2, output_tokens=60000, tool_calls=20,
                        slices=dict(planned=2, proven=2), started='2026-09-25T09:00:00Z')
                   for n in range(5)]

        section = context.compare(tickets, BASELINE, minimum=5)

        self.assertEqual(section['output_tokens_per_slice'], 30000.0)

    def test_a_report_of_tickets_with_no_slices_says_so_rather_than_dividing(self):
        section = context.compare(self.qualifying(5), BASELINE, minimum=5)

        self.assertIsNone(section['output_tokens_per_slice'])

    def test_the_rendered_table_shows_the_slice_row_beside_the_point_row(self):
        from harness import report, thresholds
        from harness.tests.helpers import PROJECT
        tickets = [dict(ticket='SEEN-200', points=2, output_tokens=60000, tool_calls=20,
                        slices=dict(planned=2, proven=2), started='2026-09-25T09:00:00Z')] * 5

        section = context.compare(tickets, BASELINE, minimum=5)
        lines = report.render_context(section, thresholds.load(PROJECT)['context'])

        table = '\n'.join(lines)
        self.assertIn('Output tokens per point', table)
        self.assertIn('Output tokens per slice', table)

    def with_agents(self, count, both=True):
        return [dict(ticket=f'SEEN-{300 + n}', points=2, output_tokens=30000, tool_calls=10,
                     started='2026-09-25T09:00:00Z',
                     subagents=dict(briefs=1, agents=['seen-scout'], review='subagent', both=both))
                for n in range(count)]

    def test_the_tickets_worked_with_the_agents_are_divided_on_their_own(self):
        section = context.compare(self.qualifying(4) + self.with_agents(1), BASELINE, minimum=5)

        self.assertEqual(section['tickets_with_agents'], 1)
        self.assertEqual(section['output_tokens_per_point_with_agents'], 15000.0)

    def test_a_report_with_no_such_ticket_says_nothing_rather_than_zero(self):
        section = context.compare(self.qualifying(5), BASELINE, minimum=5)

        self.assertEqual(section['tickets_with_agents'], 0)
        self.assertIsNone(section['output_tokens_per_point_with_agents'])

    def test_a_ticket_that_used_one_agent_and_not_the_other_does_not_count(self):
        section = context.compare(self.with_agents(3, both=False), BASELINE, minimum=5)

        self.assertEqual(section['tickets_with_agents'], 0)

    def test_the_ticket_that_built_the_agents_is_not_counted_as_worked_with_them(self):
        """G4: SEEN-098's own rule, applied to the agents this time."""
        built_them = self.with_agents(1)
        built_them[0]['started'] = '2026-09-24T09:00:00Z'

        section = context.compare(built_them + self.with_agents(1), BASELINE, minimum=5,
                                  agents_from='2026-09-24T12:18:27Z')

        self.assertEqual(section['tickets_with_agents'], 1)

    def test_the_row_names_the_tickets_it_counted(self):
        section = context.compare(self.with_agents(2), BASELINE, minimum=5)

        self.assertEqual(section['tickets_named_with_agents'], ['SEEN-300', 'SEEN-301'])

    def test_the_rendered_table_names_the_scout_and_the_reviewer(self):
        from harness import report, thresholds
        from harness.tests.helpers import PROJECT

        section = context.compare(self.with_agents(5), BASELINE, minimum=5)
        table = '\n'.join(report.render_context(section, thresholds.load(PROJECT)['context']))

        self.assertIn('scout and the reviewer', table)
        self.assertIn('15000.0', table)

    def test_too_few_tickets_concludes_nothing_and_says_so(self):
        """Two numbers divided is not evidence when there are two tickets."""
        section = context.compare(self.qualifying(2), BASELINE, minimum=5)

        self.assertIsNone(section['conclusion'])
        self.assertIn('2 of 5', section['not_measurable'])

    def test_a_ticket_with_no_token_count_does_not_qualify(self):
        blind = self.qualifying(5)
        blind[0]['output_tokens'] = None

        section = context.compare(blind, BASELINE, minimum=5)

        self.assertIn('4 of 5', section['not_measurable'])


class OverlapTest(unittest.TestCase):
    """One question with two right addressees is one tool too many."""

    def graph_record(self, ticket, tool, about):
        return dict(ticket=ticket, kind='note',
                    data=dict(source=tool, mode='explain', command=[tool, 'x', about]))

    def test_the_same_subject_asked_of_two_tools_is_named(self):
        found = context.overlaps([self.graph_record('SEEN-001', 'codegraph', 'the policy gate'),
                                  self.graph_record('SEEN-001', 'repowise', 'the policy gate')])

        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['subject'], 'the policy gate')
        self.assertEqual(sorted(found[0]['tools']), ['codegraph', 'repowise'])

    def test_the_same_subject_asked_twice_of_one_tool_is_not(self):
        """Asking again is not redundancy between tools."""
        found = context.overlaps([self.graph_record('SEEN-001', 'codegraph', 'the policy gate'),
                                  self.graph_record('SEEN-001', 'codegraph', 'the policy gate')])

        self.assertEqual(found, [])

    def test_two_tools_on_different_tickets_are_not_one_overlap(self):
        found = context.overlaps([self.graph_record('SEEN-001', 'codegraph', 'the gate'),
                                  self.graph_record('SEEN-002', 'repowise', 'the gate')])

        self.assertEqual(found, [])


if __name__ == '__main__':
    unittest.main()


class CostPerPointByModelTest(unittest.TestCase):
    """What a point cost on each model, beside the tokens per point.

    The point of the route is that a cheaper model on the slices that can take
    one costs less per point than the strongest on everything. That claim is
    only worth making with the figure printed beside it, per model, with the
    date the prices were read.
    """

    def tickets(self):
        return [
            dict(ticket='SEEN-001', points=3, started='2026-09-25T00:00:00+00:00',
                 output_tokens=60000, tool_calls=40,
                 execution=[dict(position=1, points=2, model='opus', effort='high',
                                 ran_on_tier='opus', output_tokens=40000, cost_cents=300.0),
                            dict(position=2, points=1, model='opus', effort='low',
                                 ran_on_tier='haiku', output_tokens=20000, cost_cents=8.0)]),
            dict(ticket='SEEN-002', points=2, started='2026-09-25T00:00:00+00:00',
                 output_tokens=30000, tool_calls=20,
                 execution=[dict(position=1, points=2, model='sonnet', effort='medium',
                                 ran_on_tier='haiku', output_tokens=30000, cost_cents=12.0)]),
        ]

    def test_it_divides_each_model_s_cost_by_the_points_it_carried(self):
        from harness import context
        by_model = context.cost_by_model(self.tickets())
        self.assertEqual(by_model['opus'], dict(slices=1, points=2, priced_points=2,
                                                cost_cents=300, cost_per_point=150.0,
                                                output_tokens=40000))
        self.assertEqual(by_model['haiku']['points'], 3)
        self.assertEqual(by_model['haiku']['cost_per_point'], round(20.0 / 3, 2))

    def test_a_ticket_with_no_execution_contributes_nothing(self):
        from harness import context
        tickets = self.tickets() + [dict(ticket='SEEN-003', points=5, execution=None)]
        self.assertEqual(sorted(context.cost_by_model(tickets)), ['haiku', 'opus'])

    def test_it_groups_by_the_model_the_work_ran_on_not_the_one_it_was_routed_to(self):
        """In shadow those differ, and only one of them cost anything."""
        from harness import context
        by_model = context.cost_by_model(self.tickets())
        self.assertEqual(sorted(by_model), ['haiku', 'opus'])
        self.assertEqual(by_model['haiku']['slices'], 2)
        self.assertEqual(by_model['opus']['slices'], 1)

    def test_a_slice_nobody_can_say_ran_where_is_its_own_row(self):
        from harness import context
        tickets = [dict(ticket='SEEN-005', points=1, execution=[
            dict(position=1, points=1, model='opus', effort='high',
                 ran_on_tier=None, output_tokens=5000, cost_cents=None)])]
        self.assertEqual(list(context.cost_by_model(tickets)), ['unknown'])

    def test_a_partly_priced_row_divides_by_the_points_it_could_price(self):
        """F3: dividing a partial cost by every point understates the model.

        On SEEN-108's own figures opus read 103.8 cents per point where its
        priced slices gave 173.0, in the table that decides whether routing
        saves money.
        """
        from harness import context
        tickets = [dict(ticket='SEEN-006', points=5, execution=[
            dict(position=1, points=3, model='opus', effort='high', ran_on_tier='opus',
                 output_tokens=60000, cost_cents=519),
            dict(position=2, points=2, model='opus', effort='high', ran_on_tier='opus',
                 output_tokens=None, cost_cents=None)])]
        entry = context.cost_by_model(tickets)['opus']
        self.assertEqual(entry['points'], 5)
        self.assertEqual(entry['priced_points'], 3)
        self.assertEqual(entry['cost_per_point'], 173.0)

    def test_a_row_nothing_could_price_reports_no_cost_rather_than_zero(self):
        from harness import context
        tickets = [dict(ticket='SEEN-007', points=2, execution=[
            dict(position=1, points=2, model='opus', effort='high', ran_on_tier=None,
                 output_tokens=68043, cost_cents=None)])]
        entry = context.cost_by_model(tickets)['unknown']
        self.assertIsNone(entry['cost_cents'])
        self.assertEqual(entry['output_tokens'], 68043)

    def test_a_slice_with_no_cost_still_counts_its_points_and_says_so(self):
        from harness import context
        tickets = [dict(ticket='SEEN-004', points=1, execution=[
            dict(position=1, points=1, model='sonnet', effort='low', ran_on_tier='sonnet',
                 output_tokens=None, cost_cents=None)])]
        entry = context.cost_by_model(tickets)['sonnet']
        self.assertEqual(entry['points'], 1)
        self.assertIsNone(entry['cost_per_point'])

    def test_the_report_prints_the_row_and_the_date_the_prices_were_read(self):
        from harness import report as reporting, thresholds
        rules = thresholds.load(PROJECT)
        rendered = reporting.render_cost(context.cost_by_model(self.tickets()),
                                         rules['routing']['prices'])
        self.assertIn('opus', '\n'.join(rendered))
        self.assertIn(rules['routing']['prices']['priced_on'], '\n'.join(rendered))
        self.assertIn('EUR', '\n'.join(rendered))


class SprintReportCostTest(ProjectTest):
    """The cost table, from the command rather than from its helpers.

    F4 of SEEN-108's first review: every test of this section called
    context.cost_by_model and report.render_cost directly, so the two lines in
    write_report that populate the section were unguarded and could be deleted
    with all 751 tests still green.
    """

    def setUp(self):
        super().setUp()
        self.write('docs/harness/reports/context-tools-baseline.json', json.dumps(BASELINE))
        self.write('docs/tickets/SEEN-001-a-ticket-to-work.md',
                   '---\nid: SEEN-001\nestimate: 2\nsprint: 0\nexecutor: claude-code\n'
                   'changes_agent_action: false\nstatus: done\n---\n# SEEN-001: A ticket\n\n'
                   '## Acceptance criteria\n\n- [x] Something observable happens\n')
        self._write_journal()

    def _write_journal(self):
        from harness import journal
        from harness.tests.test_kpi import journal_with_a_route
        folder = self.root / 'docs' / 'harness' / 'history' / 'SEEN-001'
        folder.mkdir(parents=True)
        previous = None
        for position, record in enumerate(journal_with_a_route(), start=1):
            path = folder / f'{position:04d}.json'
            body = dict(record, sequence=position, ticket='SEEN-001', prev_hash=previous)
            path.write_bytes(journal.serialise(body))
            previous = journal.digest(path)

    def report(self):
        from harness import cli
        cli.execute(cli.parse(['--root', str(self.root), 'report', '--sprint', '0']))
        return (self.root / 'docs' / 'harness' / 'reports' / 'sprint-0.md').read_text()

    def test_the_sprint_report_carries_the_cost_table(self):
        rendered = self.report()
        self.assertIn('Cost per point by the model the work ran on', rendered)
        self.assertIn('opus', rendered)

    def test_the_report_json_carries_the_figures_the_table_was_drawn_from(self):
        self.report()
        payload = json.loads(
            (self.root / 'docs' / 'harness' / 'reports' / 'sprint-0.json').read_text())
        self.assertIn('opus', payload['context']['cost_by_model'])
        self.assertIn('priced_on', payload['context']['prices'])

    def test_the_table_names_the_date_the_prices_were_read(self):
        rules = thresholds.load(self.root)
        self.assertIn(rules['routing']['prices']['priced_on'], self.report())


class ForwardReferenceTest(unittest.TestCase):
    """F5 of SEEN-108's third review: what the printed report tells a reader to run.

    `report --calibration` is criterion 2 of SEEN-109 and nothing implements it,
    so a table that names it in the present tense sends its reader to a command
    argparse rejects.
    """

    def rendered(self):
        from harness import report as reporting
        rules = thresholds.load(PROJECT)
        return '\n'.join(reporting.render_cost(
            dict(opus=dict(slices=1, points=2, cost_cents=300, output_tokens=40000,
                           cost_per_point=150.0)),
            rules['routing']['prices']))

    def test_it_does_not_claim_the_calibration_command_exists_yet(self):
        rendered = self.rendered()
        self.assertIn('report --calibration', rendered)
        self.assertRegex(rendered, r'(?i)SEEN-109')

    def test_the_command_it_names_is_not_one_the_parser_accepts_today(self):
        """If this ever fails, SEEN-109 has landed and the sentence can lose its tense."""
        from harness import cli
        from harness.errors import HarnessError
        with self.assertRaisesRegex(HarnessError, 'calibration'):
            cli.parse(['report', '--calibration'])
