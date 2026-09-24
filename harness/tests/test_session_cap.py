"""The slice as the unit of context: the plan, the session, the pack and the budget.

A ticket is still delivered as one branch and one receipt. What is capped here is
what one context holds, so the tests are about what the solution gate refuses,
what a record says about the session that wrote it, and what a session can be
told about its own spending.
"""

import hashlib

import os
import unittest

from harness.errors import HarnessError
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence

# The variables a session id can arrive in, most specific first. Claude Code
# sets the first; which one a Codex session sets is not known from this machine,
# and null is what the harness records until one does.
VARIABLES = ('CLAUDE_CODE_SESSION_ID',)
SESSION_ID = 'f32bb893-ed20-4792-bcfb-b6e19e7c05ae'
DIGEST = hashlib.sha256(SESSION_ID.encode()).hexdigest()[:12]


def plan(count=1, points=1):
    """A slice plan of the shape the solution record carries."""
    return [dict(name=f'Slice {position}',
                 points=points,
                 files=['harness/journal.py'],
                 red=f'Nothing yet proves behaviour {position}')
            for position in range(1, count + 1)]


class SessionEnvironment(CommandTest):
    """Tests that decide for themselves which session they are running in.

    The harness reads the session from the environment, and the environment of
    the session running the tests is not the fixture: a test that inherited it
    would pass or fail depending on who ran it.
    """

    session = SESSION_ID

    def setUp(self):
        super().setUp()
        for name in VARIABLES:
            if name in os.environ:
                value = os.environ.pop(name)
                self.addCleanup(os.environ.__setitem__, name, value)
        if self.session is not None:
            os.environ[VARIABLES[0]] = self.session
            self.addCleanup(os.environ.pop, VARIABLES[0], None)


class SlicePlanTest(CommandTest):
    """What the solution gate does with the plan it is now given."""

    def setUp(self):
        super().setUp()
        self.start()
        self.submit('clarify', clarify_evidence())

    def test_a_slice_over_the_cap_is_refused_and_named(self):
        with self.assertRaisesRegex(HarnessError, 'Slice 1'):
            self.submit('solution', solution_evidence(slices=plan(1, points=3)))

    def test_the_refusal_names_the_cap_it_broke(self):
        with self.assertRaisesRegex(HarnessError, '2 points'):
            self.submit('solution', solution_evidence(slices=plan(1, points=3)))

    def test_a_plan_over_the_slice_cap_is_refused(self):
        with self.assertRaisesRegex(HarnessError, '5 slices'):
            self.submit('solution', solution_evidence(slices=plan(5)))

    def test_a_code_mode_record_without_a_plan_is_refused_naming_slices(self):
        record = solution_evidence()
        record.pop('slices', None)
        with self.assertRaisesRegex(HarnessError, 'slices'):
            self.submit('solution', record)

    def test_a_slice_missing_its_red_is_refused(self):
        incomplete = plan(1)
        incomplete[0].pop('red')
        with self.assertRaisesRegex(HarnessError, 'red'):
            self.submit('solution', solution_evidence(slices=incomplete))

    def test_a_slice_whose_points_are_not_a_number_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'points'):
            self.submit('solution', solution_evidence(slices=plan(1, points='one')))

    def test_a_plan_inside_both_caps_advances(self):
        record = self.submit('solution', solution_evidence(slices=plan(3)))
        self.assertEqual(record['data']['to_stage'], 'tdd')
        self.assertEqual(len(record['data']['evidence']['slices']), 3)

    def test_the_points_sum_is_reported_rather_than_refused(self):
        """A plan may disagree with the estimate; the gate says so and proceeds.

        The caps are about what one context holds. The estimate is a forecast,
        and a gate that made them equal would turn every re-estimate into a
        returned record.
        """
        record = self.submit('solution', solution_evidence(slices=plan(4, points=2)))
        self.assertEqual(record['data']['evidence']['slice_points'], 8)


class NonCodeSlicePlanTest(CommandTest):
    """A ticket with no behaviour to prove plans no slices.

    Its own class because a setUp shared with code tickets cannot declare
    non-code, which is what SEEN-103 found when it moved mode to this stage.
    """

    def setUp(self):
        super().setUp()
        self.start()
        self.submit('clarify', clarify_evidence())

    def test_a_non_code_record_advances_with_no_plan_at_all(self):
        record = solution_evidence(mode='non-code', tests_first=[])
        record.pop('slices', None)
        advanced = self.submit('solution', record)
        self.assertEqual(advanced['data']['to_stage'], 'tdd')


class SessionOnEveryRecordTest(SessionEnvironment):
    """Which session wrote a record, without saying what the session is called."""

    def test_a_record_says_which_session_wrote_it(self):
        record = self.start()
        self.assertEqual(record['session'], DIGEST)

    def test_the_session_id_itself_is_in_no_record(self):
        self.start()
        text = (self.root / 'docs' / 'harness' / 'history' / self.ticket_id / '0001.json').read_text()
        self.assertNotIn(SESSION_ID, text)

    def test_every_later_record_carries_it_too(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.assertTrue(all(record['session'] == DIGEST for record in self.records()))


class SessionUnknownTest(SessionEnvironment):
    """No session id is an absence, not a claim that there was one session."""

    session = None

    def test_a_record_carries_null_rather_than_a_guess(self):
        record = self.start()
        self.assertIsNone(record['session'])


class SessionDigestTest(unittest.TestCase):

    def test_the_digest_is_twelve_hex_characters_of_the_sha256(self):
        from harness import sessions
        self.assertEqual(sessions.digest(SESSION_ID), DIGEST)
        self.assertEqual(len(sessions.digest(SESSION_ID)), 12)

    def test_an_unset_session_digests_to_nothing(self):
        from harness import sessions
        self.assertIsNone(sessions.digest(None))
        self.assertIsNone(sessions.digest(''))

    def test_the_harness_reads_the_variable_this_assistant_sets(self):
        from harness import sessions
        self.assertEqual(sessions.SESSION_VARIABLES[0], VARIABLES[0])


class SessionThresholdTest(unittest.TestCase):
    """The four numbers the session cap is made of, in the file people tune."""

    def test_the_session_section_carries_the_four_numbers(self):
        from harness import thresholds
        from harness.tests.helpers import PROJECT
        section = thresholds.load(PROJECT)['session']
        self.assertEqual(section['max_points_per_slice'], 2)
        self.assertEqual(section['max_slices_per_ticket'], 4)
        self.assertEqual(section['output_token_budget'], 60000)
        self.assertEqual(section['handoff_token_limit'], 2000)


if __name__ == '__main__':
    unittest.main()
