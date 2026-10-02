"""Weekly and sprint reports, aggregated from the tickets' own figures.

SEEN-114's rule loop is the part under test here: what the registry already
caught, what recurred with no rule written for it, what predates the field
entirely, and the rules that arrived. `rule_loop` and `rules_added_in_week`
are read over a fabricated window rather than a real journal, because what is
asserted is the arithmetic and not any one ticket's history.
"""

import unittest

from harness import report


# A sentinel distinct from None, so a test can ask for a finding that omits
# `rule_candidate` entirely, which is a different fixture from one that carries
# it as an explicit empty value.
_OMIT = object()


def _finding(identifier, severity, rule_candidate=_OMIT, **extra):
    body = dict(id=identifier, severity=severity, claim='It breaks',
                failure_scenario='It breaks like this', status='resolved', resolution='Fixed')
    if rule_candidate is not _OMIT:
        body['rule_candidate'] = rule_candidate
    body.update(extra)
    return body


def _advance(sequence, findings, ticket='SEEN-701'):
    """A review advance as the gate writes one, carrying its findings."""
    return dict(sequence=sequence, ticket=ticket, timestamp='2026-10-01T10:00:00+00:00',
                harness_version='2', kind='advance', stage='review', attempt=1,
                actor='claude:implementer', session='a' * 12, head='0' * 40, prev_hash=None,
                data=dict(from_stage='review', to_stage='deliver', decisions=[],
                          evidence=dict(reviewer='codex:reviewer', independence='subagent',
                                        read=[], findings=findings, verdict='pass')))


class RuleLoopTest(unittest.TestCase):
    """What `rule_loop` reads out of a window's own findings."""

    registry = [dict(id='ast-grep/no-euro-sign', tool='ast-grep')]

    def test_a_candidate_naming_a_registry_id_is_caught(self):
        records = [_advance(1, [_finding('F1', 'high', rule_candidate='ast-grep/no-euro-sign')])]
        section = report.rule_loop([('SEEN-701', records)], self.registry)
        self.assertEqual(len(section['caught']), 1)
        self.assertEqual(section['caught'][0]['rule'], 'ast-grep/no-euro-sign')
        self.assertEqual(section['caught'][0]['ticket'], 'SEEN-701')

    def test_a_candidate_not_in_the_registry_is_not_caught(self):
        records = [_advance(1, [_finding('F1', 'high',
                                         rule_candidate='ast-grep/no-settlement-mutation')])]
        section = report.rule_loop([('SEEN-701', records)], self.registry)
        self.assertEqual(section['caught'], [])

    def test_a_candidate_recurring_on_two_findings_is_named(self):
        first = [_advance(1, [_finding('F1', 'high',
                                       rule_candidate='ast-grep/no-settlement-mutation')])]
        second = [_advance(1, [_finding('F2', 'medium',
                                        rule_candidate='ast-grep/no-settlement-mutation')],
                           ticket='SEEN-702')]
        section = report.rule_loop([('SEEN-701', first), ('SEEN-702', second)], self.registry)
        self.assertIn('ast-grep/no-settlement-mutation', section['recurred'])
        self.assertEqual(len(section['recurred']['ast-grep/no-settlement-mutation']), 2)

    def test_a_candidate_seen_once_does_not_recur(self):
        records = [_advance(1, [_finding('F1', 'high',
                                         rule_candidate='ast-grep/no-settlement-mutation')])]
        section = report.rule_loop([('SEEN-701', records)], self.registry)
        self.assertEqual(section['recurred'], {})

    def test_a_none_candidate_is_neither_caught_nor_recurring(self):
        reason = 'none: nothing static catches a missing test case'
        first = [_advance(1, [_finding('F1', 'high', rule_candidate=reason)])]
        second = [_advance(1, [_finding('F2', 'medium', rule_candidate=reason)],
                           ticket='SEEN-702')]
        section = report.rule_loop([('SEEN-701', first), ('SEEN-702', second)], self.registry)
        self.assertEqual(section['caught'], [])
        self.assertEqual(section['recurred'], {})

    def test_a_finding_with_no_rule_candidate_at_all_predates_the_field(self):
        records = [_advance(1, [_finding('F1', 'high')])]
        section = report.rule_loop([('SEEN-701', records)], self.registry)
        self.assertEqual(section['predates'], 1)
        self.assertEqual(section['caught'], [])
        self.assertEqual(section['recurred'], {})

    def test_a_low_severity_finding_is_out_of_scope_entirely(self):
        """Low never carries rule_candidate, by the gate's own rule; it is not a miss."""
        records = [_advance(1, [_finding('F1', 'low')])]
        section = report.rule_loop([('SEEN-701', records)], self.registry)
        self.assertEqual(section['caught'], [])
        self.assertEqual(section['recurred'], {})
        self.assertEqual(section['predates'], 0)

    def test_an_empty_window_states_every_figure_as_nothing(self):
        section = report.rule_loop([], self.registry)
        self.assertEqual(section, dict(caught=[], recurred={}, predates=0))


