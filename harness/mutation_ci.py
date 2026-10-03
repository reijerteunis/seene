"""Which files CI's incremental mutation job mutates, chosen by a tested function.

SEEN-116. The job used to carry this selection as inline shell no test ran. It
reads the changed paths (`git diff --name-only` output) and answers with the
value Stryker's --mutate takes, or nothing when no product file qualifies.

The rules: a product .ts file under packages/core/src is selected with the
package prefix stripped, in the order given. A changed test file is selected as
the source it tests, its sibling when that exists and otherwise the globs of its
directory, by the same mapping the tdd gate uses (`mutation.source_files` and
`mutation.patterns`), so a test-only change is measured and not skipped. A change to the
mutation config, the test setup or the package's tsconfig changes what every mutant faces, so the stored
results for unchanged files no longer describe it, and all of src is selected
instead. Anything else, including paths outside packages/core/src, is ignored.

Run as `git diff --name-only ... | python3 -m harness.mutation_ci`; it appends
`any=true|false` and, when any, `files=<value>` to the file named by
GITHUB_OUTPUT, and prints one human line.
"""

import os
import sys

from .mutation import patterns, source_files

PACKAGE_DIRECTORY = 'packages/core/'
CONFIG_FILES = tuple(PACKAGE_DIRECTORY + name
                     for name in ('stryker.config.mjs', 'vitest.config.ts', 'package.json', 'tsconfig.json'))
ALL_OF_SRC = 'src/**/*.ts,!src/**/*.test.ts'


def select(changed_paths, exists):
    """The --mutate value for these changed paths, or None when nothing qualifies.

    `exists` answers for a repository-relative path, and is what decides whether
    a changed test has a sibling to stand for it. Input order is kept.
    """
    paths = [path.strip() for path in changed_paths]
    if any(path in CONFIG_FILES for path in paths):
        return ALL_OF_SRC
    entries = []
    for path in paths:
        if not path.endswith('.ts'):
            continue
        for entry in source_files([path], exists):
            if entry not in entries:
                entries.append(entry)
    relative = [entry[len(PACKAGE_DIRECTORY):] for entry in entries]
    return ','.join(patterns(relative)) or None


def main():
    """Read changed paths on stdin and write the job's outputs; always exits 0."""
    files = select(sys.stdin.read().splitlines(), lambda path: os.path.isfile(path))
    lines = ['any=false'] if files is None else ['any=true', f'files={files}']
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
        output.write(''.join(f'{line}\n' for line in lines))
    if files is None:
        print('No product file under packages/core/src changed.')
    elif files == ALL_OF_SRC:
        print(f'The mutation config or the test setup changed: mutating all of src ({files}).')
    else:
        print(f'Mutating: {files}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
