"""One source for the lifecycle hooks, and the two copies each assistant reads.

The copies are generated, for the reason harness/skills.py gives about the skill
and harness/agents.py about the agents: two files that must agree and are edited
separately will not agree, and the one that is wrong is the one somebody read.

The departure these tests exist for is that neither copy is wholly ours.
.claude/settings.json carries the permissions block and graphify's own read
guards; .codex/hooks.json carries repowise's context loader. So sync replaces
only the entries the harness owns and writes the rest back untouched, and drift
compares only those. Ownership is read off the command prefix, which makes one
case worth more than the others: a hand edit to a harness command stops the
entry being ours, so a check that compared only what it still owned would report
nothing at all. That is the silent pass, and it has a test of its own.
"""

import json
import unittest

import harness.hooks as hooks
from harness import doctor as doctoring, triage
from harness.errors import HarnessError
from harness.repository import Repository
from harness.tests.test_lifecycle import CommandTest

CLAUDE_COPY = '.claude/settings.json'
CODEX_COPY = '.codex/hooks.json'

# The six the ticket's description names, in the order the source declares them.
EVENTS = ('SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PreCompact', 'SubagentStop', 'Stop')

# What each copy holds that is none of the harness's business, as this
# repository holds it: graphify's two guards and the permissions block on the
# Claude Code side, repowise's loader on the Codex side. The Codex fixture puts
# a foreign entry on SessionStart under the matcher the harness also uses, which
# is the case a merge by event name alone would overwrite.
FOREIGN_CLAUDE = {
    'hooks': {
        'PreToolUse': [
            {'matcher': 'Bash|Grep',
             'hooks': [{'type': 'command', 'command': 'graphify hook-guard search',
                        'timeout': 10}]},
            {'matcher': 'Read|Glob',
             'hooks': [{'type': 'command', 'command': 'graphify hook-guard read',
                        'timeout': 10}]},
        ],
    },
    'permissions': {
        'allow': ['Bash(python3 harness/run.py:*)', 'Bash(graphify:*)', 'Bash(gitleaks:*)'],
        'deny': [],
        'defaultMode': 'acceptEdits',
    },
}
FOREIGN_CODEX = {
    'hooks': {
        'SessionStart': [
            {'matcher': 'startup|resume|clear',
             'hooks': [{'type': 'command', 'command': 'repowise-augment --client codex',
                        'timeout': 10, 'statusMessage': 'Loading repowise context...'}]},
        ],
        'PostToolUse': [
            {'matcher': 'Bash|shell_command',
             'hooks': [{'type': 'command', 'command': 'repowise-augment --client codex',
                        'timeout': 10, 'statusMessage': 'Checking repowise freshness...'}]},
        ],
    },
}


