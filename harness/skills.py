"""One maintained skill, and the copies each assistant reads.

The copies are generated, never edited. Two files that must agree and are edited
separately will not agree, and the one that is wrong is the one somebody read.
"""

from pathlib import Path

SOURCE = Path('docs/harness/skill.md')

# Committed, versioned, and checked by doctor.
COMMITTED = (
    Path('.claude/skills/seen-harness/SKILL.md'),
    Path('.agents/skills/seen-harness/SKILL.md'),
)

# Where Codex actually reads a skill: outside any repository, so it cannot be
# committed or checked. sync rewrites it whenever it runs, and never creates the
# directory: a repository command does not install things on a machine that has
# not asked.
CODEX_HOME = Path.home() / '.codex' / 'skills' / 'seen-harness' / 'SKILL.md'

NAME = 'seen-harness'
DESCRIPTION = (
    'The procedure every Seen ticket goes through: clarify, solution, tdd, review, deliver, '
    'with the evidence recorded as it happens. Use when starting, resuming, reviewing or '
    'delivering any SEEN ticket, or when asked how the harness works.'
)
HEADER = """---
name: {name}
description: >
  {description}
---

<!-- Generated from {source} by `python3 harness/run.py sync`. Do not edit this
     file: `doctor` compares it against the source and refuses when they differ. -->

"""


def render(body):
    """One copy: the frontmatter an assistant reads, then the maintained body."""
    return HEADER.format(name=NAME, description=DESCRIPTION, source=SOURCE) + body


def sync(root):
    """Write every copy from the source, and say which were written."""
    from .errors import require
    source = root / SOURCE
    require(source.is_file(),
            f'{SOURCE} does not exist, so there is no skill to sync')
    rendered = render(source.read_text())
    written = []
    for relative in COMMITTED:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered)
        written.append(str(relative))
    if CODEX_HOME.parent.parent.is_dir():
        CODEX_HOME.parent.mkdir(parents=True, exist_ok=True)
        CODEX_HOME.write_text(rendered)
        written.append(str(CODEX_HOME))
    return dict(source=str(SOURCE), written=written)


def drift(root):
    """Committed copies that do not match what the source would generate."""
    source = root / SOURCE
    if not source.is_file():
        return [f'{SOURCE} does not exist, so the skill copies have no source']
    rendered = render(source.read_text())
    problems = []
    for relative in COMMITTED:
        path = root / relative
        if not path.is_file():
            problems.append(f'{relative} is missing; run python3 harness/run.py sync')
        elif path.read_text() != rendered:
            problems.append(f'{relative} differs from {SOURCE}; it is generated, so edit the '
                            'source and run python3 harness/run.py sync')
    return problems
