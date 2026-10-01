"""The rule set that runs before a model reads anything, and its one registry.

SEEN-114. Sprint 0 delivered 63 review findings on 20 tickets. A finding a static
rule could have caught is paid for three times: the reviewer's reading, the
return, the second review. The rules that stop that live where each tool looks
for them, which is four files at the repository root plus the compiler's own
flags, and that is four places a rule can appear with nothing behind it.

So `rules/registry.toml` is the one place a rule's citation lives, and this module
is what makes an entry there more than prose. `problems` cross-checks the registry
against the configurations in both directions: a rule a tool enables and the
registry does not carry is reported, and so is a registry entry for a rule no
configuration enables. Padding the registry is as loud as writing an untraceable
rule, which is the point, because a registry that only had to be a superset would
be a list nobody read.

`fixture_results` proves each rule by running its own tool against a fixture the
rule must refuse. The fixture is copied into a tree laid out like the repository
rather than scanned where it lies: a rule scoped to `packages/core/**` says
nothing about a file in `rules/fixtures/`, and a rule proven against a rewritten
glob is not the rule that runs in anger.

What this module never does is run the rule set over real code. That is
`scripts/rules.sh`, which the pre-commit hook and CI both call, because SEEN-097
recorded what happens when the same environment has two definitions.
"""

import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib

# Every field a registry entry carries, and the reader's question each answers:
# which rule, which tool runs it, what it stands on, what proves it, and what it
# is for. All five are required, because an entry missing any one of them is an
# entry somebody would have to go and ask about.
ENTRY_KEYS = ('id', 'tool', 'citation', 'fixture', 'reason')

REGISTRY = Path('rules') / 'registry.toml'

# The tools the registry may name. A tool with a configuration file is
# cross-checked against it; a tool with None has no file this module can read,
# and its entry is held to its citation and its fixture like any other. gitleaks
# and the harness's own checks are in the set because they run in the same hook,
# and a registry that left them out would not be a map of what runs.
CONFIG_FOR_TOOL = {
    'tsconfig': 'tsconfig.base.json',
    'biome': 'biome.json',
    'ast-grep': 'sgconfig.yml',
    'dependency-cruiser': '.dependency-cruiser.json',
    'knip': 'knip.json',
    'gitleaks': None,
    'harness': None,
}

# The compiler options that are rules rather than build settings: tsc refuses
# code because of these, and emits differently because of the rest. Only the ones
# a configuration turns on need an entry, so this list is read rather than
# enforced. Named here rather than derived, because `target` and
# `noUncheckedIndexedAccess` are both booleans-or-strings in one object and
# nothing in the file says which of them is a reviewer.
TSCONFIG_RULE_FLAGS = (
    'allowUnreachableCode', 'allowUnusedLabels', 'alwaysStrict', 'erasableSyntaxOnly',
    'exactOptionalPropertyTypes', 'isolatedModules', 'noFallthroughCasesInSwitch',
    'noImplicitAny', 'noImplicitOverride', 'noImplicitReturns', 'noImplicitThis',
    'noPropertyAccessFromIndexSignature', 'noUncheckedIndexedAccess', 'noUncheckedSideEffectImports',
    'noUnusedLocals', 'noUnusedParameters', 'strict', 'strictBindCallApply',
    'strictFunctionTypes', 'strictNullChecks', 'strictPropertyInitialization',
    'useUnknownInCatchVariables', 'verbatimModuleSyntax',
)

# A citation has to be something a reader can open: the finding a rule came from,
# or the document that states it. A ticket id on its own is neither, which is the
# case worth being strict about: every rule is added by some ticket, so a bare
# ticket id would let a rule cite the act of writing it and nothing else, and the
# criterion this implements asks for a finding id or an architecture section. So a
# ticket must carry the finding inside it, in the shapes this repository's
# journals actually use (F1, R-05, CODEX-03), or the citation names a path that is
# in the tree.
FINDING = re.compile(r'\bSEEN-\d{3}\s+[A-Z]+-?\d+\b')
DOCUMENT = re.compile(r'\b[\w./-]+\.(?:md|toml|json|ts|tsx|yml|yaml|sql|sh)\b')

# ast-grep's format allows several rule documents in one file. Nothing here
# parses YAML, so a second id in a file is either read by accident or not read at
# all; the shape is refused instead of guessed at.
AST_GREP_ID = re.compile(r'^id:\s*(\S+)\s*$', re.MULTILINE)
RULE_DIRS = re.compile(r'^ruleDirs:\s*$(.*?)(?=^\S|\Z)', re.MULTILINE | re.DOTALL)
RULE_DIR_ENTRY = re.compile(r'^\s*-\s*(\S+)\s*$', re.MULTILINE)

