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

The second half of this file is the dispatcher: `harness hook <event> --client
<claude|codex>`, fed each assistant's own hook JSON on stdin. It goes through
subprocess for the reason test_guard.py does, that what a hook reads is the
process's stdout, its stderr and its exit code, and an envelope built in process
proves none of the three.

## What was verified about the Codex side, and how

Slice 2 left the Codex payload field names unestablished rather than guess them.
They are established here from the tool itself: codex-cli 0.156.1 carries a JSON
Schema for every hook event's input and output inside its own binary, and
`strings` on it prints all twenty-three, titled `pre-tool-use.command.input`,
`session-start.command.output` and so on. They name the same fields Claude Code
documents, `hook_event_name`, `cwd`, `session_id`, `tool_name`, `tool_input`,
`prompt`, `trigger`, `agent_type`, `last_assistant_message`, `stop_hook_active`,
and the same response envelope, `hookSpecificOutput` with `hookEventName` and
`additionalContext`, `decision` with `reason`, and `systemMessage`; one of them
says so in as many words, describing `reason` as what "Claude requires when
`decision` is `block`". The payload fixtures below carry every field those
schemas mark required, so a Codex payload here is a Codex payload.

Two things the binary does not settle and no fixture can. Whether Codex loads a
project-level .codex/hooks.json at all is criterion 5 and needs a real session.
And what `tool_input` holds for an edit is opaque in the schema (`"tool_input":
true`), so the patch shapes below come from the instruction the binary itself
gives the model, a command array of `apply_patch` and a patch whose lines carry
`*** Update File: path/to/file`, and from the patch grammar printed beside it. A
payload the dispatcher finds no path in is allowed rather than refused, which is
what makes an unrecognised shape a missed guard rather than a blocked session.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

import harness.hooks as hooks
from harness import cli, doctor as doctoring, triage
from harness.errors import HarnessError
from harness.repository import Repository
from harness.tests.helpers import HARNESS
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence
from harness.tests.test_session_cap import SESSION_ID, plan
from harness.tests.test_triage import TriageTest, review_evidence

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

    def test_both_copies_carry_all_six_events(self):
        """F2: the withholding this replaces rested on a reason known to be false.

        Slice 1 gave PreCompact and SubagentStop to Claude Code alone because
        Codex was thought to document neither. Record 20 of this ticket disproved
        both from the codex-cli 0.156.1 binary, which carries a JSON Schema per
        hook event, so the choice was between correcting the reason and correcting
        the behaviour. The behaviour, because with the schemas in hand there is no
        reason left to write: a compacting Codex session loses its pack and a Codex
        reviewer is held to no findings rule.
        """
        self.run_harness('sync')
        claude, codex = self.copy(CLAUDE_COPY)['hooks'], self.copy(CODEX_COPY)['hooks']
        for event in EVENTS:
            self.assertIn(event, claude)
            self.assertIn(event, codex)

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


class PartlyGeneratedCopyTest(TriageTest):
    """F1: one list answered two questions, and a security control fell through it.

    `generated_paths` is asked two different things. The review triage asks
    whether a change in a file is an unplanned change, and a synced entry is not
    one. The code fingerprint the review gate compares asks whether a change in a
    file is evidence about the work, and for a copy that is generated whole the
    two answers are the same. Neither hook copy is generated whole:
    .claude/settings.json carries the permission allowlist and `defaultMode`,
    which no source generates and `hooks.drift` cannot see, so excluding the file
    from the fingerprint let the permission surface widen between the triage and
    the review advance with nothing refusing it.

    So the scenario is run rather than described. A test that asserted only that
    two path sets differ would pass against a refactor that left the hole open,
    which is how the defect survived attempt 1.
    """

    def advance_review(self, read):
        return self.submit('review', review_evidence(read), actor='codex:reviewer')

    def widen_the_permissions(self):
        """The part of the copy nobody generates, changed the way a session would."""
        document = json.loads((self.root / CLAUDE_COPY).read_text())
        document['permissions'] = {'allow': ['Bash(curl:*)'], 'deny': []}
        document['defaultMode'] = 'bypassPermissions'
        self.write(CLAUDE_COPY, json.dumps(document, indent=2) + '\n')

    def test_a_permission_widened_after_the_triage_refuses_the_review_advance(self):
        self.reach_review()
        record = self.triage()
        self.widen_the_permissions()

        with self.assertRaisesRegex(HarnessError, 'moved'):
            self.advance_review(record['data']['focus'])

    def test_a_changed_hook_copy_is_still_not_an_unplanned_change(self):
        """The other half, and the reason the two sets are separated rather than
        the hook copies dropped: a triage that read a synced entry as unplanned
        would fail slice_files on every ticket that runs sync."""
        self.reach_review()
        self.widen_the_permissions()

        ran = {check['name']: check for check in self.triage()['data']['deterministic']}
        self.assertEqual(ran['slice_files']['outcome'], 'pass', ran['slice_files']['detail'])


