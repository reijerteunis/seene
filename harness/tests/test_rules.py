"""The rule set in front of the model, and what makes one of its rules traceable.

SEEN-114. A finding a static rule could have caught is paid for three times: the
reviewer's reading, the return, the second review. The rules that stop that live
in four tools' own configuration files, which means they are four places a rule
can appear with nothing behind it. `rules/registry.toml` is the one place a rule's
citation lives, and these tests are the reason an entry there cannot be prose: a
rule a config enables and the registry does not carry is reported, a registry
entry citing nothing a reader can open is reported, and a registry entry whose
fixture is not on disk is reported. The check runs in both directions, because a
registry that only had to be a superset of the configs could be padded with rules
nobody runs.

The refusals are measured against a throwaway project, the way every harness test
is. The one assertion over this repository's own rule set is the last test here:
it is what CI runs, and it is the only place the live registry is read.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from harness import rules
from harness.tests.helpers import PROJECT, ProjectTest

# What a registry entry must carry. Written out here rather than imported so that
# a field added to the module without a thought about what it is for fails a test
# that says what the five are: a reader's question each.
ENTRY_KEYS = ('id', 'tool', 'citation', 'fixture', 'reason')


def entry(identifier='biome/noFloatingPromises', **changes):
    """A registry entry that passes, so a test can break exactly one thing."""
    return dict({
        'id': identifier,
        'tool': identifier.split('/')[0],
        'citation': 'docs/architecture.md: Deterministic code reconciles, the model reasons',
        'fixture': 'rules/fixtures/biome-nofloatingpromises',
        'reason': 'An unawaited promise in an ingest handler loses the error it threw.',
    }, **changes)


class RegistryTest(ProjectTest):
    """What `harness rules --check` reports, against a project we build by hand."""

    def registry(self, *entries):
        lines = []
        for found in entries:
            lines.append('[[rule]]')
            for key, value in found.items():
                lines.append(f'{key} = {json.dumps(value)}')
            lines.append('')
        self.write('rules/registry.toml', '\n'.join(lines))

    def fixture(self, relative, name='violation.ts', body='export const x = 1;\n'):
        self.write(f'{relative}/{name}', body)

    def biome(self, preset=None, **enabled):
        """A biome.json enabling exactly the rules a test names, by group."""
        groups = {'preset': preset} if preset else {}
        for name, group in enabled.items():
            groups.setdefault(group, {})[name] = 'error'
        self.write('biome.json',
                   json.dumps({'linter': {'enabled': True, 'rules': groups}}, indent=2))

    def tsconfig(self, **flags):
        self.write('tsconfig.base.json',
                   json.dumps({'compilerOptions': dict({'strict': True}, **flags)}, indent=2))

    def problems(self):
        return rules.problems(self.root)

    def test_a_registry_entry_needs_every_field(self):
        for key in ENTRY_KEYS:
            with self.subTest(missing=key):
                self.registry({name: value for name, value in entry().items() if name != key})
                self.assertTrue(any(key in problem for problem in self.problems()),
                                f'nothing reported the missing {key}')

    def test_a_citation_nobody_can_open_is_reported(self):
        self.registry(entry(citation='because it is good practice'))
        problems = self.problems()
        self.assertTrue(any('citation' in problem and 'biome/noFloatingPromises' in problem
                            for problem in problems), problems)

    def test_a_ticket_and_a_finding_is_a_citation(self):
        self.biome(noFloatingPromises='nursery')
        self.fixture('rules/fixtures/biome-nofloatingpromises')
        self.registry(entry(citation='SEEN-097 F1: a source-text search reported the wrong line'))
        self.assertEqual(self.problems(), [])

    def test_a_document_in_the_repository_is_a_citation(self):
        self.biome(noFloatingPromises='nursery')
        self.fixture('rules/fixtures/biome-nofloatingpromises')
        self.write('docs/architecture.md', '# Architecture\n')
        self.registry(entry(citation='docs/architecture.md: Services'))
        self.assertEqual(self.problems(), [])

    def test_a_document_that_is_not_there_is_not_a_citation(self):
        self.biome(noFloatingPromises='nursery')
        self.fixture('rules/fixtures/biome-nofloatingpromises')
        self.registry(entry(citation='docs/invented.md: a section nobody wrote'))
        problems = self.problems()
        self.assertTrue(any('docs/invented.md' in problem for problem in problems), problems)

    def test_a_fixture_that_is_not_on_disk_is_reported(self):
        self.biome(noFloatingPromises='nursery')
        self.registry(entry(fixture='rules/fixtures/nothing-here'))
        problems = self.problems()
        self.assertTrue(any('fixture' in problem and 'nothing-here' in problem
                            for problem in problems), problems)

    def test_the_recommended_set_is_one_rule_and_needs_one_citation(self):
        """`recommended: true` is one decision, taken once, and citable as one.

        Three hundred entries for a preset nobody chose rule by rule would be a
        registry a reader skims, which is the one thing it cannot be. A rule
        named explicitly beside the preset is a second decision and carries its
        own entry, which the test below is about.
        """
        self.write('docs/harness/workflow.md', '# The harness\n\n## A bounded review\n')
        self.biome(preset='recommended')
        self.fixture('rules/fixtures/biome-recommended')
        self.registry(entry('biome/recommended',
                            citation='docs/harness/workflow.md: A bounded review',
                            fixture='rules/fixtures/biome-recommended'))
        self.assertEqual(self.problems(), [])

    def test_a_ticket_id_on_its_own_is_not_a_citation(self):
        """Every rule was added by some ticket, so naming one proves nothing.

        This is the case the citation check exists for. A rule that cites the
        act of writing it is a rule nobody can trace, and the criterion asks
        for a finding id or an architecture section. The ticket has to carry the
        finding inside it, in the shapes this repository's journals use.
        """
        self.biome(noFloatingPromises='nursery')
        self.fixture('rules/fixtures/biome-nofloatingpromises')
        self.registry(entry(citation='SEEN-114: turn every recurring finding into a rule'))
        problems = self.problems()
        self.assertTrue(any('citation' in problem for problem in problems), problems)
        self.registry(entry(citation='SEEN-114 F7: the hook ran no rule at all'))
        self.assertEqual(self.problems(), [])

    def test_a_biome_rule_the_registry_does_not_carry_is_reported(self):
        self.biome(noFloatingPromises='nursery', noMisusedPromises='nursery')
        self.fixture('rules/fixtures/biome-nofloatingpromises')
        self.registry(entry())
        problems = self.problems()
        self.assertTrue(any('noMisusedPromises' in problem for problem in problems), problems)

    def test_a_registry_entry_for_a_rule_no_config_enables_is_reported(self):
        self.biome(noFloatingPromises='nursery')
        self.fixture('rules/fixtures/biome-nofloatingpromises')
        self.fixture('rules/fixtures/biome-nomisusedpromises')
        self.registry(entry(), entry('biome/noMisusedPromises',
                                     fixture='rules/fixtures/biome-nomisusedpromises'))
        problems = self.problems()
        self.assertTrue(any('noMisusedPromises' in problem and 'biome.json' in problem
                            for problem in problems), problems)

    def test_a_compiler_flag_is_a_rule_like_any_other(self):
        self.tsconfig(noUncheckedIndexedAccess=True)
        self.fixture('rules/fixtures/tsconfig-nouncheckedindexedaccess')
        self.registry(entry('tsconfig/strict',
                            citation='docs/harness/workflow.md: Rules from findings',
                            fixture='rules/fixtures/tsconfig-nouncheckedindexedaccess'))
        problems = self.problems()
        self.assertTrue(any('noUncheckedIndexedAccess' in problem for problem in problems),
                        problems)

    def test_a_build_setting_is_not_a_rule(self):
        """Only the compiler's checking flags need an entry.

        `target`, `declaration` and `esModuleInterop` decide what comes out of
        the compiler rather than what it refuses, and asking for a citation per
        build setting would fill the registry with entries nobody could cite and
        teach a reader to skim it.
        """
        self.write('docs/harness/workflow.md', '# The harness\n\n## Rules from findings\n')
        self.write('tsconfig.base.json', json.dumps({'compilerOptions': {
            'strict': True, 'target': 'ES2023', 'declaration': True, 'esModuleInterop': True,
        }}, indent=2))
        self.fixture('rules/fixtures/tsconfig-strict')
        self.registry(entry('tsconfig/strict',
                            citation='docs/harness/workflow.md: Rules from findings',
                            fixture='rules/fixtures/tsconfig-strict'))
        self.assertEqual(self.problems(), [])

    def test_an_ast_grep_rule_is_read_from_its_own_file(self):
        self.write('CLAUDE.md', '# Ground rules\n\nUse EUR in text, never the euro sign.\n')
        self.write('sgconfig.yml', 'ruleDirs:\n  - rules/ast-grep\n')
        self.write('rules/ast-grep/no-euro-sign.yml',
                   'id: no-euro-sign\nlanguage: TypeScript\nseverity: error\n')
        self.fixture('rules/fixtures/ast-grep-no-euro-sign')
        self.registry(entry('ast-grep/no-euro-sign',
                            citation='CLAUDE.md: use EUR in text, never the euro sign',
                            fixture='rules/fixtures/ast-grep-no-euro-sign'))
        self.assertEqual(self.problems(), [])

    def test_two_ast_grep_rules_in_one_file_are_refused(self):
        """One id per file, so that reading the ids is reading the files.

        ast-grep's own format allows several documents in one YAML file. Nothing
        here parses YAML, so a second id in a file is either read by accident or
        not read at all, and the honest answer is to refuse the shape rather
        than to guess which rule the file is.
        """
        self.write('sgconfig.yml', 'ruleDirs:\n  - rules/ast-grep\n')
        self.write('rules/ast-grep/two.yml', 'id: one\n---\nid: two\n')
        self.registry()
        problems = self.problems()
        self.assertTrue(any('two.yml' in problem for problem in problems), problems)

    def test_a_dependency_cruiser_rule_is_read_by_name(self):
        self.write('.dependency-cruiser.json', json.dumps({'forbidden': [
            {'name': 'core-no-io', 'severity': 'error', 'from': {}, 'to': {}},
        ]}, indent=2))
        self.fixture('rules/fixtures/dependency-cruiser-core-no-io')
        self.registry(entry('dependency-cruiser/core-no-io',
                            citation='docs/architecture.md: Services',
                            fixture='rules/fixtures/dependency-cruiser-core-no-io'))
        self.write('docs/architecture.md', '# Architecture\n')
        self.assertEqual(self.problems(), [])

    def test_a_tool_with_no_configuration_to_read_still_needs_its_entry_checked(self):
        """gitleaks and the harness's own checks are rules of the set too.

        Neither has a configuration file this module can read, so neither can be
        cross-checked against one. What is still checked is the citation and the
        fixture, because an entry nobody can trace is the thing the registry
        exists to refuse, whatever runs it.
        """
        self.registry(entry('harness/no-marketplace-host-in-tests',
                            citation='SEEN-090: no test may call a live marketplace',
                            fixture='rules/fixtures/nothing-here'))
        problems = self.problems()
        self.assertTrue(any('fixture' in problem for problem in problems), problems)

    def test_an_unknown_tool_is_refused(self):
        self.registry(entry('invented/whatever',
                            citation='SEEN-114: it seemed like a good idea',
                            fixture='rules/fixtures/nothing'))
        problems = self.problems()
        self.assertTrue(any('invented' in problem for problem in problems), problems)

    def test_an_id_that_does_not_name_its_tool_is_refused(self):
        self.registry(entry('noFloatingPromises', tool='biome'))
        problems = self.problems()
        self.assertTrue(any('noFloatingPromises' in problem for problem in problems), problems)

    def test_a_missing_registry_is_reported_rather_than_read_as_empty(self):
        self.biome(noFloatingPromises='nursery')
        problems = self.problems()
        self.assertTrue(any('registry' in problem for problem in problems), problems)


class ArrivalDateTest(RegistryTest):
    """When a rule arrived, read from git rather than from a new registry field.

    `rules/registry.toml` already carries five required fields, and it is not
    a file this slice's own plan names: `harness guard` refuses an edit to it
    from here, and a sixth field nine existing entries would need the day it
    was added is not a field this slice can add responsibly. Git already
    knows the answer without the registry carrying anything new: the first
    commit whose diff of the file introduces the id's own line is read with
    `git log -S`, the pickaxe search.
    """

    def commit(self, when, message='feat: a rule'):
        self.git('add', 'rules/registry.toml')
        os.environ['GIT_AUTHOR_DATE'] = when
        os.environ['GIT_COMMITTER_DATE'] = when
        self.addCleanup(os.environ.pop, 'GIT_AUTHOR_DATE', None)
        self.addCleanup(os.environ.pop, 'GIT_COMMITTER_DATE', None)
        self.git('commit', '-q', '-m', message)

    def test_a_rule_is_dated_by_the_commit_that_introduced_its_id(self):
        self.registry(entry('ast-grep/no-euro-sign'))
        self.commit('2026-09-24T09:00:00+00:00')
        dates = rules.arrival_dates(self.root)
        # git's own `%cI` normalises a +00:00 offset to Z, which is what is
        # asserted here; `datetime.fromisoformat` reads both shapes alike.
        self.assertEqual(dates['ast-grep/no-euro-sign'], '2026-09-24T09:00:00Z')

    def test_a_rule_added_later_in_a_second_commit_is_dated_by_that_one(self):
        self.registry(entry('ast-grep/no-euro-sign'))
        self.commit('2026-09-24T09:00:00+00:00', message='feat: the first rule')
        self.registry(entry('ast-grep/no-euro-sign'), entry('biome/noFloatingPromises'))
        self.commit('2026-10-01T09:00:00+00:00', message='feat: a second rule')
        dates = rules.arrival_dates(self.root)
        self.assertEqual(dates['ast-grep/no-euro-sign'], '2026-09-24T09:00:00Z')
        self.assertEqual(dates['biome/noFloatingPromises'], '2026-10-01T09:00:00Z')

    def test_a_rule_never_committed_carries_no_date(self):
        """Written but not committed, as every other test in this file leaves it."""
        self.registry(entry('ast-grep/no-euro-sign'))
        self.assertEqual(rules.arrival_dates(self.root), {})


class FixtureTest(ProjectTest):
    """A rule is proven by a fixture the rule itself refuses.

    The fixture is copied into a tree laid out like the repository and the real
    configuration is run against it, because a rule scoped to `packages/core/**`
    proves nothing about a file sitting in `rules/fixtures/`. The end-to-end
    proof is `harness rules --fixtures` in CI's node job, where the four tools
    are installed; what is asserted here is the half that must hold with nothing
    installed at all, which is that an absence is reported as an absence. A rule
    whose tool is missing, or whose fixture its own rule accepts, is named rather
    than passed over, because a fixture runner that stayed quiet when it could
    not run would be the one thing worse than no fixture runner.
    """

    quiet = [sys.executable, '-c', 'raise SystemExit(0)']

    def register(self, identifier, tool, fixture):
        self.write('rules/registry.toml', '\n'.join([
            '[[rule]]',
            f'id = "{identifier}"',
            f'tool = "{tool}"',
            'citation = "SEEN-114: the fixture runner is what a rule is proven by"',
            f'fixture = "{fixture}"',
            'reason = "Stand-in: what this test is about is the runner, not the rule."',
            '',
        ]))

    def test_a_fixture_the_rule_accepts_is_reported_as_not_firing(self):
        self.register('biome/noFloatingPromises', 'biome',
                      'rules/fixtures/biome-nofloatingpromises')
        self.write('biome.json', json.dumps({'linter': {'enabled': True}}))
        self.write('rules/fixtures/biome-nofloatingpromises/packages/core/src/a.ts',
                   'export const total = 1250;\n')
        results = rules.fixture_results(self.root, binaries={'biome': self.quiet})
        found = {result['id']: result for result in results}
        self.assertIn('biome/noFloatingPromises', found)
        self.assertFalse(found['biome/noFloatingPromises']['fired'])
        self.assertIn('not firing', found['biome/noFloatingPromises']['detail'])

    def test_a_tool_that_is_not_installed_is_an_absence_and_not_a_pass(self):
        self.register('biome/noFloatingPromises', 'biome',
                      'rules/fixtures/biome-nofloatingpromises')
        self.write('rules/fixtures/biome-nofloatingpromises/packages/core/src/a.ts',
                   'export const x = 1;\n')
        results = rules.fixture_results(self.root, binaries={})
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]['fired'])
        self.assertIn('not installed', results[0]['detail'])

    def test_the_fixture_tree_carries_the_ast_grep_rules(self):
        """A rule proven in a tree that holds no rules is a rule nothing proved.

        sgconfig.yml names its `ruleDirs` relative to itself, so copying that
        configuration into the fixture tree without the directory it points at
        leaves ast-grep scanning with no rule loaded at all, and the fixture
        passes for the one reason a fixture must never pass for. It is the same
        absence as a tool running on its own defaults, one level further in: the
        configuration is present and what it configures is not.
        """
        self.write('sgconfig.yml', 'ruleDirs:\n  - rules/ast-grep\n')
        self.write('rules/ast-grep/no-euro-sign.yml',
                   'id: no-euro-sign\nlanguage: Tsx\nseverity: error\n')
        self.write('rules/fixtures/ast-grep-no-euro-sign/packages/core/src/a.ts',
                   'export const label = 1;\n')
        tree = rules._fixture_tree(self.root, 'rules/fixtures/ast-grep-no-euro-sign')
        try:
            self.assertTrue((tree / 'sgconfig.yml').is_file(), 'the configuration was not copied')
            self.assertTrue((tree / 'rules' / 'ast-grep' / 'no-euro-sign.yml').is_file(),
                            'sgconfig.yml was copied into the fixture tree without the rule '
                            'directory it names, so ast-grep would scan the fixture with no rule')
        finally:
            shutil.rmtree(tree, ignore_errors=True)

    def test_a_fixture_directory_that_is_empty_is_reported(self):
        """An empty fixture cannot refuse anything, and would pass quietly.

        `problems` already refuses a fixture path that is not on disk. A
        directory that exists and holds no file the tool would read is the same
        absence one step further in, and it is the shape a half-finished fixture
        has.
        """
        self.register('biome/noFloatingPromises', 'biome',
                      'rules/fixtures/biome-nofloatingpromises')
        # The configuration has to be there, or the absence reported is that one:
        # a tool with no configuration in the tree would run on its own defaults,
        # which is the check one step before this.
        self.write('biome.json', json.dumps({'linter': {'enabled': True}}))
        (self.root / 'rules/fixtures/biome-nofloatingpromises').mkdir(parents=True)
        results = rules.fixture_results(self.root, binaries={'biome': self.quiet})
        self.assertFalse(results[0]['fired'])
        self.assertIn('empty', results[0]['detail'])


class ThisRepositoryTest(unittest.TestCase):
    """The live rule set, which is the assertion CI's harness job runs.

    Every other test here builds a project to break; this one reads the one that
    matters. A rule added to a config without a registry entry fails here, which
    is the whole mechanism: the citation is written the same week as the rule or
    the build goes red.
    """

    def test_every_rule_in_this_repository_is_traceable(self):
        self.assertEqual(rules.problems(PROJECT), [])

    def test_the_registry_carries_a_rule_for_each_tool_the_set_runs(self):
        """A tool with no entry is a tool nobody can trace.

        The compiler and Biome arrived first; ast-grep, dependency-cruiser and
        knip are the three that carry the rules no general linter can express,
        and a configuration file added without an entry is what the check in
        `problems` refuses from the other direction. Read from
        `RUNNER_FOR_TOOL` rather than from a list written here, which is SEEN-114
        F4: the harness's own check ran in the hook and in CI with no registry
        entry, so a reviewer naming it as a rule candidate had it counted as a
        rule nobody had written, and a list in this test would have had to be
        edited to notice.
        """
        carried = {found['tool'] for found in rules.load(PROJECT)}
        for tool in sorted(rules.RUNNER_FOR_TOOL):
            self.assertIn(tool, carried, f'{tool} runs in the set and the registry does not name it')

    def test_the_harness_check_is_proven_by_its_own_fixture(self):
        """The one rule of the set whose tool is this repository's own Python.

        The others are proven by a binary the lockfile pins. This one is proven
        the way the hook runs it, by calling the check, so what the fixture
        proves is `harness lint` and not a command line.
        """
        results = {found['id']: found
                   for found in rules.fixture_results(PROJECT, binaries=rules.binaries(PROJECT))}
        found = results['harness/no-live-marketplace-host']
        self.assertTrue(found['fired'], found['detail'])
        host = 'api.' + 'bol.com'  # Split so this assertion is not itself a violation.
        self.assertIn(host, found['detail'])

    def test_the_fixture_tree_is_not_read_by_the_check_it_proves(self):
        """Otherwise the fixture would fail the repository's own lint.

        Every fixture in the set is a violation by construction, and the four
        binaries ignore them by scope. This check walks the whole tree, so it is
        told, and the tell is what keeps `harness lint` green with a fixture in
        the tree that names a live marketplace.
        """
        from harness import secrets
        self.assertEqual(secrets.marketplace_hosts(PROJECT), [])




class WhereTheSetRunsTest(unittest.TestCase):
    """The two places the set is called from, read from the files that are them.

    `scripts/rules.sh` is the one definition of what running the rule set means,
    and the hook and the CI workflow are the two callers the criterion names. The
    rules themselves are proven against their fixtures, which is what `FixtureTest`
    and `rules --fixtures` do; whether the hook and CI still call the runner was
    proven by running each of them once and recording the result, and a
    measurement taken on one afternoon is not a property the next commit keeps. An
    edit moving knip into the staged run, or dropping the tree run from the
    workflow, would leave every fixture firing and every other test here green.
    These read the wiring, so the budget and the reach of the set are carried by
    the regression instead.
    """

    def hook(self):
        return (PROJECT / '.githooks' / 'pre-commit').read_text()

    def workflow(self):
        return (PROJECT / '.github' / 'workflows' / 'ci.yml').read_text()

    def shell_function(self, name):
        """One function's body out of scripts/rules.sh, by its opening line.

        The two modes differ in what they hand each tool and in whether knip runs
        at all, so a test about one of them has to read that one rather than the
        whole file.
        """
        text = (PROJECT / 'scripts' / 'rules.sh').read_text()
        opened = text.index(f'{name}() {{')
        return text[opened:text.index('\n}\n', opened)]

    def test_the_pre_commit_hook_runs_the_set_over_the_staged_files(self):
        self.assertIn('./scripts/rules.sh staged', self.hook())

    def test_the_hook_never_runs_the_set_over_the_whole_tree(self):
        """What keeps the hook inside its ten-second budget, as a rule.

        The budget is the reason the hook exists in this shape: the tree run takes
        tens of seconds and belongs to CI, and a hook calling it would be a hook
        people turn off with --no-verify.
        """
        self.assertNotIn('./scripts/rules.sh tree', self.hook())

    def test_the_staged_run_hands_each_tool_only_the_staged_paths(self):
        staged = self.shell_function('run_staged')
        self.assertIn('staged_paths', staged)
        for paths in ('"${code_paths[@]}"', '"${module_paths[@]}"'):
            self.assertIn(paths, staged)
        # Biome over the tree is `biome check .`, which is the tree run's call and
        # would make the staged mode a tree run wearing its name.
        self.assertNotIn('check .', staged)

    def test_the_staged_run_never_word_splits_its_path_list(self):
        """SEEN-114 F21, as a rule rather than as a comment.

        An unquoted `$code_paths` splits on whitespace, so a staged `my page.tsx`
        reaches Biome as two paths that are not there, and Biome with
        --no-errors-on-unmatched reports Checked 0 files and exits 0. The hook then
        says ok having read nothing, which is the absence-is-not-a-pass rule this
        whole module is written around, one layer out in the shell.
        """
        staged = self.shell_function('run_staged')
        for unquoted in ('$code_paths', '$module_paths', '$all'):
            self.assertNotIn(unquoted, staged.replace('${', '@{'))
        self.assertIn("read -r -d ''", staged)
        self.assertIn('-z', self.shell_function('staged_paths'))

    def test_knip_runs_over_the_tree_and_never_over_a_staged_file(self):
        """A dead export is a property of the whole import graph.

        Asked of a staged file, knip reports every export the files around it
        happen not to use, so it is in the tree run and in CI and not in the hook.
        """
        self.assertNotIn('knip', self.shell_function('run_staged'))
        self.assertIn('knip', self.shell_function('run_tree'))

    def test_every_tool_runs_through_timed_so_the_budget_is_measured(self):
        """The hook prints what each tool took, on every commit.

        A budget nobody measures is a budget that drifts, so each tool is invoked
        through `timed` rather than called directly, in both modes.
        """
        for mode in ('run_staged', 'run_tree'):
            body = self.shell_function(mode)
            for line in body.splitlines():
                stripped = line.strip()
                if stripped.startswith('"$bin/'):
                    self.fail(f'{mode} calls {stripped} without timing it')
            self.assertIn('timed ', body)

    def test_ci_runs_the_set_on_the_tree_and_proves_every_rule_and_every_citation(self):
        """Criterion 2's other half and criterion 5's, in the workflow itself.

        Three steps rather than one, because they need different runners: the
        traceability check reads files and runs in the job with no workspace, the
        fixture proof and the tree run need the installed tools.
        """
        workflow = self.workflow()
        for step in ('rules --check', 'rules --fixtures', './scripts/rules.sh tree'):
            self.assertIn(step, workflow)

    def test_ci_executes_the_staged_run_and_does_not_only_read_it(self):
        """SEEN-114 F23: the one test that runs the script has to run somewhere.

        `StagedPathWithASpaceTest` needs the workspace, so it skips wherever
        node_modules is absent, and the job that runs the harness suite does not
        install it. Skipped in every job, it guarded F21's fix with two substring
        assertions over the script's text, and a regression that kept both
        substrings would have gone through. It is named in the job that installs.
        """
        self.assertIn('StagedPathWithASpaceTest', self.workflow())

    def test_every_workspace_package_declares_an_exports_map(self):
        """So nothing reaches into another package's internals.

        Read from the workspace globs rather than from a list here, so a package
        added without an exports map fails this test rather than being missed by
        it.
        """
        found = sorted(PROJECT.glob('apps/*/package.json')) + \
            sorted(PROJECT.glob('packages/*/package.json'))
        self.assertEqual(len(found), 7, [str(path) for path in found])
        for path in found:
            manifest = json.loads(path.read_text())
            self.assertIn('exports', manifest, f'{path} declares no exports map')


class SummaryTest(unittest.TestCase):
    """The last line of a long report, which is the line most readers get.

    A fixture run prints ten kilobytes of JSON and a terminal, a log and the
    excerpt a triage hands Jev all read the end of it. So the end says what the
    run proved: how many rules refused their own fixture, and which rules those
    were, by tool.
    """

    def test_the_summary_names_every_rule_grouped_by_its_tool(self):
        answer = rules.report(PROJECT)
        line = answer['summary']
        # Counted from the registry rather than written here, so a rule added
        # next week does not fail this test for the one reason it must not.
        self.assertIn(f'{len(answer["rules"])} rules in the registry', line)
        for tool in ('tsconfig', 'biome', 'ast-grep', 'dependency-cruiser', 'knip'):
            self.assertIn(f'{tool}: ', line)
        for name in ('core-no-io', 'database-through-repository',
                     'marketplace-write-through-policy-gate'):
            self.assertIn(name, line)

    def test_a_fixture_run_counts_the_rules_that_fired(self):
        """Counted from the results rather than from the registry.

        An unproven rule must not be summarised as a rule that fired, which is
        the one way this line could lie.
        """
        answer = dict(rules=[dict(id='biome/noFloatingPromises')],
                      fixtures=[dict(id='biome/noFloatingPromises', fired=False, detail='no')])
        self.assertIn('0 of 1 rules refused', rules.summary(answer))


class StagedPathWithASpaceTest(unittest.TestCase):
    """A staged path with a space reaches every tool whole, measured.

    SEEN-114 F21. The assertions above read the script; this one runs it, because
    the defect was not in what the script said but in what the shell did with it.
    It runs against this repository, since `scripts/rules.sh` cds to its own root
    and there is no second tree to point it at: the violation is written here and
    removed in tearDown, and the index is a throwaway, so the real index and the
    real staging area are untouched.
    """

    # Under packages/core/src because that is where the rule being tripped is
    # scoped, and with the space that used to split the list.
    violation = PROJECT / 'packages' / 'core' / 'src' / 'violation with space.ts'

    def setUp(self):
        self.index = Path(tempfile.mkdtemp()) / 'index'
        self.violation.write_text(
            "/** A commission of \u20ac 1,50, written the one way the ground rules refuse. */\n"
            "export const COMMISSION_LABEL = '\u20ac 1,50';\n")
        environment = dict(os.environ, GIT_INDEX_FILE=str(self.index))
        subprocess.run(['git', 'read-tree', 'HEAD'], cwd=PROJECT, env=environment, check=True,
                       capture_output=True)
        subprocess.run(['git', 'update-index', '--add', '--', str(self.violation.relative_to(PROJECT))],
                       cwd=PROJECT, env=environment, check=True, capture_output=True)
        self.environment = environment

    def tearDown(self):
        self.violation.unlink(missing_ok=True)
        shutil.rmtree(self.index.parent, ignore_errors=True)

    def test_the_staged_run_refuses_a_violation_in_a_path_with_a_space(self):
        if not (PROJECT / 'node_modules' / '.bin' / 'ast-grep').exists():
            self.skipTest('the workspace is not installed, so no tool can run')
        result = subprocess.run(['./scripts/rules.sh', 'staged'], cwd=PROJECT,
                                env=self.environment, capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertIn('violation with space.ts', output)
        self.assertNotIn('Checked 0 files', output)


class WhatTheRulesActuallyRefuseTest(unittest.TestCase):
    """Two rules whose registry entries promised more than their patterns read.

    SEEN-114 F22 and F24, both found by the fifth review by running the rules
    against shapes no fixture carried rather than by reading them. A fixture
    proves a rule fires at all; these prove it fires where its own entry says it
    does. Both write a probe into `packages/core/src`, because that is the scope
    both rules are written for and the tools read the real configuration from the
    repository root, and both remove it again.
    """

    probe = PROJECT / 'packages' / 'core' / 'src' / 'probe-what-rules-refuse.ts'

    def tearDown(self):
        self.probe.unlink(missing_ok=True)

    def installed(self, tool):
        if not (PROJECT / 'node_modules' / '.bin' / tool).exists():
            self.skipTest(f'{tool} is not installed here')

    def test_every_library_deny_list_anchors_the_bare_specifier(self):
        """F22, as the comparison that would have caught it.

        A specifier resolves to `node_modules/axios/...` when the package is
        installed and to the bare `axios` when it is not, so a pattern anchored
        only on `node_modules/` is silent on a dependency nobody has installed
        yet, which is every dependency at the moment somebody writes the import.
        Three of the four library deny-lists wrote `(^|node_modules/)` and
        `core-no-io`, the one guarding the money core, wrote `node_modules/`.
        """
        rules_file = json.loads((PROJECT / '.dependency-cruiser.json').read_text())
        by_name = {rule['name']: rule for rule in rules_file['forbidden'] if rule.get('name')}
        for name in ('core-no-io', 'network-only-through-generated-clients',
                     'database-through-repository', 'no-cloud-sdk-outside-providers'):
            path = by_name[name]['to']['path']
            self.assertIn('(^|node_modules/)', path,
                          f'{name} matches an installed package and not a bare specifier')

    def test_the_money_core_may_not_import_an_uninstalled_io_library(self):
        """F22 again, run rather than read."""
        self.installed('depcruise')
        self.probe.write_text("import { Queue } from 'bullmq';\nexport const QUEUE = Queue;\n")
        result = subprocess.run(
            [str(PROJECT / 'node_modules' / '.bin' / 'depcruise'), '--config',
             '.dependency-cruiser.json', '--output-type', 'err', '--no-progress',
             str(self.probe.relative_to(PROJECT))],
            cwd=PROJECT, capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
        self.assertIn('core-no-io', output)
        self.assertNotEqual(result.returncode, 0, output)

    def test_money_as_integer_cents_reads_a_schedule_and_a_tariff(self):
        """F24: the two positions a fee schedule is actually written in.

        SEEN-016 encodes fee schedules per marketplace and SEEN-071 models margin
        from cost layers, and a schedule is an object literal and a tariff a class
        field. The rule read only a variable declarator, so both passed while its
        registry entry said it read a non-integer literal bound to a name that
        says it is money.
        """
        self.installed('ast-grep')
        self.probe.write_text('const priceEur = 19.99;\n'
                              'const schedule = { feeCents: 1.5, price: 19.99 };\n'
                              'class Tariff { private price = 19.99; }\n')
        result = subprocess.run(
            [str(PROJECT / 'node_modules' / '.bin' / 'ast-grep'), 'scan',
             str(self.probe.relative_to(PROJECT)), '--json=compact'],
            cwd=PROJECT, capture_output=True, text=True, timeout=120)
        found = json.loads(result.stdout or '[]')
        money = [row for row in found if row.get('ruleId') == 'money-as-integer-cents']
        # One for the declarator, two for the object's properties, one for the field.
        self.assertEqual(len(money), 4, [row.get('text') for row in money])
        self.assertTrue(any('feeCents' in row['text'] for row in money), money)
        self.assertTrue(any('private price' in row['text'] for row in money), money)


if __name__ == '__main__':
    unittest.main()
