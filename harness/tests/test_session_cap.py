"""The slice as the unit of context: the plan, the session, the pack and the budget.

A ticket is still delivered as one branch and one receipt. What is capped here is
what one context holds, so the tests are about what the solution gate refuses,
what a record says about the session that wrote it, and what a session can be
told about its own spending.
"""

import hashlib
import json
import os
from pathlib import Path
import tempfile
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


class AtTddTest(SessionEnvironment):
    """A journal standing where a slice boundary happens: tdd, with a plan."""

    slices = 3

    def setUp(self):
        super().setUp()
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence(slices=plan(self.slices)))

    def handoff(self, actor='claude:implementer'):
        return self.run_harness('handoff', self.ticket_id, '--actor', actor)

    def brief(self):
        return self.run_harness('status', self.ticket_id, '--brief')

    def pack_file(self):
        return self.root / '.harness-drafts' / f'{self.ticket_id}-handoff.md'

    def green(self, sequence=None):
        """A green check, recorded the way a slice ends."""
        script = self.root / 'passes.sh'
        script.write_text('#!/bin/sh\nexit 0\n')
        script.chmod(0o755)
        return self.run_harness('check', self.ticket_id, '--phase', 'green',
                                '--actor', 'claude:implementer', '--', str(script))


class HandoffPackTest(AtTddTest):
    """The only thing that crosses a slice boundary."""

    def test_the_pack_is_written_where_the_drafts_live(self):
        self.handoff()
        self.assertTrue(self.pack_file().is_file())

    def test_the_record_carries_the_sha256_of_the_pack_on_disk(self):
        record = self.handoff()
        written = hashlib.sha256(self.pack_file().read_bytes()).hexdigest()
        self.assertEqual(record['data']['sha256'], written)

    def test_the_record_is_a_handoff_and_leaves_the_stage_alone(self):
        record = self.handoff()
        self.assertEqual(record['kind'], 'handoff')
        self.assertEqual(self.run_harness('status', self.ticket_id)['stage'], 'tdd')

    def test_the_record_carries_this_sessions_figures(self):
        record = self.handoff()
        figures = record['data']['figures']
        self.assertEqual(figures['session'], DIGEST)
        self.assertIsNone(figures['output_tokens'])
        self.assertIsNone(figures['tool_calls'])

    def test_the_pack_names_the_first_slice_before_any_green(self):
        self.handoff()
        self.assertIn('Slice 1', self.pack_file().read_text())

    def test_a_green_moves_the_pack_on_to_the_next_slice(self):
        self.green()
        self.handoff()
        text = self.pack_file().read_text()
        self.assertIn('Slice 2', text)
        self.assertIn('1 of 3', text)

    def test_the_pack_carries_the_criteria_and_the_next_command(self):
        self.handoff()
        text = self.pack_file().read_text()
        self.assertIn('The journal holds one record per stage', text)
        self.assertIn('harness check', text)

    def test_the_pack_stays_under_the_limit_however_long_the_journal(self):
        for number in range(12):
            note = self.root / '.harness-drafts' / f'note-{number}.md'
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(f'Decision {number}. ' + ('why this and not that, at length. ' * 60))
            self.run_harness('note', self.ticket_id, '--file',
                             f'.harness-drafts/note-{number}.md',
                             '--actor', 'claude:implementer')
        record = self.handoff()
        self.assertLessEqual(record['data']['estimated_tokens'], 2000)

    def test_a_pack_that_would_carry_an_environment_value_is_refused(self):
        # A value that really does appear in the pack: the pack names the ticket
        # file, and a variable named like a credential is one whatever it holds.
        os.environ['SEEN_TEST_API_KEY'] = f'{self.ticket_id}-a-ticket-to-work'
        self.addCleanup(os.environ.pop, 'SEEN_TEST_API_KEY', None)
        with self.assertRaisesRegex(HarnessError, 'SEEN_TEST_API_KEY'):
            self.handoff()

    def test_the_refusal_names_the_variable_and_not_its_value(self):
        secret = f'{self.ticket_id}-a-ticket-to-work'
        os.environ['SEEN_TEST_API_KEY'] = secret
        self.addCleanup(os.environ.pop, 'SEEN_TEST_API_KEY', None)
        with self.assertRaises(HarnessError) as caught:
            self.handoff()
        self.assertNotIn(secret, str(caught.exception))
        self.assertFalse(self.pack_file().exists())


