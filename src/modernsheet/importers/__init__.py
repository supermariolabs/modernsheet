"""Importers from other chord-sheet formats into .chs."""
from .chordsheet_com import Conversion, convert as from_chordsheet_com

__all__ = ["Conversion", "from_chordsheet_com"]
