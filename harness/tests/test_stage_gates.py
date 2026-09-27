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

    def journal(self, plan=None, proved=None):
        """Slice one proved in attempt 1, slice three in attempt 2, which is now."""
        now = self.repository.fingerprint()
        return self.records + [
            advance_record(2, 'solution',
                           dict(mode='code', slices=plan or self.plan), attempt=1),
            check_record(3, 'red', attempt=1, after=proved or self.proved),
            check_record(4, 'green', attempt=1, after=proved or self.proved),
            check_record(5, 'red', attempt=2, after=now),
            check_record(6, 'green', attempt=2, after=now),
            check_record(7, 'regression', attempt=2, after=now),
            coverage_record(8, attempt=2)]

    def citing(self, position=1, **changes):
        data = self.template(
            'tdd',
            slices=[dict(position=position, behaviour='Slice one, proved in attempt 1',
                         failure_reason='expected 1, received nothing',
                         red=3, green=4),
                    dict(position=3, behaviour='Slice three, proved in this attempt',
                         failure_reason='expected 3, received nothing',
                         red=5, green=6)],
            regression=7)
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
        self.write('harness/one/deep.py', 'def deep():\n    return 1\n')
        self.write('harness/one_beside.py', 'def beside():\n    return 1\n')
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
        self.assertIn('tree moved under check 3', message)


class UnattributableCitationFallsBack(ScopedToTheSlicesFiles):
    """A citation belonging to no slice is held to the strict whole-tree rule.

    Fail closed: a citation nothing can attribute is the case where the scoped
    comparison would be a guess, so it is refused rather than scoped to whatever
    happens to be at hand.
    """

    def test_a_citation_that_names_its_slice_is_scoped_to_that_slice(self):
        self.slice_three_writes_its_own_file()
        self.evaluate('tdd', self.citing(position=1), records=self.journal(), attempt=2)

    def test_a_citation_that_names_no_slice_is_held_to_the_whole_tree(self):
        self.slice_three_writes_its_own_file()
        message = self.refusal(data=self.citing(position=None))
        self.assertIn('tree moved under check 3', message)
        self.assertIn(self.proved[:12], message)

    def test_the_whole_tree_refusal_says_that_is_what_it_compared(self):
        self.slice_three_writes_its_own_file()
        self.assertIn('whole tree', self.refusal(data=self.citing(position=None)))

    def test_a_tree_no_commit_carries_cannot_be_scoped_and_is_refused(self):
        """A check whose tree was never committed as it stood: nothing says which
        files it held, so the whole tree is the only comparison left."""
        self.slice_three_writes_its_own_file()
        message = self.refusal(records=self.journal(proved='f' * 64))
        self.assertIn('tree moved under check 3', message)
        self.assertIn('whole tree', message)

    def test_the_fingerprint_this_rule_reads_is_the_one_the_repository_writes(self):
        """The scoped comparison identifies a check's tree by its fingerprint, so
        the two readings of that hash must agree, or the scope is read off the
        wrong commit."""
        self.assertEqual(gates.content_fingerprint(self.repository, 'HEAD'),
                         self.repository.fingerprint())


if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