class DeclaredSliceTest(AtTddTest):
    """Who says a slice is done.

    The pack counts greens, which is right until a slice records two of them. It
    happened on SEEN-105's own slice 1: a green, a correction to .gitignore, a
    second green, and a pack that pointed the next session at slice 3 of 4 with
    slice 2 unworked. Only the session that worked the slice knows it finished it,
    so it can say so, and the record says whether the number was declared or
    inferred.
    """

    def red(self):
        script = self.root / 'fails.sh'
        script.write_text('#!/bin/sh\nexit 1\n')
        script.chmod(0o755)
        return self.run_harness('check', self.ticket_id, '--phase', 'red',
                                '--actor', 'claude:implementer', '--', str(script))

    def handoff_declaring(self, done, actor='claude:implementer'):
        return self.run_harness('handoff', self.ticket_id, '--actor', actor,
                                '--slice-done', str(done))

    def test_a_declaration_puts_the_pack_on_the_slice_that_is_next(self):
        self.red()
        self.green()
        self.green()
        self.handoff_declaring(1)
        text = self.pack_file().read_text()
        self.assertIn('Slice 2', text)
        self.assertIn('1 of 3', text)

    def test_the_record_says_the_count_was_declared(self):
        self.green()
        record = self.handoff_declaring(1)
        self.assertEqual(record['data']['slice']['done'], 1)
        self.assertTrue(record['data']['slice']['declared'])

    def test_a_record_with_no_declaration_says_the_count_was_inferred(self):
        self.green()
        record = self.handoff()
        self.assertFalse(record['data']['slice']['declared'])

    def test_a_declaration_over_the_plan_is_refused_and_names_the_plan(self):
        with self.assertRaises(HarnessError) as raised:
            self.handoff_declaring(self.slices + 1)
        self.assertIn(str(self.slices), str(raised.exception))

    def test_a_declaration_below_zero_is_refused(self):
        with self.assertRaises(HarnessError):
            self.handoff_declaring(-1)

    def test_status_brief_honours_the_count_a_handoff_declared(self):
        """F1: the rendered pack is what a resuming session actually reads."""
        self.red()
        self.green()
        self.green()
        self.handoff_declaring(1)

        self.assertIn('Slice 2', self.brief()['pack'])

    def test_a_green_recorded_after_the_last_declaration_still_counts(self):
        self.handoff_declaring(1)
        self.green()

        self.assertIn('Slice 3', self.brief()['pack'])

    def test_the_record_carries_the_count_the_journal_would_have_inferred(self):
        """F7: a declaration the journal contradicts is visible, not prevented."""
        self.green()
        record = self.handoff_declaring(3)

        self.assertEqual(record['data']['slice']['done'], 3)
        self.assertEqual(record['data']['slice']['inferred'], 1)

    def test_a_return_does_not_discard_the_count_already_declared(self):
        """H4: F1 again, with a return as the trigger instead of a second green."""
        self.green()
        self.handoff_declaring(2)
        self.run_harness('return', self.ticket_id, '--to', 'solution', '--reason',
                         'A finding from the review', '--actor', 'claude:reviewer')

        self.assertIn('Slice 3', self.brief()['pack'])

    def test_two_greens_for_one_slice_are_miscounted_without_a_declaration(self):
        """The limit the flag exists for, pinned so nobody is surprised by it."""
        self.green()
        self.green()
        self.handoff()
        self.assertIn('Slice 3', self.pack_file().read_text())


