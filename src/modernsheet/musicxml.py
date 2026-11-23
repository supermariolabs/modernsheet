"""MusicXML reader for notated zones (notes, chord symbols, lyrics, tuplets, repeats, endings)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .theory import *  # noqa: F401,F403

# =============================================================================
# MusicXML (notated zones)
# =============================================================================

STEPS = "CDEFGAB"
STEP_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
NOTE_TYPES = {"whole": 4.0, "half": 2.0, "quarter": 1.0, "eighth": 0.5, "16th": 0.25, "32nd": 0.125}
HARMONY_KINDS = {
    "major": "", "minor": "m", "augmented": "aug", "diminished": "dim", "dominant": "7",
    "major-seventh": "maj7", "minor-seventh": "m7", "diminished-seventh": "dim7",
    "augmented-seventh": "aug7", "half-diminished": "m7b5", "major-minor": "m(maj7)",
    "major-sixth": "6", "minor-sixth": "m6", "dominant-ninth": "9", "major-ninth": "maj9",
    "minor-ninth": "m9", "dominant-11th": "11", "major-11th": "maj11", "minor-11th": "m11",
    "dominant-13th": "13", "major-13th": "maj13", "minor-13th": "m13",
    "suspended-second": "sus2", "suspended-fourth": "sus4", "power": "5", "none": "N.C.",
}


@dataclass
class Note:
    step: str | None            # None = rest
    alter: int = 0
    octave: int = 4
    start: float = 0.0          # quarters from bar start
    dur: float = 1.0            # quarters
    type: str = "quarter"
    dots: int = 0
    chord: bool = False         # stacked on the previous note's stem
    tie_start: bool = False
    tie_stop: bool = False
    beams: dict = field(default_factory=dict)   # {1: 'begin'|'continue'|'end'|'forward hook'|'backward hook', 2: ...}
    lyric: str = ""
    measure_rest: bool = False
    tuplet: tuple | None = None   # (actual, normal), e.g. (3, 2) for a triplet
    tuplet_start: bool = False
    tuplet_stop: bool = False

    @property
    def diatonic(self) -> int:
        return self.octave * 7 + STEPS.index(self.step)

    @property
    def midi(self) -> int:
        return 12 * (self.octave + 1) + STEP_PC[self.step] + self.alter


@dataclass
class Notation:
    notes: list[Note]
    source: str = ""


def _text(el, path, default=None):
    found = el.find(path)
    return found.text.strip() if found is not None and found.text else default


def read_musicxml(path: Path, text: str | None = None) -> tuple[list[dict], list[str]]:
    """Read the first part of a MusicXML (.musicxml/.xml) or compressed (.mxl) file.
    `text`: the file's content, if already in memory (e.g. unsaved in the app's editor).
    Returns one dict per measure: {notes, harmonies [(start, chord)], beats, beat_type, fifths}."""
    import xml.etree.ElementTree as ET
    import zipfile
    warnings: list[str] = []
    if text is not None:
        root = ET.fromstring(text)
    elif path.suffix.lower() == ".mxl":
        with zipfile.ZipFile(path) as z:
            container = ET.fromstring(z.read("META-INF/container.xml"))
            root_file = container.find(".//rootfile").get("full-path")
            root = ET.fromstring(z.read(root_file))
    else:
        root = ET.parse(path).getroot()
    if root.tag != "score-partwise":
        raise ValueError("only partwise MusicXML is supported")
    part = root.find("part")
    divisions, beats, beat_type, fifths = 1, 4, 4, 0
    measures = []
    for m in part.findall("measure"):
        attrs = m.find("attributes")
        if attrs is not None:
            divisions = int(_text(attrs, "divisions", divisions))
            if attrs.find("key") is not None:
                fifths = int(_text(attrs, "key/fifths", fifths))
            if attrs.find("time") is not None:
                beats, beat_type = int(_text(attrs, "time/beats", beats)), int(_text(attrs, "time/beat-type", beat_type))
        t, last_start = 0.0, 0.0
        notes, harmonies = [], []
        repeat_start, repeat_end, volta, volta_end = False, 0, None, None
        double_bar = False
        for el in m:
            if el.tag == "harmony":
                step = _text(el, "root/root-step")
                if step is None:
                    continue
                alter = int(float(_text(el, "root/root-alter", "0")))
                kind_el = el.find("kind")
                kind = kind_el.text.strip() if kind_el is not None and kind_el.text else "major"
                suffix = HARMONY_KINDS.get(kind)
                if suffix is None:
                    suffix = kind_el.get("text", "") if kind_el is not None else ""
                for deg in el.findall("degree"):
                    val, alt = _text(deg, "degree-value"), int(_text(deg, "degree-alter", "0"))
                    suffix += {-1: "b", 1: "#"}.get(alt, "add" if _text(deg, "degree-type") == "add" else "") + (val or "")
                name = step + {-1: "b", 1: "#"}.get(alter, "") + suffix
                bass = _text(el, "bass/bass-step")
                if bass:
                    name += "/" + bass + {-1: "b", 1: "#"}.get(int(float(_text(el, "bass/bass-alter", "0"))), "")
                off = int(_text(el, "offset", "0")) / divisions
                harmonies.append((t + off, name))
            elif el.tag == "note":
                if el.find("grace") is not None or _text(el, "voice", "1") != "1":
                    continue
                dur = int(_text(el, "duration", "0")) / divisions
                is_chord = el.find("chord") is not None
                start = last_start if is_chord else t
                rest = el.find("rest")
                n = Note(step=None if rest is not None else _text(el, "pitch/step"), start=start, dur=dur,
                         chord=is_chord)
                if rest is None:
                    n.alter = int(float(_text(el, "pitch/alter", "0")))
                    n.octave = int(_text(el, "pitch/octave", "4"))
                else:
                    n.measure_rest = rest.get("measure") == "yes"
                n.type = _text(el, "type") or ("whole" if n.measure_rest else "quarter")
                n.dots = len(el.findall("dot"))
                for tie in el.findall("tie"):
                    n.tie_start |= tie.get("type") == "start"
                    n.tie_stop |= tie.get("type") == "stop"
                for b in el.findall("beam"):
                    n.beams[int(b.get("number", "1"))] = b.text.strip()
                tm = el.find("time-modification")
                if tm is not None:
                    n.tuplet = (int(_text(tm, "actual-notes", "3")), int(_text(tm, "normal-notes", "2")))
                for tp in el.findall("notations/tuplet"):
                    n.tuplet_start |= tp.get("type") == "start"
                    n.tuplet_stop |= tp.get("type") == "stop"
                lyr = el.find("lyric")
                if lyr is not None and _text(lyr, "text"):
                    syl = _text(lyr, "syllabic", "single")
                    n.lyric = _text(lyr, "text") + ("-" if syl in ("begin", "middle") else "")
                notes.append(n)
                if not is_chord:
                    last_start = t
                    t += dur
            elif el.tag == "barline":
                rep_el, end_el = el.find("repeat"), el.find("ending")
                if el.get("location", "right") == "right" and _text(el, "bar-style") in ("light-light", "light-heavy", "heavy-heavy"):
                    double_bar = True
                if rep_el is not None:
                    if rep_el.get("direction") == "forward":
                        repeat_start = True
                    else:
                        repeat_end = int(rep_el.get("times", "2"))
                if end_el is not None:
                    kind = end_el.get("type")
                    if kind == "start":
                        nums = [x.strip() for x in end_el.get("number", "1").replace(" ", "").split(",") if x.strip()]
                        volta = ", ".join(f"{x}." for x in nums)
                    elif kind in ("stop", "discontinue"):
                        volta_end = "hook" if kind == "stop" else "open"
            elif el.tag == "backup":
                t -= int(_text(el, "duration", "0")) / divisions
            elif el.tag == "forward":
                t += int(_text(el, "duration", "0")) / divisions
        measures.append(dict(notes=notes, harmonies=sorted(harmonies), beats=beats, beat_type=beat_type,
                             fifths=fifths, length=t, number=m.get("number"), repeat_start=repeat_start,
                             repeat_end=repeat_end, volta=volta, volta_end=volta_end, double_bar=double_bar))
    return measures, warnings


def transpose_notes(notes: list[Note], semis: int, key: str) -> None:
    """Transpose in place, spelling pitches with the target key's note names."""
    if semis % 12 == 0:
        return
    names = spelling_for(key)
    for n in notes:
        if n.step is None:
            continue
        midi = n.midi + semis
        name = names[midi % 12]
        n.step, n.alter = name[0], {"": 0, "b": -1, "#": 1}[name[1:]]
        n.octave = (midi - STEP_PC[n.step] - n.alter) // 12 - 1

