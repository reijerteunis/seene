"""Three agents with a context of their own, and the copies each assistant reads.

A session fills up with three kinds of work: the research at clarify and
solution, the review, which has to hold the diff, the journal and the criteria
at once, and the slice itself. Each moves out into an agent with a context
window of its own that returns a bounded answer. A subagent is a context
boundary and nothing more: it is not independence by itself, which is why the
review by the other assistant stays required where a missed defect costs money.

The structure lives here and the prose lives in harness/agents/<name>.md, the way
harness/skills.py holds the skill's frontmatter and docs/harness/skill.md holds
its body. Two unlike targets are rendered from one source: Claude Code reads
markdown with camel-case frontmatter, Codex reads TOML. The standard library has
no YAML parser and the harness takes no dependency, so a source file carrying its
own frontmatter would need a hand-rolled parser for five keys; keeping structure
in code is what avoids it.

Neither reader holds Edit or Write; the implementer holds both, because writing
the slice is what it is for. No copy depends on anything but its source and
thresholds.toml: a generated file whose content varied with the ticket in hand
was wrong on a detached HEAD, after a replan, the moment a green landed and
after the receipt, which is F1 of this ticket's first review, F4 of its second,
F1 of its seventh and F3 of its eighth. The scout has no Bash at all, because everything it
needs is a graph query. The reviewer holds Bash, because it cannot
read a diff without it, and that is a real hole rather than a closed one: Claude
Code has no read-only Bash, so on that side the reviewer is held to reading by its
instructions and by holding no Edit and no Write, and nothing refuses a write it
makes through a shell. `sandbox_mode` closes it on the Codex side only. Enforcing
it on both is SEEN-106, which puts hooks in front of both assistants. Recorded
here rather than implied, because F9 of this ticket's first review found this
module claiming the sandbox covered it.
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
# The implementer is the one agent whose model is not its own. The scout always
# researches and the reviewer always reviews, so a fixed model is right for
# both; what a slice needs depends on the slice, which is what SEEN-108's route
# decides from the plan. It is also the first agent to hold Edit and Write,
# because writing the slice is what it is for: the controls that hold are the
# ones that already hold for the session, the branch check, the RED before the
# green, the journal, and the fingerprint the review attests.
IMPLEMENTER = dict(
    name='seen-implementer',
    description=('Work one slice of a ticket: the RED first, then the code that turns it green, '
                 'in the context of that slice alone. Spawned on the model the route decided, '
                 'which it never chooses for itself.'),
    tools=('Read, Edit, Write, Grep, Glob, Bash, mcp__codegraph__codegraph_explore, '
           'mcp__repowise__get_why, mcp__repowise__get_risk'),
    # Filled from the route of the slice in hand by `resolved`. Never read from
    # here: a default that could reach a copy would be a slice worked on a model
    # nobody chose.
    model=None,
    effort=None,
    permissionMode='default',
    omitClaudeMd=False,
    sandbox_mode='workspace-write',
)
AGENTS = (SCOUT, REVIEWER, IMPLEMENTER)

# effort is documented by Claude Code as a subagent frontmatter key that
# overrides the session's, and there is no documented way to override it per
# invocation, which is why the implementer's copies are generated per slice.
# An agent that carries no effort takes the session's, which is what leaving the
# key out means, so it is rendered only when the agent has one.
CLAUDE_KEYS = ('name', 'description', 'tools', 'model', 'effort', 'permissionMode',
               'omitClaudeMd')
CODEX_KEYS = ('name', 'description', 'developer_instructions', 'sandbox_mode', 'model',
              'model_reasoning_effort')


def implementer_default(root):
    """The model and effort the implementer's copies carry, which never vary.

    The strongest tier at the highest effort, from thresholds.toml, and not the
    route of whichever slice is in hand. A file whose correct content depends on
    the state of a ticket has no correct content once the ticket is delivered:
    after the receipt no slice was in hand, the generator fell back, `doctor`
    reported drift on the commit being merged and `verify-merge` refused, and
    the copies could not be re-synced without changing a tree the receipt
    attests. It was wrong on a detached HEAD, wrong after a replan, wrong the
    moment a green landed and wrong after delivery: four findings across four
    reviews, one design. F3 of the eighth review, decided at record 121.

    The routed model reaches the implementer through the per-invocation override
    the route record's spawn instruction names, and the routed effort through
    the Codex agent TOML; criterion 3 is amended to say what that does and does
    not give on each side.
    """
    from . import routing, thresholds
    rules = thresholds.load(root)
    return routing.strongest(rules), routing.rule_effort(rules)


def resolved(root):
    """Every agent as this repository defines it, from its source and one table."""
    model, effort = implementer_default(root)
    return tuple(dict(agent, model=model, effort=effort) if agent['name'] == IMPLEMENTER['name']
                 else agent
                 for agent in AGENTS)


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
        value = agent.get(key)
        if value is None:
            continue
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
             f'model = "{agent["model"]}"']
    if agent.get('effort') is not None:
        lines.append(f'model_reasoning_effort = "{agent["effort"]}"')
    lines += [f'sandbox_mode = "{agent["sandbox_mode"]}"',
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
    for agent in resolved(root):
        body = _body(root, agent)
        for relative, rendered in ((claude_copy(agent), render_claude(agent, body)),
                                   (codex_copy(agent), render_codex(agent, body))):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered)
            written.append(str(relative))
    return written


def strays(root):
    """Agent files in the directories sync owns that no source generates.

    F10 in SEEN-105's first review: drift walked the two agents rather than the
    directories, so a .claude/agents/seen-implementer.md holding Edit and Write
    was invisible to doctor and, since .codex/agents/ is no longer ignored,
    committable. An agent with no source under harness/agents/ has had no review.
    """
    generated = ({claude_copy(agent) for agent in AGENTS}
                 | {codex_copy(agent) for agent in AGENTS})
    # Only a file claiming to be one of ours. .claude/agents/ is where a person
    # keeps their own agents, and G7 of SEEN-105's second review found this failing
    # doctor and CI on every ticket for a debugger somebody saved there.
    ours = 'seen-'
    found = []
    for directory, suffix in ((CLAUDE_DIRECTORY, '.md'), (CODEX_DIRECTORY, '.toml')):
        path = root / directory
        if not path.is_dir():
            continue
        for entry in sorted(path.glob(f'*{suffix}')):
            relative = directory / entry.name
            if relative not in generated and entry.stem.startswith(ours):
                found.append(f'{relative} is named like one of this harness\'s agents and is not '
                             f'generated from {SOURCES}/, so nothing reviews '
                             'what it tells an agent to do; remove it, or add its source and run '
                             'python3 harness/run.py sync')
    return found


def drift(root):
    """Copies that do not match what their source would generate."""
    problems = []
    for agent in resolved(root):
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
    return problems + strays(root)
