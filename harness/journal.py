"""The append-only journal: one directory of numbered records per ticket.

Each record names the sha256 of the previous record file exactly as it sits on
disk, so the chain is verifiable with shasum and no harness. A record holds no
hash of itself; the file's bytes are its hash. See
docs/adr/0001-journal-integrity-file-bytes-and-git-as-notary.md.
"""

from datetime import datetime, timezone
import hashlib
import json
import os

from .errors import HarnessError, require
from .paths import ALLOWED_BESIDE_RECORDS, HARNESS_VERSION, KINDS, RECORD_NAME

ENVELOPE = ('sequence', 'ticket', 'timestamp', 'harness_version', 'kind', 'stage',
            'attempt', 'actor', 'head', 'prev_hash', 'data')


def digest(path):
    """The sha256 of a record file, over its bytes and nothing else."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def serialise(record):
    """The one byte representation of a record. Never re-run on a written file."""
    return json.dumps(record, indent=2, ensure_ascii=False).encode() + b'\n'


def read(folder):
    """Read one ticket's records in order, verifying the chain as it goes.

    Refuses a gap, a renamed record, an edited record and an unrecognised file
    beside the records, rather than repairing any of them.
    """
    if not folder.is_dir():
        return []
    paths, records, previous = [], [], None
    for entry in sorted(folder.iterdir()):
        if RECORD_NAME.match(entry.name):
            paths.append(entry)
        else:
            require(entry.name in ALLOWED_BESIDE_RECORDS,
                    f'Unrecognised file in the journal: {entry.name}. A journal holds '
                    f'NNNN.json records plus {", ".join(ALLOWED_BESIDE_RECORDS)}')
    for position, path in enumerate(paths, start=1):
        require(path.name == f'{position:04d}.json',
                f'Journal record {position:04d}.json is missing or renamed; found {path.name}')
        try:
            record = json.loads(path.read_text())
        except json.JSONDecodeError as error:
            raise HarnessError(f'Journal record {path.name} is not readable JSON: {error}')
        require(record.get('prev_hash') == previous,
                f'Journal chain breaks at {path.name}; its record or the one before it changed')
        previous = digest(path)
        records.append(record)
    return records


def append(folder, records, *, kind, stage, attempt, actor, head, ticket, data):
    """Write the next record. Exclusive and atomic, so a crash cannot truncate one."""
    require(kind in KINDS, f'Unknown record kind: {kind}')
    record = dict(sequence=len(records) + 1,
                  ticket=ticket,
                  timestamp=datetime.now(timezone.utc).isoformat(),
                  harness_version=HARNESS_VERSION,
                  kind=kind,
                  stage=stage,
                  attempt=attempt,
                  actor=actor,
                  head=head,
                  prev_hash=digest(folder / f'{len(records):04d}.json') if records else None,
                  data=data)
    folder.mkdir(parents=True, exist_ok=True)
    write_once(folder / f'{record["sequence"]:04d}.json', serialise(record))
    return record


def write_once(path, payload):
    """Write bytes to a name that must not already exist, atomically.

    A direct exclusive create prevents overwrites but not truncation: a process
    killed between write and close would leave half a record and break the chain
    for good. Writing aside and linking into place cannot.
    """
    temporary = path.with_name(f'.{path.name}.{os.getpid()}.part')
    try:
        with temporary.open('wb') as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


TRANSITIONS = ('advance', 'return', 'receipt', 'reopen')


def state(records):
    """Where a ticket stands now.

    A record's envelope says where the ticket was when it was written, so an
    advance is stamped with the stage it left. The transition it describes lives
    in its data, and applying it to the last record is what "now" means.
    """
    require(records, 'No journal exists for this ticket; start it first')
    last = records[-1]
    stage, attempt = last['stage'], last['attempt']
    if last['kind'] in TRANSITIONS:
        stage = last['data']['to_stage']
        attempt = last['data'].get('to_attempt', attempt)
    return dict(stage=stage, attempt=attempt, records=len(records))
