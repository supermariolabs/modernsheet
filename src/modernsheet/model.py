"""Data model: Song, Section, Bar, Event."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .musicxml import Notation

# =============================================================================
# Data model
# =============================================================================


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
    text_after: list[str] = field(default_factory=list)    # {text: …} lines after the last row
    note: str = ""
    is_ref: bool = False
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