class RulesAddedInWeekTest(unittest.TestCase):
    """Which registry entries arrived in the report's own ISO week."""

    registry = [dict(id='ast-grep/no-euro-sign'), dict(id='biome/noFloatingPromises')]
    arrivals = {'ast-grep/no-euro-sign': '2026-09-24T09:00:00Z',
               'biome/noFloatingPromises': '2026-10-08T09:00:00Z'}

    def test_a_rule_that_arrived_in_the_reports_week_is_listed(self):
        found = report.rules_added_in_week(self.registry, self.arrivals, '2026-09-26')
        self.assertEqual([entry['id'] for entry in found], ['ast-grep/no-euro-sign'])

    def test_a_rule_that_arrived_a_different_week_is_not_listed(self):
        found = report.rules_added_in_week(self.registry, self.arrivals, '2026-09-26')
        self.assertNotIn('biome/noFloatingPromises', [entry['id'] for entry in found])

    def test_a_rule_with_no_date_is_not_listed(self):
        registry = self.registry + [dict(id='knip/no-unused-exports')]
        found = report.rules_added_in_week(registry, self.arrivals, '2026-09-26')
        self.assertNotIn('knip/no-unused-exports', [entry['id'] for entry in found])


class RenderRulesTest(unittest.TestCase):
    """The markdown, beside `render_context` and `calibration_line`."""

    def test_it_states_all_four_figures(self):
        section = dict(
            caught=[dict(ticket='SEEN-701', id='F1', rule='ast-grep/no-euro-sign')],
            recurred={'ast-grep/no-settlement-mutation': [dict(ticket='SEEN-701', id='F2'),
                                                           dict(ticket='SEEN-702', id='F3')]},
            predates=4, rules_added=[dict(id='ast-grep/no-euro-sign')])
        lines = '\n'.join(report.render_rules(section))
        self.assertIn('Findings a rule could have caught: 1', lines)
        self.assertIn('ast-grep/no-euro-sign', lines)
        self.assertIn('ast-grep/no-settlement-mutation', lines)
        self.assertIn('Findings that predate rule_candidate: 4', lines)

    def test_a_clean_window_says_so_rather_than_nothing(self):
        section = dict(caught=[], recurred={}, predates=0, rules_added=[])
        lines = '\n'.join(report.render_rules(section))
        self.assertIn('Findings a rule could have caught: 0', lines)
        self.assertIn('Rules added this week: none', lines)
        self.assertIn('Recurred without a rule: none', lines)
        self.assertIn('Findings that predate rule_candidate: 0', lines)


class MutationColumnTest(unittest.TestCase):
    """The sprint report prints the mutation score beside coverage, SEEN-116."""

    FIGURES = dict(first_pass_ci_rate=None, median_cycle_time_seconds=None,
                   rework_per_ticket=None, points_delivered=0, findings_by_severity={})

    def rendered(self, **ticket):
        body = dict(ticket='SEEN-701', points=2, attempts=1, rework=0, findings={},
                    coverage=dict(delta=0.5), cycle_time_seconds=None)
        body.update(ticket)
        return report.render('Sprint', [body], self.FIGURES, [])

    def row(self, text):
        return next(line for line in text.splitlines() if line.startswith('| SEEN-701'))

    def test_the_table_names_the_column_beside_coverage(self):
        header = next(line for line in self.rendered().splitlines() if line.startswith('| Ticket'))
        cells = [cell.strip() for cell in header.strip('|').split('|')]
        self.assertEqual(cells[cells.index('Coverage') + 1], 'Mutation')

    def test_a_scored_ticket_shows_its_score_against_the_floor(self):
        row = self.row(self.rendered(mutation=dict(score=82.5, floor=70, mutants=12)))
        self.assertTrue(row.rstrip().endswith('| 82.5% of 12 |'), row)

    def test_a_measurement_with_no_mutants_says_so_rather_than_a_hundred(self):
        row = self.row(self.rendered(mutation=dict(score=None, floor=70, mutants=0,
                                                   reason='no mutants in the files named')))
        self.assertTrue(row.rstrip().endswith('| not applicable |'), row)
        self.assertNotIn('100', row)

    def test_a_ticket_that_measured_none_shows_a_dash(self):
        self.assertTrue(self.row(self.rendered(mutation=None)).rstrip().endswith('| - |'))


if __name__ == '__main__':
    unittest.main()
