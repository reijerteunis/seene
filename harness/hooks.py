"""The lifecycle hooks, one source and the copy each assistant reads.

The skill tells a session what to do and a hook makes it unable to do otherwise,
which is the whole difference between a procedure and an enforced one. Both
assistants run the same events with the same JSON shape, so one source describes
them once: harness/hooks.json names the event, the matcher, the harness command,
the timeout and which clients take it, and `sync` writes both copies from it.

The departure from harness/skills.py and harness/agents.py, which generate their
copies whole: neither copy here is wholly ours. .claude/settings.json carries the
permissions block and graphify's read guards, .codex/hooks.json carries
repowise's context loader, and both belong to somebody else. A sync that
rewrote them would turn every graphify release into a doctor failure in this
repository. So `sync` replaces only the entries the harness owns and writes the
rest back untouched, and `drift` compares only those.

Ownership is the command prefix and nothing else. Neither assistant documents its
hook schema as extensible, so a marker key beside the command is a refusal
waiting for a release, and the command is already the thing that makes an entry
the harness's. The consequence worth stating: a hand edit to a command stops the
entry being ours, so `drift` cannot ask only whether what it owns still matches.
It compares both ways, which is what reports an edited command as missing and a
harness-looking entry no source names as unnamed, rather than disowning either in
silence.

The second half of this module is the dispatcher the generated commands call:
`harness hook <event> --client <claude|codex>` reads that event's JSON on stdin
and prints that client's response envelope on stdout. Each event calls what the
harness already has, the pack, the budget, the guard, the handoff and the quick
self-check, and adds nothing of its own; an event that needed new judgement would
be a rule a hook invented, which is the one thing a hook must never be.

## The two envelopes, and what was verified about them

`--client` rather than a subcommand per client because the envelope differs by
client and not by event, which is the reason repowise-augment takes the same
flag. Verified on codex-cli 0.156.1 on 26 September 2026: the binary carries a
JSON Schema for every hook event's input and output, and `strings` on it prints
all twenty-three, titled `pre-tool-use.command.input`,
`session-start.command.output` and so on. They name the same payload fields
Claude Code documents and the same response envelope, `hookSpecificOutput` with
`hookEventName` and `additionalContext`, `decision` with `reason`, and
`systemMessage`; the subagent-stop and stop schemas say so outright, describing
`reason` as what "Claude requires when `decision` is `block`". So the two
envelopes are one envelope here, and the client is validated rather than branched
on: a typo in a generated command is a refusal instead of a silent success.

Three things that verification does not reach. Whether Codex loads a
project-level .codex/hooks.json at all is criterion 5 and only a real session
settles it. What `tool_input` carries for an edit is opaque in the schema, so
`paths_in` reads every shape either assistant is known to send and allows a
payload it finds no path in. And the same schemas show Codex supports PreCompact
and SubagentStop after all, which harness/hooks.json gives to Claude Code alone;
that file is slice 1's and the correction belongs to whoever amends it.
"""

from collections import Counter
import json
from pathlib import Path
import re

from .errors import HarnessError, require
from .paths import CLAUDE_SETTINGS, CODEX_HOOKS, DRAFTS, HOOK_SOURCE

SOURCE = HOOK_SOURCE

# One copy per client, keyed by the name the generated commands carry in
# --client. The renderer is the only thing that writes those commands, which is
# what keeps the ownership rule true.
COPIES = {'claude': CLAUDE_SETTINGS, 'codex': CODEX_HOOKS}

# How this repository invokes the harness, and so how an entry says it is ours.
# Written once here because a second spelling anywhere would be an entry sync
# disowns and drift reports against itself.
INVOCATION = 'python3 harness/run.py'

FIX = 'it is generated, so edit {source} and run {invocation} sync'.format(
    source=SOURCE, invocation=INVOCATION)


