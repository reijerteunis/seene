"""The numbers and vocabularies the stage gates apply.

Missing or malformed, this file is fatal rather than defaulted: a harness
running on built-in fallbacks is a harness whose rules nobody can read.
"""

import tomllib

from .errors import require
from .paths import THRESHOLDS

EXPECTED = {
    'tickets': ('prefix',),
    'actors': ('tools', 'roles'),
    'stages': ('return_targets',),
    'checks': ('phases', 'default_timeout_seconds', 'maximum_timeout_seconds',
               'output_limit_bytes'),
    'review': ('severities',),
    'non_code': ('change_types',),
}


def load(root):
    path = root / THRESHOLDS
    require(path.is_file(), f'{THRESHOLDS} is missing; the harness has no rules without it')
    try:
        values = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        require(False, f'{THRESHOLDS} is not readable TOML: {error}')
    for section, keys in EXPECTED.items():
        require(isinstance(values.get(section), dict), f'{THRESHOLDS} is missing [{section}]')
        for key in keys:
            require(key in values[section], f'{THRESHOLDS} is missing {section}.{key}')
    return values
