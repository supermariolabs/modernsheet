"""App settings: library folder, PDF folder and the default display options of the editor.

Standard library only, no Flet: the app stores `Settings.to_json()` in its shared preferences.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields

def env(name: str) -> str | None:
    """Environment variable MODERNSHEET_<name>, or the pre-0.19 name CHORDSHEET_<name>."""
    return os.environ.get(f"MODERNSHEET_{name}") or os.environ.get(f"CHORDSHEET_{name}")


LAYOUT_KEYS = ("theme", "bar_width", "row_spacing", "notation", "chord_symbols", "label_colors")
CHOICES = {
    "theme": ("realbook", "clean"),
    "bar_width": ("uniform", "fit"),
    "row_spacing": ("compact", "normal", "wide", "extra"),
    "notation": ("staff", "both", "tab"),
    "chord_symbols": ("text", "jazz"),
    "label_colors": ("theme", "by_type"),
    "library_view": ("cards", "list"),
    "sort_by": ("title", "artist", "key", "tempo", "modified"),
    "language": ("it", "en"),
    "sync_mode": ("none", "folder", "gdrive"),
}


@dataclass
class Settings:
    library_root: str | None = None     # None: the bundled examples folder
    pdf_dir: str | None = None          # None: the file dialog decides
    theme: str = "realbook"
    bar_width: str = "uniform"
    row_spacing: str = "normal"         # space between rows (a song's {row_spacing} wins)
    notation: str = "staff"             # notated bars: staff, staff + guitar tablature, tablature
    chord_symbols: str = "text"
    label_colors: str = "theme"
    library_view: str = "cards"         # library screen: cards or list
    sort_by: str = "title"
    sort_desc: bool = False
    language: str = "it"                # user interface language (see i18n.LANGUAGES)
    sync_mode: str = "none"             # none | folder | gdrive: see sync.py, gdrive.py
    sync_folder: str | None = None      # folder mode: the remote folder (e.g. inside iCloud Drive)
    sync_account: str | None = None     # gdrive mode: the Google account (e-mail) the library belongs to
    sync_drive_folder: str = "Modern Sheet"   # gdrive mode: name of the app's folder in the Drive root
    csm_email: str = ""                       # chordsheet.com login remembered for the import (never the password)

    def layout_options(self) -> dict:
        """Keyword arguments for `layout()`."""
        return {k: getattr(self, k) for k in LAYOUT_KEYS}

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str | None) -> "Settings":
        """Settings from stored JSON; unknown keys, wrong types and invalid choices fall back to defaults."""
        s = cls()
        try:
            data = json.loads(raw) if raw else {}
        except ValueError:
            data = {}
        if not isinstance(data, dict):
            return s
        for f in fields(cls):
            v = data.get(f.name)
            if f.name in CHOICES:
                if v in CHOICES[f.name]:
                    setattr(s, f.name, v)
            elif f.type in (bool, "bool"):
                if isinstance(v, bool):
                    setattr(s, f.name, v)
            elif isinstance(v, str) and v.strip():
                setattr(s, f.name, v)
        return s