# Where each tool's binary is, relative to the repository root. The workspace
# install puts all four here, and resolving them by path rather than by PATH is
# what keeps a fixture run honest: the tool that proves the rule is the tool the
# hook runs, at the version the lockfile pins.
BINARY_FOR_TOOL = {
    'tsconfig': 'node_modules/.bin/tsc',
    'biome': 'node_modules/.bin/biome',
    'ast-grep': 'node_modules/.bin/ast-grep',
    'dependency-cruiser': 'node_modules/.bin/depcruise',
    'knip': 'node_modules/.bin/knip',
}

# Everything a fixture tree needs beside the fixture itself: the configurations
# the tools read, copied so that the run is against the real rules, and the
# workspace manifests a resolver needs to answer what `@seen/core` is.
#
# `rules/ast-grep` is a directory rather than a file and is here for the same
# reason the configurations are. sgconfig.yml names its `ruleDirs` relative to
# itself, so copying the configuration without the directory it points at leaves
# ast-grep scanning the fixture with no rule loaded, and the fixture then passes
# for the one reason a fixture must never pass for.
FIXTURE_SUPPORT = ('biome.json', 'sgconfig.yml', '.dependency-cruiser.json', 'knip.json',
                   'tsconfig.base.json', 'package.json', 'pnpm-workspace.yaml',
                   'rules/ast-grep')


def load(root):
    """Every rule in the registry, in the order the file writes them."""
    path = Path(root) / REGISTRY
    if not path.is_file():
        return []
    return tomllib.loads(path.read_text()).get('rule') or []


def arrival_dates(root):
    """When each rule in the registry first appeared there, read from git.

    SEEN-114's weekly report needs to say which rules were added this week
    (criterion 4), and the honest place to date an entry would be a sixth
    field beside `ENTRY_KEYS`. That field is not here: `rules/registry.toml`
    is not a file this slice's own plan names, `harness guard` refuses an
    edit to it from here, and a field nine existing entries would need to be
    missing on day one is not a field this slice can add responsibly. Git
    already carries the answer without asking the registry for anything new:
    the first commit whose diff of this file introduces the id's own line is
    when the rule arrived, and `git log -S` (the "pickaxe") finds exactly
    that commit, `--follow` carrying it across a rename of the file itself.

    An id with no such commit, because the registry is not inside a git
    repository, or because the line was never actually committed, is simply
    left out of the answer. That is the same absence `configured` and
    `fixture_results` already report elsewhere in this module as what it is,
    rather than guessed at: a rule dated nothing rather than dated today.
    """
    root = Path(root)
    found = {}
    for entry in load(root):
        identifier = entry.get('id')
        if not identifier or identifier in found:
            continue
        result = subprocess.run(
            ['git', 'log', '--follow', '--format=%cI', '--reverse', '-S',
             f'id = "{identifier}"', '--', str(REGISTRY)],
            cwd=str(root), capture_output=True, text=True, check=False)
        if result.returncode != 0:
            continue
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        if lines:
            found[identifier] = lines[0]
    return found


def _tsconfig_rules(root):
    """The compiler's checking flags this repository turns on."""
    path = Path(root) / CONFIG_FOR_TOOL['tsconfig']
    options = json.loads(path.read_text()).get('compilerOptions') or {}
    return {f'tsconfig/{flag}': str(path.name)
            for flag in TSCONFIG_RULE_FLAGS if options.get(flag) is True}


def _biome_rules(root):
    """The lint rules biome.json names, and the preset when one is chosen.

    A preset is one entry rather than three hundred: it is one decision, taken
    once, and it is citable as one. Three hundred entries for rules nobody chose
    one by one would be a registry a reader skims, which is the one thing it
    cannot be. A rule named explicitly beside the preset is a second decision
    and carries its own entry. `recommended: true` is read as well as `preset`,
    because 2.5 deprecates the first in favour of the second and a reader of an
    older configuration should still get an answer rather than silence.
    """
    path = Path(root) / CONFIG_FOR_TOOL['biome']
    configured = (json.loads(path.read_text()).get('linter') or {}).get('rules') or {}
    found = {}
    preset = configured.get('preset')
    if preset and preset != 'none':
        found[f'biome/{preset}'] = f'{path.name} (preset)'
    elif configured.get('recommended') is True:
        found['biome/recommended'] = path.name
    for group, value in configured.items():
        if not isinstance(value, dict):
            continue
        for name, severity in value.items():
            if name in ('recommended', 'preset') or severity == 'off':
                continue
            found[f'biome/{name}'] = f'{path.name} ({group})'
    return found


