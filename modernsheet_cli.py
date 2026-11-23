#!/usr/bin/env python3
"""Command line entry point: python modernsheet_cli.py song.chs [options]  (see --help)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from modernsheet.cli import main  # noqa: E402

sys.exit(main())
