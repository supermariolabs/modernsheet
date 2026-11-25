"""Data model: Song, Section, Bar, Event."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .musicxml import Notation

# =============================================================================
# Data model
# =============================================================================


NOTATIONS = ("staff", "both", "tab")     # notated bars: staff, staff + guitar tablature, tablature only
ROW_SPACINGS = {"compact": 0.75, "normal": 1.0, "wide": 1.3, "extra": 1.6}   # space between rows


def row_spacing_factor(value) -> float | None:
    """A row spacing as a factor of the normal one: a name (compact, normal, wide, extra), a percentage
    ("120%") or a number ("1.2"), between 0.5 and 3; None if not valid."""
    if isinstance(value, (int, float)):
        f = float(value)
    else:
        v = str(value).strip().lower()
        if v in ROW_SPACINGS:
            return ROW_SPACINGS[v]
        try:
            f = float(v[:-1]) / 100 if v.endswith("%") else float(v.replace(",", "."))
        except ValueError:
            return None
    return f if 0.5 <= f <= 3 else None


@dataclass
class Event:
    chord: str | None          # None = no new chord (continuation); "/" = stop
    start: float = 0.0         # beat offset inside the bar
    dur: float | None = None   # beats; None until resolved
    lyric: str = ""
    # rhythm marks and optional chords (inside the brackets: [<(C)~,, fermata], SPEC §2.4b)
    optional: bool = False     # printed in parentheses
    push: int = 0              # anticipation: 1 = an eighth early (<C), 2 = a sixteenth (<<C)
    tie: bool = False          # tied to the next chord (C~)
    strokes: int = 0           # rhythm slashes after the chord, one per comma (C,,,)
    fermata: bool = False
    diamond: bool = False      # let ring: diamond after the chord
    note: str = ""             # annotation: [A "1°"] → small text over the chord


@dataclass
class Bar:
    num: int
    den: int
    key: str
    events: list[Event] = field(default_factory=list)
    time_change: bool = False
    key_change: bool = False
    prev_key: str | None = None
    double_after: bool = False
    break_before: bool = False
    repeat_start: bool = False
    repeat_end: int = 0        # 0 = none, else total times played
    notation: "Notation | None" = None   # notated zone imported from MusicXML
    volta: str | None = None   # ending bracket starts here, label e.g. "1." or "1., 2."
    volta_end: str | None = None   # bracket ends here: "hook" (closed) or "open"
    marks_start: list[str] = field(default_factory=list)   # "segno" / "coda": signs at the start of the bar
    marks_end: list[tuple[str, str]] = field(default_factory=list)   # ("to_coda" | "fine" | "dc" | "ds", text)
    text_before: list[str] = field(default_factory=list)   # {text: …} lines shown above this bar's row

    @property
    def beats(self) -> float:
        return self.num * 4 / self.den

    @property
    def has_chord(self) -> bool:
        return any(e.chord for e in self.events)


@dataclass
class Section:
    kind: str
    label: str
    key: str
    bars: list[Bar] = field(default_factory=list)
    bars_per_line: int | None = None
    bar_width: str | None = None       # "uniform" | "fit": {bar_width} inside the section (else the song's)
    notation: str | None = None        # "staff" | "both" | "tab": {notation} inside the section (else the song's)
    text_after: list[str] = field(default_factory=list)    # {text: …} lines after the last row
    note: str = ""
    is_ref: bool = False
    ref_label: str = ""              # a {ref}: the label of the section it repeats (it may show another one)
    short: bool = False              # a {ref … short}: just the box (no bars: they are printed further up)
    ref_key: str = ""                # a short {ref} in another key than the original: that key
    times: int = 1


@dataclass
class Song:
    meta: dict = field(default_factory=dict)
    sections: list[Section] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    format: int = 1            # .chs format the file declares ({format: vN}; 1 if missing)
    tags: list[str] = field(default_factory=list)   # {tags: a, b}: lowercase, no duplicates

    @property
    def bars(self) -> list[Bar]:
        return [b for s in self.sections for b in s.bars]