def _ast_grep_rules(root):
    """One id per rule file, with a file carrying two reported rather than read."""
    root = Path(root)
    path = root / CONFIG_FOR_TOOL['ast-grep']
    block = RULE_DIRS.search(path.read_text())
    directories = RULE_DIR_ENTRY.findall(block.group(1)) if block else []
    found, broken = {}, []
    for directory in directories:
        for rule_file in sorted((root / directory).glob('*.yml')):
            identifiers = AST_GREP_ID.findall(rule_file.read_text())
            if len(identifiers) != 1:
                broken.append(f'{rule_file.relative_to(root)} carries {len(identifiers)} rule '
                              'ids and a rule file carries exactly one, so that reading the ids '
                              'is reading the files')
                continue
            found[f'ast-grep/{identifiers[0]}'] = str(rule_file.relative_to(root))
    return found, broken


def _dependency_cruiser_rules(root):
    """Every named rule in the layering configuration.

    `allowed` is one rule however many clauses it has, which is how
    dependency-cruiser reports it: `not-in-allowed`. It is registered under that
    name so the entry matches what a violation says.
    """
    path = Path(root) / CONFIG_FOR_TOOL['dependency-cruiser']
    content = json.loads(path.read_text())
    found = {f'dependency-cruiser/{rule["name"]}': path.name
             for rule in content.get('forbidden') or [] if rule.get('name')}
    if content.get('allowed'):
        found['dependency-cruiser/not-in-allowed'] = path.name
    return found


def _knip_rules(root):
    """knip is one rule in this set: an export nothing reads is dead."""
    return {'knip/no-unused-exports': CONFIG_FOR_TOOL['knip']}


READER_FOR_TOOL = {
    'tsconfig': _tsconfig_rules,
    'biome': _biome_rules,
    'dependency-cruiser': _dependency_cruiser_rules,
    'knip': _knip_rules,
}


def configured(root):
    """Every rule the tools' own configurations enable, and what cannot be read.

    Returns the rules by id with where each is written, and the problems that
    stopped a configuration being read at all, because a configuration this
    module cannot parse must not read as a configuration enabling nothing.
    """
    root = Path(root)
    found, broken = {}, []
    for tool, relative in CONFIG_FOR_TOOL.items():
        if relative is None or not (root / relative).exists():
            continue
        try:
            if tool == 'ast-grep':
                rules_found, rules_broken = _ast_grep_rules(root)
                found.update(rules_found)
                broken.extend(rules_broken)
            else:
                found.update(READER_FOR_TOOL[tool](root))
        except (json.JSONDecodeError, tomllib.TOMLDecodeError, OSError, KeyError) as error:
            broken.append(f'{relative} could not be read, so the rules it enables are unknown '
                          f'rather than none: {error}')
    return found, broken


def _citation_problem(root, entry):
    """Whether a citation names something a reader can open."""
    citation = entry.get('citation') or ''
    if FINDING.search(citation):
        return None
    paths = [match.group(0) for match in DOCUMENT.finditer(citation)]
    if not paths:
        return (f'{entry["id"]} has a citation nothing can be read from: {citation!r}. A rule '
                'cites the ticket and the finding inside it, as SEEN-097 F1, or the document and '
                'the section that states it, as docs/architecture.md: Services. A ticket id on '
                'its own is not a citation, because every rule was added by some ticket')
    missing = [name for name in paths if not (Path(root) / name).exists()]
    if missing:
        return (f'{entry["id"]} cites {", ".join(missing)}, which is not in this repository. A '
                'citation is something a reader can open')
    return None