def load(root):
    """The events the source declares, in the order it declares them.

    Order is kept because it is the order the entries are written in, and a
    generated file whose entries move about on every sync is a diff nobody can
    read.
    """
    path = root / SOURCE
    require(path.is_file(), f'{SOURCE} does not exist, so there are no hooks to generate from')
    try:
        document = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise HarnessError(f'{SOURCE} is not valid JSON: {error}') from error
    events = document.get('events')
    require(isinstance(events, list) and events, f'{SOURCE} declares no events')
    for event in events:
        for key in ('event', 'command', 'timeout', 'clients'):
            require(event.get(key) is not None,
                    f'{SOURCE} has an entry with no {key}: {json.dumps(event)}')
        unknown = [client for client in event['clients'] if client not in COPIES]
        require(not unknown,
                f'{SOURCE} names {", ".join(unknown)} for {event["event"]}, and the clients are '
                + ', '.join(COPIES))
    return events


def command_for(event, client):
    """The command an entry carries: the harness, the dispatch, the client.

    --client rather than one subcommand per client, for the reason
    repowise-augment takes the same flag: the response envelope differs by
    client and not by event, so the difference belongs in one place.
    """
    return f'{INVOCATION} {event["command"]} --client {client}'


def groups(events, client):
    """What the harness owns in one copy: event name to the groups under it."""
    built = {}
    for event in events:
        if client not in event['clients']:
            continue
        group = {}
        # Omitted rather than null when the event has none. UserPromptSubmit,
        # SubagentStop and Stop match on nothing, and a matcher that matched
        # nothing would be a hook that never ran.
        if event.get('matcher'):
            group['matcher'] = event['matcher']
        group['hooks'] = [dict(type='command', command=command_for(event, client),
                               timeout=event['timeout'])]
        built.setdefault(event['event'], []).append(group)
    return built


def ours(entry):
    """Whether one command entry is the harness's."""
    command = entry.get('command')
    return isinstance(command, str) and command.startswith(INVOCATION)


def _kept(group):
    """The group with the harness's entries taken out."""
    return dict(group, hooks=[entry for entry in group.get('hooks', []) if not ours(entry)])


def owned(document):
    """The harness's entries in a loaded copy, in the shape `groups` returns.

    A group can hold a foreign entry beside one of ours, so it is the entry that
    is kept or dropped rather than the group.
    """
    found = {}
    for event, existing in (document.get('hooks') or {}).items():
        mine = [dict(group, hooks=[entry for entry in group.get('hooks', []) if ours(entry)])
                for group in existing]
        mine = [group for group in mine if group['hooks']]
        if mine:
            found[event] = mine
    return found


def merge(document, events, client):
    """The copy with the harness's entries replaced and everything else as it was.

    Replaced rather than appended, so a sync run twice writes the same file, and
    an event the source no longer names loses its harness entry without taking
    anybody else's with it.
    """
    hooks = {}
    for event, existing in (document.get('hooks') or {}).items():
        kept = [group for group in (_kept(group) for group in existing) if group['hooks']]
        if kept:
            hooks[event] = kept
    for event, mine in groups(events, client).items():
        hooks[event] = hooks.get(event, []) + mine
    return dict(document, hooks=hooks)


def _pin(group):
    """One group as a string, so two of them can be compared and counted.

    Counted rather than listed: the order of the groups under one event is not
    something either assistant acts on, so a copy that holds ours in another
    order is not drift, and a copy that holds one of ours twice is a hook that
    runs twice and has to be reported.
    """
    return json.dumps(group, sort_keys=True)


def _command_in(pinned):
    return json.loads(pinned)['hooks'][0]['command']


def _read(path):
    """A copy as it stands, or nothing if there is none yet."""
    if not path.is_file():
        return {}, None
    try:
        return json.loads(path.read_text()), None
    except json.JSONDecodeError as error:
        return {}, f'is not valid JSON ({error})'


def sync(root):
    """Write the harness's entries into every copy, and say which were written."""
    events = load(root)
    written = []
    for client, relative in COPIES.items():
        path = root / relative
        document, unreadable = _read(path)
        require(not unreadable,
                f'{relative} {unreadable}, so sync cannot tell what it must leave alone; '
                'fix the file by hand first')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(merge(document, events, client), indent=2) + '\n')
        written.append(str(relative))
    return written