RUN = HARNESS / 'run.py'

# What this slice's RED demonstrates, in the words of the failure that is
# actually available. The solution record wrote it as a ModuleNotFoundError on
# harness.hooks; slice 1 created that module, so before the dispatcher exists the
# failure is argparse exiting 2 on `hook` as a command it does not recognise. The
# demonstration is the one the record meant: nothing in this harness reads a hook
# payload, so there is no envelope and no additionalContext to assert against.
NOTHING_ANSWERS = ('Nothing answered this hook payload. Slice 3 RED: the solution record '
                   'predicted ModuleNotFoundError on harness.hooks, and slice 1 created that '
                   'module, so the failure available here is argparse exiting 2 on `hook` as an '
                   'unknown command. Same demonstration, that nothing reads a payload yet. ')

# One reviewer answer of the shape harness/agents/seen-reviewer.md asks for.
REVIEW = {
    'reviewer': 'claude:reviewer',
    'independence': 'subagent',
    'reviewer_session': 'a1b2c3d4e5f6',
    'read': ['harness/journal.py'],
    'acceptance_evidence': ['1. The journal holds one record per stage: record 4'],
    'findings': [{'id': 'F1', 'severity': 'high', 'file': 'harness/journal.py:31',
                  'claim': 'A record edited after the fact reads back without complaint',
                  'failure_scenario': 'Edit 0002.json, run history, and the chain still verifies',
                  'status': 'open', 'resolution': ''}],
    'checks': [],
    'verdict': 'return',
}


def claude_edit_payload(root, path):
    """Claude Code's PreToolUse payload for an Edit, whose path is absolute."""
    return dict(session_id=SESSION_ID, transcript_path=None, cwd=str(root),
                permission_mode='default', model='claude-opus-5',
                hook_event_name='PreToolUse', tool_name='Edit', tool_use_id='toolu_01',
                turn_id='turn_01', tool_input=dict(file_path=str(root / path),
                                                   old_string='a', new_string='b'))


def codex_patch(path, action='Update File'):
    """A patch of the shape the codex binary's own instruction shows."""
    return (f'*** Begin Patch\n*** {action}: {path}\n@@\n-old\n+new\n*** End Patch\n')


def codex_patch_payload(root, path, freeform=False):
    """Codex's PreToolUse payload for an apply_patch, in both shapes it has.

    Every field pre-tool-use.command.input marks required, and the patch text
    where the schema is opaque: freeform carries it as the tool's whole input,
    the command array is how the prompt in the binary tells the model to call it.
    """
    patch = codex_patch(path)
    tool_input = dict(input=patch) if freeform else dict(command=['apply_patch', patch])
    return dict(session_id=SESSION_ID, transcript_path=None, cwd=str(root),
                permission_mode='default', model='gpt-5.1-codex-max',
                hook_event_name='PreToolUse', tool_name='apply_patch', tool_use_id='call_01',
                turn_id='turn_01', tool_input=tool_input)


def session_start_payload(root, source='startup'):
    return dict(session_id=SESSION_ID, transcript_path=None, cwd=str(root),
                permission_mode='default', model='claude-opus-5',
                hook_event_name='SessionStart', source=source)


def user_prompt_payload(root, prompt='Work the slice.'):
    return dict(session_id=SESSION_ID, transcript_path=None, cwd=str(root),
                permission_mode='default', model='claude-opus-5', turn_id='turn_01',
                hook_event_name='UserPromptSubmit', prompt=prompt)


def pre_compact_payload(root, trigger='auto'):
    return dict(session_id=SESSION_ID, transcript_path=None, cwd=str(root),
                model='claude-opus-5', turn_id='turn_01',
                hook_event_name='PreCompact', trigger=trigger)


def subagent_stop_payload(root, message, agent='seen-reviewer', stop_hook_active=False):
    return dict(session_id=SESSION_ID, transcript_path=None, cwd=str(root),
                permission_mode='default', model='claude-opus-5', turn_id='turn_01',
                hook_event_name='SubagentStop', agent_id='agent_01', agent_type=agent,
                agent_transcript_path=None, last_assistant_message=message,
                stop_hook_active=stop_hook_active)


