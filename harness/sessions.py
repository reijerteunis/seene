"""Which session wrote a record, and what that session has spent.

A session id names one context window. The KPI needs to tell one from another,
not to know what either is called, so a record carries twelve hex characters of
its sha256 and never the id itself. That is not only good manners:
`secrets.SECRET_NAME` matches SESSION, so `journal.append` already refuses any
record carrying the value of a variable named like that, correctly, and this
module is how a session is counted without breaking that refusal.
"""

import hashlib
import json
import os

from . import cost

# Most specific first. Claude Code sets the first one. Which variable a Codex
# session exposes its id in is not known from this machine and cannot be read
# here, so the list is ordered and short, null is recorded until one of them is
# set, and the first Codex session on this repository settles it. Null is an
# absence; 1 would be a claim that a ticket was worked in one session, which is
# the claim this whole ticket exists because nobody could make.
SESSION_VARIABLES = ('CLAUDE_CODE_SESSION_ID',)
DIGEST_LENGTH = 12


def digest(identifier):
    """Twelve hex characters of the sha256 of a session id, or nothing.

    Twelve because sixty-four characters of noise in every record buys nothing
    at this scale: the question a record answers is whether two records came
    from the same session, and twelve settles that for every ticket this
    repository will ever hold.
    """
    if not identifier:
        return None
    return hashlib.sha256(identifier.encode()).hexdigest()[:DIGEST_LENGTH]


def identifier(environ=None):
    """The raw session id, for the commands that must find its log file."""
    environ = os.environ if environ is None else environ
    for name in SESSION_VARIABLES:
        value = (environ.get(name) or '').strip()
        if value:
            return value
    return None


def current(environ=None):
    """The session this command is running in, as a digest or an absence."""
    return digest(identifier(environ))


def log(root, identity=None):
    """This session's own log file, by the naming Claude Code uses.

    One file rather than the whole directory: the cost KPI reads every session in
    a ticket's window, and this reads the session asking the question.
    """
    identity = identifier() if identity is None else identity
    if not identity:
        return None
    path = cost.log_directory(root) / f'{identity}.jsonl'
    return path if path.is_file() else None


def model(root, identity=None):
    """The model this session is running on, from its own log, or nothing.

    Read when a check is recorded rather than derived later, because a record
    carries the digest of its session and not the id, so no later reader can
    find the log of the session that wrote one. The last entry wins: it is the
    model in effect when the command ran, and a session whose model changed
    halfway is a session whose later work is what a check is evidence of.

    Null when there is no log, and null is never compared against: a machine
    whose logs are elsewhere must not have its checks refused for it.
    """
    path = log(root, identity)
    if path is None:
        return None
    found = None
    for line in path.read_text(errors='replace').splitlines():
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        name = (entry.get('message') or {}).get('model')
        # Claude Code writes `<synthetic>` on an entry it generated itself,
        # which is not a model anybody routed a slice to.
        if name and not name.startswith('<'):
            found = name
    return found


def figures(root, identity=None):
    """Output tokens and tool calls this session has spent, or that nobody knows.

    Null rather than zero when there is no log, which is the rule cost.py already
    applies: zero is a claim that nothing was spent, and the honest answer on a
    machine whose logs are elsewhere is that nobody knows. Only two numbers are
    read; a session log holds prompts and file contents, none of which belongs in
    a journal.
    """
    identity = identifier() if identity is None else identity
    path = log(root, identity)
    answer = dict(session=digest(identity), output_tokens=None, tool_calls=None,
                  unavailable=None)
    if path is None:
        answer['unavailable'] = ('No session log for this session, so its spending cannot be '
                                 'read; null is not zero')
        return answer
    output, calls = 0, 0
    for line in path.read_text(errors='replace').splitlines():
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        message = entry.get('message') or {}
        usage = message.get('usage') or {}
        output += usage.get('output_tokens', 0) or 0
        content = message.get('content')
        if isinstance(content, list):
            calls += sum(1 for block in content
                         if isinstance(block, dict) and block.get('type') == 'tool_use')
    return dict(answer, output_tokens=output, tool_calls=calls)


def subagent_figures(root, identity=None):
    """Each subagent's own spending, apart from the parent that spawned it.

    A Claude Code subagent inherits its parent's session id (settled in
    SEEN-111's clarify record from a real log), so nothing in the parent's own
    log tells a subagent's spending from its own: it writes a subagent's
    transcript to `<session>/subagents/agent-*.jsonl` beside the parent's, and
    that directory is the only place the split exists to read. One entry per
    file found there, named from the `.meta.json` Claude Code writes beside
    it, which is the only place that says what kind of agent it was.

    Null rather than zero when the directory does not exist, the rule cost.py
    already applies to a session with no log at all: an absence and a low
    figure must not read the same.
    """
    identity = identifier() if identity is None else identity
    answer = dict(agents=None, output_tokens=None, tool_calls=None, unavailable=None)
    if not identity:
        return dict(answer, unavailable='No session to look for subagents beside, so their '
                                        'spending cannot be read; null is not zero')
    directory = cost.log_directory(root) / identity / 'subagents'
    if not directory.is_dir():
        return dict(answer, unavailable='No subagents directory for this session, so their '
                                        'spending cannot be read; null is not zero')
    agents = []
    total_output, total_calls = 0, 0
    for path in sorted(directory.glob('agent-*.jsonl')):
        output, calls, model = 0, 0, None
        for line in path.read_text(errors='replace').splitlines():
            try:
                entry = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            message = entry.get('message') or {}
            usage = message.get('usage') or {}
            output += usage.get('output_tokens', 0) or 0
            content = message.get('content')
            if isinstance(content, list):
                calls += sum(1 for block in content
                             if isinstance(block, dict) and block.get('type') == 'tool_use')
            name = message.get('model')
            # Claude Code writes `<synthetic>` on an entry it generated itself,
            # the same convention `model()` above already reads.
            if name and not name.startswith('<'):
                model = name
        meta = path.with_suffix('.meta.json')
        agent_type = None
        if meta.is_file():
            try:
                agent_type = json.loads(meta.read_text()).get('agentType')
            except (json.JSONDecodeError, ValueError):
                agent_type = None
        agents.append(dict(agent=agent_type, agent_id=path.stem, output_tokens=output,
                           tool_calls=calls, model=model))
        total_output += output
        total_calls += calls
    return dict(agents=agents, output_tokens=total_output, tool_calls=total_calls,
               unavailable=None)


def against_budget(spent, limit, subagents=None):
    """This session's spending set beside the budget for one slice.

    It reports and refuses nothing. Only the person at the keyboard can end a
    session, so the honest thing a command can do is say where the session
    stands and name the stop, which is the slice boundary and not the ticket.

    `subagents` is carried through rather than folded into `output_tokens`,
    because it is a different session's spending told apart from this one's,
    read separately by `subagent_figures`; folding it in would make a
    delegated slice's cost count twice against a budget that is this
    session's own.
    """
    answer = dict(spent, budget=limit, over=None, remaining=None, next_stop=None,
                  subagents=subagents)
    if spent.get('output_tokens') is None:
        return answer
    over = spent['output_tokens'] > limit
    return dict(answer,
                over=over,
                remaining=max(limit - spent['output_tokens'], 0),
                next_stop=('Over budget: the next stop is the slice boundary. Finish the slice '
                           'in hand, run harness handoff <ticket> and start a fresh session from '
                           'the pack. A fresh context is cheaper than a compacted one.')
                if over else None)
