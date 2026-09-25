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
        """F10: a file with no source under harness/agents/ has had no review.

        The name must be one no source generates. Both of these used
        seen-implementer until SEEN-108 made it the third agent, at which point
        its name entered the set `strays` skips and `drift` reported the
        hand-written bytes instead: the assertion still passed and the check it
        was written for was exercised by nothing. F3 of that ticket's third
        review.
        """
        self.run_harness('sync')
        stray = self.root / '.claude' / 'agents' / 'seen-architect.md'
        stray.write_text('---\nname: seen-architect\ntools: Edit, Write, Bash\n---\n')

        found = [problem for problem in self.problems() if 'seen-architect' in problem]
        self.assertTrue(found, self.problems())

    def test_a_stray_codex_agent_file_is_reported_too(self):
        self.run_harness('sync')
        (self.root / '.codex' / 'agents' / 'seen-architect.toml').write_text('name = "x"\n')

        self.assertTrue([problem for problem in self.problems() if 'seen-architect' in problem],
                        self.problems())

    def test_only_the_stray_check_can_report_a_file_with_no_source(self):
        """The guard the two above lost: drift must not be able to stand in for strays.

        A generated copy differs from its rendering, which is what drift reports;
        a file no source generates has no rendering to differ from, so if this
        passes with `strays` removed from `drift` the check is decorative.
        """
        from harness import agents
        self.run_harness('sync')
        (self.root / '.claude' / 'agents' / 'seen-architect.md').write_text(
            '---\nname: seen-architect\ntools: Edit, Write, Bash\n---\n')

        self.assertEqual(agents.drift(self.root), agents.strays(self.root),
                         'drift reports this file only because it calls strays')
        self.assertTrue(agents.strays(self.root))

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
    """What each agent is allowed to do, which is the point of separating them."""

    def test_neither_reader_may_write(self):
        """The scout and the reviewer read and nothing else.

        SEEN-105 could say this of every agent because every agent was a reader.
        SEEN-108 adds one that writes the slice, so the rule is stated of the
        two it was always about rather than quietly dropped.
        """
        from harness import agents
        for agent in (agents.SCOUT, agents.REVIEWER):
            for forbidden in ('Edit', 'Write', 'NotebookEdit'):
                self.assertNotIn(forbidden, agent['tools'],
                                 f'{agent["name"]} must not hold {forbidden}')

    def test_the_implementer_is_the_only_agent_that_may_write(self):
        from harness import agents
        writers = [agent['name'] for agent in agents.AGENTS if 'Write' in agent['tools']]
        self.assertEqual(writers, ['seen-implementer'])

    def test_the_scout_can_reach_the_graphs_and_the_reviewer_cannot_be_the_implementer(self):
        from harness import agents
        self.assertIn('codegraph', agents.SCOUT['tools'])
        self.assertEqual(agents.REVIEWER['sandbox_mode'], 'read-only')

    def test_the_roster_and_the_brief_cap_are_a_diff_a_person_reviews(self):
        from harness import thresholds
        rules = thresholds.load(self.root)
        self.assertEqual(sorted(rules['agents']['names']),
                         ['seen-implementer', 'seen-reviewer', 'seen-scout'])
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
        # A name nobody has a source for. seen-implementer was this fixture's
        # unknown until SEEN-108 made it one of the three.
        with self.assertRaises(HarnessError) as raised:
            self.brief(10, agent='seen-architect')
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


IMPLEMENTER_CLAUDE = '.claude/agents/seen-implementer.md'
IMPLEMENTER_CODEX = '.codex/agents/seen-implementer.toml'
IMPLEMENTER_BODY = '# The implementer\n\nWork one slice. Red, then green, then stop.\n'


class ImplementerTest(CommandTest):
    """The one agent whose model and effort are not its own to choose.

    The scout and the reviewer carry a model because what they do never changes.
    The implementer's is the route's, read from the branch's journal, which is
    why its copies are generated per slice rather than once.
    """

    def setUp(self):
        super().setUp()
        self.write('harness/agents/seen-scout.md', SCOUT_BODY)
        self.write('harness/agents/seen-reviewer.md', REVIEWER_BODY)
        self.write('harness/agents/seen-implementer.md', IMPLEMENTER_BODY)

    def frontmatter(self):
        self.run_harness('sync')
        return (self.root / IMPLEMENTER_CLAUDE).read_text().split('---\n')[1]

    def codex(self):
        self.run_harness('sync')
        return tomllib.loads((self.root / IMPLEMENTER_CODEX).read_text())

    def test_sync_writes_both_implementer_copies(self):
        self.run_harness('sync')
        for relative in (IMPLEMENTER_CLAUDE, IMPLEMENTER_CODEX):
            self.assertTrue((self.root / relative).is_file(),
                            f'{relative} was not written')

    def test_the_implementer_holds_edit_and_write(self):
        """The first agent that does, because writing the slice is what it is for."""
        frontmatter = self.frontmatter()
        self.assertIn('Edit', frontmatter)
        self.assertIn('Write', frontmatter)

    def test_the_claude_copy_carries_an_effort_key(self):
        """Claude Code has no per-invocation effort override, so the file is where it goes."""
        self.assertRegex(self.frontmatter(), r'\neffort: (low|medium|high|max)\n')

    def test_the_codex_copy_carries_a_reasoning_effort(self):
        self.assertIn('model_reasoning_effort', self.codex())

    def test_a_branch_with_no_route_gets_the_strongest_at_high_effort(self):
        """Main, a fresh clone and CI all land here, and the safe value is the strong one."""
        self.assertIn('model: opus', self.frontmatter())
        self.assertIn('effort: high', self.frontmatter())
        self.assertEqual(self.codex()['model_reasoning_effort'], 'high')

    def test_the_scout_and_the_reviewer_carry_no_effort_key(self):
        """An agent with no effort of its own takes the session's, which is what omitting it means."""
        self.run_harness('sync')
        for relative in CLAUDE_COPIES:
            self.assertNotIn('\neffort:', (self.root / relative).read_text())

    def test_doctor_reports_no_drift_after_sync(self):
        self.run_harness('sync')
        self.assertEqual(self.problems(), [])

    def problems(self):
        return doctoring.report(Repository(self.root), {})['problems']

    def test_an_edited_implementer_copy_is_reported_as_drift(self):
        self.run_harness('sync')
        path = self.root / IMPLEMENTER_CLAUDE
        path.write_text(path.read_text().replace('model: opus', 'model: haiku'))
        self.assertTrue(any('seen-implementer' in problem for problem in self.problems()))