def stop_payload(root, stop_hook_active=False):
    return dict(session_id=SESSION_ID, transcript_path=None, cwd=str(root),
                permission_mode='default', model='claude-opus-5', turn_id='turn_01',
                hook_event_name='Stop', last_assistant_message='Done.',
                stop_hook_active=stop_hook_active)


class HookDispatchTest(CommandTest):
    """`harness hook <event> --client <client>`, fed a payload on stdin."""

    def hook(self, event, payload, client='claude', **environment):
        return subprocess.run(
            [sys.executable, str(RUN), '--root', str(self.root), 'hook', event,
             '--client', client],
            input=json.dumps(payload), capture_output=True, text=True,
            env=dict(os.environ, **environment))

    def envelope(self, event, payload, client='claude', **environment):
        """The envelope the hook printed, which must be the only thing on stdout."""
        result = self.hook(event, payload, client, **environment)
        self.assertEqual(result.returncode, 0, NOTHING_ANSWERS + result.stderr)
        return json.loads(result.stdout)

    def injected(self, envelope):
        return (envelope.get('hookSpecificOutput') or {}).get('additionalContext')

    def at_tdd(self, slices=1):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence(slices=plan(slices)))


class SessionStartTest(HookDispatchTest):
    """The pack, injected before the session reads anything else."""

    def test_it_injects_the_pack_as_additional_context(self):
        self.at_tdd()
        for client in ('claude', 'codex'):
            with self.subTest(client=client):
                envelope = self.envelope('session-start', session_start_payload(self.root), client)
                self.assertEqual(envelope['hookSpecificOutput']['hookEventName'], 'SessionStart')
                self.assertIn(f'# {self.ticket_id} handoff pack', self.injected(envelope))

    def test_the_injected_pack_carries_the_slice_in_hand(self):
        self.at_tdd(slices=2)
        envelope = self.envelope('session-start', session_start_payload(self.root))
        self.assertIn('Slice 1 of 2', self.injected(envelope))

    def test_it_injects_nothing_when_the_branch_names_no_ticket(self):
        """A session on main is not working a ticket, and a hook with nothing to
        say says nothing rather than something empty."""
        self.at_tdd()
        self.git('checkout', '-q', 'main')
        self.assertEqual(self.envelope('session-start', session_start_payload(self.root)), {})

    def test_it_injects_nothing_before_the_ticket_has_started(self):
        self.assertEqual(self.envelope('session-start', session_start_payload(self.root)), {})

    def test_it_writes_no_record(self):
        self.at_tdd()
        before = len(self.records())
        self.envelope('session-start', session_start_payload(self.root))
        self.assertEqual(len(self.records()), before)


class UserPromptSubmitTest(HookDispatchTest):
    """The budget, said once it is spent and not before."""

    def log(self, output_tokens):
        """A session log where the hook's own process will look for it.

        HOME rather than a patched module attribute: the hook runs in a process
        of its own, and cost.LOGS is read off the home directory at import.
        """
        home = Path(self.root) / 'home'
        named = str(Path(self.root).resolve()).replace('/', '-')
        directory = home / '.claude' / 'projects' / named
        directory.mkdir(parents=True, exist_ok=True)
        entry = dict(timestamp='2026-09-26T10:00:00Z',
                     message=dict(usage=dict(output_tokens=output_tokens),
                                  content=[dict(type='tool_use')]))
        (directory / f'{SESSION_ID}.jsonl').write_text(json.dumps(entry) + '\n')
        return dict(HOME=str(home), CLAUDE_CODE_SESSION_ID=SESSION_ID)

    def test_it_injects_nothing_while_the_session_is_under_budget(self):
        self.at_tdd()
        envelope = self.envelope('user-prompt-submit', user_prompt_payload(self.root),
                                 **self.log(1000))
        self.assertEqual(envelope, {}, 'a hook that speaks every turn is a hook people turn off')

    def test_it_names_the_figure_once_the_session_is_over_budget(self):
        self.at_tdd()
        for client in ('claude', 'codex'):
            with self.subTest(client=client):
                envelope = self.envelope('user-prompt-submit', user_prompt_payload(self.root),
                                         client, **self.log(70000))
                self.assertEqual(envelope['hookSpecificOutput']['hookEventName'],
                                 'UserPromptSubmit')
                injected = self.injected(envelope)
                self.assertIn('70000', injected)
                self.assertIn('60000', injected)
                self.assertIn('handoff', injected)

    def test_it_injects_nothing_when_there_is_no_log_to_read(self):
        """Null is not zero, and a session whose spending nobody can read is not
        a session over budget."""
        self.at_tdd()
        self.assertEqual(self.envelope('user-prompt-submit', user_prompt_payload(self.root),
                                       HOME=str(self.root / 'nowhere')), {})