def problems(root):
    """Everything that makes this repository's rule set untraceable.

    Both directions, and the reverse one is the load-bearing half: a rule a tool
    enables that the registry does not carry is a rule with nothing behind it,
    and a registry entry for a rule no tool enables is padding. One check cannot
    be had without the other, because either on its own is satisfied by a list
    that grows in one direction and never shrinks.
    """
    root = Path(root)
    found = load(root)
    enabled, broken = configured(root)
    reported = list(broken)
    if not (root / REGISTRY).is_file():
        if enabled:
            reported.append(f'{REGISTRY} does not exist, and {len(enabled)} rule(s) are enabled '
                            'in this repository. The registry is where a rule\'s citation lives, '
                            'so a rule set without one is a rule set nobody can trace')
        return reported
    carried = {}
    for position, entry in enumerate(found, start=1):
        if not isinstance(entry, dict):
            reported.append(f'Rule {position} in {REGISTRY} is not a table')
            continue
        identifier = entry.get('id') or f'rule {position}'
        for key in ENTRY_KEYS:
            if not str(entry.get(key) or '').strip():
                reported.append(f'{identifier} is missing {key}')
        if not entry.get('id') or not entry.get('tool'):
            continue
        tool = entry['tool']
        if tool not in CONFIG_FOR_TOOL:
            reported.append(f'{entry["id"]} names the tool {tool!r}, which is not one of '
                            f'{", ".join(sorted(CONFIG_FOR_TOOL))}. A rule run by a tool nobody '
                            'declared is a rule nothing runs')
            continue
        if not entry['id'].startswith(f'{tool}/'):
            reported.append(f'{entry["id"]} is run by {tool} and a rule id names its own tool, '
                            f'so this one reads {tool}/{entry["id"]}')
            continue
        carried[entry['id']] = entry
        if entry.get('citation'):
            problem = _citation_problem(root, entry)
            if problem:
                reported.append(problem)
        fixture = entry.get('fixture')
        if fixture and not (root / fixture).exists():
            reported.append(f'{entry["id"]} names the fixture {fixture}, which is not on disk. A '
                            'rule is proven by a fixture the rule itself refuses')
        if CONFIG_FOR_TOOL[tool] and entry['id'] not in enabled:
            reported.append(f'{entry["id"]} is in {REGISTRY} and {CONFIG_FOR_TOOL[tool]} does not '
                            'enable it. A registry that may hold rules nothing runs is a registry '
                            'that can be padded')
    for identifier, where in sorted(enabled.items()):
        if identifier not in carried:
            reported.append(f'{identifier} is enabled in {where} and {REGISTRY} does not carry '
                            'it. Write the entry with the finding id or the architecture section '
                            'the rule stands on, in the week the rule is written')
    return reported


def binaries(root):
    """The tools that are installed here, by the path the lockfile pins."""
    root = Path(root)
    found = {}
    for tool, relative in BINARY_FOR_TOOL.items():
        path = root / relative
        if path.exists():
            found[tool] = [str(path)]
    return found


def _fixture_tree(root, fixture):
    """A copy of the fixture laid out like the repository, with the real configs.

    Outside the repository and with `node_modules` linked in, which is the only
    arrangement in which both halves hold: the fixture's paths are the paths the
    rules' globs are written against, and a resolver can still answer what `pg`
    or `@seen/core` is.
    """
    root = Path(root)
    tree = Path(tempfile.mkdtemp(prefix='seen-rule-fixture-'))
    shutil.copytree(root / fixture, tree, dirs_exist_ok=True)
    for name in FIXTURE_SUPPORT:
        source = root / name
        if source.is_file():
            (tree / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, tree / name)
        elif source.is_dir():
            shutil.copytree(source, tree / name, dirs_exist_ok=True)
    modules = root / 'node_modules'
    if modules.is_dir():
        (tree / 'node_modules').symlink_to(modules)
    return tree


def _sources(tree):
    """The files in a fixture tree a tool would read."""
    return sorted(path for path in tree.rglob('*')
                  if path.is_file() and 'node_modules' not in path.parts
                  and path.suffix in ('.ts', '.tsx', '.js', '.jsx', '.mts', '.cts', '.json')
                  and path.name not in FIXTURE_SUPPORT)


def _run(command, cwd):
    result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, check=False)
    return result.returncode, (result.stdout or '') + (result.stderr or '')


def _named(name, output):
    """Whether a tool's own report says which rule refused the fixture.

    The weaker half of every proof but the compiler's, and worth saying why it
    is accepted: a fixture a tool refuses for a reason nobody asked about proves
    that the tool runs, not that the rule does. The rule's own name in the
    report is what tells the two apart, and it is what each of these tools
    prints beside a diagnostic.
    """
    return name in output


def _project(tree, flags=None):
    """A tsconfig in the fixture tree that extends the repository's own base.

    The flags are read from the copied base rather than restated on the command
    line, because restating them would prove a rule this repository does not
    run. `flags` turns named options off again, which is how a compiler flag is
    proven: see `_run_tsconfig`.
    """
    (tree / 'tsconfig.json').write_text(json.dumps({
        'extends': './tsconfig.base.json',
        'compilerOptions': dict({'noEmit': True, 'types': []}, **(flags or {})),
        'include': [str(path.relative_to(tree)) for path in _sources(tree)
                    if path.suffix in ('.ts', '.tsx')],
    }, indent=2))


