"""What each stage gate proves before a ticket may leave its stage.

The three layers are visible here: the template says which fields must be
present, these relations live in code, and the vocabularies come from
thresholds.toml.
"""

import json

from harness import gates, thresholds
from harness.errors import HarnessError
from harness.repository import Repository
from harness.tests.helpers import ProjectTest


def check_record(sequence, phase, stage='tdd', attempt=1, exit_code=None, **extra):
    """A recorded check. A red fails by default, because a red that passed is not one."""
    if exit_code is None:
        exit_code = 1 if phase == 'red' else 0
    return dict(sequence=sequence, ticket='SEEN-001', kind='check', stage=stage,
                attempt=attempt, actor='claude:implementer',
                data=dict(phase=phase, exit_code=exit_code, command=['pytest'], **extra))


def coverage_record(sequence, delta=0.5, attempt=1):
    """A measurement of the gated package, which the tdd gate requires for the attempt."""
    return check_record(sequence, 'coverage', attempt=attempt, package='@seen/core',
                        lines=90.0, baseline=None if delta is None else 90.0 - delta, delta=delta)


def advance_record(sequence, from_stage, evidence, attempt=1):
    return dict(sequence=sequence, ticket='SEEN-001', kind='advance', stage=from_stage,
                attempt=attempt, actor='claude:implementer',
                data=dict(from_stage=from_stage, to_stage='tdd', evidence=evidence, decisions=[]))


class GateTest(ProjectTest):

    def setUp(self):
        super().setUp()
        self.repository = Repository(self.root)
        self.thresholds = thresholds.load(self.root)
        self.records = [dict(sequence=1, kind='start', stage='clarify', attempt=1,
                             actor='claude:implementer', data={})]
        self.current = dict(stage='clarify', attempt=1, records=1)

    def template(self, stage, **changes):
        name = gates.template_name(stage, changes.get('mode'))
        data = json.loads((self.root / 'harness' / 'templates' / name).read_text())
        data.update(changes)
        return data

    def evaluate(self, stage, data, records=None, attempt=1):
        current = dict(self.current, stage=stage, attempt=attempt)
        return gates.evaluate(stage, data, records or self.records, current,
                              self.repository, self.thresholds)

    def filled_clarify(self):
        return self.template('clarify',
                             scope='Build the thing.',
                             acceptance=['AC1 proven by the unit test'],
                             decisions=['Chose A over B because B needs a second service'])


class RequiredFieldTest(GateTest):

    def test_a_missing_field_is_named(self):
        data = self.filled_clarify()
        del data['decisions']
        with self.assertRaisesRegex(HarnessError, 'decisions'):
            self.evaluate('clarify', data)

    def test_an_empty_field_is_treated_as_missing(self):
        data = self.filled_clarify()
        data['scope'] = '   '
        with self.assertRaisesRegex(HarnessError, 'scope'):
            self.evaluate('clarify', data)

    def test_a_list_the_template_ships_with_an_entry_may_not_be_empty(self):
        data = self.filled_clarify()
        data['acceptance'] = []
        with self.assertRaisesRegex(HarnessError, 'acceptance'):
            self.evaluate('clarify', data)

    def test_a_list_the_template_ships_empty_may_stay_empty(self):
        self.evaluate('clarify', self.filled_clarify())

    def test_template_example_text_left_unchanged_counts_as_missing(self):
        data = self.filled_clarify()
        data['decisions'] = ['Decision taken, why, and on whose authority.']
        with self.assertRaisesRegex(HarnessError, 'template'):
            self.evaluate('clarify', data)

    def test_an_enumerated_value_may_match_the_template(self):
        self.evaluate('tdd', self.filled_non_code())

    def filled_non_code(self):
        return self.template('tdd', mode='non-code', reason='This ticket only moves prose.',
                             change_type='documentation')


class ClarifyGateTest(GateTest):

    def test_an_open_question_blocks_the_stage(self):
        data = self.filled_clarify()
        data['open_questions'] = ['Does Bol return the commission on a cancelled order?']
        with self.assertRaisesRegex(HarnessError, 'open question'):
            self.evaluate('clarify', data)


