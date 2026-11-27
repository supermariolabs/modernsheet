"""Import from Chord Sheet Maker (chordsheet.com) into .chs: a command-line tool kept outside the app
(SPEC §9). `convert` turns the text of the "Chords" field into a .chs; `account` logs in to the site and
downloads the songs of an account. Run it with `python chordsheet_cli.py --help`."""
from .convert import Conversion, convert as from_chordsheet_com

__all__ = ["Conversion", "from_chordsheet_com"]
