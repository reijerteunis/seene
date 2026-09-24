"""A ticket with no executable behaviour, saying so before it is asked for tests.

The solution template required tests_first of every ticket while non-code mode
was declared a stage later, so a registration, verification, research or policy
ticket had to write tests it would never run in order to reach the stage where
it said it had no tests. SEEN-102 was the first non-code ticket the harness saw
and it stopped there.
"""

import unittest

from harness import gates
from harness.errors import HarnessError
from harness.tests.test_lifecycle import (CommandTest, clarify_evidence, solution_evidence)

POLICY = dict(mode='non-code', change_type='policy',
              reason='A decision and two documentation edits; there is no behaviour to prove.',
              sources=['docs/harness/history/SEEN-102/0002.json'],
              checks=[])


class NonCodeSolutionTest(CommandTest):

    def reach_solution(self):
        self.start()
        self.submit('clarify', clarify_evidence())

    def test_a_non_code_solution_advances_with_no_tests_first(self):
        """The hole SEEN-102 fell into, closed."""
        self.reach_solution()

        record = self.submit('solution', solution_evidence(mode='non-code', tests_first=[]))

        self.assertEqual(record['data']['to_stage'], 'tdd')

    def test_a_code_solution_still_refuses_without_tests_first(self):
        """The guard: this must not become a way round the gate."""
        self.reach_solution()

        with self.assertRaisesRegex(HarnessError, 'tests_first'):
            self.submit('solution', solution_evidence(mode='code', tests_first=[]))

    def test_a_mode_that_is_neither_is_refused_naming_both(self):
        self.reach_solution()

        with self.assertRaises(HarnessError) as refused:
            self.submit('solution', solution_evidence(mode='sideways'))

        self.assertIn('code', str(refused.exception))
        self.assertIn('non-code', str(refused.exception))

    def test_a_new_solution_record_must_carry_the_mode(self):
        """The template asks, so a record that does not answer is not finished."""
        self.reach_solution()
        evidence = solution_evidence()
        evidence.pop('mode', None)

        with self.assertRaisesRegex(HarnessError, 'mode'):
            self.submit('solution', evidence)

    def test_a_record_written_before_the_field_existed_reads_as_code(self):
        """Nine solution records are already written without it, and stay valid."""
        self.assertEqual(gates.mode_of({}), 'code')
        self.assertEqual(gates.mode_of(dict(approach='from before SEEN-103')), 'code')

    def test_no_solution_record_at_all_is_not_a_claim_about_mode(self):
        """Absent is not the same as a record that said nothing."""
        self.assertIsNone(gates.latest_evidence(
            [dict(kind='start', stage='clarify', data={})], 'solution'))


class ModesMustAgreeTest(CommandTest):
    """A ticket that plans no tests and then records a code TDD changed its mind."""

    def reach_tdd(self, solution_mode):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence(mode=solution_mode,
                                                  tests_first=[] if solution_mode == 'non-code'
                                                  else ['a test, first']))

    def test_a_tdd_mode_that_disagrees_with_the_solution_is_refused(self):
        """With a well-formed slice, so it is the disagreement that refuses."""
        self.reach_tdd('non-code')
        code_tdd = dict(mode='code', regression=3, coverage_delta=0.0,
                        slices=[dict(behaviour='something observable',
                                     failure_reason='AssertionError: it did not',
                                     red=1, green=2)])

        with self.assertRaises(HarnessError) as refused:
            self.submit('tdd', code_tdd)

        self.assertIn('non-code', str(refused.exception))
        self.assertIn('code', str(refused.exception))

    def test_the_other_direction_is_refused_too(self):
        self.reach_tdd('code')

        with self.assertRaises(HarnessError) as refused:
            self.submit('tdd', POLICY)

        self.assertIn('non-code', str(refused.exception))

    def test_agreeing_modes_advance(self):
        self.reach_tdd('non-code')

        record = self.submit('tdd', POLICY)

        self.assertEqual(record['data']['to_stage'], 'review')


if __name__ == '__main__':
    unittest.main()