# Flags that cannot be relaxed on their own. tsc refuses
# `exactOptionalPropertyTypes` without `strictNullChecks`, and `strict` is what
# turns that on, so the second compile of `tsconfig/strict` failed on the
# configuration rather than on the fixture and reported the rule as unproven. The
# only such pair in this repository's set today; a flag added here with a
# dependency of its own joins it, and the alternative, inferring the dependency
# from tsc's own message, would be a parser for one sentence of a compiler.
RELAXES_WITH = {'strict': {'exactOptionalPropertyTypes': False}}


def _run_tsconfig(entry, tree, binary):
    """A compiler flag is proven by compiling its fixture twice.

    tsc names the option in its message for `exactOptionalPropertyTypes` and
    not for the other three: `noUncheckedIndexedAccess` says "possibly
    'undefined'" and `strict` says whatever its member said. So the name in the
    output cannot be the test here, and the honest one is better anyway: the
    fixture must fail with the flag the base configuration sets, and compile
    cleanly with that one flag turned off. Both halves are needed. A fixture
    that fails either way fails for a reason that has nothing to do with the
    flag, and would report a rule as proven that is not being exercised at all.
    """
    flag = entry['id'].split('/', 1)[1]
    _project(tree)
    strict, with_flag = _run(binary + ['--noEmit', '-p', '.'], tree)
    if strict == 0:
        return False, (f'the fixture compiles with {flag} on, so this rule is not firing: '
                       + _tail(with_flag))
    _project(tree, flags=dict({flag: False}, **RELAXES_WITH.get(flag, {})))
    relaxed, without_flag = _run(binary + ['--noEmit', '-p', '.'], tree)
    if relaxed != 0:
        return False, (f'the fixture fails with {flag} off as well, so what refuses it is not '
                       f'{flag}: ' + _tail(without_flag))
    return True, f'the fixture fails with {flag} on and compiles with it off: ' + _tail(with_flag)


def _refusal(tool, name, code, output):
    """The shape every tool but the compiler is read with."""
    if code == 0:
        return False, f'{tool} accepted the fixture, so this rule is not firing: ' + _tail(output)
    if not _named(name, output):
        return False, (f'{tool} refused the fixture without naming {name}, so what refused it is '
                       'unknown: ' + _tail(output))
    return True, f'{tool} refused the fixture and named {name}'


def _expected(entry):
    """What the tool's report must name for this rule to count as fired.

    The rule's own name by default, which is what each of these tools prints
    beside a diagnostic. `expect` overrides it for the one case where the rule's
    name is not a thing any report says: a preset names no rule of its own, so
    what proves it is a named rule from inside the preset's set.
    """
    return entry.get('expect') or entry['id'].split('/', 1)[1]


def _run_biome(entry, tree, binary):
    # No git repository in a fixture tree, so the ignore file the real
    # configuration reads is not there to read. `--vcs-enabled=false` says so,
    # rather than letting biome decide what a missing one means.
    code, output = _run(binary + ['check', '--max-diagnostics=50', '--vcs-enabled=false', '.'],
                        tree)
    return _refusal('biome', _expected(entry), code, output)


def _run_ast_grep(entry, tree, binary):
    code, output = _run(binary + ['scan', '--json=compact', '.'], tree)
    return _refusal('ast-grep', _expected(entry), code, output)


def _run_dependency_cruiser(entry, tree, binary):
    code, output = _run(binary + ['--config', '.dependency-cruiser.json', '--output-type', 'err',
                                  '--no-progress', '.'], tree)
    return _refusal('dependency-cruiser', _expected(entry), code, output)


def _run_knip(entry, tree, binary):
    code, output = _run(binary + ['--no-progress', '--no-exit-code', '--reporter', 'symbols'],
                        tree)
    # knip's exit code is the count of issues, and `--no-exit-code` turns that
    # off, so the report is what says whether it found anything.
    found = 'Unused export' in output or 'Unused exported type' in output
    if not found:
        return False, 'knip found no unused export, so this rule is not firing: ' + _tail(output)
    return True, 'knip reported an unused export: ' + _tail(output)