class PackEdgesTest(AtTddTest):
    """Three things the first packs written in anger got wrong."""

    def complete_the_plan(self):
        """A green per planned slice, which is what a complete plan looks like."""
        for _ in range(self.slices):
            self.green()
        from harness import thresholds
        return self.records(), thresholds.load(self.root)

    def test_a_complete_plan_at_tdd_names_what_is_left_there(self):
        from harness import handoff as building
        records, rules = self.complete_the_plan()
        built = building.pack(records, dict(stage='tdd', attempt=1), rules)
        self.assertIn('regression', built['markdown'])
        self.assertIn('3 of 3 slices', built['markdown'])

    def test_a_complete_plan_at_review_does_not_send_you_back_to_tdd(self):
        """At review the regression and the coverage are already behind you."""
        from harness import handoff as building
        records, rules = self.complete_the_plan()
        built = building.pack(records, dict(stage='review', attempt=1), rules)
        self.assertNotIn('What is left is the regression', built['markdown'])
        self.assertIn('every slice has an accepted GREEN', built['markdown'])

    def test_a_section_that_does_not_fit_charges_nothing(self):
        from harness import handoff as building
        lines = []
        remaining = building._section(lines, 'Decisions', ['x' * 300] * 4, 6, remaining=10)
        self.assertEqual(lines, [])
        self.assertEqual(remaining, 10)

    def test_a_later_section_still_fits_after_one_that_did_not(self):
        from harness import handoff as building
        lines = []
        remaining = building._section(lines, 'Long', ['x' * 300], 6, remaining=40)
        building._section(lines, 'Short', ['fits'], 6, remaining=remaining)
        self.assertIn('- fits', lines)

    def test_the_pack_is_written_as_utf_8_whatever_the_locale(self):
        """The bytes on disk are compared against a recorded hash."""
        source = (Path(__file__).resolve().parents[1] / 'cli.py').read_text()
        self.assertIn("write_text(text, encoding='utf-8')", source)
        self.assertIn("read_text(encoding='utf-8')", source)


class NoPlanYetTest(SessionEnvironment):
    """A pack before the solution record has advanced names no slice."""

    def setUp(self):
        super().setUp()
        self.start()

    def test_it_says_there_is_no_plan_rather_than_inventing_one(self):
        answer = self.run_harness('status', self.ticket_id, '--brief')
        self.assertIn('No plan yet', answer['pack'])

    def test_it_names_the_stage_the_plan_is_written_at(self):
        self.assertIn('solution stage',
                      self.run_harness('status', self.ticket_id, '--brief')['pack'])


class StatusBriefTest(AtTddTest):
    """What a fresh session reads before it does anything else."""

    def test_brief_prints_a_pack_built_from_the_journal(self):
        answer = self.brief()
        self.assertIn('Slice 1', answer['pack'])
        self.assertEqual(answer['stage'], 'tdd')

    def test_brief_works_before_any_handoff_has_been_written(self):
        answer = self.brief()
        self.assertIsNone(answer['recorded_at'])
        self.assertIsNone(answer['pack_matches_record'])

    def test_brief_says_the_file_still_matches_what_was_recorded(self):
        record = self.handoff()
        answer = self.brief()
        self.assertEqual(answer['recorded_at'], record['sequence'])
        self.assertTrue(answer['pack_matches_record'])

    def test_brief_says_when_the_file_has_drifted_from_the_record(self):
        self.handoff()
        self.pack_file().write_text('# Edited by hand\n')
        self.assertFalse(self.brief()['pack_matches_record'])

    def test_brief_does_not_write_a_record(self):
        before = len(self.records())
        self.brief()
        self.assertEqual(len(self.records()), before)