class PreToolUseTest(HookDispatchTest):
    """The guard, reached through each assistant's own payload."""

    def test_it_refuses_a_file_the_accepted_slice_does_not_name(self):
        self.at_tdd()
        result = self.hook('pre-tool-use', claude_edit_payload(self.root, 'apps/web/src/page.tsx'))
        self.assertEqual(result.returncode, 2, NOTHING_ANSWERS + result.stderr)
        self.assertEqual(result.stdout, '', 'a refusal must not print an envelope')
        self.assertIn('apps/web/src/page.tsx', result.stderr)

    def test_it_allows_a_file_the_accepted_slice_names(self):
        self.at_tdd()
        envelope = self.envelope('pre-tool-use',
                                 claude_edit_payload(self.root, 'harness/journal.py'))
        self.assertEqual(envelope, {},
                         'an allowance says nothing: permissionDecision allow would bypass the '
                         'permissions the person set')

    def test_it_reads_the_path_out_of_a_codex_apply_patch_payload(self):
        self.at_tdd()
        for freeform in (False, True):
            with self.subTest(freeform=freeform):
                payload = codex_patch_payload(self.root, 'apps/web/src/page.tsx',
                                              freeform=freeform)
                result = self.hook('pre-tool-use', payload, 'codex')
                self.assertEqual(result.returncode, 2, NOTHING_ANSWERS + result.stderr)
                self.assertIn('apps/web/src/page.tsx', result.stderr)

    def test_a_patch_touching_several_files_is_refused_on_the_one_that_is_refused(self):
        self.at_tdd()
        patch = ('*** Begin Patch\n*** Update File: harness/journal.py\n@@\n-old\n+new\n'
                 '*** Add File: apps/web/src/page.tsx\n+line\n*** End Patch\n')
        payload = dict(codex_patch_payload(self.root, 'harness/journal.py'),
                       tool_input=dict(command=['apply_patch', patch]))
        result = self.hook('pre-tool-use', payload, 'codex')
        self.assertEqual(result.returncode, 2, NOTHING_ANSWERS + result.stderr)
        self.assertIn('apps/web/src/page.tsx', result.stderr)

    def test_a_payload_it_can_find_no_path_in_is_allowed(self):
        """An unrecognised shape must be a guard that missed, never a session
        that cannot edit anything."""
        self.at_tdd()
        payload = dict(claude_edit_payload(self.root, 'harness/journal.py'),
                       tool_name='mcp__something__write', tool_input=dict(query='what changed'))
        self.assertEqual(self.envelope('pre-tool-use', payload, 'codex'), {})

    def test_it_writes_no_record_when_it_refuses(self):
        self.at_tdd()
        before = len(self.records())
        self.hook('pre-tool-use', claude_edit_payload(self.root, 'apps/web/src/page.tsx'))
        self.assertEqual(len(self.records()), before)