class SolutionGateTest(GateTest):

    def filled_solution(self, **changes):
        data = self.template('solution',
                             approach='Add a pure function and call it from the worker.',
                             changes=['packages/core/src/fees.ts: add the detector'],
                             tests_first=['fees.test.ts: expects EUR 0 when the fee is correct'],
                             alternatives=['Do it in SQL, rejected because it cannot be unit tested'],
                             risks=['Wrong rounding; mitigated by cent integers and a table test'],
                             rollback='Revert the commit; no migration runs.',
                             tenant_tables=['none'],
                             buyer_pii='none')
        data.update(changes)
        return data

    def test_it_passes_when_every_field_is_answered(self):
        self.evaluate('solution', self.filled_solution())

    def test_a_policy_gate_action_ticket_must_declare_its_action(self):
        records = self.records + [advance_record(2, 'clarify', dict(changes_agent_action=True))]
        with self.assertRaisesRegex(HarnessError, 'policy_gate_action'):
            self.evaluate('solution', self.filled_solution(), records=records)

    def test_the_declaration_needs_reversibility_action_type_and_impact(self):
        records = self.records + [advance_record(2, 'clarify', dict(changes_agent_action=True))]
        data = self.filled_solution(policy_gate_action=dict(reversibility='reversible'))
        with self.assertRaisesRegex(HarnessError, 'action_type'):
            self.evaluate('solution', data, records=records)

    def test_a_complete_declaration_passes(self):
        records = self.records + [advance_record(2, 'clarify', dict(changes_agent_action=True))]
        data = self.filled_solution(policy_gate_action=dict(
            reversibility='reversible', action_type='listing_fix',
            euro_impact_estimator='price delta times units on the offer'))
        self.evaluate('solution', data, records=records)


class TddGateTest(GateTest):

    def code_tdd(self, **changes):
        data = self.template('tdd',
                             slices=[dict(behaviour='Detects a fee overcharge',
                                          failure_reason='expected 250, received 0',
                                          red=2, green=3)],
                             regression=4)
        data.update(changes)
        return data

    def journal_with_checks(self, attempt=1):
        return self.records + [check_record(2, 'red', attempt=attempt),
                               check_record(3, 'green', attempt=attempt),
                               check_record(4, 'regression', attempt=attempt),
                               coverage_record(5, attempt=attempt)]

    def test_a_slice_citing_recorded_checks_passes(self):
        self.evaluate('tdd', self.code_tdd(), records=self.journal_with_checks())

    def test_a_cited_check_that_does_not_exist_is_refused(self):
        with self.assertRaisesRegex(HarnessError, '9'):
            self.evaluate('tdd', self.code_tdd(slices=[dict(behaviour='x', failure_reason='y',
                                                            red=9, green=3)], regression=4),
                          records=self.journal_with_checks())

    def test_a_check_from_an_earlier_attempt_may_not_be_reused(self):
        records = self.records + [check_record(2, 'red', attempt=1),
                                  check_record(3, 'green', attempt=2),
                                  check_record(4, 'regression', attempt=2),
                                  coverage_record(5, attempt=2)]
        with self.assertRaisesRegex(HarnessError, 'attempt'):
            self.evaluate('tdd', self.code_tdd(), records=records, attempt=2)

    def test_a_green_recorded_before_its_red_is_refused(self):
        records = self.records + [check_record(2, 'green'), check_record(3, 'red'),
                                  check_record(4, 'regression'), coverage_record(5)]
        data = self.code_tdd(slices=[dict(behaviour='x', failure_reason='y', red=3, green=2)])
        with self.assertRaisesRegex(HarnessError, 'order'):
            self.evaluate('tdd', data, records=records)

    def test_citing_a_green_where_a_red_belongs_is_refused(self):
        data = self.code_tdd(slices=[dict(behaviour='x', failure_reason='y', red=3, green=3)])
        with self.assertRaisesRegex(HarnessError, 'red'):
            self.evaluate('tdd', data, records=self.journal_with_checks())

    def test_the_regression_must_run_after_the_last_green(self):
        records = self.records + [check_record(2, 'regression'), check_record(3, 'red'),
                                  check_record(4, 'green'), coverage_record(5)]
        data = self.code_tdd(slices=[dict(behaviour='x', failure_reason='y', red=3, green=4)],
                             regression=2)
        with self.assertRaisesRegex(HarnessError, 'order'):
            self.evaluate('tdd', data, records=records)

    def test_a_cited_check_of_the_wrong_phase_is_refused(self):
        records = self.records + [check_record(2, 'green'), check_record(3, 'green'),
                                  check_record(4, 'regression'), coverage_record(5)]
        with self.assertRaisesRegex(HarnessError, 'red'):
            self.evaluate('tdd', self.code_tdd(), records=records)

    def test_code_mode_needs_at_least_one_slice(self):
        with self.assertRaisesRegex(HarnessError, 'slices'):
            self.evaluate('tdd', self.code_tdd(slices=[]), records=self.journal_with_checks())


