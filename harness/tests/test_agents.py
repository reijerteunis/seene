"""Two agents with a context of their own, and the copies each assistant reads.

The copies are generated, never edited, for the reason harness/skills.py already
gives about the skill: two files that must agree and are edited separately will
not agree, and the one that is wrong is the one somebody read. The frontmatter
keys are pinned key by key because Claude Code skips a file with invalid YAML and
silently ignores a key it does not recognise, so a wrong key produces no error
anywhere and a test is the only thing that will catch it.
"""

import tomllib
import unittest
from pathlib import Path

from harness import doctor as doctoring
from harness.errors import HarnessError
from harness.repository import Repository
from harness.tests.test_lifecycle import CommandTest

PROJECT = Path(__file__).resolve().parents[2]

CLAUDE_COPIES = ('.claude/agents/seen-scout.md', '.claude/agents/seen-reviewer.md')
CODEX_COPIES = ('.codex/agents/seen-scout.toml', '.codex/agents/seen-reviewer.toml')

# The keys each assistant reads, spelled the way it reads them. Camel case on the
# Claude Code side is not a preference: the documentation spells permissionMode
# and omitClaudeMd that way, and a hyphenated copy would be ignored in silence.
CLAUDE_KEYS = ('name', 'description', 'tools', 'model', 'permissionMode', 'omitClaudeMd')
CODEX_KEYS = ('name', 'description', 'developer_instructions', 'sandbox_mode', 'model')

SCOUT_BODY = '# The scout\n\nAnswer the question and stop. At most 400 words.\n'
REVIEWER_BODY = '# The reviewer\n\nRead the diff against the criteria. Never edit.\n'


