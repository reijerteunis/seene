"""What must never appear: credentials in a record, live marketplaces in a test.

Two scans, kept together because both answer the same question in different
places. Neither repairs anything: they report, and their callers refuse.
"""

import re

# Shorter than this and a value is a word rather than a credential. Longer, and
# a coincidence is unlikely enough that refusing the record is the right call.
MINIMUM_CREDENTIAL_LENGTH = 12

# Variables whose value is a path or a terminal setting. A journal record
# legitimately contains file paths, so these are skipped whatever their length.
NOT_CREDENTIALS = frozenset({
    'PATH', 'PWD', 'OLDPWD', 'SHLVL', 'TERM', 'TERM_PROGRAM', 'TERM_PROGRAM_VERSION',
    'LANG', 'LC_ALL', 'LC_CTYPE', 'HOME', 'TMPDIR', 'SHELL', 'USER', 'LOGNAME',
    'MANPATH', 'INFOPATH', 'XPC_SERVICE_NAME', 'COMMAND_MODE', '__CF_USER_TEXT_ENCODING',
})

# The hosts a test may never name. A connector's source must name its API; a
# test that names it is a test that can call it.
MARKETPLACE_HOSTS = (
    'api.bol.com',
    'sellingpartnerapi',
    'api.ebay.com',
    'sellerapi.kaufland.com',
    'api.otto.market',
)

# A line that names a host on purpose says so, visibly, rather than the lint
# carrying a list of files it has quietly stopped checking.
ALLOW_MARKER = 'harness-allow-marketplace-host'

TEST_FILE = re.compile(r'(\.test\.[tj]sx?|\.spec\.[tj]sx?|(^|/)test_[^/]+\.py)$')
TESTS_DIRECTORY = re.compile(r'(^|/)(tests|__tests__)/')

# A shell turns text into instructions, which is exactly what ticket text and
# marketplace payloads must never become.
SHELL_USE = (
    re.compile(r'shell\s*=\s*True'),
    re.compile(r'os\.system\s*\('),
    re.compile(r'os\.popen\s*\('),
    re.compile(r'subprocess\.(getoutput|getstatusoutput)\s*\('),
)


def credentials(environ):
    """Environment values worth refusing a record over, by variable name."""
    return {name: value for name, value in environ.items()
            if name not in NOT_CREDENTIALS
            and isinstance(value, str)
            and len(value.strip()) >= MINIMUM_CREDENTIAL_LENGTH}


def leaked(text, environ):
    """The names of any environment variables whose value appears in the text.

    Names only. A refusal that prints the secret has leaked it.
    """
    return sorted(name for name, value in credentials(environ).items() if value.strip() in text)


def _files(root):
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        relative = str(path.relative_to(root))
        if relative.startswith(('.git/', 'node_modules/', 'graphify-out/', '.turbo/')):
            continue
        if '/node_modules/' in relative or '__pycache__/' in relative:
            continue
        # Compiled and packed files carry the same strings as their sources and
        # would report every hit twice, in a file nobody can fix.
        if path.suffix in ('.pyc', '.pyo', '.map', '.zst', '.lock'):
            continue
        yield relative, path


def marketplace_hosts(root):
    """Live marketplace hosts named in test code."""
    found = []
    for relative, path in _files(root):
        if not (TEST_FILE.search(relative) or TESTS_DIRECTORY.search(relative)):
            continue
        try:
            text = path.read_text(errors='replace')
        except OSError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if ALLOW_MARKER in line:
                continue
            for host in MARKETPLACE_HOSTS:
                if host in line:
                    found.append(dict(path=relative, line=number, host=host))
    return found


def shell_use(source_root):
    """Places in the harness's own source where text could reach a shell."""
    found = []
    for path in sorted(source_root.rglob('*.py')):
        if '/tests/' in str(path):
            continue
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            if line.lstrip().startswith('#'):
                continue
            for pattern in SHELL_USE:
                if pattern.search(line):
                    found.append(dict(path=str(path), line=number, text=line.strip()))
    return found
