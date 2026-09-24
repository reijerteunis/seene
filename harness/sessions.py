"""Which session wrote a record, and what that session has spent.

A session id names one context window. The KPI needs to tell one from another,
not to know what either is called, so a record carries twelve hex characters of
its sha256 and never the id itself. That is not only good manners:
`secrets.SECRET_NAME` matches SESSION, so `journal.append` already refuses any
record carrying the value of a variable named like that, correctly, and this
module is how a session is counted without breaking that refusal.
"""

import hashlib
import os

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
