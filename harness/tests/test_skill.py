"""One maintained skill, two generated copies, neither edited by hand."""

import unittest
from pathlib import Path

from harness import skills
from harness.tests.test_lifecycle import CommandTest

PROJECT = Path(__file__).resolve().parents[2]


class SyncTest(CommandTest):

    def setUp(self):
        super().setUp()
        self.write('docs/harness/skill.md', '# The Seen harness\n\nWork the five stages.\n')

    def copies(self):
        return [self.root / path for path in skills.COMMITTED]

    def test_sync_writes_both_committed_copies(self):
        self.run_harness('sync')
        for path in self.copies():
            self.assertTrue(path.is_file(), f'{path} was not written')

    def test_each_copy_carries_the_frontmatter_an_assistant_reads(self):
        self.run_harness('sync')
        for path in self.copies():
            text = path.read_text()
            self.assertTrue(text.startswith('---\n'), 'a skill starts with its frontmatter')
            self.assertIn('name: seen-harness', text)
            self.assertIn('description:', text)

    def test_each_copy_says_where_it_came_from(self):
        self.run_harness('sync')
        for path in self.copies():
            self.assertIn('docs/harness/skill.md', path.read_text())
            self.assertIn('generated', path.read_text().lower())

    def test_the_body_is_the_source(self):
        self.run_harness('sync')
        for path in self.copies():
            self.assertIn('Work the five stages.', path.read_text())

    def test_doctor_is_quiet_immediately_after_sync(self):
        self.run_harness('sync')
        self.assertTrue(self.run_harness('doctor')['ok'])

    def test_doctor_reports_a_copy_edited_by_hand_and_names_it(self):
        self.run_harness('sync')
        edited = self.copies()[0]
        edited.write_text(edited.read_text() + '\nsomeone added a line here\n')
        from harness import doctor as doctoring
        from harness.repository import Repository
        problems = doctoring.skill_problems(Repository(self.root))
        self.assertTrue(any(str(skills.COMMITTED[0]) in problem for problem in problems), problems)

    def test_doctor_repairs_nothing(self):
        self.run_harness('sync')
        edited = self.copies()[0]
        edited.write_text('edited by hand\n')
        self.run_harness('doctor') if False else None
        from harness import doctor as doctoring
        from harness.repository import Repository
        doctoring.skill_problems(Repository(self.root))
        self.assertEqual(edited.read_text(), 'edited by hand\n', 'a self-check reports, never repairs')

    def test_a_missing_source_is_reported_rather_than_invented(self):
        (self.root / 'docs' / 'harness' / 'skill.md').unlink()
        from harness import doctor as doctoring
        from harness.repository import Repository
        problems = doctoring.skill_problems(Repository(self.root))
        self.assertTrue(any('skill.md' in problem for problem in problems), problems)


class RouteInTheSkillTest(unittest.TestCase):
    """What the skill says about where a slice's model comes from.

    The whole point of the route is that it is decided where the information is
    and never inside the session that would benefit from a stronger model, so
    the document both assistants read has to say so.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = (PROJECT / 'docs' / 'harness' / 'skill.md').read_text()

    def test_it_names_the_command(self):
        self.assertIn('harness route', self.text)

    def test_it_says_the_route_is_read_from_the_pack_and_never_chosen_in_the_session(self):
        self.assertRegex(self.text, r'(?i)never chosen inside the session')
        self.assertRegex(self.text, r'(?i)handoff pack')

    def test_it_names_the_rules_that_are_never_jev_s_to_answer(self):
        for word in ('money', 'credential', 'migration'):
            self.assertRegex(self.text, rf'(?i){word}')

    def test_it_names_the_implementer_agent(self):
        self.assertIn('seen-implementer', self.text)


class AgentCountTest(unittest.TestCase):
    """F8 of SEEN-108's first review: the heading counted two of three."""

    @classmethod
    def setUpClass(cls):
        cls.text = (PROJECT / 'docs' / 'harness' / 'skill.md').read_text()

    def test_the_heading_counts_the_agents_the_roster_holds(self):
        self.assertNotIn('## The two agents', self.text)
        self.assertIn('## The three agents', self.text)

    def test_every_agent_in_the_roster_is_named_under_it(self):
        from harness import thresholds
        section = self.text.split('## The three agents')[1]
        for name in thresholds.load(PROJECT)['agents']['names']:
            self.assertIn(name, section)