class NonCodeGateTest(GateTest):

    def non_code(self, **changes):
        data = self.template('tdd', mode='non-code', reason='Registration, no code changes.',
                             change_type='verification')
        data.update(changes)
        return data

    def test_a_verification_must_name_its_sources(self):
        with self.assertRaisesRegex(HarnessError, 'sources'):
            self.evaluate('tdd', self.non_code(sources=[]))

    def test_a_verification_with_sources_passes(self):
        self.evaluate('tdd', self.non_code(sources=[
            'Report name GET_FBA_FULFILLMENT_ADJUSTMENTS observed in Seller Central on 2026-09-24',
            'attachments/amazon-report-list.json sha256 abc123']))

    def test_documentation_needs_no_sources(self):
        self.evaluate('tdd', self.non_code(change_type='documentation', sources=[]))

    def test_an_unknown_change_type_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'change_type'):
            self.evaluate('tdd', self.non_code(change_type='refactor'))

    def test_an_unknown_mode_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'mode'):
            self.evaluate('tdd', self.non_code(mode='partial'))


class ReviewGateTest(GateTest):

    def review(self, **changes):
        data = self.template('review',
                             acceptance_evidence=['AC1 proven by check 4'],
                             independence='self-review',
                             reviewer='claude:reviewer')
        data.update(changes)
        return data

    def tdd_done(self, actors=('claude:implementer',)):
        records = [dict(sequence=1, kind='start', stage='clarify', attempt=1,
                        actor=actors[0], data={})]
        records.append(dict(sequence=2, kind='advance', stage='tdd', attempt=1,
                            actor=actors[-1],
                            data=dict(from_stage='tdd', to_stage='review',
                                      evidence=dict(regression=0), decisions=[])))
        return records

    def test_a_self_review_passes_when_it_says_so(self):
        self.evaluate('review', self.review(), records=self.tdd_done())

    def test_a_verdict_other_than_pass_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'verdict'):
            self.evaluate('review', self.review(verdict='fail'), records=self.tdd_done())

    def test_an_unresolved_finding_is_refused(self):
        finding = dict(id='R-01', severity='high', claim='The detector rounds the wrong way',
                       failure_scenario='A EUR 0.005 fee rounds up and the claim overstates',
                       status='open', resolution='')
        with self.assertRaisesRegex(HarnessError, 'R-01 is open'):
            self.evaluate('review', self.review(findings=[finding]), records=self.tdd_done())

    def test_a_finding_needs_a_failure_scenario(self):
        finding = dict(id='R-01', severity='high', claim='Something smells',
                       status='resolved', resolution='Rewrote it')
        with self.assertRaisesRegex(HarnessError, 'failure_scenario'):
            self.evaluate('review', self.review(findings=[finding]), records=self.tdd_done())

    def test_a_finding_may_omit_the_file_and_line(self):
        finding = dict(id='R-01', severity='medium', claim='No test covers the empty settlement',
                       failure_scenario='An empty settlement file would go unnoticed',
                       status='resolved', resolution='Added the case')
        self.evaluate('review', self.review(findings=[finding]), records=self.tdd_done())

    def test_an_unknown_severity_is_refused(self):
        finding = dict(id='R-01', severity='annoying', claim='x', failure_scenario='y',
                       status='resolved', resolution='z')
        with self.assertRaisesRegex(HarnessError, 'severity'):
            self.evaluate('review', self.review(findings=[finding]), records=self.tdd_done())

    def test_independence_is_refused_when_one_tool_wrote_every_record(self):
        with self.assertRaisesRegex(HarnessError, 'independent'):
            self.evaluate('review', self.review(independence='independent',
                                                reviewer='claude:reviewer'),
                          records=self.tdd_done())

    def test_independence_passes_when_another_tool_worked_the_ticket(self):
        records = self.tdd_done(actors=('claude:implementer', 'claude:implementer'))
        self.evaluate('review', self.review(independence='independent', reviewer='codex:reviewer'),
                      records=records)


if __name__ == '__main__':
    unittest.main()
