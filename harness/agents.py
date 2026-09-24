"""Two agents with a context of their own, and the copies each assistant reads.

A session fills up with two kinds of reading: the research at clarify and
solution, and the review, which has to hold the diff, the journal and the
criteria at once. Both move out into an agent with a context window of its own
that returns a bounded answer. A subagent is a context boundary and nothing more:
it is not independence by itself, which is why the review by the other assistant
stays required where a missed defect costs money.

The structure lives here and the prose lives in harness/agents/<name>.md, the way
harness/skills.py holds the skill's frontmatter and docs/harness/skill.md holds
its body. Two unlike targets are rendered from one source: Claude Code reads
markdown with camel-case frontmatter, Codex reads TOML. The standard library has
no YAML parser and the harness takes no dependency, so a source file carrying its
own frontmatter would need a hand-rolled parser for five keys; keeping structure
in code is what avoids it.

Neither agent holds Edit or Write. The scout has no Bash at all, because
everything it needs is a graph query; the reviewer has it for `git diff`, and its
instructions and Codex's read-only sandbox are what keep it to reading.
"""

from pathlib import Path

SOURCES = Path('harness/agents')
CLAUDE_DIRECTORY = Path('.claude/agents')
CODEX_DIRECTORY = Path('.codex/agents')

# The scout answers one scoped question from the graphs and stops. omitClaudeMd
# is true for it on purpose: it is given the question and the three graph tools,
# and the ticket index in CLAUDE.md is the kind of reading this ticket exists to
# keep out of a context.
SCOUT = dict(
    name='seen-scout',
    description=('Research one scoped question about this repository from the knowledge graphs '
                 'and return a brief of at most 400 words. Use at clarify and solution, and '
                 'whenever a question would otherwise be answered by reading files.'),
    tools=('Read, Grep, Glob, mcp__codegraph__codegraph_explore, mcp__graphify__query_graph, '
           'mcp__graphify__shortest_path, mcp__graphify__get_neighbors, '
           'mcp__graphify__get_pr_impact, mcp__repowise__get_answer, mcp__repowise__get_why, '
           'mcp__repowise__get_risk, mcp__repowise__get_health, mcp__repowise__search_codebase'),
    model='sonnet',
    permissionMode='default',
    omitClaudeMd=True,
    sandbox_mode='read-only',
)

# The reviewer reads CLAUDE.md, which is the opposite call and the right one: the
# ground rules it reviews against are in there, and a reviewer that has not read
# them reviews against nothing.
REVIEWER = dict(
    name='seen-reviewer',
    description=('Review a ticket\'s diff against its acceptance criteria and its journal in a '
                 'fresh context, and return findings with a failure scenario each. Use at the '
                 'review stage, never in the session that wrote the code.'),
    tools=('Read, Grep, Glob, Bash, mcp__codegraph__codegraph_explore, mcp__repowise__get_risk, '
           'mcp__repowise__get_why'),
    model='opus',
    permissionMode='default',
    omitClaudeMd=False,
    sandbox_mode='read-only',
)
AGENTS = (SCOUT, REVIEWER)

CLAUDE_KEYS = ('name', 'description', 'tools', 'model', 'permissionMode', 'omitClaudeMd')
CODEX_KEYS = ('name', 'description', 'developer_instructions', 'sandbox_mode', 'model')

GENERATED = ('Generated from {source} by `python3 harness/run.py sync`. Do not edit this '
             'file: `doctor` compares it against the source and refuses when they differ.')


def source_of(agent):
    return SOURCES / f'{agent["name"]}.md'


def claude_copy(agent):
    return CLAUDE_DIRECTORY / f'{agent["name"]}.md'


def codex_copy(agent):
    return CODEX_DIRECTORY / f'{agent["name"]}.toml'


def _folded(text):
    """Long prose as a folded scalar, the form the skill's own frontmatter uses."""
    return '>\n  ' + ' '.join(str(text).split())


def render_claude(agent, body):
    """The markdown copy Claude Code reads, frontmatter first.

    Only the description is folded. A folded scalar carries a trailing newline
    into its value, which is harmless in prose and would be a different agent
    name, so name, model, permissionMode and tools are plain one-line values and
    omitClaudeMd is a bare boolean.
    """
    lines = ['---']
    for key in CLAUDE_KEYS:
        value = agent[key]
        if isinstance(value, bool):
            lines.append(f'{key}: {str(value).lower()}')
        elif key == 'description':
            lines.append(f'{key}: {_folded(value)}')
        else:
            lines.append(f'{key}: {" ".join(str(value).split())}')
    lines.append('---')
    lines.append('')
    lines.append(f'<!-- {GENERATED.format(source=source_of(agent))} -->')
    lines.append('')
    lines.append('')
    return '\n'.join(lines) + body


def _toml_string(text):
    r"""One multi-line basic string, with the two sequences that could end it early."""
    return '"""\n' + text.replace('\\', '\\\\').replace('"""', '\\"\\"\\"') + '"""'


def render_codex(agent, body):
    """The TOML copy Codex reads.

    The keys are the ones SEEN-105 names. No Codex session has ever run on this
    repository, so they are unverified against a Codex release: doctor checks
    that the copy matches its source, not that Codex accepts it, and the first
    Codex session settles it. That is the same position SEEN-104 took on which
    variable a Codex session carries its id in.
    """
    lines = [f'# {GENERATED.format(source=source_of(agent))}',
             '',
             f'name = "{agent["name"]}"',
             f'description = {_toml_string(agent["description"])}',
             f'model = "{agent["model"]}"',
             f'sandbox_mode = "{agent["sandbox_mode"]}"',
             f'developer_instructions = {_toml_string(body)}']
    return '\n'.join(lines) + '\n'


def _body(root, agent):
    from .errors import require
    path = root / source_of(agent)
    require(path.is_file(),
            f'{source_of(agent)} does not exist, so {agent["name"]} has no source to generate from')
    return path.read_text()


def sync(root):
    """Write every copy of every agent from its source, and say which were written."""
    written = []
    for agent in AGENTS:
        body = _body(root, agent)
        for relative, rendered in ((claude_copy(agent), render_claude(agent, body)),
                                   (codex_copy(agent), render_codex(agent, body))):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered)
            written.append(str(relative))
    return written


def drift(root):
    """Copies that do not match what their source would generate."""
    problems = []
    for agent in AGENTS:
        source = root / source_of(agent)
        if not source.is_file():
            problems.append(f'{source_of(agent)} does not exist, so the {agent["name"]} copies '
                            'have no source')
            continue
        body = source.read_text()
        for relative, rendered in ((claude_copy(agent), render_claude(agent, body)),
                                   (codex_copy(agent), render_codex(agent, body))):
            path = root / relative
            if not path.is_file():
                problems.append(f'{relative} is missing; run python3 harness/run.py sync')
            elif path.read_text() != rendered:
                problems.append(f'{relative} differs from {source_of(agent)}; it is generated, so '
                                'edit the source and run python3 harness/run.py sync')
    return problems
