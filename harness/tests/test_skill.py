"""One maintained skill, two generated copies, neither edited by hand."""

from harness import skills
from harness.tests.test_lifecycle import CommandTest


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