class PreCompactTest(HookDispatchTest):
    """The pack, written before the context that holds it is summarised."""

    def pack_file(self):
        return self.root / '.harness-drafts' / f'{self.ticket_id}-handoff.md'

    def test_it_writes_the_pack_and_appends_a_handoff_record(self):
        self.at_tdd()
        before = len(self.records())
        envelope = self.envelope('pre-compact', pre_compact_payload(self.root, 'auto'))
        records = self.records()
        self.assertEqual(len(records), before + 1)
        self.assertEqual(records[-1]['kind'], 'handoff')
        self.assertTrue(self.pack_file().is_file())
        self.assertIn('handoff', envelope['systemMessage'])

    def test_a_manual_compaction_writes_one_too(self):
        self.at_tdd()
        before = len(self.records())
        self.envelope('pre-compact', pre_compact_payload(self.root, 'manual'))
        self.assertEqual(len(self.records()), before + 1)

    def test_the_record_says_the_compaction_wrote_it(self):
        """A pack written by a compaction is not a session declaring a boundary,
        and a later reader has to be able to tell the two apart."""
        self.at_tdd()
        self.envelope('pre-compact', pre_compact_payload(self.root))
        record = self.records()[-1]
        self.assertTrue(record['data'].get('auto'))
        self.assertFalse(record['data']['slice']['declared'])

    def test_no_accepted_slice_plan_writes_nothing_and_does_not_fail(self):
        self.start()
        before = len(self.records())
        envelope = self.envelope('pre-compact', pre_compact_payload(self.root))
        self.assertEqual(len(self.records()), before)
        self.assertFalse(self.pack_file().exists())
        self.assertIn('slice', envelope.get('systemMessage', '').lower())

    def test_it_does_not_fail_on_a_branch_that_is_not_the_ticket_s(self):
        """A hook that fails compaction loses the context it was protecting."""
        self.at_tdd()
        self.git('checkout', '-q', 'main')
        result = self.hook('pre-compact', pre_compact_payload(self.root))
        self.assertEqual(result.returncode, 0, NOTHING_ANSWERS + result.stderr)
        self.assertEqual(len(self.records()), 3)

    def test_it_does_not_fail_when_the_journal_cannot_be_read(self):
        self.at_tdd()
        (self.root / 'docs' / 'harness' / 'history' / self.ticket_id / '0002.json').unlink()
        result = self.hook('pre-compact', pre_compact_payload(self.root))
        self.assertEqual(result.returncode, 0, NOTHING_ANSWERS + result.stderr)
        self.assertIn('not written', result.stdout)

    def test_handoff_auto_is_still_bound_to_the_ticket_s_branch(self):
        """--auto writes a record, so it keeps every rule a writing command has."""
        self.at_tdd()
        self.git('checkout', '-q', 'main')
        with self.assertRaisesRegex(HarnessError, 'branch'):
            self.run_harness('handoff', self.ticket_id, '--actor', 'claude:implementer', '--auto')


class SubagentStopTest(HookDispatchTest):
    """The reviewer's findings, validated where they are cheapest to fix."""

    def draft(self):
        return self.root / '.harness-drafts' / f'{self.ticket_id}-review.json'

    def message(self, review=None):
        """A reviewer's last message: prose, the record in a fence, more prose."""
        return ('Here is the review.\n\n```json\n'
                + json.dumps(review or REVIEW, indent=2)
                + '\n```\n\nOne finding, so the verdict is a return.\n')

    def test_it_drafts_the_review_record_from_the_reviewer_s_answer(self):
        self.at_tdd()
        envelope = self.envelope('subagent-stop',
                                 subagent_stop_payload(self.root, self.message()))
        self.assertTrue(self.draft().is_file())
        self.assertEqual(json.loads(self.draft().read_text())['findings'][0]['id'], 'F1')
        self.assertIn(f'{self.ticket_id}-review.json', envelope['systemMessage'])

    def test_it_blocks_a_finding_the_review_gate_would_refuse(self):
        """A high finding naming no file is refused at the gate. Refusing it here
        costs the reviewer one more answer instead of a whole round trip."""
        self.at_tdd()
        review = dict(REVIEW, findings=[dict(REVIEW['findings'][0], file='')])
        envelope = self.envelope('subagent-stop',
                                 subagent_stop_payload(self.root, self.message(review)))
        self.assertEqual(envelope['decision'], 'block')
        self.assertIn('file', envelope['reason'])
        self.assertFalse(self.draft().exists())

    def test_it_blocks_a_finding_with_no_failure_scenario(self):
        self.at_tdd()
        review = dict(REVIEW, findings=[dict(REVIEW['findings'][0], failure_scenario='')])
        envelope = self.envelope('subagent-stop',
                                 subagent_stop_payload(self.root, self.message(review)))
        self.assertEqual(envelope['decision'], 'block')
        self.assertIn('failure_scenario', envelope['reason'])

    def test_it_blocks_an_answer_carrying_no_review_record_at_all(self):
        self.at_tdd()
        envelope = self.envelope('subagent-stop',
                                 subagent_stop_payload(self.root, 'It all looks fine to me.'))
        self.assertEqual(envelope['decision'], 'block')

    def test_a_review_with_no_findings_is_drafted_rather_than_blocked(self):
        self.at_tdd()
        review = dict(REVIEW, findings=[], verdict='pass')
        envelope = self.envelope('subagent-stop',
                                 subagent_stop_payload(self.root, self.message(review)))
        self.assertNotIn('decision', envelope)
        self.assertTrue(self.draft().is_file())

    def test_it_says_nothing_about_another_agent_stopping(self):
        """Which agent stopped is read from the payload, because the matcher on
        this event is not documented as matching an agent name."""
        self.at_tdd()
        envelope = self.envelope('subagent-stop',
                                 subagent_stop_payload(self.root, self.message(),
                                                       agent='seen-scout'))
        self.assertEqual(envelope, {})
        self.assertFalse(self.draft().exists())

    def test_it_does_not_block_the_same_answer_twice(self):
        self.at_tdd()
        envelope = self.envelope('subagent-stop',
                                 subagent_stop_payload(self.root, 'No JSON here.',
                                                       stop_hook_active=True))
        self.assertEqual(envelope, {})

    def test_it_never_overwrites_a_draft_that_is_already_there(self):
        """A second reviewer's answer must not replace the first's."""
        self.at_tdd()
        self.envelope('subagent-stop', subagent_stop_payload(self.root, self.message()))
        second = dict(REVIEW, reviewer='codex:reviewer', findings=[], verdict='pass')
        envelope = self.envelope('subagent-stop',
                                 subagent_stop_payload(self.root, self.message(second)))
        self.assertEqual(json.loads(self.draft().read_text())['reviewer'], 'claude:reviewer')
        self.assertIn(f'{self.ticket_id}-review-2.json', envelope['systemMessage'])

    def test_it_writes_no_journal_record(self):
        self.at_tdd()
        before = len(self.records())
        self.envelope('subagent-stop', subagent_stop_payload(self.root, self.message()))
        self.assertEqual(len(self.records()), before)