def drift(root):
    """Copies whose harness entries are not what the source would generate.

    Only the harness's entries, both ways. graphify and repowise ship hooks on
    their own release cycle and a check that reported one would make every
    upgrade a harness failure; an entry that carries the harness invocation and
    comes from no source has had no review, which is the same hole `strays`
    closes for the agent copies.
    """
    problems = []
    source = root / SOURCE
    if not source.is_file():
        return [f'{SOURCE} does not exist, so the hook copies have no source']
    events = load(root)
    for client, relative in COPIES.items():
        path = root / relative
        if not path.is_file():
            problems.append(f'{relative} is missing; run {INVOCATION} sync')
            continue
        document, unreadable = _read(path)
        if unreadable:
            problems.append(f'{relative} {unreadable}, so nothing can tell whether it carries the '
                            f'harness hooks; {FIX}')
            continue
        expected, found = groups(events, client), owned(document)
        for event in sorted(set(expected) | set(found)):
            want = Counter(_pin(group) for group in expected.get(event, []))
            have = Counter(_pin(group) for group in found.get(event, []))
            if want == have:
                continue
            for pinned in want - have:
                problems.append(f'{relative} does not carry the {event} hook {SOURCE} names '
                                f'({_command_in(pinned)}); {FIX}')
            for pinned in have - want:
                problems.append(f'{relative} carries a harness {event} hook that {SOURCE} does '
                                f'not name ({_command_in(pinned)}); {FIX}')
    return problems


def dispatch_name(event):
    """SessionStart as the dispatcher and the generated commands spell it.

    Derived rather than tabulated, so an event added to the source needs no
    second list here to be added to as well.
    """
    return re.sub(r'(?<!^)(?=[A-Z])', '-', event).lower()


def event_name(dispatch):
    """The inverse: session-start as the payload and the envelope spell it."""
    return ''.join(part.capitalize() for part in dispatch.split('-'))


def _context(dispatch, text):
    """The one envelope that injects, which is two of the six events.

    hookSpecificOutput rather than plain text on stdout: Claude Code accepts
    both on SessionStart and UserPromptSubmit and Codex's schema accepts only
    this, so the JSON form is the one that is right on both sides.
    """
    return dict(hookSpecificOutput=dict(hookEventName=event_name(dispatch),
                                        additionalContext=text))


def _block(reason):
    """A refusal on an event whose schema has no permission decision.

    Stop and SubagentStop take `decision` and `reason`, and the reason is what
    reaches the model. PreToolUse is the one refusal that does not come through
    here: exit 2 is the contract both assistants read for an edit.
    """
    return dict(decision='block', reason=reason)


def _say(message):
    """A line for the person at the keyboard, which no schema turns into context."""
    return dict(systemMessage=message)


def _ticket_in_hand(repository):
    """The ticket the branch names and its journal, or an absence.

    The resolution `harness guard` already does, and for its reason: a hook
    payload names no ticket, and the branch is the one thing a session and a
    journal are both bound to.
    """
    from . import journal
    from .cli import BRANCH
    from .paths import HISTORY
    branch = repository.branch_or_none()
    match = BRANCH.match(branch or '')
    if match is None:
        return None, []
    return match.group('ticket'), journal.read(repository.root / HISTORY / match.group('ticket'))


def _session_start(repository, rules, payload, client):
    """The brief `status --brief` builds, injected before the session reads on.

    The payload's `source` is not read: the matcher in the source already says
    which starts this runs on, and a hook that re-decided that would be a second
    place to keep in step with the first.
    """
    del payload, client
    from . import cli, journal
    ticket, records = _ticket_in_hand(repository)
    if not records:
        return {}
    answer = cli.brief(repository, ticket, records, journal.state(records), rules)
    return _context('session-start', answer['pack'])


def _user_prompt_submit(repository, rules, payload, client):
    """The budget command's figures, and only once they say something.

    Nothing under budget: a hook that speaks on every turn is a hook people turn
    off, and then it is no longer a control. Nothing either when the spending
    cannot be read, because null is not zero and a machine whose logs are
    elsewhere is not a session over budget.
    """
    del payload, client
    from . import cli
    ticket, _ = _ticket_in_hand(repository)
    figures = cli.budget(repository, ticket, rules)
    if not figures.get('over'):
        return {}
    return _context('user-prompt-submit',
                    f'Session budget: {figures["output_tokens"]} output tokens spent against a '
                    f'budget of {figures["budget"]}. {figures["next_stop"]}')


