"""What the clarified question asks, and what it must not have changed.

The shape is testable here; the behaviour is not, because no test may call Jev.
That is verified by the measurement in SEEN-100's journal, which harness/
measure_criteria.py reproduces.
"""

import unittest

from harness import jev, thresholds
from harness.tests.helpers import PROJECT


class ClarifiedCriteriaTest(unittest.TestCase):

    def setUp(self):
        self.question = jev.QUESTIONS['clarified']

    def test_a_question_only_the_work_can_settle_counts_as_resolved_when_named(self):
        """Naming an unknown used to read as leaving it open, three times over."""
        allowed = self.question['criteria']['true'].lower()

        self.assertIn('only doing the work can settle', allowed)
        self.assertIn('names what will settle it', allowed)

    def test_the_false_criterion_needs_both_halves(self):
        """Unresolved is not enough: nothing said about what would resolve it."""
        refused = self.question['criteria']['false'].lower()

        self.assertIn('still unresolved', refused)
        self.assertIn('what would resolve it', refused)

    def test_the_question_itself_is_unchanged(self):
        self.assertEqual(self.question['ask'],
                         'Are all material questions in this clarify record resolved?')

    def test_the_threshold_is_untouched(self):
        rules = thresholds.load(PROJECT)

        self.assertEqual(rules['jev']['thresholds']['clarified'], 0.8)

    def test_the_other_six_questions_are_still_there(self):
        self.assertEqual(sorted(jev.QUESTIONS),
                         ['clarified', 'is_destructive', 'must_fix', 'risk', 'severity',
                          'solution_complete', 'touches_billing_or_policy_gate'])

    def test_solution_complete_keeps_the_wording_SEEN_006_gave_it(self):
        """The other calibrated question, unchanged by this one."""
        self.assertIn('without stopping', jev.QUESTIONS['solution_complete']['ask'].lower())

    def test_every_question_still_carries_criteria(self):
        for name, question in jev.QUESTIONS.items():
            with self.subTest(question=name):
                self.assertTrue(question.get('criteria'), f'{name} has no criteria')