class HookSyncTest(CommandTest):
    """sync against a project whose copies already hold somebody else's entries."""

    def setUp(self):
        super().setUp()
        self.write(CLAUDE_COPY, json.dumps(FOREIGN_CLAUDE, indent=2) + '\n')
        self.write(CODEX_COPY, json.dumps(FOREIGN_CODEX, indent=2) + '\n')

    def copy(self, relative):
        return json.loads((self.root / relative).read_text())

    def commands(self, relative):
        """Every command in a copy, whoever owns it."""
        return [entry.get('command')
                for groups in self.copy(relative)['hooks'].values()
                for group in groups
                for entry in group['hooks']]

    def problems(self):
        return doctoring.report(Repository(self.root), {})['problems']

    def test_the_source_names_the_six_events_the_ticket_describes(self):
        self.assertEqual(tuple(event['event'] for event in hooks.load(self.root)), EVENTS)

    def test_sync_writes_both_copies_and_says_so(self):
        written = self.run_harness('sync')['written']
        for relative in (CLAUDE_COPY, CODEX_COPY):
            self.assertIn(relative, written)
            self.assertIn('hooks', self.copy(relative))

    def test_sync_leaves_the_permissions_block_exactly_as_it_found_it(self):
        """The permissions are the person's. A sync that rewrote them would make
        every graphify or allowlist change a doctor failure in this repository."""
        self.run_harness('sync')
        self.assertEqual(self.copy(CLAUDE_COPY)['permissions'], FOREIGN_CLAUDE['permissions'])

    def test_sync_leaves_the_graphify_hooks_in_place(self):
        self.run_harness('sync')
        commands = self.commands(CLAUDE_COPY)
        self.assertIn('graphify hook-guard search', commands)
        self.assertIn('graphify hook-guard read', commands)

    def test_sync_leaves_the_repowise_entries_in_place_including_a_shared_event(self):
        self.run_harness('sync')
        document = self.copy(CODEX_COPY)
        self.assertEqual(document['hooks']['PostToolUse'], FOREIGN_CODEX['hooks']['PostToolUse'])
        self.assertIn(FOREIGN_CODEX['hooks']['SessionStart'][0], document['hooks']['SessionStart'])

    def test_every_event_reaches_the_clients_that_take_it_and_no_other(self):
        self.run_harness('sync')
        for event in hooks.load(self.root):
            for client, relative in (('claude', CLAUDE_COPY), ('codex', CODEX_COPY)):
                command = hooks.command_for(event, client)
                if client in event['clients']:
                    self.assertIn(command, self.commands(relative))
                else:
                    self.assertNotIn(command, self.commands(relative))

    def test_the_codex_copy_takes_no_event_codex_does_not_document(self):
        """The `clients` key carries weight or it carries nothing.

        PreCompact and SubagentStop are Claude Code's; Codex documents neither,
        so a copy naming them would be a command nothing ever runs.
        """
        self.run_harness('sync')
        claude, codex = self.copy(CLAUDE_COPY)['hooks'], self.copy(CODEX_COPY)['hooks']
        for event in ('PreCompact', 'SubagentStop'):
            self.assertIn(event, claude)
            self.assertNotIn(event, codex)

    def test_every_generated_command_begins_with_the_harness_invocation(self):
        """Ownership is the command prefix, so a command written any other way is
        an entry sync would disown and drift would report against itself."""
        for event in hooks.load(self.root):
            for client in event['clients']:
                self.assertTrue(hooks.command_for(event, client).startswith(hooks.INVOCATION),
                                hooks.command_for(event, client))

    def test_every_generated_entry_carries_a_command_type_and_a_timeout(self):
        self.run_harness('sync')
        for relative in (CLAUDE_COPY, CODEX_COPY):
            for groups in hooks.owned(self.copy(relative)).values():
                for group in groups:
                    for entry in group['hooks']:
                        self.assertEqual(entry['type'], 'command')
                        self.assertIsInstance(entry['timeout'], int)
                        self.assertGreater(entry['timeout'], 0)

    def test_syncing_twice_changes_nothing(self):
        """A merge that appended rather than replaced would double every entry."""
        self.run_harness('sync')
        first = [(self.root / relative).read_text() for relative in (CLAUDE_COPY, CODEX_COPY)]
        self.run_harness('sync')
        self.assertEqual([(self.root / relative).read_text()
                          for relative in (CLAUDE_COPY, CODEX_COPY)], first)

    def test_doctor_is_quiet_immediately_after_sync(self):
        self.run_harness('sync')
        self.assertEqual(self.problems(), [])

    def test_doctor_reports_a_harness_command_edited_by_hand(self):
        """The silent pass this check exists for.

        The edit breaks the invocation prefix, so the entry is no longer the
        harness's by the rule sync uses. A drift check that compared only the
        entries it still owned would find nothing missing and pass.
        """
        self.run_harness('sync')
        document = self.copy(CLAUDE_COPY)
        document['hooks']['Stop'][0]['hooks'][0]['command'] = 'true # disabled by hand'
        self.write(CLAUDE_COPY, json.dumps(document, indent=2) + '\n')

        found = [problem for problem in self.problems() if CLAUDE_COPY in problem]
        self.assertTrue(found, self.problems())
        self.assertIn('Stop', found[0])
        self.assertIn('sync', found[0])

    def test_doctor_reports_a_harness_command_whose_client_was_changed(self):
        """The other half: still ours by its prefix, and no longer what the
        source generates."""
        self.run_harness('sync')
        document = self.copy(CODEX_COPY)
        entry = document['hooks']['PreToolUse'][0]['hooks'][0]
        entry['command'] = entry['command'].replace('--client codex', '--client claude')
        self.write(CODEX_COPY, json.dumps(document, indent=2) + '\n')

        found = [problem for problem in self.problems() if CODEX_COPY in problem]
        self.assertTrue(found, self.problems())
        self.assertIn('PreToolUse', found[0])

    def test_doctor_says_nothing_about_a_foreign_entry_added_by_hand(self):
        """graphify and repowise ship hooks on their own release cycle. A drift
        check that reported one would make every upgrade a harness failure."""
        self.run_harness('sync')
        document = self.copy(CLAUDE_COPY)
        document['hooks']['PreToolUse'].append(
            {'matcher': 'WebFetch',
             'hooks': [{'type': 'command', 'command': 'graphify hook-guard fetch', 'timeout': 5}]})
        document['hooks']['SessionEnd'] = [
            {'hooks': [{'type': 'command', 'command': 'graphify update .', 'timeout': 30}]}]
        self.write(CLAUDE_COPY, json.dumps(document, indent=2) + '\n')

        self.assertEqual(self.problems(), [])

    def test_sync_leaves_a_foreign_entry_added_by_hand_alone(self):
        self.run_harness('sync')
        document = self.copy(CLAUDE_COPY)
        document['hooks']['SessionEnd'] = [
            {'hooks': [{'type': 'command', 'command': 'graphify update .', 'timeout': 30}]}]
        self.write(CLAUDE_COPY, json.dumps(document, indent=2) + '\n')

        self.run_harness('sync')
        self.assertIn('graphify update .', self.commands(CLAUDE_COPY))

    def test_doctor_reports_a_harness_entry_the_source_does_not_name(self):
        """The strays case, one layer in: an entry that claims the harness's name
        and comes from no source has had no review."""
        self.run_harness('sync')
        document = self.copy(CLAUDE_COPY)
        document['hooks']['PostToolUse'] = [
            {'matcher': 'Edit',
             'hooks': [{'type': 'command',
                        'command': f'{hooks.INVOCATION} hook post-tool-use --client claude',
                        'timeout': 10}]}]
        self.write(CLAUDE_COPY, json.dumps(document, indent=2) + '\n')

        found = [problem for problem in self.problems() if CLAUDE_COPY in problem]
        self.assertTrue(found, self.problems())
        self.assertIn('PostToolUse', found[0])

    def test_doctor_reports_one_of_the_harness_entries_duplicated_by_hand(self):
        """A copy that holds one of ours twice runs that hook twice.

        The groups under an event are compared as a count rather than a list,
        because their order is not something either assistant acts on; a
        comparison that ignored order and not number would pass this.
        """
        self.run_harness('sync')
        document = self.copy(CLAUDE_COPY)
        document['hooks']['SessionStart'].append(document['hooks']['SessionStart'][0])
        self.write(CLAUDE_COPY, json.dumps(document, indent=2) + '\n')

        found = [problem for problem in self.problems() if CLAUDE_COPY in problem]
        self.assertTrue(found, self.problems())
        self.assertIn('SessionStart', found[0])

    def test_doctor_reports_a_missing_copy(self):
        self.run_harness('sync')
        (self.root / CODEX_COPY).unlink()

        found = [problem for problem in self.problems() if CODEX_COPY in problem]
        self.assertTrue(found, self.problems())
        self.assertIn('missing', found[0].lower())

    def test_doctor_reports_a_copy_that_is_not_valid_json_rather_than_raising(self):
        self.run_harness('sync')
        self.write(CLAUDE_COPY, '{ "hooks": ,}\n')

        self.assertTrue([problem for problem in self.problems() if CLAUDE_COPY in problem],
                        self.problems())

    def test_sync_refuses_a_source_that_names_no_command(self):
        self.write(str(hooks.SOURCE),
                   json.dumps({'events': [{'event': 'Stop', 'timeout': 10,
                                           'clients': ['claude']}]}) + '\n')

        with self.assertRaisesRegex(HarnessError, 'command'):
            self.run_harness('sync')

    def test_the_two_copies_count_as_generated_for_the_review_triage(self):
        """A review that read a generated file as an unplanned change would force
        full depth on every ticket that runs sync."""
        self.assertTrue({CLAUDE_COPY, CODEX_COPY} <= triage.generated_paths())

    def test_doctor_repairs_nothing(self):
        self.run_harness('sync')
        document = self.copy(CLAUDE_COPY)
        document['hooks']['Stop'][0]['hooks'][0]['command'] = 'true # disabled by hand'
        edited = json.dumps(document, indent=2) + '\n'
        self.write(CLAUDE_COPY, edited)

        self.problems()
        self.assertEqual((self.root / CLAUDE_COPY).read_text(), edited)


if __name__ == '__main__':
    unittest.main()
