#!/usr/bin/env python3
"""Entry point: python3 harness/run.py <command>."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.cli import main  # noqa: E402  (the path must be set before the import)

if __name__ == '__main__':
    raise SystemExit(main())
