"""The context budget, and the measurement that decides whether it paid.

Three MCP servers put three sets of tool schemas into every session before a
ticket is read. The budget says what that buys; the measurement says whether it
was worth it, against a baseline captured before any of them existed. The rule
for reading the number is written before the number exists, because a rule
chosen after seeing the figure is not a rule.
"""

import json
import unittest

from harness import context, cost, thresholds
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
        source = (PROJECT / 'harness' / 'delivery.py').read_text()

        self.assertIn('Points and tokens stay null here on purpose', source)


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