class StopTest(HookDispatchTest):
    """The self-check at the end of a turn, quick rather than whole."""

    def test_it_is_quiet_when_the_quick_check_finds_nothing(self):
        self.at_tdd()
        self.assertEqual(self.envelope('stop', stop_payload(self.root)), {})

    def test_it_blocks_once_when_a_generated_copy_has_been_edited_by_hand(self):
        self.at_tdd()
        document = json.loads((self.root / CLAUDE_COPY).read_text())
        document['hooks']['Stop'][0]['hooks'][0]['command'] = 'true # disabled by hand'
        self.write(CLAUDE_COPY, json.dumps(document, indent=2) + '\n')

        envelope = self.envelope('stop', stop_payload(self.root))
        self.assertEqual(envelope['decision'], 'block')
        self.assertIn(CLAUDE_COPY, envelope['reason'])

    def test_it_does_not_block_twice_in_the_same_turn(self):
        """stop_hook_active is the loop guard both payloads carry, and a hook
        that blocked on a problem it cannot fix would never let a turn end."""
        self.at_tdd()
        self.write(CLAUDE_COPY, '{ "hooks": ,}\n')
        self.assertEqual(self.envelope('stop', stop_payload(self.root, stop_hook_active=True)), {})

    def test_the_quick_check_leaves_out_the_sections_that_read_every_file(self):
        quick = doctoring.report(Repository(self.root), {}, quick=True)['checked']
        whole = doctoring.report(Repository(self.root), {})['checked']
        self.assertEqual([section for section in whole if section not in quick],
                         ['marketplace_hosts', 'links'])
        for section in ('journals', 'append_only', 'skill', 'agents', 'hook_files',
                        'ticket_status'):
            self.assertIn(section, quick)


class DispatcherShapeTest(CommandTest):
    """What the dispatcher is, beside what each event does."""

    def test_every_event_the_source_names_has_a_handler(self):
        named = {hooks.dispatch_name(event['event']) for event in hooks.load(self.root)}
        self.assertEqual(named, set(hooks.HANDLERS))

    def test_the_dispatch_name_and_the_event_name_are_each_other_s_inverse(self):
        for event in EVENTS:
            self.assertEqual(hooks.event_name(hooks.dispatch_name(event)), event)

    def test_the_hook_command_writes_no_record_and_so_takes_no_actor(self):
        self.assertNotIn('hook', cli.WRITING_COMMANDS)
        self.assertNotIn('hook', cli.TICKET_COMMANDS)

    def test_an_unknown_client_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'client'):
            hooks.respond(Repository(self.root), {}, 'stop', {}, 'gemini')

    def test_an_unknown_event_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'post-tool-use'):
            hooks.respond(Repository(self.root), {}, 'post-tool-use', {}, 'claude')


if __name__ == '__main__':
    unittest.main()
