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
"""

from collections import Counter
import json

from .errors import HarnessError, require
from .paths import CLAUDE_SETTINGS, CODEX_HOOKS, HOOK_SOURCE

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