class AgentSyncTest(CommandTest):

    def setUp(self):
        super().setUp()
        self.write('harness/agents/seen-scout.md', SCOUT_BODY)
        self.write('harness/agents/seen-reviewer.md', REVIEWER_BODY)

    def copies(self):
        return [self.root / path for path in CLAUDE_COPIES + CODEX_COPIES]

    def problems(self):
        return doctoring.report(Repository(self.root), {})['problems']

    def test_sync_writes_a_copy_for_each_assistant_and_each_agent(self):
        self.run_harness('sync')
        for path in self.copies():
            self.assertTrue(path.is_file(), f'{path.relative_to(self.root)} was not written')

    def test_each_claude_copy_carries_the_frontmatter_claude_code_reads(self):
        self.run_harness('sync')
        for relative in CLAUDE_COPIES:
            text = (self.root / relative).read_text()
            self.assertTrue(text.startswith('---\n'), f'{relative} must start with frontmatter')
            frontmatter = text.split('---\n')[1]
            for key in CLAUDE_KEYS:
                self.assertIn(f'{key}:', frontmatter, f'{relative} is missing {key}')
            self.assertNotIn('permission-mode', text, 'the key Claude Code reads is permissionMode')
            self.assertNotIn('omit-claude-md', text, 'the key Claude Code reads is omitClaudeMd')

    def test_each_codex_copy_is_toml_carrying_the_keys_codex_reads(self):
        self.run_harness('sync')
        for relative in CODEX_COPIES:
            parsed = tomllib.loads((self.root / relative).read_text())
            for key in CODEX_KEYS:
                self.assertIn(key, parsed, f'{relative} is missing {key}')

    def test_the_body_of_every_copy_is_its_source(self):
        self.run_harness('sync')
        for relative in ('.claude/agents/seen-scout.md', '.codex/agents/seen-scout.toml'):
            self.assertIn('At most 400 words.', (self.root / relative).read_text())
        for relative in ('.claude/agents/seen-reviewer.md', '.codex/agents/seen-reviewer.toml'):
            self.assertIn('Never edit.', (self.root / relative).read_text())

    def test_every_copy_says_it_was_generated_and_from_where(self):
        self.run_harness('sync')
        for path in self.copies():
            text = path.read_text()
            self.assertIn('generated', text.lower())
            self.assertIn('harness/agents/', text)

    def test_sync_reports_the_agent_copies_it_wrote(self):
        written = self.run_harness('sync')['written']
        for relative in CLAUDE_COPIES + CODEX_COPIES:
            self.assertIn(relative, written)

    def test_doctor_is_quiet_immediately_after_sync(self):
        self.run_harness('sync')
        self.assertEqual(self.problems(), [])

    def test_doctor_names_a_copy_edited_by_hand_and_the_command_that_fixes_it(self):
        self.run_harness('sync')
        edited = self.root / CLAUDE_COPIES[0]
        edited.write_text(edited.read_text() + '\nsomeone added a line here\n')
        found = [problem for problem in self.problems() if CLAUDE_COPIES[0] in problem]
        self.assertTrue(found, self.problems())
        self.assertIn('sync', found[0])

    def test_doctor_names_a_codex_copy_edited_by_hand(self):
        self.run_harness('sync')
        edited = self.root / CODEX_COPIES[1]
        edited.write_text(edited.read_text() + '\nhand_edited = true\n')
        self.assertTrue([problem for problem in self.problems() if CODEX_COPIES[1] in problem],
                        self.problems())

    def test_doctor_reports_a_missing_copy(self):
        self.run_harness('sync')
        (self.root / CODEX_COPIES[0]).unlink()
        found = [problem for problem in self.problems() if CODEX_COPIES[0] in problem]
        self.assertTrue(found, self.problems())
        self.assertIn('missing', found[0].lower())

    def test_doctor_reports_a_missing_source_rather_than_inventing_one(self):
        self.run_harness('sync')
        (self.root / 'harness' / 'agents' / 'seen-scout.md').unlink()
        self.assertTrue([problem for problem in self.problems() if 'seen-scout' in problem],
                        self.problems())

    def test_an_agent_file_nobody_generates_is_reported(self):
        """F10: a file with no source under harness/agents/ has had no review."""
        self.run_harness('sync')
        stray = self.root / '.claude' / 'agents' / 'seen-implementer.md'
        stray.write_text('---\nname: seen-implementer\ntools: Edit, Write, Bash\n---\n')

        found = [problem for problem in self.problems() if 'seen-implementer' in problem]
        self.assertTrue(found, self.problems())

    def test_a_stray_codex_agent_file_is_reported_too(self):
        self.run_harness('sync')
        (self.root / '.codex' / 'agents' / 'seen-implementer.toml').write_text('name = "x"\n')

        self.assertTrue([problem for problem in self.problems() if 'seen-implementer' in problem],
                        self.problems())

    def test_a_project_agent_of_ones_own_is_left_alone(self):
        """G7: .claude/agents/ belongs to the person; only the seen- names are ours."""
        self.run_harness('sync')
        (self.root / '.claude' / 'agents' / 'my-debugger.md').write_text('---\nname: x\n---\n')

        self.assertEqual(self.problems(), [])

    def test_doctor_repairs_nothing(self):
        self.run_harness('sync')
        edited = self.root / CLAUDE_COPIES[0]
        edited.write_text('edited by hand\n')
        self.problems()
        self.assertEqual(edited.read_text(), 'edited by hand\n',
                         'a self-check reports, it never repairs')


class AgentDefinitionTest(CommandTest):
    """What the two agents are allowed to do, which is the point of separating them."""

    def test_neither_agent_may_write(self):
        from harness import agents
        for agent in agents.AGENTS:
            for forbidden in ('Edit', 'Write', 'NotebookEdit'):
                self.assertNotIn(forbidden, agent['tools'],
                                 f'{agent["name"]} must not hold {forbidden}')

    def test_the_scout_can_reach_the_graphs_and_the_reviewer_cannot_be_the_implementer(self):
        from harness import agents
        self.assertIn('codegraph', agents.SCOUT['tools'])
        self.assertEqual(agents.REVIEWER['sandbox_mode'], 'read-only')

    def test_the_roster_and_the_brief_cap_are_a_diff_a_person_reviews(self):
        from harness import thresholds
        rules = thresholds.load(self.root)
        self.assertEqual(sorted(rules['agents']['names']), ['seen-reviewer', 'seen-scout'])
        self.assertEqual(rules['agents']['brief_word_limit'], 400)