# Where a path can be in a payload, and where a patch can be. The first three are
# keys either assistant puts a path in directly; the patch shapes are how Codex's
# apply_patch arrives, which its own schema leaves opaque.
PATH_KEYS = ('file_path', 'notebook_path', 'path')
PATCH_HEADERS = ('*** Add File: ', '*** Update File: ', '*** Delete File: ', '*** Move to: ')


def _patched(text):
    """Every file one apply_patch patch touches, by its own grammar."""
    return [line[len(header):].strip()
            for line in text.splitlines()
            for header in PATCH_HEADERS
            if line.startswith(header)]


def paths_in(payload):
    """Every path one PreToolUse payload is about, whichever assistant sent it.

    An empty answer allows the edit. That is deliberate: a shape nobody
    anticipated is a guard that missed one edit, and the alternative is a session
    that cannot write anything the moment either assistant renames a field.
    """
    tool_input = payload.get('tool_input')
    if not isinstance(tool_input, dict):
        return []
    found = [tool_input[key] for key in PATH_KEYS
             if isinstance(tool_input.get(key), str) and tool_input[key]]
    texts = [tool_input.get('input')]
    if isinstance(tool_input.get('command'), list):
        texts += tool_input['command']
    for text in texts:
        if isinstance(text, str) and text.startswith('*** Begin Patch'):
            found += _patched(text)
    return found


def _pre_tool_use(repository, rules, payload, client):
    """guard.decide, on every path the payload names, refusing with exit 2.

    An allowance is an empty envelope rather than a permissionDecision of allow.
    Saying allow would bypass the permission rules the person set, which is a
    wider answer than this guard was ever asked for.
    """
    del client
    from . import guard
    from .cli import GuardRefusal
    branch = repository.branch_or_none()
    _, records = _ticket_in_hand(repository)
    for path in paths_in(payload):
        decision = guard.decide(repository.root, records, branch, path, rules)
        if not decision['allowed']:
            raise GuardRefusal(decision['reason'])
    return {}


def _pre_compact(repository, rules, payload, client):
    """The handoff pack, written before the context that holds it is summarised.

    It never raises and never blocks. A hook that fails compaction loses the
    context it exists to protect, so every refusal below becomes a line a person
    can read instead of a compaction that did not happen. The broad except is
    that guarantee: what could go wrong here is a journal mid-write, a branch
    that is not the ticket's or a pack over its limit, and none of them is worth
    a lost context.
    """
    del rules, payload
    from . import cli
    try:
        ticket, _ = _ticket_in_hand(repository)
        if ticket is None:
            return {}
        answer = cli.execute(cli.parse(['--root', str(repository.root), 'handoff', ticket,
                                        '--actor', f'{client}:implementer', '--auto']))
    except Exception as error:                            # noqa: BLE001 - see the docstring
        return _say(f'The handoff pack was not written before this compaction: {error}')
    if not answer.get('written'):
        return _say(f'No handoff pack was written before this compaction: {answer["reason"]}')
    return _say(f'Handoff pack written to {answer["pack"]} as record {answer["record"]}; a fresh '
                'session starts from it rather than from this compacted context.')


def _agent_that_stopped(payload):
    """Which agent the payload says stopped, or nothing.

    From the payload rather than from a matcher, because the matcher on this
    event is not documented as matching an agent name. Three keys because only
    Codex's schema, which requires agent_type, could be read from this machine;
    on the Claude Code side the key is what a live session settles, and an
    answer of nothing means the hook says nothing at all.
    """
    for key in ('agent_type', 'subagent_type', 'agent_name'):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ''


def review_in(text):
    """The review record inside an answer that is also prose.

    The reviewer writes JSON inside a fence with a sentence either side, so the
    object is looked for rather than assumed to be the whole message: the first
    one that parses and carries a verdict or findings is it.
    """
    decoder = json.JSONDecoder()
    for position, character in enumerate(text):
        if character != '{':
            continue
        try:
            found, _ = decoder.raw_decode(text[position:])
        except ValueError:
            continue
        if isinstance(found, dict) and ('findings' in found or 'verdict' in found):
            return found
    return None


