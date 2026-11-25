"""modernsheet — engine for the .chs chord-sheet format.

Three layers:
    1. parser / model    parse(text) -> Song                      (parser.py, model.py, musicxml.py, theory.py)
    2. layout            layout(song, **opts) -> DisplayList       (layout.py, fonts.py, display.py)
    3. backends          write_pdf / pdf_bytes (pdf.py), Flet canvas (flet_view.py), SVG (svg.py)

Typical use:
    from modernsheet import parse, layout, render_pdf
    song = parse(open("song.chs").read(), transpose=2, base_dir=".")
    dl = layout(song, theme="realbook")          # pages of drawing operations
    render_pdf(song, "song.pdf")                  # or: write_pdf(dl, "song.pdf")
"""
from __future__ import annotations

from .display import DisplayList
from .layout import THEMES, Layout
from .model import Bar, Event, Section, Song
from .parser import parse

__version__ = "0.46.0"


def layout(song: Song, **opts) -> DisplayList:
    """Lay out a parsed song. Options: bars_per_line, bar_width (uniform|fit), row_spacing (compact|normal|
    wide|extra or a factor / percentage), notation (staff|both|tab: guitar tablature), paper (A4|Letter),
    theme (realbook|clean), chord_symbols (text|jazz), label_colors (theme|by_type|#RRGGBB)."""
    return Layout(song, **opts).run()


def render_pdf(song: Song, target, **opts) -> DisplayList:
    """Lay out and write a PDF to a path or binary file object; returns the DisplayList."""
    from .pdf import write_pdf
    dl = layout(song, **opts)
    write_pdf(dl, target)
    return dl


__all__ = ["parse", "layout", "render_pdf", "Layout", "DisplayList", "Song", "Section", "Bar", "Event", "THEMES"]