class ScoutBriefTest(CommandTest):
    """What comes back from a context of its own, and how small it has to be.

    A brief is the only thing that crosses back into the session that asked, so
    it is capped and the cap is enforced where the record is written rather than
    in the agent's instructions, which are a request and not a control.
    """

    def setUp(self):
        super().setUp()
        self.start()

    def brief(self, words, agent='seen-scout'):
        relative = '.harness-drafts/brief.md'
        self.write(relative, ' '.join(['word'] * words) + '\n')
        return self.run_harness('note', self.ticket_id, '--file', relative,
                                '--actor', 'claude:implementer', '--from', agent)

    def test_a_brief_at_the_cap_is_recorded_with_its_agent_and_its_count(self):
        record = self.brief(400)
        self.assertEqual(record['kind'], 'note')
        self.assertEqual(record['data']['agent'], 'seen-scout')
        self.assertEqual(record['data']['words'], 400)

    def test_a_brief_over_the_cap_is_refused_naming_the_count_and_the_cap(self):
        with self.assertRaises(HarnessError) as raised:
            self.brief(401)
        message = str(raised.exception)
        self.assertIn('401', message)
        self.assertIn('400', message)

    def test_a_refused_brief_is_not_recorded(self):
        before = len(self.records())
        with self.assertRaises(HarnessError):
            self.brief(401)
        self.assertEqual(len(self.records()), before)

    def test_a_brief_says_which_session_recorded_it(self):
        self.assertEqual(self.brief(10)['session'], self.records()[-1]['session'])

    def test_an_unknown_agent_is_refused_and_the_roster_is_named(self):
        with self.assertRaises(HarnessError) as raised:
            self.brief(10, agent='seen-implementer')
        self.assertIn('seen-scout', str(raised.exception))

    def test_an_ordinary_note_is_not_capped(self):
        relative = '.harness-drafts/long-note.md'
        self.write(relative, ' '.join(['word'] * 900) + '\n')
        record = self.run_harness('note', self.ticket_id, '--file', relative,
                                  '--actor', 'claude:implementer')
        self.assertEqual(record['kind'], 'note')
        self.assertNotIn('agent', record['data'])

    def test_a_brief_stays_a_note_so_the_record_kinds_are_unchanged(self):
        from harness.paths import KINDS
        self.assertNotIn('brief', KINDS)
        self.assertEqual(self.brief(10)['kind'], 'note')


class TheSkillSaysSoTest(unittest.TestCase):
    """The one maintained skill, on the two agents a session may send work to."""

    @classmethod
    def setUpClass(cls):
        cls.text = (PROJECT / 'docs' / 'harness' / 'skill.md').read_text()

    def test_it_names_both_agents(self):
        self.assertIn('seen-scout', self.text)
        self.assertIn('seen-reviewer', self.text)

    def test_it_says_codex_spawns_one_only_when_told_to(self):
        self.assertIn('Codex', self.text)
        self.assertRegex(self.text, r'(?i)codex[^.]*only when')

    def test_it_says_a_subagent_is_a_context_boundary_and_not_independence(self):
        self.assertRegex(self.text, r'(?i)context boundary')

    def test_it_tells_a_session_to_set_the_codex_depth_rather_than_asserting_it(self):
        """F11: the setting lives in a file this repository does not track."""
        self.assertIn('.codex/config.toml', self.text)
        self.assertNotRegex(self.text, r'(?i)max_depth. is 1 on both sides')

    def test_it_discloses_that_the_reviewer_holds_bash(self):
        """F9: Claude Code has no read-only Bash, so the hole is named, not implied."""
        self.assertIn('Bash', self.text)
        self.assertIn('SEEN-106', self.text)

    def test_it_names_the_trigger_the_gate_actually_reads(self):
        """H5: the skill described the rule as it was before G3."""
        self.assertIn('changes_agent_action', self.text)

    def test_it_points_at_the_assistants_rather_than_every_actor(self):
        """H5: [actors] tools carries human, and the gate reads [actors] assistants."""
        self.assertIn('[actors] assistants', self.text)

    def test_it_says_a_reviewer_session_is_refused_whichever_attempt_it_worked(self):
        """H6: F5 widened this from the current attempt to every attempt."""
        self.assertNotRegex(self.text, r"(?i)this attempt's own records")

    def test_it_names_the_word_cap_on_a_brief(self):
        self.assertIn('400', self.text)