def _check_review(record, rules):
    """The findings, against the rule the review gate will apply to them.

    gates.check_findings and nothing of its own, with resolved off: the
    reviewer's findings are open by definition, and it is the session that asked
    for the review that resolves them.
    """
    from . import gates
    require(isinstance(record.get('findings'), list),
            'A review record carries findings as a JSON array, empty when there are none')
    gates.check_findings(record['findings'], rules['review']['severities'], resolved=False)
    require(record.get('verdict') in ('pass', 'return'),
            f'A review verdict is pass or return, not {record.get("verdict")!r}')


def _draft_review(repository, ticket, record):
    """The record written where `harness draft` writes one, never over another.

    A second reviewer's answer must not replace the first's, and a draft a
    session edited by hand is not a hook's to overwrite, so the name moves
    rather than the file.
    """
    directory = repository.root / DRAFTS
    directory.mkdir(parents=True, exist_ok=True)
    name, number = f'{ticket}-review.json', 1
    while (directory / name).exists():
        number += 1
        name = f'{ticket}-review-{number}.json'
    (directory / name).write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
    return str(Path(DRAFTS) / name)


def _subagent_stop(repository, rules, payload, client):
    """The reviewer's findings, validated where they are cheapest to fix.

    Blocking here costs the reviewer one more answer; the same finding reaching
    `advance` costs a round trip through a session that has to spawn it again.
    `stop_hook_active` is the loop guard both payloads carry: a second refusal on
    the same answer would be a subagent that can never stop.
    """
    del client
    from . import agents
    if _agent_that_stopped(payload) != agents.REVIEWER['name']:
        return {}
    if payload.get('stop_hook_active'):
        return {}
    ticket, records = _ticket_in_hand(repository)
    if not records:
        return {}
    found = review_in(payload.get('last_assistant_message') or '')
    if found is None:
        return _block('This review carries no JSON review record. Return the shape '
                      'harness/agents/seen-reviewer.md names, findings and verdict included, so '
                      'the session that spawned you can pass it to harness advance.')
    try:
        _check_review(found, rules)
    except HarnessError as error:
        return _block(f'The review gate would refuse these findings: {error}. Fix them and '
                      'answer again; a finding it refuses costs a whole review round.')
    drafted = _draft_review(repository, ticket, found)
    return _say(f'{agents.REVIEWER["name"]} returned {len(found["findings"])} finding(s), verdict '
                f'{found["verdict"]}; drafted as {drafted}')


# How much of a failing self-check goes in the reason. Enough to act on, and not
# a whole report in a field the model reads as an instruction.
STOP_PROBLEMS = 10


def _stop(repository, rules, payload, client):
    """The quick self-check, blocking once when it finds something.

    Once, because a problem printed into a transcript nobody reads is not a
    check and a hook that blocked every time would never let the turn end. The
    quick set is the sections that read the journal and the generated copies:
    the two that read every tracked file have no business running at the end of
    every turn.
    """
    del client
    from . import doctor
    if payload.get('stop_hook_active'):
        return {}
    found = doctor.report(repository, rules, quick=True)
    if found['ok']:
        return {}
    problems = found['problems'][:STOP_PROBLEMS]
    left = len(found['problems']) - len(problems)
    return _block('The harness self-check found problems before this turn ended:\n  '
                  + '\n  '.join(problems)
                  + (f'\n  and {left} more' if left > 0 else '')
                  + f'\nFix them, or run {INVOCATION} doctor to see the whole check.')


# One handler per event the source names, keyed as the generated commands spell
# it. A test holds the two to each other, because an event in the source with no
# handler here is a hook that exits 2 on every payload, and on PreToolUse exit 2
# is how both assistants spell deny.
HANDLERS = {
    'session-start': _session_start,
    'user-prompt-submit': _user_prompt_submit,
    'pre-tool-use': _pre_tool_use,
    'pre-compact': _pre_compact,
    'subagent-stop': _subagent_stop,
    'stop': _stop,
}


def respond(repository, rules, event, payload, client):
    """One event's envelope, from what the underlying command answered."""
    require(client in COPIES,
            f'{client} is not a client this harness generates hooks for, and the clients are '
            + ', '.join(COPIES))
    require(event in HANDLERS,
            f'{event} is not an event this harness answers, and they are '
            + ', '.join(sorted(HANDLERS)))
    require(isinstance(payload, dict), f'A {event} payload is a JSON object')
    return HANDLERS[event](repository, rules, payload, client)
