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
                             slices=[dict(name='The detector',
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


if __name__ == '__main__':
    unittest.main()