class BudgetTest(SessionEnvironment):
    """What a session can be told about its own spending, and when it cannot."""

    def setUp(self):
        super().setUp()
        self.start()
        from harness import cost
        self.logs = Path(tempfile.mkdtemp())
        self.addCleanup(setattr, cost, 'LOGS', cost.LOGS)
        cost.LOGS = self.logs

    def write_log(self, output_tokens, tool_calls=0):
        """A session log of the shape the assistant writes, and nothing else."""
        from harness import cost
        directory = cost.log_directory(self.root)
        directory.mkdir(parents=True, exist_ok=True)
        entry = dict(timestamp='2026-09-24T10:00:00Z',
                     message=dict(usage=dict(output_tokens=output_tokens),
                                  content=[dict(type='tool_use')] * tool_calls))
        (directory / f'{SESSION_ID}.jsonl').write_text(json.dumps(entry) + '\n')

    def write_subagent_log(self, agent_id, agent_type, output_tokens, tool_calls=0):
        """A subagent's own transcript, beside the parent's, the way Claude Code writes it."""
        from harness import cost
        directory = cost.log_directory(self.root) / SESSION_ID / 'subagents'
        directory.mkdir(parents=True, exist_ok=True)
        entry = dict(timestamp='2026-09-24T10:00:00Z',
                     message=dict(usage=dict(output_tokens=output_tokens),
                                  content=[dict(type='tool_use')] * tool_calls))
        (directory / f'agent-{agent_id}.jsonl').write_text(json.dumps(entry) + '\n')
        (directory / f'agent-{agent_id}.meta.json').write_text(
            json.dumps(dict(agentType=agent_type)))

    def budget(self):
        return self.run_harness('budget', self.ticket_id)

    def test_a_session_under_budget_says_what_is_left(self):
        self.write_log(1000, tool_calls=3)
        answer = self.budget()
        self.assertEqual(answer['output_tokens'], 1000)
        self.assertEqual(answer['tool_calls'], 3)
        self.assertFalse(answer['over'])
        self.assertEqual(answer['remaining'], 59000)

    def test_a_session_over_budget_names_the_slice_boundary(self):
        self.write_log(70000)
        answer = self.budget()
        self.assertTrue(answer['over'])
        self.assertIn('handoff', answer['next_stop'])

    def test_a_session_under_budget_is_told_no_next_stop(self):
        self.write_log(100)
        self.assertIsNone(self.budget()['next_stop'])

    def test_no_log_for_this_session_is_null_rather_than_zero(self):
        answer = self.budget()
        self.assertIsNone(answer['output_tokens'])
        self.assertIsNone(answer['tool_calls'])
        self.assertIsNone(answer['over'])
        self.assertIn('null is not zero', answer['unavailable'])

    def test_budget_writes_no_record(self):
        self.write_log(10)
        before = len(self.records())
        self.budget()
        self.assertEqual(len(self.records()), before)

    def test_the_budget_reports_subagents_apart_from_the_parent(self):
        self.write_log(1000, tool_calls=3)
        self.write_subagent_log('x', 'seen-implementer', 500, tool_calls=2)
        answer = self.budget()
        # The parent's own figures do not move for a subagent's spending.
        self.assertEqual(answer['output_tokens'], 1000)
        self.assertEqual(answer['tool_calls'], 3)
        subagents = answer['subagents']
        self.assertEqual(subagents['output_tokens'], 500)
        self.assertEqual(subagents['tool_calls'], 2)
        self.assertEqual(len(subagents['agents']), 1)
        entry = subagents['agents'][0]
        self.assertEqual(entry['agent'], 'seen-implementer')
        self.assertEqual(entry['output_tokens'], 500)
        self.assertEqual(entry['tool_calls'], 2)

    def test_no_subagents_directory_is_null_rather_than_zero(self):
        self.write_log(10)
        subagents = self.budget()['subagents']
        self.assertIsNone(subagents['agents'])
        self.assertIsNone(subagents['output_tokens'])
        self.assertIn('null is not zero', subagents['unavailable'])

    def test_budget_carries_the_budget_it_judged_against(self):
        self.write_log(10)
        self.assertEqual(self.budget()['budget'], 60000)


class TheSkillSaysSoTest(unittest.TestCase):
    """The rule a session actually reads, in the one file both assistants get."""

    def source(self):
        from harness.tests.helpers import PROJECT
        return (PROJECT / 'docs' / 'harness' / 'skill.md').read_text()

    def test_it_says_one_slice_per_session(self):
        self.assertIn('one slice per session', self.source().lower())

    def test_it_names_the_pack_a_later_session_starts_from(self):
        text = self.source()
        self.assertIn('harness handoff', text)
        # The skill writes the command with the ticket in it, so the flag is what
        # a substring can honestly look for.
        self.assertIn('harness status', text)
        self.assertIn('--brief', text)

    def test_it_names_the_command_that_reads_the_budget(self):
        self.assertIn('harness budget', self.source())

    def test_it_says_the_prd_and_the_architecture_are_read_once(self):
        self.assertIn('once, at clarify', self.source())


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

if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
