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
import shutil
import sys
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
        """Five tools, and a tool with no entry is a tool nobody can trace.

        The compiler and Biome arrived first; ast-grep, dependency-cruiser and
        knip are the three that carry the rules no general linter can express,
        and a configuration file added without an entry is what the check in
        `problems` refuses from the other direction.
        """
        carried = {found['tool'] for found in rules.load(PROJECT)}
        for tool in ('tsconfig', 'biome', 'ast-grep', 'dependency-cruiser', 'knip'):
            self.assertIn(tool, carried)


if __name__ == '__main__':
    unittest.main()