RUNNER_FOR_TOOL = {
    'tsconfig': _run_tsconfig,
    'biome': _run_biome,
    'ast-grep': _run_ast_grep,
    'dependency-cruiser': _run_dependency_cruiser,
    'knip': _run_knip,
}


def fixture_results(root, binaries=None):
    """Whether each rule refuses the fixture it stands on.

    An absence is never a pass. A tool that is not installed, a fixture
    directory with nothing in it and a fixture the rule accepts are three
    different ways of proving nothing, and each is reported as what it is: a
    runner that went quiet when it could not run would be worse than no runner,
    because the report would read as though every rule had been proven.
    """
    root = Path(root)
    available = binaries if binaries is not None else globals()['binaries'](root)
    results = []
    for entry in load(root):
        tool, identifier = entry.get('tool'), entry.get('id')
        if not identifier or tool not in RUNNER_FOR_TOOL:
            continue
        binary = available.get(tool)
        if not binary:
            results.append(dict(id=identifier, tool=tool, fired=False,
                                detail=f'{tool} is not installed here, so this rule was not '
                                       'proven. Run it where the workspace is installed'))
            continue
        # A tool with no configuration in the tree runs on its own defaults, and
        # a rule proven against a tool's defaults is not proven at all: Biome's
        # recommended set is on when there is no biome.json, so this fixture
        # runner reported a rule as firing that this repository had not yet
        # enabled. Measured while the rule set was being written, which is the
        # only run on which it could have been seen.
        relative = CONFIG_FOR_TOOL[tool]
        if relative and not (root / relative).is_file():
            results.append(dict(id=identifier, tool=tool, fired=False,
                                detail=f'{relative} is not in this repository, so what would run '
                                       f"is {tool}'s own defaults rather than this repository's "
                                       'rules, and nothing a default refuses proves a rule'))
            continue
        fixture = root / (entry.get('fixture') or '')
        if not fixture.is_dir():
            results.append(dict(id=identifier, tool=tool, fired=False,
                                detail=f'the fixture {entry.get("fixture")} is not a directory'))
            continue
        tree = _fixture_tree(root, entry['fixture'])
        try:
            if not _sources(tree):
                results.append(dict(id=identifier, tool=tool, fired=False,
                                    detail=f'the fixture {entry["fixture"]} is empty, so there '
                                           'is nothing for this rule to refuse'))
                continue
            fired, detail = RUNNER_FOR_TOOL[tool](entry, tree, binary)
            results.append(dict(id=identifier, tool=tool, fired=fired, detail=detail))
        finally:
            shutil.rmtree(tree, ignore_errors=True)
    return results


def _tail(output, lines=6):
    kept = [line for line in output.splitlines() if line.strip()][-lines:]
    return ' / '.join(kept) if kept else 'no output'


def summary(answer):
    """The one line a reader of a long report gets, grouped by tool.

    A fixture run over twenty-two rules prints ten kilobytes of JSON, and
    everything that reads the tail of a command rather than the whole of it was
    getting a fragment of the last two entries: a terminal, a log, and the excerpt
    a triage puts in front of Jev, which is capped at 800 characters and is how
    SEEN-114's own criterion 2 came to read as unevidenced four times over.
    Written last so it is the last thing in the JSON too, because the tail is
    where it is wanted.
    """
    by_tool = {}
    for entry in answer['rules']:
        tool, _, name = str(entry['id']).partition('/')
        by_tool.setdefault(tool, []).append(name)
    grouped = '; '.join(f'{tool}: {", ".join(names)}' for tool, names in by_tool.items())
    if 'fixtures' not in answer:
        return (f'{len(answer["rules"])} rules in the registry, each citing a finding or a '
                f'section of the architecture. {grouped}')
    fired = [result['id'] for result in answer['fixtures'] if result['fired']]
    return (f'{len(fired)} of {len(answer["fixtures"])} rules refused their own fixture and named '
            f'themselves doing it. {grouped}')


def report(root, fixtures=False):
    """What `harness rules` answers: the registry, its problems, and the proofs."""
    found = load(root)
    answer = dict(rules=[dict(id=entry.get('id'), tool=entry.get('tool'),
                              citation=entry.get('citation'), fixture=entry.get('fixture'))
                         for entry in found if isinstance(entry, dict)],
                  problems=problems(root))
    if fixtures:
        results = fixture_results(root)
        answer['fixtures'] = results
        answer['unproven'] = [result['id'] for result in results if not result['fired']]
    answer['ok'] = not answer['problems'] and not answer.get('unproven')
    answer['summary'] = summary(answer)
    return answer
