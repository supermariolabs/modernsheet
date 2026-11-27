#!/usr/bin/env python3
"""Import from chordsheet.com (kept outside the app): python chordsheet_cli.py --help  (SPEC §9)."""
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path[:0] = [str(here / "src"), str(here / "tools")]

from chordsheet_import.cli import main  # noqa: E402

sys.exit(main())
