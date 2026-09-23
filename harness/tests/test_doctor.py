"""The self-check a session runs before it starts working."""

import json

from harness import doctor, thresholds
from harness.errors import HarnessError
from harness.repository import Repository
from harness.tests.test_lifecycle import CommandTest, clarify_evidence


class DoctorTest(CommandTest):

    def report(self):
        repository = Repository(self.root)
        return doctor.report(repository, thresholds.load(self.root))

    def commit(self, message='docs: record'):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', message)

    def test_a_healthy_project_passes(self):
        self.start()
        report = self.report()
        self.assertTrue(report['ok'], report['problems'])

    def test_it_names_the_ticket_whose_chain_is_broken(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        record = self.root / 'docs/harness/history' / self.ticket_id / '0001.json'
        record.write_text(record.read_text().replace('claude:implementer', 'codex:reviewer'))
        report = self.report()
        self.assertFalse(report['ok'])
        self.assertTrue(any(self.ticket_id in problem and 'chain' in problem
                            for problem in report['problems']), report['problems'])

    def test_it_fails_when_a_record_was_committed_as_a_modification(self):
        self.start()
        self.commit()
        record = self.root / 'docs/harness/history' / self.ticket_id / '0001.json'
        content = json.loads(record.read_text())
        content['actor'] = 'codex:reviewer'
        record.write_text(json.dumps(content, indent=2) + '\n')
        self.commit('docs: quietly rewrite the record')
        problems = self.report()['problems']
        self.assertTrue(any('0001.json' in problem and 'history' in problem
                            for problem in problems), problems)

    def test_it_fails_when_a_record_was_removed_from_a_live_journal(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.commit()
        (self.root / 'docs/harness/history' / self.ticket_id / '0002.json').unlink()
        self.commit('docs: drop the last record')
        problems = self.report()['problems']
        self.assertTrue(any('0002.json' in problem for problem in problems), problems)

    def test_retiring_a_whole_journal_is_not_a_rewrite(self):
        self.start()
        self.commit()
        import shutil
        shutil.rmtree(self.root / 'docs/harness/history' / self.ticket_id)
        self.commit('chore: retire the previous project')
        self.assertTrue(self.report()['ok'], self.report()['problems'])

    def test_it_fails_on_a_stray_file_beside_the_records(self):
        self.start()
        (self.root / 'docs/harness/history' / self.ticket_id / '0001.json.bak').write_text('{}')
        self.assertTrue(any('0001.json.bak' in problem for problem in self.report()['problems']))

    def test_it_fails_on_a_markdown_link_that_does_not_resolve(self):
        self.write('docs/guide.md', 'See the [ticket](SEEN-999-nothing.md) for detail.\n')
        problems = self.report()['problems']
        self.assertTrue(any('docs/guide.md:1' in problem for problem in problems), problems)

    def test_it_ignores_links_inside_code_fences_and_to_the_web(self):
        self.write('docs/guide.md',
                   'A [live link](https://example.test/x).\n\n```\n[not a link](nope.md)\n```\n')
        self.assertTrue(self.report()['ok'], self.report()['problems'])

    def test_it_fails_when_the_drafts_directory_is_not_ignored(self):
        self.write('.gitignore', '\n')
        problems = self.report()['problems']
        self.assertTrue(any('.harness-drafts' in problem for problem in problems), problems)

    def test_it_fails_on_a_template_that_is_not_readable(self):
        self.write('harness/templates/review.json', '{oops')
        problems = self.report()['problems']
        self.assertTrue(any('review.json' in problem for problem in problems), problems)

    def test_it_reports_every_problem_rather_than_the_first(self):
        self.write('.gitignore', '\n')
        self.write('harness/templates/review.json', '{oops')
        self.write('docs/guide.md', 'A [broken link](nowhere.md).\n')
        self.assertGreaterEqual(len(self.report()['problems']), 3)

    def test_it_refuses_a_python_below_the_floor(self):
        self.assertEqual(doctor.python_problems((3, 14, 0)), [])
        self.assertTrue(doctor.python_problems((3, 11, 9)))

    def test_the_command_exits_non_zero_when_something_is_wrong(self):
        self.write('.gitignore', '\n')
        with self.assertRaisesRegex(HarnessError, 'self-check'):
            self.run_harness('doctor')

    def test_the_command_passes_on_a_healthy_project(self):
        self.assertTrue(self.run_harness('doctor')['ok'])


class AppendOnlyScopeTest(DoctorTest):
    """Records are append-only. The files beside them are not records."""

    def test_a_rewritten_kpi_cache_is_not_a_rewritten_record(self):
        self.start()
        self.write('docs/harness/history/' + self.ticket_id + '/kpi.json', '{"ticket": "a"}')
        self.commit()
        self.write('docs/harness/history/' + self.ticket_id + '/kpi.json', '{"ticket": "b"}')
        self.commit('docs: the ticket delivered again, so its figures changed')

        report = self.report()
        self.assertTrue(report['ok'], report['problems'])

    def test_a_rewritten_record_is_still_caught(self):
        self.start()
        self.commit()
        record = self.root / 'docs/harness/history' / self.ticket_id / '0001.json'
        record.write_text(record.read_text().replace('claude:implementer', 'codex:reviewer'))
        self.commit('docs: quietly rewrite the record')

        problems = self.report()['problems']
        self.assertTrue(any('0001.json' in problem for problem in problems), problems)
