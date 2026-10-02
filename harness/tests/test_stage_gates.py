"""What each stage gate proves before a ticket may leave its stage.

The three layers are visible here: the template says which fields must be
present, these relations live in code, and the vocabularies come from
thresholds.toml.
"""

import json
import os
import unittest

from harness import gates, thresholds
from harness.errors import HarnessError
from harness.repository import Repository
from harness.tests.helpers import PROJECT, ProjectTest


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


def advance_record(sequence, from_stage, evidence, attempt=1, to_stage='tdd'):
    return dict(sequence=sequence, ticket='SEEN-001', kind='advance', stage=from_stage,
                attempt=attempt, actor='claude:implementer',
                data=dict(from_stage=from_stage, to_stage=to_stage, evidence=evidence,
                          decisions=[]))


def routed_slice(position, model, effort='high', files=('harness/journal.py',)):
    """One entry of a route record's execution list, as routing.run writes it."""
    return dict(position=position, name=f'Slice {position}', points=1, files=list(files),
                red=f'Nothing yet proves behaviour {position}', model=model, effort=effort,
                source='jev', rule=None, reason=None, model_probability=0.7,
                effort_probability=0.7, model_passed=True, model_threshold=0.5)


def route_record(sequence, solution, entries, attempt=1):
    """A route record naming the solution advance it routes, which is how it is read."""
    return dict(sequence=sequence, ticket='SEEN-001', kind='route', stage='tdd',
                attempt=attempt, actor='claude:implementer',
                data=dict(solution=solution, shadow=False, strongest='opus',
                          tiers=['haiku', 'sonnet', 'opus'], rules=[],
                          jev=dict(asked=False, model=None, answers=[], reason='a fixture'),
                          execution=entries))


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


