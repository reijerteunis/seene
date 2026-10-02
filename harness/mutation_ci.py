"""Which files CI's incremental mutation job mutates, chosen by a tested function.

SEEN-116. The job used to carry this selection as inline shell no test ran. It
reads the changed paths (`git diff --name-only` output) and answers with the
value Stryker's --mutate takes, or nothing when no product file qualifies.

The rules: a product .ts file under packages/core/src is selected with the
package prefix stripped, tests left out, in the order given. A change to the
mutation config or the test setup changes what every mutant faces, so the stored
results for unchanged files no longer describe it, and all of src is selected
instead. Anything else, including paths outside packages/core/src, is ignored.

Run as `git diff --name-only ... | python3 -m harness.mutation_ci`; it appends
`any=true|false` and, when any, `files=<value>` to the file named by
GITHUB_OUTPUT, and prints one human line.
"""

import os
import re
import sys

PACKAGE_DIRECTORY = 'packages/core/'
SOURCE_DIRECTORY = 'packages/core/src/'
CONFIG_FILES = tuple(PACKAGE_DIRECTORY + name
                     for name in ('stryker.config.mjs', 'vitest.config.ts', 'package.json'))
ALL_OF_SRC = 'src/**/*.ts,!src/**/*.test.ts'
TEST_FILE = re.compile(r'\.test\.ts$')


def select(changed_paths):
    """The --mutate value for these changed paths, or None when nothing qualifies."""
    paths = [path.strip() for path in changed_paths]
    if any(path in CONFIG_FILES for path in paths):
        return ALL_OF_SRC
    files = [path[len(PACKAGE_DIRECTORY):] for path in paths
             if path.startswith(SOURCE_DIRECTORY) and path.endswith('.ts')
             and not TEST_FILE.search(path)]
    return ','.join(files) or None


def main():
    """Read changed paths on stdin and write the job's outputs; always exits 0."""
    files = select(sys.stdin.read().splitlines())
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