class PlaceholderShapeTest(GateTest):
    """F8: shaping the template must not stop guarding the fields it kept."""

    def test_prose_from_a_dropped_field_pasted_into_a_kept_one_is_refused(self):
        template = self.template('solution')
        record = self.template('solution', mode='non-code',
                               approach=template['tests_first'][0],
                               changes=['harness/x.py, the thing'],
                               migrations=[], alternatives=['B, because it needs a service'],
                               risks=['It breaks, so there is a test'],
                               rollback='git revert', new_dependencies=[],
                               tenant_tables=['none'], buyer_pii='none',
                               policy_gate_action=None)
        with self.assertRaisesRegex(HarnessError, 'Replace the template text'):
            self.evaluate('solution', record)


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
                             slices=[dict(position=1, name='The detector',
                                          points=2,
                                          files=['packages/core/src/fees.ts'],
                                          red='No detector exists, so an overcharge reads as correct')],
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
                             slices=[dict(position=1, behaviour='Detects a fee overcharge',
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
            self.evaluate('tdd', self.code_tdd(slices=[dict(position=1, behaviour='x', failure_reason='y',
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
        data = self.code_tdd(slices=[dict(position=1, behaviour='x', failure_reason='y', red=3, green=2)])
        with self.assertRaisesRegex(HarnessError, 'order'):
            self.evaluate('tdd', data, records=records)

    def test_citing_a_green_where_a_red_belongs_is_refused(self):
        data = self.code_tdd(slices=[dict(position=1, behaviour='x', failure_reason='y', red=3, green=3)])
        with self.assertRaisesRegex(HarnessError, 'red'):
            self.evaluate('tdd', data, records=self.journal_with_checks())

    def test_the_regression_must_run_after_the_last_green(self):
        records = self.records + [check_record(2, 'regression'), check_record(3, 'red'),
                                  check_record(4, 'green'), coverage_record(5)]
        data = self.code_tdd(slices=[dict(position=1, behaviour='x', failure_reason='y', red=3, green=4)],
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


def mutation_record(sequence, score, files=('packages/core/src/fee.ts',), attempt=1,
                    reason=None, not_applicable=False):
    """A mutation measurement of the files a slice names, which the tdd gate requires."""
    return check_record(sequence, 'mutation', attempt=attempt, score=score, floor=70,
                        files=list(files), killed=7, survived=3, mutants=10, reason=reason,
                        not_applicable=not_applicable)


class MutationJournal(GateTest):
    """A plan naming one file under packages/core/src, and the checks that prove it."""

    FEE = 'packages/core/src/fee.ts'

    def plan(self, *files):
        return advance_record(2, 'solution',
                              dict(mode='code', slices=[dict(name='One', points=1,
                                                             files=list(files), red='r')]),
                              to_stage='tdd')

    def journal(self, *files, measurement=None, **red):
        records = self.records + [self.plan(*(files or (self.FEE,))),
                                  check_record(3, 'red', **red),
                                  check_record(4, 'green'), check_record(5, 'regression'),
                                  coverage_record(6)]
        return records + ([measurement] if measurement else [])

    def tdd(self):
        return self.template('tdd',
                             slices=[dict(position=1, behaviour='Detects a fee overcharge',
                                          failure_reason='expected 250, received 0',
                                          red=3, green=4)], regression=5)


class MutationFloorTest(MutationJournal):
    """The floor on the files a slice names under packages/core/src, SEEN-116.

    Only the product source is held to it: a slice that names nothing there has
    nothing to mutate, and a measurement that found no mutants is not applicable
    and passes, by Ruud's decision, while a missing, uncovering or sub-floor one
    is refused.
    """

    def test_a_score_below_the_floor_is_refused_with_both_figures(self):
        records = self.journal(measurement=mutation_record(7, 60.0))
        with self.assertRaisesRegex(HarnessError, '60.0.*70'):
            self.evaluate('tdd', self.tdd(), records=records)

    def test_a_score_at_the_floor_passes(self):
        self.evaluate('tdd', self.tdd(), records=self.journal(measurement=mutation_record(7, 70.0)))

    def test_no_measurement_is_refused_and_the_command_is_named(self):
        with self.assertRaisesRegex(HarnessError, 'harness mutation'):
            self.evaluate('tdd', self.tdd(), records=self.journal())

    def test_a_slice_naming_only_harness_files_needs_no_measurement(self):
        self.evaluate('tdd', self.tdd(), records=self.journal('harness/gates.py'))

    def test_a_slice_naming_a_fixture_or_the_db_needs_none_either(self):
        self.evaluate('tdd', self.tdd(), records=self.journal(
            'packages/core/fixtures/tolerance/detector.ts', 'packages/core/db/repository.ts'))

    def test_no_mutants_in_the_files_is_not_applicable_and_passes(self):
        """Ruud's decision: recorded with its count and no score, and let through."""
        records = self.journal(measurement=mutation_record(
            7, None, reason='no mutants in the files named', not_applicable=True))
        self.evaluate('tdd', self.tdd(), records=records)

    def test_a_not_applicable_measurement_over_other_files_is_still_refused(self):
        records = self.journal(measurement=mutation_record(
            7, None, files=('packages/core/src/vat.ts',), not_applicable=True))
        with self.assertRaisesRegex(HarnessError, 'fee.ts'):
            self.evaluate('tdd', self.tdd(), records=records)

    def test_a_run_that_measured_nothing_is_not_not_applicable(self):
        """No score because the run failed or wrote no report is a missing measurement."""
        records = self.journal(measurement=mutation_record(
            7, None, reason='the Stryker run failed (exit 1)'))
        with self.assertRaisesRegex(HarnessError, 'measured nothing|no score'):
            self.evaluate('tdd', self.tdd(), records=records)

    def test_a_measurement_of_other_files_does_not_cover_this_slice(self):
        records = self.journal(measurement=mutation_record(
            7, 100.0, files=('packages/core/src/vat.ts',)))
        with self.assertRaisesRegex(HarnessError, 'fee.ts'):
            self.evaluate('tdd', self.tdd(), records=records)

    def test_a_directory_measured_covers_the_file_under_it(self):
        records = self.journal(measurement=mutation_record(
            7, 90.0, files=('packages/core/src',)))
        self.evaluate('tdd', self.tdd(), records=records)

    def test_only_this_attempts_measurement_counts(self):
        records = self.journal(measurement=mutation_record(7, 99.0, attempt=2))
        with self.assertRaisesRegex(HarnessError, 'harness mutation'):
            self.evaluate('tdd', self.tdd(), records=records)

    def test_the_latest_measurement_is_the_one_held_to_the_floor(self):
        records = self.journal(measurement=mutation_record(7, 40.0)) + [mutation_record(8, 80.0)]
        self.evaluate('tdd', self.tdd(), records=records)


class AKilledMutantAsRedTest(MutationJournal):
    """A RED at exit 0 is accepted when its Stryker report killed a mutant in the slice."""

    def journal(self, *files, killed=None, exit_code=0):
        extra = dict(mutants_killed=killed) if killed is not None else {}
        return super().journal(*files, measurement=mutation_record(
            7, 80.0, files=('packages/core/src',)),
                               exit_code=exit_code, **extra)

    def test_a_kill_in_a_file_the_slice_names_is_a_red(self):
        self.evaluate('tdd', self.tdd(), records=self.journal(killed={self.FEE: ['3']}))

    def test_a_kill_under_a_directory_the_slice_names_is_a_red(self):
        self.evaluate('tdd', self.tdd(), records=self.journal('packages/core/src',
                                                              killed={self.FEE: ['3']}))

    def test_a_report_of_survivors_is_not(self):
        with self.assertRaisesRegex(HarnessError, 'did not fail'):
            self.evaluate('tdd', self.tdd(), records=self.journal(killed={}))

    def test_a_check_with_no_report_at_all_is_not(self):
        with self.assertRaisesRegex(HarnessError, 'did not fail'):
            self.evaluate('tdd', self.tdd(), records=self.journal())

    def test_a_kill_in_a_file_the_slice_does_not_name_is_refused_by_name(self):
        with self.assertRaisesRegex(HarnessError, 'packages/core/src/vat.ts'):
            self.evaluate('tdd', self.tdd(),
                          records=self.journal(killed={'packages/core/src/vat.ts': ['1']}))

    def test_a_real_failure_is_still_a_red_wherever_the_report_points(self):
        self.evaluate('tdd', self.tdd(), records=self.journal(
            exit_code=1, killed={'packages/core/src/vat.ts': ['1']}))


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
                             read=['harness/gates.py'],
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
                       status='resolved', resolution='Added the case',
                       # SEEN-114: a medium finding still names no file, which is
                       # what this test is about; it still needs rule_candidate,
                       # which is a different field asking a different question.
                       rule_candidate='none: a stand-in finding, not a real one')
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

    def test_an_independent_review_by_the_tool_that_wrote_the_code_is_refused(self):
        """G2: a second tool having recorded anything is not independence."""
        records = self.tdd_done()
        records.append(dict(sequence=3, kind='return', stage='review', attempt=1,
                            actor='codex:reviewer', session='cccccccccccc',
                            data=dict(from_stage='review', to_stage='tdd', reason='a finding')))

        with self.assertRaisesRegex(HarnessError, 'independent'):
            self.evaluate('review', self.review(independence='independent',
                                                reviewer='claude:reviewer'),
                          records=records)

    def test_independence_passes_when_another_tool_worked_the_ticket(self):
        records = self.tdd_done(actors=('claude:implementer', 'claude:implementer'))
        self.evaluate('review', self.review(independence='independent', reviewer='codex:reviewer'),
                      records=records)



class AuthorshipTest(unittest.TestCase):
    """Which tools wrote the work, asked of every journal this repository holds.

    H1 of SEEN-105's third review: F2, G1 and H1 are three generations of one
    question, each fixed with another predicate and each tested against another
    fixture. This asks it of the twenty real journals instead, plus the two record
    shapes the fixtures kept missing: a return written at the deliver stage and a
    reopen written at delivered, both of which this repository actually contains.
    """

    @classmethod
    def setUpClass(cls):
        from harness import journal
        history = PROJECT / 'docs' / 'harness' / 'history'
        cls.journals = {folder.name: journal.read(folder)
                        for folder in sorted(history.iterdir()) if folder.is_dir()}

    def test_every_real_journal_has_an_author(self):
        for ticket, records in self.journals.items():
            with self.subTest(ticket=ticket):
                self.assertTrue(gates._implementer_tools(records),
                                f'{ticket} would let any tool review it')

    def test_a_return_at_the_deliver_stage_is_not_authorship(self):
        records = [dict(sequence=1, kind='start', stage='clarify', attempt=1,
                        actor='claude:implementer', data={}),
                   dict(sequence=2, kind='return', stage='deliver', attempt=1,
                        actor='codex:reviewer',
                        data=dict(from_stage='deliver', to_stage='tdd', reason='CI refused it'))]

        self.assertEqual(gates._implementer_tools(records), {'claude'})

    def test_a_reopen_at_delivered_is_not_authorship(self):
        records = [dict(sequence=1, kind='start', stage='clarify', attempt=1,
                        actor='claude:implementer', data={}),
                   dict(sequence=2, kind='reopen', stage='delivered', attempt=1,
                        actor='codex:reviewer', data=dict(reason='a defect after delivery'))]

        self.assertEqual(gates._implementer_tools(records), {'claude'})

    def test_work_recorded_by_the_other_assistant_is_authorship(self):
        records = [dict(sequence=1, kind='start', stage='clarify', attempt=1,
                        actor='claude:implementer', data={}),
                   dict(sequence=2, kind='check', stage='tdd', attempt=1,
                        actor='codex:implementer', data=dict(phase='green', exit_code=0))]

        self.assertEqual(gates._implementer_tools(records), {'claude', 'codex'})


class SubagentReviewTest(ReviewGateTest):
    """A review from a context of its own, and the one case the gate can detect.

    A Claude Code subagent inherits its parent's session id, observed and recorded
    in SEEN-105's journal at record 7, so the harness cannot derive a reviewer's
    context and the record declares it. What the gate refuses is the case it can
    see: a review that names a session which wrote this attempt's own records.
    """

    def in_session(self, session='aaaaaaaaaaaa', actors=('claude:implementer',)):
        records = self.tdd_done(actors=actors)
        for record in records:
            record['session'] = session
        return records

    def test_an_unknown_disclosure_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'independence'):
            self.evaluate('review', self.review(independence='another-context'),
                          records=self.in_session())

    def test_a_subagent_review_must_name_the_session_it_came_from(self):
        with self.assertRaisesRegex(HarnessError, 'reviewer_session'):
            self.evaluate('review', self.review(independence='subagent', reviewer_session=''),
                          records=self.in_session())

    def test_a_subagent_review_from_the_implementers_own_session_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'aaaaaaaaaaaa'):
            self.evaluate('review',
                          self.review(independence='subagent', reviewer_session='aaaaaaaaaaaa'),
                          records=self.in_session())

    def test_a_subagent_review_from_another_session_passes(self):
        self.evaluate('review',
                      self.review(independence='subagent', reviewer_session='bbbbbbbbbbbb'),
                      records=self.in_session())

    def test_the_session_running_the_advance_cannot_be_the_reviewer(self):
        from harness import sessions
        os.environ['CLAUDE_CODE_SESSION_ID'] = 'the-session-running-advance'
        self.addCleanup(os.environ.pop, 'CLAUDE_CODE_SESSION_ID', None)
        mine = sessions.digest('the-session-running-advance')
        with self.assertRaisesRegex(HarnessError, mine):
            self.evaluate('review', self.review(independence='subagent', reviewer_session=mine),
                          records=self.in_session())

    def test_a_review_by_the_other_assistant_names_no_session(self):
        """It has a context of its own by construction, so the field is not asked for."""
        data = self.review(independence='independent', reviewer='codex:reviewer')
        data.pop('reviewer_session', None)
        self.evaluate('review', data, records=self.in_session())

    def test_a_session_from_an_earlier_attempt_is_still_the_implementers(self):
        """F5: criterion 3 says the implementer's session, not this attempt's."""
        with self.assertRaisesRegex(HarnessError, 'aaaaaaaaaaaa'):
            self.evaluate('review',
                          self.review(independence='subagent', reviewer_session='aaaaaaaaaaaa'),
                          records=self.in_session(), attempt=2)

    def test_a_self_review_names_no_session_either(self):
        data = self.review()
        data.pop('reviewer_session', None)
        self.evaluate('review', data, records=self.in_session())


class TwoReviewerTest(ReviewGateTest):
    """What a ticket that touches billing or the policy gate still owes.

    A subagent is a context boundary and not independence by itself. Where a
    missed defect costs money, the review comes from the other assistant, and a
    declared session that cannot be verified is not allowed to stand in for it.
    """

    CHECKLIST = ['No secret in the diff', 'No live marketplace call in a test']

    def billing_journal(self, actors=('claude:implementer',)):
        records = [dict(sequence=1, kind='start', stage='clarify', attempt=1,
                        actor=actors[0], session='aaaaaaaaaaaa',
                        data=dict(ticket_file=self.ticket_file)),
                   dict(sequence=2, kind='advance', stage='solution', attempt=1,
                        actor=actors[0], session='aaaaaaaaaaaa',
                        data=dict(from_stage='solution', to_stage='tdd', evidence={},
                                  decisions=[dict(question='touches_billing_or_policy_gate',
                                                  outcome='yes')])),
                   dict(sequence=3, kind='advance', stage='tdd', attempt=1, actor=actors[-1],
                        session='aaaaaaaaaaaa',
                        data=dict(from_stage='tdd', to_stage='review',
                                  evidence=dict(regression=0), decisions=[]))]
        return records

    def test_it_still_needs_a_second_reviewer(self):
        with self.assertRaisesRegex(HarnessError, 'second_reviewer'):
            self.evaluate('review', self.review(independence='independent',
                                                reviewer='codex:reviewer'),
                          records=self.billing_journal())

    def test_it_still_needs_the_security_checklist(self):
        with self.assertRaisesRegex(HarnessError, 'checklist'):
            self.evaluate('review', self.review(independence='independent',
                                                reviewer='codex:reviewer',
                                                second_reviewer='codex:reviewer',
                                                security_checklist=[]),
                          records=self.billing_journal())

    def test_a_subagent_of_the_implementers_own_tool_is_not_enough(self):
        with self.assertRaisesRegex(HarnessError, 'other assistant'):
            self.evaluate('review', self.review(independence='subagent',
                                                reviewer='claude:reviewer',
                                                reviewer_session='bbbbbbbbbbbb',
                                                second_reviewer='claude:reviewer',
                                                security_checklist=self.CHECKLIST),
                          records=self.billing_journal())

    def test_the_other_assistant_as_the_second_reviewer_is_enough(self):
        self.evaluate('review', self.review(independence='subagent',
                                            reviewer='claude:reviewer',
                                            reviewer_session='bbbbbbbbbbbb',
                                            second_reviewer='codex:reviewer',
                                            security_checklist=self.CHECKLIST),
                      records=self.billing_journal())

    def test_a_return_by_the_other_assistant_does_not_disqualify_its_own_review(self):
        """F2: a codex return is the documented path, not a claim that codex wrote it."""
        records = self.billing_journal()
        records.append(dict(sequence=4, kind='return', stage='review', attempt=1,
                            actor='codex:reviewer', session='cccccccccccc',
                            data=dict(from_stage='review', to_stage='tdd', reason='a finding')))

        self.evaluate('review', self.review(independence='independent',
                                            reviewer='codex:reviewer',
                                            second_reviewer='codex:reviewer',
                                            security_checklist=self.CHECKLIST),
                      records=records)

    def test_a_tool_that_is_not_an_assistant_is_not_the_other_assistant(self):
        """F6: a typo satisfied the one control that stands where a session cannot."""
        for named in ('codexx:reviewer', 'Ruud'):
            with self.subTest(named=named):
                with self.assertRaisesRegex(HarnessError, 'other assistant'):
                    self.evaluate('review', self.review(independence='independent',
                                                        reviewer=named,
                                                        second_reviewer=named,
                                                        security_checklist=self.CHECKLIST),
                                  records=self.billing_journal())

    def test_a_ticket_recorded_entirely_as_reviewer_still_has_an_author(self):
        """G1: the F2 fix read authorship from the role, which is self-reported."""
        records = [dict(record, actor='claude:reviewer') for record in self.billing_journal()]

        with self.assertRaisesRegex(HarnessError, 'other assistant'):
            self.evaluate('review', self.review(independence='subagent',
                                                reviewer='claude:reviewer',
                                                reviewer_session='bbbbbbbbbbbb',
                                                second_reviewer='claude:reviewer',
                                                security_checklist=self.CHECKLIST),
                          records=records)

    def test_a_human_reviewer_is_not_the_other_assistant(self):
        """G6: [actors] tools carries human, and a person is not an assistant."""
        with self.assertRaisesRegex(HarnessError, 'other assistant'):
            self.evaluate('review', self.review(independence='independent',
                                                reviewer='human:reviewer',
                                                second_reviewer='human:reviewer',
                                                security_checklist=self.CHECKLIST),
                          records=self.billing_journal())

    def test_a_ticket_that_changes_an_agent_action_needs_the_other_assistant_too(self):
        """G3: criterion 4 says an agent action or billing, not one of the two."""
        records = self.billing_journal()
        records[1]['data']['decisions'] = [dict(question='touches_billing_or_policy_gate',
                                                outcome='no')]
        records.insert(1, dict(sequence=2, kind='advance', stage='clarify', attempt=1,
                               actor='claude:implementer', session='aaaaaaaaaaaa',
                               data=dict(from_stage='clarify', to_stage='solution', decisions=[],
                                         evidence=dict(changes_agent_action=True))))

        with self.assertRaisesRegex(HarnessError, 'other assistant'):
            self.evaluate('review', self.review(independence='subagent',
                                                reviewer='claude:reviewer',
                                                reviewer_session='bbbbbbbbbbbb',
                                                second_reviewer='claude:reviewer',
                                                security_checklist=self.CHECKLIST),
                          records=records)

    def test_a_ticket_returned_from_deliver_can_still_be_reviewed(self):
        """H1: twelve such records exist, and each one bricked the review gate."""
        records = self.billing_journal()
        records.append(dict(sequence=4, kind='return', stage='deliver', attempt=1,
                            actor='codex:reviewer', session='cccccccccccc',
                            data=dict(from_stage='deliver', to_stage='tdd', reason='CI refused')))

        self.evaluate('review', self.review(independence='independent',
                                            reviewer='codex:reviewer',
                                            second_reviewer='codex:reviewer',
                                            security_checklist=self.CHECKLIST),
                      records=records)

    def test_the_frontmatter_declaration_is_read_beside_the_clarify_record(self):
        """H2: the repository owns the ticket file; a clarify record is self-declared."""
        path = self.root / self.ticket_file
        path.write_text(path.read_text().replace('changes_agent_action: false',
                                                 'changes_agent_action: true'))
        records = self.billing_journal()
        records[1]['data']['decisions'] = [dict(question='touches_billing_or_policy_gate',
                                                outcome='no')]

        with self.assertRaisesRegex(HarnessError, 'second_reviewer'):
            self.evaluate('review', self.review(independence='subagent',
                                                reviewer='claude:reviewer',
                                                reviewer_session='bbbbbbbbbbbb'),
                          records=records)

    def test_an_ordinary_ticket_needs_neither(self):
        self.evaluate('review',
                      self.review(independence='subagent', reviewer_session='bbbbbbbbbbbb'),
                      records=self.in_session() if hasattr(self, 'in_session')
                      else self.tdd_done())


class TemplatePositionTest(unittest.TestCase):
    """F1 of the sixth review: what the template teaches about the position.

    Every other field of the tdd template ships instructive prose, and a literal
    1 taught the one value that is wrong for most rounds after the first. Note
    83 asked the next ticket touching this file to put the reading in its prose,
    and the attempt that made the field mandatory did not.
    """

    def slice_template(self):
        from harness import gates
        return gates.load_template(PROJECT, 'tdd')['slices'][0]

    def test_the_template_says_what_the_position_means(self):
        position = self.slice_template()['position']
        self.assertIsInstance(position, str, 'a literal number teaches the wrong default')
        self.assertIn('null', position)

    def test_the_prose_names_the_round_that_belongs_to_no_slice(self):
        self.assertRegex(self.slice_template()['position'], r'(?i)no single slice')

    def test_a_draft_left_unedited_is_refused_rather_than_routed(self):
        """The placeholder must not be a value the gate accepts."""
        from harness import gates
        from harness.errors import HarnessError
        template = gates.load_template(PROJECT, 'tdd')
        # Everything but the position filled in, so the refusal is about the one
        # field under test rather than the first unedited string in the record.
        left = dict(self.slice_template(), behaviour='The behaviour', failure_reason='It failed')
        with self.assertRaisesRegex(HarnessError, 'no single slice'):
            gates.reject_placeholders(template, dict(slices=[left]))


class SeenOneTwelveShape(TddGateTest):
    """SEEN-112's shape: five attempts, the early slices proved in the first two.

    A return resets the attempt, and the attempt was what decided which checks a
    tdd record could cite, so a ticket returned more than once could not
    accumulate its evidence. The slices proved in its first attempts are still
    green and their tests are still in the branch; re-proving one would need a
    RED for code that already passes, which is the one thing this harness
    refuses outright. What says whether evidence is still about this code is the
    tree the check ran against, and every check records it.
    """

    def setUp(self):
        super().setUp()
        self.tree = self.repository.fingerprint()

    def journal(self, moved=()):
        """Slice 1 proved in attempt 1, slice 2 in attempt 2, slice 3 in attempt 5.

        `moved` names the checks whose recorded tree is not the one this record
        is written against, which is the mirror case that must stay refused.
        """
        def tree_for(sequence):
            return 'f' * 64 if sequence in moved else self.tree
        return self.records + [check_record(2, 'red', attempt=1, after=tree_for(2)),
                               check_record(3, 'green', attempt=1, after=tree_for(3)),
                               check_record(4, 'red', attempt=2, after=tree_for(4)),
                               check_record(5, 'green', attempt=2, after=tree_for(5)),
                               check_record(6, 'red', attempt=5, after=tree_for(6)),
                               check_record(7, 'green', attempt=5, after=tree_for(7)),
                               check_record(8, 'regression', attempt=5, after=tree_for(8)),
                               coverage_record(9, attempt=5)]

    def citing_all(self, **changes):
        data = self.template('tdd',
                             slices=[dict(position=1, behaviour='Slice 1, proved in attempt 1',
                                          failure_reason='expected 250, received 0',
                                          red=2, green=3),
                                     dict(position=2, behaviour='Slice 2, proved in attempt 2',
                                          failure_reason='expected a refusal, got none',
                                          red=4, green=5),
                                     dict(position=3, behaviour='Slice 3, proved in attempt 5',
                                          failure_reason='expected slice 3, read slice 1',
                                          red=6, green=7)],
                             regression=8)
        data.update(changes)
        return data


class CiteAcrossAttempts(SeenOneTwelveShape):
    """A record cites the evidence a return did not invalidate."""

    def test_a_record_may_cite_the_slices_earlier_attempts_proved(self):
        self.evaluate('tdd', self.citing_all(), records=self.journal(), attempt=5)

    def test_nothing_is_re_proved_in_the_attempt_that_cites_them(self):
        records = self.journal()
        self.evaluate('tdd', self.citing_all(), records=records, attempt=5)
        proved_here = [record['sequence'] for record in records
                       if record['kind'] == 'check' and record['attempt'] == 5
                       and record['data']['phase'] in ('red', 'green')]
        self.assertEqual(proved_here, [6, 7], 'the earlier slices were re-proved to be cited')


class TreeMovedUnderTheCheck(SeenOneTwelveShape):
    """The two reasons a citation is refused, which one sentence used to answer.

    A gate saying "another attempt" where it means "different code" is what made
    this take five returns to find, so the two say different things.
    """

    def refusal(self, data, records):
        with self.assertRaises(HarnessError) as raised:
            self.evaluate('tdd', data, records=records, attempt=5)
        return str(raised.exception)

    def moved_tree(self):
        # Check 3 is a green here, which is the half a pair is judged by, so this
        # is the refusal a moved tree produces whichever rule is in force.
        return self.refusal(self.citing_all(), self.journal(moved=(3,)))

    def absent_check(self):
        data = self.citing_all()
        data['slices'][0]['green'] = 99
        return self.refusal(data, self.journal())

    def test_a_check_whose_tree_has_moved_says_the_tree_moved(self):
        self.assertIn('tree moved under check 3', self.moved_tree())

    def test_a_citation_of_a_check_that_is_not_there_says_there_is_none(self):
        self.assertIn('no such check', self.absent_check())

    def test_the_two_reasons_are_not_the_same_sentence(self):
        self.assertNotEqual(self.moved_tree(), self.absent_check())

    def test_neither_reason_answers_with_the_attempt(self):
        """The attempt was the proxy; naming it is what hid the real reason."""
        for message in (self.moved_tree(), self.absent_check()):
            self.assertNotIn('belongs to another stage or attempt', message)


class EvidenceForChangedCode(SeenOneTwelveShape):
    """The mirror the loosening is only safe with: code that moved loses its evidence.

    Without this an always-true comparison would pass everything, which is the
    whole risk of replacing the attempt test with a tree test.
    """

    def test_editing_a_file_the_check_covered_refuses_the_citation_by_name(self):
        records = self.journal()
        self.write('harness/journal.py', '# edited after the cited check ran\n')
        moved_to = self.repository.fingerprint()
        self.assertNotEqual(self.tree, moved_to, 'the edit did not move the tree')
        with self.assertRaises(HarnessError) as raised:
            self.evaluate('tdd', self.citing_all(), records=records, attempt=5)
        message = str(raised.exception)
        self.assertIn(self.tree[:12], message)
        self.assertIn(moved_to[:12], message)

    def test_a_check_that_recorded_no_tree_at_all_is_still_refused(self):
        """Every journal written before this rule: nothing says whether it moved."""
        records = self.records + [check_record(2, 'red', attempt=1),
                                  check_record(3, 'green', attempt=1),
                                  check_record(4, 'red', attempt=5, after=self.tree),
                                  check_record(5, 'green', attempt=5, after=self.tree),
                                  check_record(6, 'regression', attempt=5, after=self.tree),
                                  coverage_record(7, attempt=5)]
        data = self.template('tdd',
                             slices=[dict(position=1, behaviour='Slice 1, proved in attempt 1',
                                          failure_reason='expected 250, received 0',
                                          red=2, green=3),
                                     dict(position=2, behaviour='Slice 2, proved in attempt 5',
                                          failure_reason='expected a refusal, got none',
                                          red=4, green=5)],
                             regression=6)
        with self.assertRaisesRegex(HarnessError, 'does not say which tree'):
            self.evaluate('tdd', data, records=records, attempt=5)


class OrderingAcrossAttempts(SeenOneTwelveShape):
    """The ordering rule reads sequence numbers, which are monotonic across attempts.

    So it survives the change untouched, and this says so: a red still precedes
    its green, slices still do not overlap and the regression is still last,
    with the cited checks drawn from three different attempts.
    """

    def out_of_order(self, data, records=None):
        with self.assertRaisesRegex(HarnessError, 'out of order'):
            self.evaluate('tdd', data, records=records or self.journal(), attempt=5)

    def test_the_ordered_case_passes_with_checks_from_three_attempts(self):
        records = self.journal()
        cited = {record['attempt'] for record in records
                 if record['kind'] == 'check' and record['sequence'] in (2, 3, 4, 5, 6, 7)}
        self.assertEqual(cited, {1, 2, 5})
        self.evaluate('tdd', self.citing_all(), records=records, attempt=5)

    def test_a_green_recorded_before_its_red_is_still_out_of_order(self):
        data = self.citing_all()
        # Attempt 2's red with attempt 1's green: the green ran first, whatever
        # attempt either belongs to.
        data['slices'][0].update(red=4, green=3)
        data['slices'][1].update(red=2, green=5)
        self.out_of_order(data)

    def test_slices_may_not_overlap_across_attempts(self):
        data = self.citing_all()
        data['slices'][0].update(red=2, green=5)
        data['slices'][1].update(red=4, green=7)
        data['slices'][2].update(red=6, green=7)
        self.out_of_order(data)

    def test_the_regression_is_still_the_last_check(self):
        records = self.records + [check_record(2, 'red', attempt=1, after=self.tree),
                                  check_record(3, 'green', attempt=1, after=self.tree),
                                  check_record(4, 'regression', attempt=2, after=self.tree),
                                  check_record(5, 'red', attempt=3, after=self.tree),
                                  check_record(6, 'green', attempt=3, after=self.tree),
                                  coverage_record(7, attempt=5)]
        data = self.template('tdd',
                             slices=[dict(position=1, behaviour='Slice 1, proved in attempt 1',
                                          failure_reason='expected 250, received 0',
                                          red=2, green=3),
                                     dict(position=2, behaviour='Slice 2, proved in attempt 3',
                                          failure_reason='expected a refusal, got none',
                                          red=5, green=6)],
                             regression=4)
        self.out_of_order(data, records=records)


class ScopedToTheSlicesFiles(TddGateTest):
    """The scope of "still about this code" is the code the check covered.

    A whole-tree comparison cannot answer the question this rule exists for. The
    measurement that settled it: every green records a distinct tree, SEEN-107 13
    of 13, SEEN-109 13 of 13, SEEN-111 5 of 5, so an earlier attempt's green
    equals the tree at the advance only when nothing at all changed since, which
    is never true of a ticket whose later slices added code. A green proving
    slice 1 is still evidence about slice 1 when slice 3 has since written
    elsewhere, and stops being evidence the moment slice 1's own files move.

    The fixture is a real one, with commits: a check runs against a working tree,
    and what makes that tree findable afterwards is the commit that carried the
    work it proved.
    """

    def setUp(self):
        super().setUp()
        self.plan = [dict(name='Slice one', points=1, files=['harness/slice_one.py'],
                          red='Nothing yet proves one'),
                     dict(name='Slice two', points=1, files=['harness/slice_two.py'],
                          red='Nothing yet proves two'),
                     dict(name='Slice three', points=1, files=['harness/slice_three.py'],
                          red='Nothing yet proves three')]
        self.write('harness/slice_one.py', 'def one():\n    return 1\n')
        # Slice two's file is committed here too and never moves again, so a
        # citation mis-attributed to slice 2 is compared against a file that
        # really has not moved: the fixture must not close that hole for want of
        # a file to name.
        self.write('harness/slice_two.py', 'def two():\n    return 2\n')
        self.commit('feat(SEEN-001): slice one')
        # The tree slice one's red and green ran against, which is this commit's
        # content: the session proved the work and then committed it.
        self.proved = self.repository.fingerprint()

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', message)

    def plan_with(self, **changes):
        plan = [dict(entry) for entry in self.plan]
        plan[0].update(changes)
        return plan

    # The half of a pair a refusal in this fixture names. Its red and its green
    # ran against the same tree, so both used to be comparable and the red, being
    # cited first, was the one the refusal was about. A pair is judged by its
    # green now, so the comparison is made for the green and the green is what a
    # refusal names. The reason is the same sentence either way.
    JUDGED = 'tree moved under check 4'

    def journal(self, plan=None, proved=None, corroborated=1, corroborating=True,
                red_proved=None):
        """Slice one proved in attempt 1, slice three in attempt 2, which is now.

        Attempt 1 advanced out of tdd, and its record is what says which slice of
        the plan checks 3 and 4 proved: the scope of a cross-attempt citation is
        read from that record rather than from the record citing them, which
        names the position itself and is the thing being checked. `corroborated`
        is the position that record declared, null for a round that declared
        none, and `corroborating` False for an attempt that never advanced out of
        tdd at all.

        `red_proved` is the tree the red ran against where it is not the green's.
        That is every real red's shape and not an odd case: a red runs on a tree
        holding the test without the code that answers it, and what gets
        committed is the green, so no commit carries a red's tree. The default
        keeps the two halves equal, because the tests written before that was
        measured are about the comparison rather than about which half carries it.
        """
        now = self.repository.fingerprint()
        earlier = [advance_record(
            5, 'tdd',
            dict(mode='code',
                 slices=[dict(position=corroborated,
                              behaviour='Slice one, proved in attempt 1',
                              failure_reason='expected 1, received nothing',
                              red=3, green=4)],
                 regression=4),
            attempt=1, to_stage='review')] if corroborating else []
        return self.records + [
            advance_record(2, 'solution',
                           dict(mode='code', slices=plan or self.plan), attempt=1),
            check_record(3, 'red', attempt=1, after=red_proved or proved or self.proved),
            check_record(4, 'green', attempt=1, after=proved or self.proved),
            *earlier,
            check_record(6, 'red', attempt=2, after=now),
            check_record(7, 'green', attempt=2, after=now),
            check_record(8, 'regression', attempt=2, after=now),
            coverage_record(9, attempt=2)]

    def citing(self, position=1, **changes):
        data = self.template(
            'tdd',
            slices=[dict(position=position, behaviour='Slice one, proved in attempt 1',
                         failure_reason='expected 1, received nothing',
                         red=3, green=4),
                    dict(position=3, behaviour='Slice three, proved in this attempt',
                         failure_reason='expected 3, received nothing',
                         red=6, green=7)],
            regression=8)
        data.update(changes)
        return data

    def refusal(self, data=None, records=None):
        with self.assertRaises(HarnessError) as raised:
            self.evaluate('tdd', data or self.citing(), records=records or self.journal(),
                          attempt=2)
        return str(raised.exception)

    def slice_three_writes_its_own_file(self):
        self.write('harness/slice_three.py', 'def three():\n    return 3\n')
        self.commit('feat(SEEN-001): slice three')


class CitedAcrossAttemptsByItsOwnFiles(ScopedToTheSlicesFiles):
    """Slice one's green survives slice three writing a file slice one never names."""

    def test_a_green_stands_when_a_later_slice_wrote_somewhere_else(self):
        self.slice_three_writes_its_own_file()
        self.evaluate('tdd', self.citing(), records=self.journal(), attempt=2)

    def test_the_tree_really_did_move_so_the_comparison_is_not_vacuous(self):
        """Without this the acceptance above could be a comparison of nothing."""
        self.slice_three_writes_its_own_file()
        self.assertNotEqual(self.proved, self.repository.fingerprint())

    def test_the_file_the_later_slice_wrote_is_named_by_no_earlier_slice(self):
        self.slice_three_writes_its_own_file()
        self.assertNotIn('harness/slice_three.py', self.plan[0]['files'])

    def test_an_uncommitted_change_elsewhere_does_not_take_the_evidence_away(self):
        self.write('harness/slice_three.py', 'def three():\n    return 3\n')
        self.evaluate('tdd', self.citing(), records=self.journal(), attempt=2)


class TheSlicesOwnFilesMoved(ScopedToTheSlicesFiles):
    """The mirror, and the only thing that keeps the scoping from being a hole.

    Every way the code a check covered can move: committed, uncommitted, and
    deleted. Each must cost the citation its evidence, and the refusal must name
    the file rather than a tree, because the file is what a session can go and
    look at.
    """

    def test_a_committed_change_to_its_own_file_is_refused_by_name(self):
        self.write('harness/slice_one.py', 'def one():\n    return 2\n')
        self.commit('fix(SEEN-001): slice one again')
        self.assertIn('harness/slice_one.py', self.refusal())

    def test_an_uncommitted_change_to_its_own_file_is_refused_by_name(self):
        self.write('harness/slice_one.py', 'def one():\n    return 2\n')
        self.assertIn('harness/slice_one.py', self.refusal())

    def test_deleting_the_file_it_covered_is_refused_by_name(self):
        (self.root / 'harness' / 'slice_one.py').unlink()
        self.assertIn('harness/slice_one.py', self.refusal())

    def test_a_change_to_a_file_under_a_directory_the_slice_names_is_refused(self):
        """A slice naming a directory covers what is under it, and nothing beside it."""
        self.write('harness/one/deep.py', 'def deep():\n    return 1\n')
        self.write('harness/one_beside.py', 'def beside():\n    return 1\n')
        self.commit('feat(SEEN-001): a directory slice')
        proved = self.repository.fingerprint()
        plan = self.plan_with(files=['harness/one'])
        self.write('harness/one/deep.py', 'def deep():\n    return 2\n')
        self.assertIn('harness/one/deep.py',
                      self.refusal(records=self.journal(plan=plan, proved=proved)))

    def test_a_change_beside_a_directory_the_slice_names_is_not_inside_it(self):
        # The file beside the directory is committed before the round whose
        # checks are cited, so it is neither under the directory the slice names
        # nor among the files that round moved: the two ways into the comparison,
        # and this test is about a path that takes neither.
        self.write('harness/one_beside.py', 'def beside():\n    return 1\n')
        self.commit('feat(SEEN-001): a file beside the directory')
        self.write('harness/one/deep.py', 'def deep():\n    return 1\n')
        self.commit('feat(SEEN-001): a directory slice')
        proved = self.repository.fingerprint()
        plan = self.plan_with(files=['harness/one'])
        self.write('harness/one_beside.py', 'def beside():\n    return 2\n')
        self.evaluate('tdd', self.citing(), records=self.journal(plan=plan, proved=proved),
                      attempt=2)

    def test_a_slice_naming_no_files_is_held_to_the_whole_tree(self):
        """No scope is not an empty scope: an empty one would accept everything."""
        self.slice_three_writes_its_own_file()
        message = self.refusal(records=self.journal(plan=self.plan_with(files=[])))
        self.assertIn(self.JUDGED, message)


class UnattributableCitationFallsBack(ScopedToTheSlicesFiles):
    """A citation the journal cannot place is held to the strict whole-tree rule.

    Fail closed: a citation nothing can attribute is the case where the scoped
    comparison would be a guess, so it is refused rather than scoped to whatever
    happens to be at hand.

    Declaring null is no longer such a case by itself: a round that belongs to no
    single slice belongs to the plan and is judged over the plan's files, which
    `ARoundThatBelongsToNoSingleSlice` is about. What the two tests below keep is
    the case where it still is one, because these records do not agree: this one
    declares null and the tdd record of the round named slice 1.
    """

    def test_a_citation_that_names_its_slice_is_scoped_to_that_slice(self):
        self.slice_three_writes_its_own_file()
        self.evaluate('tdd', self.citing(position=1), records=self.journal(), attempt=2)

    def test_a_citation_the_journal_disagrees_with_is_held_to_the_whole_tree(self):
        self.slice_three_writes_its_own_file()
        message = self.refusal(data=self.citing(position=None))
        self.assertIn(self.JUDGED, message)
        self.assertIn(self.proved[:12], message)

    def test_the_whole_tree_refusal_says_that_is_what_it_compared(self):
        self.slice_three_writes_its_own_file()
        self.assertIn('whole tree', self.refusal(data=self.citing(position=None)))

    def test_a_tree_no_commit_carries_cannot_be_scoped_and_is_refused(self):
        """A check whose tree was never committed as it stood: nothing says which
        files it held, so the whole tree is the only comparison left."""
        self.slice_three_writes_its_own_file()
        message = self.refusal(records=self.journal(proved='f' * 64))
        self.assertIn(self.JUDGED, message)
        self.assertIn('whole tree', message)

    def test_the_fingerprint_this_rule_reads_is_the_one_the_repository_writes(self):
        """The scoped comparison identifies a check's tree by its fingerprint, so
        the two readings of that hash must agree, or the scope is read off the
        wrong commit."""
        self.assertEqual(gates.content_fingerprint(self.repository, 'HEAD'),
                         self.repository.fingerprint())


class ThePositionIsCorroborated(ScopedToTheSlicesFiles):
    """The scope may not be taken on the word of the record that wants it.

    F1 of this ticket's second review, reproduced end to end: the plan's slice 2
    names a file of its own, so a record citing slice 1's checks under position 2
    was compared against a file that had not moved and kept its evidence for code
    it had since rewritten. Declared honestly as position 1 the same citation was
    refused, which is the whole tell: the position decided the scope and nothing
    decided the position. What corroborates it now is the tdd record of the round
    that recorded the check, and a position nothing corroborates buys no scope at
    all.
    """

    def slice_one_is_rewritten(self):
        self.write('harness/slice_one.py', 'def one():\n    return 999\n')
        self.commit('fix(SEEN-001): rewrite the file slice one covered')

    def test_naming_another_slices_position_does_not_buy_that_slices_files(self):
        self.slice_one_is_rewritten()
        message = self.refusal(data=self.citing(position=2))
        self.assertIn(self.JUDGED, message)
        self.assertIn('whole tree', message)

    def test_the_refusal_says_which_slice_the_journal_declared_instead(self):
        self.slice_one_is_rewritten()
        self.assertIn('slice 1', self.refusal(data=self.citing(position=2)))

    def test_the_slice_it_named_really_had_not_moved(self):
        """Without this the refusal above could be a comparison with nothing to
        accept, which would pass whatever the rule did."""
        self.slice_one_is_rewritten()
        commit = gates._the_commit_holding(self.repository, self.proved)
        self.assertEqual(gates._moved_since(self.repository, commit, ['harness/slice_two.py']),
                         [])
        self.assertEqual(gates._moved_since(self.repository, commit, ['harness/slice_one.py']),
                         ['harness/slice_one.py'])

    def test_the_position_the_journal_declares_still_buys_its_own_files(self):
        """Corroboration grants the scope as well as withholding it: this is the
        citation SEEN-112 needed, and it still stands."""
        self.slice_three_writes_its_own_file()
        self.evaluate('tdd', self.citing(position=1), records=self.journal(), attempt=2)

    def test_an_attempt_that_never_advanced_out_of_tdd_corroborates_nothing(self):
        self.slice_three_writes_its_own_file()
        message = self.refusal(records=self.journal(corroborating=False))
        self.assertIn(self.JUDGED, message)
        self.assertIn('whole tree', message)

    def test_a_round_that_declared_no_position_lends_no_scope(self):
        """This ticket's own record 17 declares position 2 for a round whose
        behaviour says it belongs to no single slice. A round that declares null
        declares no mapping, and no mapping is not a mapping to anything."""
        self.slice_three_writes_its_own_file()
        message = self.refusal(records=self.journal(corroborated=None))
        self.assertIn(self.JUDGED, message)
        self.assertIn('whole tree', message)


class EveryEntryInTheScopeResolves(ScopedToTheSlicesFiles):
    """A file entry that matches no path makes the comparison vacuous.

    F2 of this ticket's second review. `git diff --name-only <commit> --
    harness/typo.py` exits 0 with no output, so a slice naming a path git cannot
    see accepted a citation however much the code had moved, and the realistic
    case is worse than a slice naming one path: a typo beside a test file that
    stood still. Every entry must resolve to something git can see in the commit
    the comparison is made against; one that does not is an untrustworthy scope
    rather than an empty one, so it falls back to the whole tree and says which
    entry could not be resolved.
    """

    def rewrite_the_file_slice_one_really_covered(self):
        self.write('harness/slice_one.py', 'def one():\n    return 999\n')
        self.commit('fix(SEEN-001): rewrite the file slice one covered')

    def test_a_typo_for_the_file_the_work_is_in_is_no_scope_at_all(self):
        self.rewrite_the_file_slice_one_really_covered()
        message = self.refusal(records=self.journal(
            plan=self.plan_with(files=['harness/slice_one_typo.py'])))
        self.assertIn('harness/slice_one_typo.py', message)
        self.assertIn('whole tree', message)

    def test_one_unresolvable_entry_beside_a_file_that_stood_still_is_refused(self):
        """The partial case: the scope is not trustworthy because part of it is
        not, however still the rest of it was."""
        self.rewrite_the_file_slice_one_really_covered()
        message = self.refusal(records=self.journal(
            plan=self.plan_with(files=['harness/slice_one_typ.py', 'harness/slice_two.py'])))
        self.assertIn('harness/slice_one_typ.py', message)
        self.assertNotIn('harness/slice_two.py', message)
        self.assertIn('whole tree', message)

    def test_a_gitignored_path_matches_nothing_git_can_see(self):
        self.write('.gitignore', '.harness-drafts/\n.harness.lock\n.env\n.env.local\n'
                                 'harness/ignored.py\n')
        self.write('harness/ignored.py', 'ignored = True\n')
        self.commit('chore(SEEN-001): ignore a path')
        message = self.refusal(records=self.journal(
            plan=self.plan_with(files=['harness/ignored.py'])))
        self.assertIn('harness/ignored.py', message)
        self.assertIn('whole tree', message)

    def test_the_entry_is_asked_of_the_commit_the_check_ran_against(self):
        """A file that did not exist yet is not code that check covered."""
        self.slice_three_writes_its_own_file()
        message = self.refusal(records=self.journal(
            plan=self.plan_with(files=['harness/slice_one.py', 'harness/slice_three.py'])))
        self.assertIn('harness/slice_three.py', message)
        self.assertIn('whole tree', message)

    def test_a_scope_whose_every_entry_resolves_is_compared_rather_than_refused(self):
        self.slice_three_writes_its_own_file()
        self.evaluate('tdd', self.citing(), attempt=2, records=self.journal(
            plan=self.plan_with(files=['harness/slice_one.py', 'harness/slice_two.py'])))


class TheRoundsOwnCommitSaysWhatItCovered(ScopedToTheSlicesFiles):
    """F1 of the third review: the corroboration was one round deep.

    A record's position was corroborated by the tdd record of the round that
    recorded the check, and that record's position had never itself been checked
    against any code: the content test is skipped for a same-attempt check, the
    route comparison only range-checks the position against the plan's length,
    and the model comparison returns while `[routing] shadow` is true. So attempt
    1 proved slice 1 and declared position 2 for it; attempt 2 rewrote slice one's
    file and cited the same checks under position 2; the claim corroborated
    itself, the scope became slice 2's untouched file and stale evidence was
    accepted, while the same citation declared honestly as position 1 was
    refused. Worse, a later record copies the position it reads from the earlier
    one, so one mis-declaration self-corroborated for the rest of the ticket.

    What settles it needs nobody's word: the commit carrying the tree the check
    ran against, whose diff with its parent is the change that round was. The
    plan's files stay in the comparison beside it, because a slice may name a file
    its round did not move and dropping it would accept a citation that is refused
    today.
    """

    def slice_one_is_rewritten(self):
        self.write('harness/slice_one.py', 'def one():\n    return 999\n')
        self.commit('fix(SEEN-001): rewrite the file slice one covered')

    def test_a_position_the_earlier_round_declared_wrongly_buys_no_scope(self):
        self.slice_one_is_rewritten()
        message = self.refusal(data=self.citing(position=2),
                               records=self.journal(corroborated=2))
        self.assertIn('harness/slice_one.py', message)

    def test_the_corroboration_really_was_satisfied(self):
        """Without this the refusal above could be the corroboration refusing,
        which would leave the mis-declaration reaching the scope untested."""
        records = self.journal(corroborated=2)
        files, because, named_by = gates._the_scope_a_citation_is_judged_in(records, 4, 2)
        self.assertEqual(files, ['harness/slice_two.py'], because)
        self.assertEqual(named_by, 'its slice')

    def test_the_file_the_mis_declaration_bought_really_had_not_moved(self):
        self.slice_one_is_rewritten()
        commit = gates._the_commit_holding(self.repository, self.proved)
        self.assertEqual(gates._moved_since(self.repository, commit,
                                            ['harness/slice_two.py']), [])

    def test_what_the_round_moved_is_read_from_the_commit_and_not_from_a_record(self):
        commit = gates._the_commit_holding(self.repository, self.proved)
        self.assertEqual(gates._the_files_the_round_moved(self.repository, commit),
                         ['harness/slice_one.py', 'harness/slice_two.py'])

    def test_a_file_the_round_moved_that_its_slice_never_names_is_compared_too(self):
        """The round committed slice two's file as well, so a later change to it
        changes code that check covered, whatever the plan calls that file."""
        self.write('harness/slice_two.py', 'def two():\n    return 22\n')
        self.commit('fix(SEEN-001): the other file that round moved')
        self.assertIn('harness/slice_two.py', self.refusal())

    def test_the_honest_declaration_still_carries_its_own_evidence(self):
        """The acceptance this rule must not cost: slice three wrote elsewhere,
        so slice one's green is still about slice one's code."""
        self.slice_three_writes_its_own_file()
        self.evaluate('tdd', self.citing(position=1), records=self.journal(), attempt=2)

    def test_the_commit_that_carries_the_tree_may_be_one_that_moved_no_code(self):
        """The shape every real journal is in, and the fixture was not: the harness
        writes its records into the same branch, so a record-only commit follows
        the work and carries the same counted content. It is the newest commit
        whose fingerprint matches, so it is the one found, and its own change is
        nothing this comparison counts. What moved is read from the commit that
        moved something, walking back while the content stands still."""
        self.write('docs/harness/history/SEEN-001/0002.json', '{"sequence": 2}\n')
        self.commit('docs(SEEN-001): a record written after the work')
        commit = gates._the_commit_holding(self.repository, self.proved)
        self.assertEqual(commit, self.repository.head())
        self.assertEqual(gates._the_files_the_round_moved(self.repository, commit),
                         ['harness/slice_one.py', 'harness/slice_two.py'])

    def test_a_record_only_commit_does_not_cost_a_citation_its_scope(self):
        """What the measurement caught: on SEEN-112 slice 1's green fell back to
        the whole tree for this reason alone, so the scoped comparison this ticket
        exists for was unreachable in every journal the harness has written."""
        self.write('docs/harness/history/SEEN-001/0002.json', '{"sequence": 2}\n')
        self.commit('docs(SEEN-001): a record written after the work')
        self.slice_three_writes_its_own_file()
        self.evaluate('tdd', self.citing(), records=self.journal(), attempt=2)

    def test_the_round_is_still_what_moved_and_not_everything_since(self):
        """The walk back stops at the first commit that moved something, so it
        cannot collect a later slice's files and refuse on those."""
        self.write('docs/harness/history/SEEN-001/0002.json', '{"sequence": 2}\n')
        self.commit('docs(SEEN-001): a record written after the work')
        self.slice_three_writes_its_own_file()
        commit = gates._the_commit_holding(self.repository, self.proved)
        self.assertNotIn('harness/slice_three.py',
                         gates._the_files_the_round_moved(self.repository, commit))

    def test_a_round_whose_commit_has_no_parent_falls_back_to_the_whole_tree(self):
        """A check whose tree is the project's first commit belongs to no round of
        this ticket's work: there is no parent for its change to be a change
        against, so what it covered cannot be established and it fails closed."""
        root = self.git('rev-list', '--max-parents=0', 'HEAD')
        message = self.refusal(records=self.journal(
            plan=self.plan_with(files=['harness/thresholds.toml']),
            proved=gates.content_fingerprint(self.repository, root)))
        self.assertIn(self.JUDGED, message)
        self.assertIn('whole tree', message)
        self.assertIn('which files that round moved cannot be read', message)

    def test_the_file_that_first_commit_names_really_had_not_moved(self):
        """Without this the refusal above could be a comparison that had already
        found something moved, which would pass whatever the rule did."""
        root = self.git('rev-list', '--max-parents=0', 'HEAD')
        self.assertEqual(gates._moved_since(self.repository, root,
                                            ['harness/thresholds.toml']), [])


class TheProcedureRewritesTheTicketFile(ScopedToTheSlicesFiles):
    """Record 50: the defect under this whole chain, and it is a step of the procedure.

    A check records the fingerprint of a tree, and what makes that tree findable
    afterwards is the commit that carried the work. Between those two moments the
    workflow requires the `## Outcome`, the frontmatter `status` and the criteria
    ticks to be written into the ticket file, so the ticket file is guaranteed to
    differ, the fingerprint counts it, and no commit holds the tree the check ran
    against. Measured on this ticket's own branch: green 35's tree is the content
    of none of the last sixty commits, and it is `36b3c57`'s content with the
    ticket file read as it stood at the check. Every refusal in this chain traces
    to a step the harness itself mandates.

    The fingerprint is not what changes. It keeps covering the whole ticket file,
    which is what gives the receipt its meaning and what SEEN-109 withdrew an
    attempt to weaken. What becomes tolerant is the search for the commit holding
    a check's tree, over the one path the procedure rewrites and no other.

    The mirror is the whole risk, because this makes a search succeed where it
    used to fail: a commit differing in the ticket file and in anything else must
    match nothing.
    """

    OUTCOME = '\n## Outcome\n\nThe slice was proved, and the review read it.\n'

    def the_outcome_is_written(self):
        """What the procedure asks for before review is left, on the real file."""
        path = self.root / self.ticket_file
        path.write_text(path.read_text() + self.OUTCOME)

    def the_criteria_are_ticked(self):
        """And what it asks for after the reviewer has read, in the same file."""
        path = self.root / self.ticket_file
        path.write_text(path.read_text().replace('- [ ]', '- [x]'))

    def the_round_committed_with_its_outcome(self):
        """The shape the procedure forces on every round, which the fixture lacked.

        The checks run on a working tree; the ticket file is then rewritten
        because the workflow says so; and the commit carrying the work carries
        that rewrite with it. So the tree the checks ran against is no commit's
        content, and the one path it differs by is the one the procedure wrote.
        """
        self.write('harness/slice_one.py', 'def one():\n    return 11\n')
        proved = self.repository.fingerprint()
        self.the_outcome_is_written()
        self.commit('feat(SEEN-001): the round, and the outcome the procedure asks for')
        return proved

    def test_a_green_whose_round_rewrote_the_ticket_file_is_still_citable(self):
        """This ticket's own case, and the reason the tolerance exists."""
        proved = self.the_round_committed_with_its_outcome()
        self.the_criteria_are_ticked()
        self.slice_three_writes_its_own_file()
        self.evaluate('tdd', self.citing(), records=self.journal(proved=proved), attempt=2)

    def test_the_tree_really_is_no_commits_content_so_the_acceptance_is_not_free(self):
        """Without this the acceptance above could be an exact match all along."""
        proved = self.the_round_committed_with_its_outcome()
        self.assertIsNone(gates._the_commit_holding(self.repository, proved))

    def test_the_commit_it_is_held_by_is_the_one_the_work_was_committed_in(self):
        proved = self.the_round_committed_with_its_outcome()
        self.assertEqual(gates._the_commit_holding(self.repository, proved, self.ticket_file),
                         self.repository.head())

    def test_the_scope_the_tolerance_grants_still_refuses_by_name(self):
        """The mirror that matters at the gate: a scope granted is a scope
        compared, so the file that round proved moving still costs the citation
        its evidence, and by name rather than as a tree."""
        proved = self.the_round_committed_with_its_outcome()
        self.write('harness/slice_one.py', 'def one():\n    return 12\n')
        self.commit('fix(SEEN-001): rewrite the file that round proved')
        message = self.refusal(records=self.journal(proved=proved))
        self.assertIn('harness/slice_one.py', message)
        self.assertNotIn('whole tree', message)

    def test_a_tree_differing_in_a_source_file_too_is_held_by_no_commit(self):
        """The guard the tolerance is worth nothing without: one path is
        tolerated, and a commit differing in it and in anything else is not the
        tree. A search that substituted two paths at once, or every path the
        procedure touches, would pass its neighbours and fail here.
        """
        self.write('harness/slice_one.py', 'def one():\n    return 11\n')
        proved = self.repository.fingerprint()
        self.the_outcome_is_written()
        self.write('harness/slice_two.py', 'def two():\n    return 22\n')
        self.commit('feat(SEEN-001): the round, its outcome, and a second file')
        self.assertIsNone(gates._the_commit_holding(self.repository, proved, self.ticket_file))

    def test_the_second_difference_is_the_only_reason_that_one_is_not_found(self):
        """Without this the refusal above could be the fixture failing to match
        for some reason of its own, which would pass whatever the search did."""
        self.write('harness/slice_one.py', 'def one():\n    return 11\n')
        proved = self.repository.fingerprint()
        self.the_outcome_is_written()
        self.commit('feat(SEEN-001): the round and its outcome, and nothing else')
        self.assertEqual(gates._the_commit_holding(self.repository, proved, self.ticket_file),
                         self.repository.head())

    def test_a_citation_whose_round_moved_a_second_file_falls_back_as_before(self):
        """The same two differences at the gate: no scope is granted, so the
        strict whole-tree rule stands where it stood."""
        self.write('harness/slice_one.py', 'def one():\n    return 11\n')
        proved = self.repository.fingerprint()
        self.the_outcome_is_written()
        self.write('harness/slice_two.py', 'def two():\n    return 22\n')
        self.commit('feat(SEEN-001): the round, its outcome, and a second file')
        self.assertIn('whole tree', self.refusal(records=self.journal(proved=proved)))

    def test_a_document_that_is_not_the_ticket_file_is_not_tolerated(self):
        """A path is tolerated because the procedure rewrites it between a check
        and its commit, not because it is documentation."""
        self.write('docs/architecture.md', 'The architecture.\n')
        self.commit('docs(SEEN-001): a document the procedure does not rewrite')
        self.write('harness/slice_one.py', 'def one():\n    return 11\n')
        proved = self.repository.fingerprint()
        self.write('docs/architecture.md', 'The architecture, restated.\n')
        self.commit('feat(SEEN-001): the round, and a document beside it')
        self.assertIsNone(gates._the_commit_holding(self.repository, proved, self.ticket_file))

    def test_a_commit_holding_the_tree_exactly_is_preferred_to_a_substitution(self):
        """Two commits can answer, and the one that needs no reconstruction wins."""
        exact = self.repository.head()
        self.the_outcome_is_written()
        self.commit('docs(SEEN-001): the outcome, and nothing else')
        self.assertEqual(gates._the_commit_holding(self.repository, self.proved,
                                                  self.ticket_file), exact)

    def test_the_newer_commit_really_would_have_answered_by_substitution(self):
        """Without this the preference above could be the newer commit matching
        nothing, which would pass whatever the order did. The substitution is done
        here by hand, which is how the reviewer reproduced a recorded fingerprint
        twice before any of this was code."""
        exact = self.repository.head()
        self.the_outcome_is_written()
        self.commit('docs(SEEN-001): the outcome, and nothing else')
        self.assertNotEqual(self.repository.head(), exact)
        listing = gates._tree_listing(self.repository, self.repository.head())
        listing[self.ticket_file] = gates._tree_listing(self.repository,
                                                        exact)[self.ticket_file]
        self.assertEqual(gates._fingerprint_of(listing), self.proved)

    def test_what_the_round_moved_leaves_out_the_path_the_procedure_rewrites(self):
        """Left in, it would cost every citation its evidence: the ticket file is
        rewritten again after the review, so a comparison counting it refuses
        whatever the code did."""
        proved = self.the_round_committed_with_its_outcome()
        commit = gates._the_commit_holding(self.repository, proved, self.ticket_file)
        self.assertEqual(gates._the_files_the_round_moved(self.repository, commit,
                                                          self.ticket_file),
                         ['harness/slice_one.py'])

    def test_a_commit_that_only_rewrote_the_ticket_file_is_not_the_round(self):
        """The commit found is often the one the procedure wrote and nothing else,
        which is what the measurement on this branch met: green 35's tree is held
        by a docs commit whose own change is the ticket file. A commit that moved
        only that path did not carry the work, so the question goes to its parent,
        exactly as it does for a commit that moved nothing counted at all."""
        self.the_outcome_is_written()
        self.commit('docs(SEEN-001): the outcome, written before the review is left')
        self.assertEqual(gates._the_files_the_round_moved(self.repository,
                                                          self.repository.head(),
                                                          self.ticket_file),
                         ['harness/slice_one.py', 'harness/slice_two.py'])

    def test_a_journal_that_cannot_say_which_ticket_file_tolerates_nothing(self):
        """No path at all where the journal cannot say which ticket file it is:
        an absence is not a licence, and the search stays exactly as strict."""
        proved = self.the_round_committed_with_its_outcome()
        self.assertIsNone(gates._the_commit_holding(self.repository, proved, None))


class AnEntryGitWillNotTakeAsAPathspec(ScopedToTheSlicesFiles):
    """F6 of the third review: an entry resolving outside the repository.

    `git ls-tree -r <commit> -- ../elsewhere.py` exits non-zero, so the session
    met `fatal: ../elsewhere.py is outside repository at '/var/folders/...'`,
    naming a temporary directory, instead of the sentence every other
    unresolvable entry gets. The verdict was already the right one; what was
    wrong was that it arrived as git's crash rather than as the harness saying
    which entry in the plan is wrong.
    """

    def refusal_over(self, *files):
        """The refusal a citation meets when its slice names these entries."""
        self.slice_three_writes_its_own_file()
        return self.refusal(records=self.journal(plan=self.plan_with(files=list(files))))

    def test_a_path_escaping_the_repository_is_named_as_an_entry_that_resolves_to_nothing(self):
        message = self.refusal_over('../outside.py')
        self.assertIn('../outside.py', message)
        self.assertIn('whole tree', message)

    def test_it_is_the_harness_sentence_and_not_gits_crash(self):
        message = self.refusal_over('../outside.py')
        self.assertNotIn('fatal:', message)
        self.assertNotIn('outside repository', message)

    def test_an_absolute_path_outside_the_working_tree_is_the_same_answer(self):
        message = self.refusal_over('/etc/hosts', 'harness/slice_one.py')
        self.assertIn('/etc/hosts', message)
        self.assertNotIn('fatal:', message)
        self.assertIn('whole tree', message)


class TheFingerprintTheRuleReads(ScopedToTheSlicesFiles):
    """Both halves of the fingerprint, because this rule needs both.

    F5 of this ticket's second review: the two readings were pinned to each other
    on a clean tree only, so a change to the pending-and-untracked half, or to
    `excluding`, would have left the pinning passing while `_the_commit_holding`
    stopped matching any check recorded on a tree with untracked files. Every
    cross-attempt citation would then fall back and be refused: closed rather
    than open, so the cost is the feature quietly ceasing to work with nothing
    failing.
    """

    def test_a_tree_with_an_untracked_file_is_found_in_the_commit_that_carries_it(self):
        self.write('harness/slice_four.py', 'def four():\n    return 4\n')
        taken = self.repository.fingerprint()
        self.assertNotEqual(taken, gates.content_fingerprint(self.repository, 'HEAD'),
                            'the untracked half of the fingerprint counted nothing')
        self.commit('feat(SEEN-001): slice four')
        self.assertEqual(gates.content_fingerprint(self.repository, 'HEAD'), taken)
        self.assertEqual(gates._the_commit_holding(self.repository, taken),
                         self.repository.head())

    def test_a_modified_tracked_file_is_found_in_the_commit_that_carries_it(self):
        self.write('harness/slice_one.py', 'def one():\n    return 4\n')
        taken = self.repository.fingerprint()
        self.assertNotEqual(taken, gates.content_fingerprint(self.repository, 'HEAD'))
        self.commit('fix(SEEN-001): slice one again')
        self.assertEqual(gates.content_fingerprint(self.repository, 'HEAD'), taken)

    def test_a_deleted_file_is_found_in_the_commit_that_carries_the_deletion(self):
        (self.root / 'harness' / 'slice_two.py').unlink()
        taken = self.repository.fingerprint()
        self.assertNotEqual(taken, gates.content_fingerprint(self.repository, 'HEAD'))
        self.commit('fix(SEEN-001): drop slice two')
        self.assertEqual(gates.content_fingerprint(self.repository, 'HEAD'), taken)

    def test_excluding_leaves_a_path_out_and_excluding_nothing_is_the_plain_reading(self):
        self.assertEqual(self.repository.fingerprint(excluding=()),
                         self.repository.fingerprint())
        self.assertNotEqual(self.repository.fingerprint(excluding=('harness/slice_one.py',)),
                            self.repository.fingerprint())

    def test_the_journal_is_left_out_of_both_readings(self):
        """The exclusion the two readings must agree on: a check's tree is
        recorded in the journal that the commit after it carries."""
        self.write('docs/harness/history/SEEN-001/0001.json', '{"sequence": 1}\n')
        taken = self.repository.fingerprint()
        self.commit('docs(SEEN-001): a record')
        self.assertEqual(gates.content_fingerprint(self.repository, 'HEAD'), taken)


class TheRegressionIsHeldToTheWholeTree(ScopedToTheSlicesFiles):
    """The one citation that is scoped to nothing on purpose, and says so.

    The regression covers the suite rather than a slice, so it is compared over
    the whole tree by design. Scoped to nothing is not the same as unexplained:
    every other way a comparison falls back to the whole tree names its reason,
    and this one has to name its own or the refusal reads as a gap in the gate.
    """

    def an_attempt_that_finished(self):
        """Attempt 1 proved slice one and ran its regression, then advanced."""
        return self.records + [
            advance_record(2, 'solution', dict(mode='code', slices=self.plan), attempt=1),
            check_record(3, 'red', attempt=1, after=self.proved),
            check_record(4, 'green', attempt=1, after=self.proved),
            check_record(5, 'regression', attempt=1, after=self.proved),
            advance_record(6, 'tdd',
                           dict(mode='code',
                                slices=[dict(position=1, behaviour='Slice one, proved here',
                                             failure_reason='expected 1, received nothing',
                                             red=3, green=4)],
                                regression=5),
                           attempt=1, to_stage='review'),
            coverage_record(7, attempt=2)]

    def citing_that_regression(self):
        return self.template('tdd',
                             slices=[dict(position=1,
                                          behaviour='Slice one, proved in attempt 1',
                                          failure_reason='expected 1, received nothing',
                                          red=3, green=4)],
                             regression=5)

    def test_a_regression_from_an_earlier_attempt_says_why_it_is_the_whole_tree(self):
        self.slice_three_writes_its_own_file()
        message = self.refusal(data=self.citing_that_regression(),
                               records=self.an_attempt_that_finished())
        self.assertIn('tree moved under check 5', message)
        self.assertIn('covers the suite rather than a slice', message)

    def test_the_reason_is_a_sentence_rather_than_a_missing_one(self):
        self.slice_three_writes_its_own_file()
        message = self.refusal(data=self.citing_that_regression(),
                               records=self.an_attempt_that_finished())
        self.assertNotIn('because None', message)

    def test_a_record_that_declares_no_slice_does_not_scope_the_regression(self):
        """The plan reading a null position gets is the slice citation's and not
        the regression's: the regression covers the suite, and it says so however
        the record citing it declares the position of the round beside it."""
        self.slice_three_writes_its_own_file()
        data = self.citing_that_regression()
        data['slices'][0]['position'] = None
        message = self.refusal(data=data, records=self.an_attempt_that_finished())
        self.assertIn('tree moved under check 5', message)
        self.assertIn('covers the suite rather than a slice', message)

    def test_the_slice_beside_it_keeps_the_scope_the_journal_corroborates(self):
        """The regression falling back does not take slice one's evidence with it:
        the refusal above is about check 5 and not about checks 3 and 4."""
        self.slice_three_writes_its_own_file()
        records = self.an_attempt_that_finished()
        for number in (3, 4):
            files, because, named_by = gates._the_scope_a_citation_is_judged_in(records,
                                                                               number, 1)
            self.assertEqual(files, ['harness/slice_one.py'], because)
            self.assertEqual(named_by, 'its slice')


class ARoundThatBelongsToNoSingleSlice(ScopedToTheSlicesFiles):
    """A null position is a claim on the plan, so the plan is what it is judged over.

    Record 47 of this ticket's own journal, found by running its own rule on its
    own journal. Attempt 4's accepted tdd record declared null for the checks it
    recorded, which is what the template asks a round that belongs to no single
    slice to say, and attempt 5 citing that pair was compared over the whole tree
    and refused: "compared over the whole tree because this citation names no
    slice, so there is nothing to scope the comparison to". A round after a return
    that touches more than one slice's work declares null by the template's own
    instruction, so the rule carried a tidy single-slice round's evidence forward
    and dropped the evidence of exactly the rounds a return produces, which is the
    case this ticket was written for.

    A round that belongs to no single slice belongs to the plan rather than to
    nothing. Its scope is every file the plan's slices name, which is wider than
    one slice's files and narrower than the tree, and wider is stricter: this is
    the one rule in this ticket that accepts more, so the mirror below is what
    keeps it from being a hole. Every file the plan names is in the comparison,
    and a change to any of them costs the citation its evidence by name.
    """

    def setUp(self):
        super().setUp()
        # Slice three's file exists in the tree the cited checks ran against,
        # because an entry git cannot see in that tree costs the scope whoever
        # named it. The plan reading is held to that rule exactly as the slice
        # reading is, and the case where it is not met has a test of its own.
        self.write('harness/slice_three.py', 'def three():\n    return 3\n')
        self.commit('feat(SEEN-001): slice three, before the round that is cited')
        self.proved = self.repository.fingerprint()

    def null_citation(self):
        return self.citing(position=None)

    def a_null_round(self, **changes):
        """The journal of a round that declared null for the checks it recorded."""
        return self.journal(corroborated=None, **changes)

    def a_file_the_plan_names_nowhere_moves(self):
        self.write('harness/elsewhere.py', 'def elsewhere():\n    return 0\n')
        self.commit('chore(SEEN-001): a file the plan names nowhere')

    def a_plan_file_moves(self, path):
        self.write(path, 'def moved():\n    return 999\n')
        self.commit(f'fix(SEEN-001): rewrite {path}')

    def test_a_null_round_stands_when_a_file_the_plan_names_nowhere_moved(self):
        """The citation record 47 recorded as refused, accepted: this is the whole
        point of the change, and every test below it is what holds it in place."""
        self.a_file_the_plan_names_nowhere_moves()
        self.evaluate('tdd', self.null_citation(), records=self.a_null_round(), attempt=2)

    def test_the_tree_really_did_move_so_that_acceptance_is_not_vacuous(self):
        self.a_file_the_plan_names_nowhere_moves()
        self.assertNotEqual(self.proved, self.repository.fingerprint())

    def test_the_file_that_moved_is_named_by_no_slice_in_the_plan(self):
        self.a_file_the_plan_names_nowhere_moves()
        for entry in self.plan:
            self.assertNotIn('harness/elsewhere.py', entry['files'])

    def test_a_change_to_the_first_slices_file_is_refused_by_name(self):
        self.a_plan_file_moves('harness/slice_one.py')
        message = self.refusal(data=self.null_citation(), records=self.a_null_round())
        self.assertIn('harness/slice_one.py', message)
        self.assertNotIn('whole tree', message)

    def test_a_change_to_a_middle_slices_file_is_refused_by_name(self):
        """The mirror that matters most: slice two is a slice this round is not,
        and the union is what puts its file in the comparison at all."""
        self.a_plan_file_moves('harness/slice_two.py')
        message = self.refusal(data=self.null_citation(), records=self.a_null_round())
        self.assertIn('harness/slice_two.py', message)
        self.assertNotIn('whole tree', message)

    def test_a_change_to_the_last_slices_file_is_refused_by_name(self):
        self.a_plan_file_moves('harness/slice_three.py')
        message = self.refusal(data=self.null_citation(), records=self.a_null_round())
        self.assertIn('harness/slice_three.py', message)
        self.assertNotIn('whole tree', message)

    def test_an_uncommitted_change_to_a_file_the_plan_names_is_refused_by_name(self):
        self.write('harness/slice_two.py', 'def two():\n    return 999\n')
        message = self.refusal(data=self.null_citation(), records=self.a_null_round())
        self.assertIn('harness/slice_two.py', message)

    def test_deleting_a_file_the_plan_names_is_refused_by_name(self):
        (self.root / 'harness' / 'slice_two.py').unlink()
        message = self.refusal(data=self.null_citation(), records=self.a_null_round())
        self.assertIn('harness/slice_two.py', message)

    def test_the_refusal_says_the_files_are_the_plans_and_not_one_slices(self):
        """Whose files the comparison was made over is what a session reading the
        refusal needs: a null round is told it was judged against the plan."""
        self.a_plan_file_moves('harness/slice_two.py')
        message = self.refusal(data=self.null_citation(), records=self.a_null_round())
        self.assertIn('the plan names', message)
        self.assertNotIn('its slice names', message)

    def test_the_scope_is_every_slices_files_and_nothing_beside_them(self):
        scope = gates._the_scope_a_citation_is_judged_in(self.a_null_round(), 4, None)
        files, because, named_by = scope
        self.assertEqual(files, ['harness/slice_one.py', 'harness/slice_three.py',
                                 'harness/slice_two.py'], because)
        self.assertEqual(named_by, 'the plan')

    def test_a_null_round_no_tdd_record_mentions_is_judged_over_the_plan_too(self):
        """A null position claims no slice, so there is nothing for another record
        to corroborate: the union is read from the accepted plan and from git, and
        no position in the citing record can widen or narrow it. Corroboration
        withholds a scope that rests on a claim, and this scope rests on none."""
        self.a_file_the_plan_names_nowhere_moves()
        self.evaluate('tdd', self.null_citation(),
                      records=self.journal(corroborating=False), attempt=2)

    def test_that_uncorroborated_null_still_loses_its_evidence_to_a_plan_file(self):
        self.a_plan_file_moves('harness/slice_two.py')
        message = self.refusal(data=self.null_citation(),
                               records=self.journal(corroborating=False))
        self.assertIn('harness/slice_two.py', message)

    def test_declaring_null_where_the_round_named_a_slice_settles_nothing(self):
        """Null is a claim and not a shrug, so a record declaring it where the
        accepted tdd record named slice 1 is the same disagreement the numbered
        direction already falls closed on, and neither reading wins. Otherwise
        null would be the word a record uses to reach the plan's files while the
        journal says which one slice that round worked, and a claim the chain
        contradicts would decide the comparison."""
        self.a_file_the_plan_names_nowhere_moves()
        message = self.refusal(data=self.null_citation(), records=self.journal())
        self.assertIn('whole tree', message)
        self.assertIn('slice 1', message)

    def test_that_disagreement_would_otherwise_have_been_accepted(self):
        """Without this the refusal above could be a comparison with nothing to
        accept: the file that moved is named by no slice, so the plan reading
        would have carried the citation had the disagreement not stopped it."""
        self.a_file_the_plan_names_nowhere_moves()
        self.evaluate('tdd', self.null_citation(), records=self.a_null_round(), attempt=2)

    def test_a_plan_whose_slices_name_no_file_is_no_scope_at_all(self):
        """An absence of files is not an empty comparison: an empty one accepts
        every citation, so it falls back to the whole tree the way one slice
        naming no file already does."""
        self.a_file_the_plan_names_nowhere_moves()
        message = self.refusal(data=self.null_citation(),
                               records=self.a_null_round(
                                   plan=[dict(entry, files=[]) for entry in self.plan]))
        self.assertIn('whole tree', message)
        self.assertIn('nothing in the plan', message)

    def test_a_plan_with_an_entry_git_cannot_see_falls_back_to_the_whole_tree(self):
        """The conservative side of the change, and the side a rule that accepts
        more has to fall on: one entry that resolves to nothing in the tree the
        check ran against makes the plan reading untrustworthy rather than
        narrower, so it is the whole tree and the entry is named."""
        self.a_file_the_plan_names_nowhere_moves()
        message = self.refusal(
            data=self.null_citation(),
            records=self.a_null_round(plan=self.plan_with(
                files=['harness/slice_one.py', 'harness/slice_one_typo.py'])))
        self.assertIn('harness/slice_one_typo.py', message)
        self.assertIn('whole tree', message)

    def test_a_numbered_citation_is_still_scoped_to_its_own_slice_alone(self):
        """The plan reading belongs to the round that belongs to no slice, and to
        no other: a round that names slice 1 keeps slice 1's files, so a change to
        slice two's file leaves its evidence standing."""
        self.a_plan_file_moves('harness/slice_two.py')
        self.evaluate('tdd', self.citing(position=1), records=self.journal(), attempt=2)


class APairIsJudgedByItsGreen(ScopedToTheSlicesFiles):
    """A red's standing rests on its green's tree, because it can have none of its own.

    Ruud's decision, recorded at record 54 of this ticket's journal after two
    rounds reached the same reading and declined to take it on their own
    authority. The measurement that forced it: a red runs on a tree holding the
    test without the code that answers it, and what gets committed is the green,
    so no commit ever carries a red's tree. None of SEEN-112's five reds nor this
    ticket's red 34 is any commit's content, modulo any single path. Cross-attempt
    citation therefore worked for a green and could never work for a red, and
    because a slice entry requires both halves, every cross-attempt pair fell
    closed on its red however untouched its code was.

    What a red loses is one thing, a tree test that could never pass for it. What
    it keeps is everything else, and each of those has a test: it exited non-zero
    and `checks.demonstrates_failure` holds of it, below; it precedes its green,
    slices do not overlap and the regression is last, in `OrderingAcrossAttempts`;
    it is the right phase at the right stage, in `TddGateTest` and below.
    """

    def a_red_whose_tree_no_commit_carries(self, **changes):
        """The shape of every real red, and of this ticket's own red 34."""
        return self.journal(red_proved='f' * 64, **changes)

    def test_the_fixture_really_models_a_red_no_commit_carries(self):
        """Without this the acceptance below could be an exact match all along."""
        self.assertIsNone(gates._the_commit_holding(self.repository, 'f' * 64))
        self.assertIsNotNone(gates._the_commit_holding(self.repository, self.proved))

    def test_a_pair_stands_when_only_its_green_is_findable(self):
        """The citation this ticket has been blocked on for two rounds."""
        self.slice_three_writes_its_own_file()
        self.evaluate('tdd', self.citing(), records=self.a_red_whose_tree_no_commit_carries(),
                      attempt=2)

    def test_the_green_it_rests_on_was_really_compared(self):
        """So the acceptance above is worth what the green's comparison is worth: a
        change to the file slice one covers takes the pair down, by name."""
        self.write('harness/slice_one.py', 'def one():\n    return 999\n')
        self.commit('fix(SEEN-001): rewrite the file slice one covered')
        message = self.refusal(records=self.a_red_whose_tree_no_commit_carries())
        self.assertIn('harness/slice_one.py', message)
        self.assertIn('check 4', message)

    def red_that_did_not_fail(self, exit_code):
        records = self.a_red_whose_tree_no_commit_carries()
        for record in records:
            if record['sequence'] == 3:
                record['data']['exit_code'] = exit_code
        return self.refusal(records=records)

    def test_an_exempt_red_that_passed_is_still_refused(self):
        """The one thing this harness refuses outright, and the exemption is not a
        way round it: the phase and the failure are read from the record, which is
        where they always were."""
        self.assertIn('did not fail', self.red_that_did_not_fail(0))

    def test_an_exempt_red_that_timed_out_is_still_refused(self):
        """A timeout is a fact about the runner rather than about the behaviour."""
        self.assertIn('did not fail', self.red_that_did_not_fail(124))

    def test_an_exempt_red_from_another_stage_is_still_refused(self):
        records = self.a_red_whose_tree_no_commit_carries()
        for record in records:
            if record['sequence'] == 3:
                record['stage'] = 'review'
        self.assertIn('counts only for the stage that produced it',
                      self.refusal(records=records))

    def test_a_red_that_is_not_there_at_all_is_still_refused(self):
        """Nothing is exempted by being absent: the green cannot carry a half the
        journal does not have."""
        data = self.citing()
        data['slices'][0]['red'] = 99
        self.assertIn('no such check', self.refusal(data=data))


class NoPairSurvivesItsGreensRefusal(ScopedToTheSlicesFiles):
    """The mirror that decides whether this is a fix or a hole.

    The change makes the gate accept more, so what it still refuses is the whole
    question: a red may not be citable where its green is not. The exemption is
    not a rule about reds, it is the pair being judged once at the half that can
    be judged, so a green that loses its evidence takes its red down with it.

    In the code that is structural rather than a matter of statement order: the
    exemption is reached only by handing the red the green `cited_check` has
    already returned, so there is no way to write the red's citation that does not
    first make the green's comparison and raise on it.
    """

    def both_halves_stale(self, **changes):
        """Neither tree is any commit's content: the worst case for the pair."""
        return self.journal(proved='f' * 64, red_proved='e' * 64, **changes)

    def test_a_pair_whose_green_is_refused_fails_as_a_pair(self):
        self.slice_three_writes_its_own_file()
        self.assertIn('tree moved under check 4', self.refusal(records=self.both_halves_stale()))

    def test_the_refusal_is_the_greens_and_never_the_reds(self):
        """A red the gate exempts cannot be the reason for anything it says."""
        self.slice_three_writes_its_own_file()
        self.assertNotIn('check 3', self.refusal(records=self.both_halves_stale()))

    def test_the_greens_own_file_moving_takes_the_pair_down_too(self):
        """The scoped refusal and not only the whole-tree one: a green whose scope
        was granted and then broken by name is still the end of its pair."""
        self.write('harness/slice_one.py', 'def one():\n    return 999\n')
        self.commit('fix(SEEN-001): rewrite the file slice one covered')
        message = self.refusal(records=self.journal(red_proved='e' * 64))
        self.assertIn('harness/slice_one.py', message)


class WhereTheJournalPutsAnExemptRed(ScopedToTheSlicesFiles):
    """A red judged by its green is still the red the journal says it is.

    F1 of the fifth review, reproduced end to end. Exempting a red from the tree
    comparison took its attribution with it, because the attribution had nowhere
    else to be spent: a contradicted position wins no scope, the comparison falls
    back to the whole tree, and the refusal carries the disagreement. With the
    comparison gone for a red there was nothing left for the contradiction to be
    spent on, so a slice entry could join one round's red to another round's green
    and the gate took its word for it, although the accepted tdd record of the
    round that recorded the red named another slice for it. The motive is in the
    same reproduction: the honest citation of the second round's own red, which
    exited zero, is refused for not having failed, and stealing a red that did
    fail cost nothing at all.

    Two rounds in attempt 1 with one accepted tdd record naming both is what makes
    the theft reachable. The pair passes every other rule: both halves are from one
    attempt, the ordering has no objection, and the green is attributed to the very
    position the citing record declares, so its own comparison is made over its own
    slice's files and accepted.
    """

    def setUp(self):
        super().setUp()
        # Slice three's file exists in the tree the cited checks ran against,
        # because the plan reading below is held to every entry resolving and an
        # entry git cannot see costs the scope whoever named it.
        self.write('harness/slice_three.py', 'def three():\n    return 3\n')
        self.commit('feat(SEEN-001): slice three, before the rounds that are cited')
        self.proved = self.repository.fingerprint()

    def rounds(self, mentioning=(1, 2), positions=(1, 2)):
        """Two rounds in attempt 1, and the tdd record that attributed them.

        `mentioning` is which of the two rounds that record carries, by round
        number rather than by position, because a check no accepted record
        mentions at all is an absence and not a contradiction. `positions` is
        what it declared for each, null included: the template asks a round that
        belongs to no single slice to declare null, so that is the commonest
        thing an accepted record says and not an odd case.
        Each red ran against a tree no commit carries, which is every real red's
        shape and the reason the exemption exists.
        """
        attributed = [dict(position=positions[0], behaviour='Round one, which proved slice one',
                           failure_reason='expected 1, received nothing', red=3, green=4),
                      dict(position=positions[1], behaviour='Round two, which proved slice two',
                           failure_reason='expected 2, received nothing', red=5, green=6)]
        entries = [entry for round_, entry in zip((1, 2), attributed) if round_ in mentioning]
        now = self.repository.fingerprint()
        return self.records + [
            advance_record(2, 'solution', dict(mode='code', slices=self.plan), attempt=1),
            check_record(3, 'red', attempt=1, after='f' * 64),
            check_record(4, 'green', attempt=1, after=self.proved),
            check_record(5, 'red', attempt=1, after='e' * 64),
            check_record(6, 'green', attempt=1, after=self.proved),
            advance_record(7, 'tdd', dict(mode='code', slices=entries, regression=6),
                           attempt=1, to_stage='review'),
            check_record(8, 'red', attempt=2, after=now),
            check_record(9, 'green', attempt=2, after=now),
            check_record(10, 'regression', attempt=2, after=now),
            coverage_record(11, attempt=2)]

    def citing(self, position=2, red=3, green=6, **changes):
        """Attempt 2 citing a pair from attempt 1, beside the slice it proved here."""
        data = self.template(
            'tdd',
            slices=[dict(position=position, behaviour='The pair this record calls one round',
                         failure_reason='expected a refusal, received none',
                         red=red, green=green),
                    dict(position=3, behaviour='Slice three, proved in this attempt',
                         failure_reason='expected 3, received nothing', red=8, green=9)],
            regression=10)
        data.update(changes)
        return data

    def refusal(self, data=None, records=None):
        return super().refusal(data or self.citing(), records or self.rounds())

    def test_a_red_the_journal_puts_at_another_slice_is_refused(self):
        """The reviewer's reproduction: position 2, round two's green, round one's
        red, and an accepted record that says check 3 proved slice 1."""
        message = self.refusal()
        self.assertIn('check 3', message)
        self.assertIn('slice 1', message)
        self.assertIn('slice 2', message)

    def test_the_refusal_is_about_where_the_red_belongs_and_not_about_a_tree(self):
        """The exemption is kept whole: a red is still compared against no tree, so
        the refusal cannot be the one a moved tree gives."""
        message = self.refusal()
        self.assertNotIn('tree moved', message)
        self.assertNotIn('whole tree', message)

    def test_the_green_it_was_joined_to_is_accepted_on_its_own_terms(self):
        """Without this the refusal above could be the green's rather than the
        red's: round two's own pair, under the same position, passes everything."""
        self.evaluate('tdd', self.citing(red=5), records=self.rounds(), attempt=2)

    def test_the_position_the_journal_declares_is_still_citable_across_attempts(self):
        """The legitimate case the fix may not cost: round one whole, declared at
        the position its own accepted record names for both halves."""
        self.evaluate('tdd', self.citing(position=1, red=3, green=4), records=self.rounds(),
                      attempt=2)

    def test_declaring_null_for_a_red_the_journal_names_is_refused_too(self):
        """The mirror the scope rule already draws for a green, read the other way
        round: null is a claim, and a claim an accepted record contradicts settles
        nothing. The green cited here is one no accepted record mentions, so it
        reaches the plan's files on its own and the refusal can only be the red's.
        """
        message = self.refusal(data=self.citing(position=None, red=3, green=6),
                               records=self.rounds(mentioning=(1,)))
        self.assertIn('check 3', message)
        self.assertIn('slice 1', message)
        self.assertNotIn('tree moved', message)

    def test_a_red_no_accepted_record_mentions_is_still_citable(self):
        """Where the line is drawn and why. Silence is an absence and not a
        contradiction, and the pair has already paid for it at the half that can
        pay: the green resolves to no scope for the same silence and is compared
        over the whole tree, or to the plan's files where it declares null, and
        only survives what that comparison lets through. A rework round whose own
        tdd advance never happened is exactly this shape, and it is the citation
        this ticket exists for.
        """
        self.evaluate('tdd', self.citing(position=None, red=5, green=6),
                      records=self.rounds(mentioning=(1,)), attempt=2)


class TheRoundTheJournalRecordedItIn(WhereTheJournalPutsAnExemptRed):
    """F1 of the fifth review again, where the earlier record declared null.

    The attribution put back above compares positions, and the template asks
    every rework round to declare null for the slice it belongs to none of. So
    where the accepted record declared null for the red and the citing record
    declares null too, the one answer in the set was null, the citation agreed
    with it, and the theft the class above refuses walked through one line later.
    The reviewer ran that class's own scenario against the fixed gate with null in
    the earlier record and it was accepted.

    **What an accepted tdd record says about a red is not only which slice it
    proved.** It says which green it was recorded beside, and that is the round
    itself. A citation joining that red to another green contradicts the record
    whatever position either side declares, and the position is the weaker half
    of what the record said: two rounds may honestly share a position, and then
    the positions agree while the rounds do not.

    **Is re-citing an earlier round's red beside a different green ever
    legitimate?** No, and that is why this is written as the general rule rather
    than as a null-only repair. A green re-run because the code moved belongs to
    a later attempt, and `_require_the_pair_is_one_round` refuses that pair
    before this rule is reached, so the corrected-green case cannot arise across
    a return. Inside one attempt a second green is one the accepted record of
    that attempt could have named and did not, and it was written when the checks
    were fresh and has been in the hash chain since. Measured over every journal
    under `docs/harness/history` plus SEEN-112's on its branch, 294 citations and
    107 pairs: the null-only repair moves no recorded verdict and the general
    rule moves no recorded verdict either, so nothing in the repository
    distinguishes them and the argument decides.

    Both halves, because a pair names two checks and the contradiction reads from
    either end: an accepted record naming another green for this red, and one
    naming another red for this green. Closing one of those is what the finding
    above this one was about.
    """

    def test_a_null_round_may_not_take_the_other_rounds_green(self):
        """The finding, verbatim: the earlier record declares null for round one,
        the citation declares null, and both of them saying nothing about a slice
        used to be an agreement."""
        message = self.refusal(data=self.citing(position=None, red=3, green=6),
                               records=self.rounds(mentioning=(1,), positions=(None, None)))
        self.assertIn('check 3', message)
        self.assertIn('check 4', message)

    def test_that_theft_is_refused_about_the_round_and_not_about_a_tree(self):
        """The exemption is kept whole: a red is compared against no tree, so this
        cannot be the refusal a moved tree gives."""
        message = self.refusal(data=self.citing(position=None, red=3, green=6),
                               records=self.rounds(mentioning=(1,), positions=(None, None)))
        self.assertNotIn('tree moved', message)
        self.assertNotIn('whole tree', message)

    def test_one_record_carrying_both_rounds_at_null_refuses_it_too(self):
        """The cleaner variant the reviewer named, which is worse: the very record
        that says check 3's green was 4 carries round two as well, so the citation
        contradicts a single record rather than two of them."""
        message = self.refusal(data=self.citing(position=None, red=3, green=6),
                               records=self.rounds(positions=(None, None)))
        self.assertIn('check 3', message)
        self.assertIn('check 4', message)

    def test_the_null_pair_that_record_names_is_still_citable_whole(self):
        """Without this the refusals above could be null being refused as such:
        round two's own pair, declared null as the record declared it, passes."""
        self.evaluate('tdd', self.citing(position=None, red=5, green=6),
                      records=self.rounds(positions=(None, None)), attempt=2)

    def test_two_rounds_at_one_position_may_not_be_joined_either(self):
        """The numbered direction, which the position comparison cannot see: an
        accepted record that proved one slice twice names the same position for
        both rounds, so the citation agrees with it about the slice and still
        claims a round the journal does not have."""
        message = self.refusal(data=self.citing(position=1, red=3, green=6),
                               records=self.rounds(positions=(1, 1)))
        self.assertIn('check 3', message)
        self.assertIn('check 4', message)

    def test_the_honest_citation_of_that_second_round_still_stands(self):
        """The same record, the same position, the pair it really names."""
        self.evaluate('tdd', self.citing(position=1, red=5, green=6),
                      records=self.rounds(positions=(1, 1)), attempt=2)

    def test_a_green_the_journal_recorded_beside_another_red_is_refused_too(self):
        """The mirror, from the green's end. The accepted record carries round two
        alone, so nothing it says attributes check 3 at all and the position rule
        has no objection; what it does say is that check 6's red was 5."""
        message = self.refusal(data=self.citing(position=2, red=3, green=6),
                               records=self.rounds(mentioning=(2,)))
        self.assertIn('check 6', message)
        self.assertIn('check 5', message)

    def test_a_pair_no_accepted_record_mentions_at_all_is_still_citable(self):
        """Where the line stays. Silence is an absence, and the citation this
        ticket exists for is a rework round whose own tdd advance never happened.
        """
        self.evaluate('tdd', self.citing(position=None, red=5, green=6),
                      records=self.rounds(mentioning=(1,)), attempt=2)


class TheDisclosureNamesWhatARedIsHeldTo(unittest.TestCase):
    """What a red is held to, said where a reader of the rule will meet it.

    The second half of F1 of the fifth review, and it is weighed the same: the
    exemption's docstring said what ties a pair together "in full" and listed
    three rules, when a fourth was being checked all along for every red an
    accepted tdd record has attributed, and this ticket removed that one without
    recording that it had. A rule whose disclosure understates what it checks
    costs a later reader exactly what the check was for.
    """

    def disclosure(self):
        return ((gates._require_the_pair_is_one_round.__doc__ or '')
                + (gates.cited_check.__doc__ or ''))

    def test_it_names_the_journals_attribution_as_one_of_the_rules(self):
        self.assertIn('attribution', self.disclosure())

    def test_it_no_longer_says_three_rules_are_all_of_them(self):
        self.assertNotIn('Nothing else.', gates._require_the_pair_is_one_round.__doc__)

    def test_the_route_clause_says_the_shadow_window_silences_it(self):
        """F3 of the fifth review. The list says a red is held to the route of the
        position its entry declares, and every route comparison returns before it
        compares while `[routing] shadow` is true. Measured: 0 of 30 slice entries
        in this repository's journals are refused by any route rule with shadow
        on, 24 of 30 with it off, so the qualification is the difference between
        a rule that refuses nothing and one that refuses most of them. The fact is
        written at each of the three route gates, which is exactly the distance
        the other half of this review's F1 was about.
        """
        held_to = gates.cited_check.__doc__ or ''
        clause = held_to[held_to.index('the route of the position'):]
        self.assertIn('shadow', clause[:clause.index(';')])

    def test_it_still_says_what_is_not_checked(self):
        """Within one attempt no accepted tdd record can mention the checks being
        cited, because it would have to have been written before they existed, so
        there the pairing really does rest on the record's word. The honest
        statement says both halves, so it has to keep saying this one."""
        self.assertIn("rests on the record's word", self.disclosure())


class WhatTiesARedToItsGreen(SeenOneTwelveShape):
    """A pair is one round, and the attempt is what a gate can check of that.

    The exemption lends the green's standing to the red, which is only honest if
    the two halves are the same work. What holds them together, in full: the
    ordering rule, which puts the red after the previous entry's green and before
    its own; the route, which holds both halves to the model and the context the
    position was routed to; and the attempt, which is what this class adds. A
    return ends a round and every return increments the attempt, so a pair split
    across a return is two halves of different work and the red would be
    borrowing a tree it has no claim on.

    Measured on every journal under `docs/harness/history`: 100 slice entries in
    accepted tdd records, and all 100 have their red and their green in the same
    attempt. So nothing any journal has recorded is refused by requiring it.

    **What is not tied, said plainly rather than implied.** Within one attempt a
    session may record two rounds, and beyond the ordering nothing here tells one
    round's red from the other's. The nearest red before the green is not the
    answer either: SEEN-098's green 8 belongs to red 6 with another red recorded
    at 7, so the nearest red would refuse a real pair. Inside an attempt the
    pairing is the record's word, and the failure reason a slice states is prose
    a reviewer reads against the runner's output at the triage, not anything this
    gate compares.
    """

    def split_across_a_return(self):
        """Attempt 1's red with attempt 2's green, and an ordering nothing objects to."""
        return self.template(
            'tdd',
            slices=[dict(position=1, behaviour='A red from attempt 1 and a green from attempt 2',
                         failure_reason='expected 250, received 0', red=2, green=5),
                    dict(position=3, behaviour='Slice 3, proved in attempt 5',
                         failure_reason='expected slice 3, read slice 1', red=6, green=7)],
            regression=8)

    def refusal(self, data=None, records=None):
        with self.assertRaises(HarnessError) as raised:
            self.evaluate('tdd', data or self.split_across_a_return(),
                          records=records or self.journal(), attempt=5)
        return str(raised.exception)

    def test_a_red_from_before_a_return_may_not_be_cited_beside_a_later_green(self):
        self.assertIn('one round', self.refusal())

    def test_the_refusal_names_both_attempts_and_both_checks(self):
        message = self.refusal()
        for named in ('red 2', 'green 5', 'attempt 1', 'attempt 2'):
            self.assertIn(named, message)

    def test_that_pair_is_one_the_rest_of_the_gate_accepts(self):
        """Without this the refusal above could be the ordering rule's: the red
        precedes the green, no entry overlaps another and the regression is last,
        and every tree in this fixture is the tree this record is written against,
        so nothing else in the gate has an objection to make."""
        self.assertNotIn('out of order', self.refusal())

    def test_a_pair_of_one_round_from_an_earlier_attempt_is_still_cited(self):
        """The rule ties the halves to each other, not to the citing attempt: the
        citation this ticket exists to allow is untouched."""
        self.evaluate('tdd', self.citing_all(), records=self.journal(), attempt=5)

    def test_a_record_whose_entries_overlap_still_hears_about_the_ordering(self):
        """Why the pair is asked after the ordering pass and not inside it: the
        ordering rule reads across entries, so a record whose entries overlap gets
        the sentence a session can act on rather than one about a pair the
        ordering was going to refuse anyway."""
        data = self.citing_all()
        data['slices'][0].update(red=2, green=5)
        data['slices'][1].update(red=4, green=7)
        data['slices'][2].update(red=6, green=7)
        self.assertIn('out of order', self.refusal(data=data))


class ANullRoundIsHeldToTheStrictestRoute(TddGateTest):
    """F2 of the fifth review: null is not the cheapest thing a record can declare.

    A null position buys the plan's whole file union for its scope, which is
    stricter than one slice's files and is the point of that rule. What it also
    bought was the route for nothing: `_require_the_routed_slice` returned before
    the comparison, so a slice routed to opus and worked on sonnet was refused
    when it declared its position and accepted when it declared null. Before the
    plan's union a null declaration at least cost the citation its evidence, which
    was the counter-pressure; once that price was gone the cheapest true-looking
    thing a record could say was that it belonged to no single slice.

    A round that belongs to no single slice touches several, so it answers to
    several routes, and it is held to the strictest of them on the same reasoning
    that makes its scope the union rather than nothing. Strictest is a floor and
    not an equality: a plan routed to sonnet and to opus can be met by neither
    model under an equality, and a rule nobody can satisfy is a rule that forces
    the record to name a position it does not have. What the route guards against
    is work done under a weaker model than the plan judged necessary; a stronger
    one is a cost, and a round that belongs to no single slice has no routed cost
    of its own to be held to.
    """

    def setUp(self):
        super().setUp()
        # Out of shadow, because in shadow no route refuses anything at all and
        # this class is about what the comparison says when it is made.
        self.thresholds = dict(self.thresholds,
                               routing=dict(self.thresholds['routing'], shadow=False))

    def journal(self, models=('sonnet', 'opus'), model='claude-sonnet-5', declared=None,
                agent='seen-implementer', routed=True):
        """A plan, its route, and one round proved under one model in this attempt.

        Every check is from the attempt the record is written in, so nothing here
        is about the citation rules: what is left to refuse is the route.
        """
        plan = [dict(name=f'Slice {position}', points=1, files=['harness/journal.py'],
                     red=f'Nothing yet proves behaviour {position}')
                for position in range(1, len(models) + 1)]
        route = [route_record(3, 2, [routed_slice(position, tier)
                                     for position, tier in enumerate(models, start=1)])]
        def check(sequence, phase):
            return check_record(sequence, phase, attempt=1, model=model,
                                model_declared=declared, agent_declared=agent)
        return self.records + [
            advance_record(2, 'solution', dict(mode='code', slices=plan), attempt=1),
            *(route if routed else []),
            check(4, 'red'), check(5, 'green'), check(6, 'regression'),
            coverage_record(7, attempt=1)]

    def citing(self, position=None):
        return self.code_tdd(slices=[dict(position=position,
                                          behaviour='A round of rework across the plan',
                                          failure_reason='expected a refusal, received none',
                                          red=4, green=5)],
                             regression=6)

    def refusal(self, data=None, records=None):
        with self.assertRaises(HarnessError) as raised:
            self.evaluate('tdd', data or self.citing(), records=records or self.journal())
        return str(raised.exception)

    def test_a_null_round_worked_below_the_plans_strictest_route_is_refused(self):
        message = self.refusal()
        self.assertIn('opus', message)
        self.assertIn('claude-sonnet-5', message)

    def test_the_refusal_says_it_is_the_strictest_route_in_the_plan(self):
        message = self.refusal()
        self.assertIn('no single slice', message)
        self.assertIn('strictest', message)

    def test_the_same_round_on_the_strictest_route_is_not_refused(self):
        self.evaluate('tdd', self.citing(), records=self.journal(model='claude-opus-5'))

    def test_declaring_null_is_not_cheaper_than_declaring_the_position(self):
        """The finding's own sentence: work routed to opus and done on sonnet was
        refused when it declared its position and accepted when it declared null.
        Both are refused now, and what still passes is the one declaration that
        would be true of work done on sonnet: the slice routed to sonnet."""
        self.assertIn('Slice 2', self.refusal(data=self.citing(position=2)))
        self.refusal(data=self.citing(position=None))
        self.evaluate('tdd', self.citing(position=1), records=self.journal())

    def test_a_round_stronger_than_every_slice_of_the_plan_is_not_refused(self):
        """The floor, argued in the class docstring: an equality against the
        strongest tier could not be met by any model a plan of two tiers routed."""
        self.evaluate('tdd', self.citing(),
                      records=self.journal(models=('sonnet', 'sonnet'), model='claude-opus-5'))

    def test_in_shadow_nothing_is_refused(self):
        """The window SEEN-109 exists to close, and no refusal crosses it."""
        self.thresholds = dict(self.thresholds,
                               routing=dict(self.thresholds['routing'], shadow=True))
        self.evaluate('tdd', self.citing(),
                      records=self.journal(model='claude-haiku-4-5-20251001'))

    def test_a_plan_nobody_routed_is_a_comparison_with_nothing(self):
        self.evaluate('tdd', self.citing(),
                      records=self.journal(routed=False, model='claude-haiku-4-5-20251001'))

    def test_a_model_id_nobody_wrote_down_is_not_compared(self):
        """The same absence the numbered rule allows: an id no tier names cannot be
        placed against a floor, and a comparison with nothing is not one."""
        self.evaluate('tdd', self.citing(), records=self.journal(model='claude-sonnet-4-5-none'))

    def test_a_declared_tier_is_what_the_gate_reads_first(self):
        """The disclosure before the log, exactly as the numbered rule reads it: a
        subagent inherits its parent's session id, so the log of its check carries
        the parent's model and only the declaration knows."""
        message = self.refusal(records=self.journal(model='claude-opus-5', declared='sonnet'))
        self.assertIn('sonnet', message)
        self.assertIn('opus', message)

    def test_a_declaration_at_the_floor_stands_whatever_the_log_says(self):
        self.evaluate('tdd', self.citing(),
                      records=self.journal(model='claude-haiku-4-5-20251001', declared='opus'))

    def test_a_declared_tier_no_route_names_cannot_meet_the_floor(self):
        """Fail closed rather than crash on it: a tier nobody routes has no place
        in the order, so nothing can show it met the floor."""
        message = self.refusal(records=self.journal(model='claude-opus-5', declared='wizard'))
        self.assertIn('wizard', message)

    def test_a_null_round_in_the_orchestrating_sessions_own_context_is_refused(self):
        """The second half of what a position bought: a slice routed at all is
        routed to a context of its own, so a round that may have touched any of
        them is too."""
        message = self.refusal(records=self.journal(model='claude-opus-5', agent=None))
        self.assertIn('context of its own', message)

    def test_a_null_round_a_subagent_worked_is_not_refused_for_its_context(self):
        self.evaluate('tdd', self.citing(), records=self.journal(model='claude-opus-5'))


if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
