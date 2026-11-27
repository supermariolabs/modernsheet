"""Parser for the .chs format, version 1 ({format: v1}, also files without {format}) → Song model.

Frozen once a later format exists: a breaking change of the syntax goes into a new module (v2.py…)
registered in formats/__init__.py, so that v1 files keep their meaning. Additive changes (a new
directive) may still land here.
"""
from __future__ import annotations

import copy
import dataclasses
import re
from datetime import datetime
from fractions import Fraction
from pathlib import Path

from ..theory import *  # noqa: F401,F403
from ..model import *  # noqa: F401,F403
from ..musicxml import *  # noqa: F401,F403
from .. import notes as notes_mod
from .. import tab as tab_mod

# =============================================================================
# Parser
# =============================================================================

TOKEN_RE = re.compile(
    r"\|:"                       # repeat start
    # repeat end, optional count: only at the start, after a space, a chord, a bar line or a directive;
    # glued to a word ("Dico:|") the colon is part of the lyrics and the | a plain bar line
    r"|(?<![^\s\]|}]):\|(?:\s*x\d+)?"
    r"|\|\|"                     # double bar
    r"|\|"                       # bar
    r"|\{[^}]*\}"                # inline directive
    r"|\[[^\]]*\]"               # chord
    r"|[^\[\]{}|:]+|:"           # lyrics
)
DIRECTIVE_LINE_RE = re.compile(r"^\{([^}]*)\}$")
META_KEYS = {"title", "subtitle", "artist", "composer", "tempo", "capo", "bar_width", "row_spacing", "label_colors",
             "section_colors"}
# directives that describe the whole song: they belong in the header, before the first section
SONG_ONLY = {"title", "subtitle", "artist", "composer", "tempo", "capo", "row_spacing", "label_colors",
             "section_colors", "tuning"}
HALF = 0.5
START_MARKS = ("segno", "coda")                  # signs at the start of the next bar
END_MARKS = ("to_coda", "fine", "dc", "ds")      # instructions at the end of the current bar


def split_tags(value: str) -> list[str]:
    """Tags of a {tags: …} value: comma separated, lowercase, inner spaces collapsed, no empties."""
    return [t for t in (" ".join(x.split()).lower() for x in value.split(",")) if t]


def add_tags(tags: list[str], value: str) -> None:
    for t in split_tags(value):
        if t not in tags:
            tags.append(t)


STAMP_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?")


def parse_stamp(value: str) -> datetime | None:
    """A {created}/{modified} value: "YYYY-MM-DD HH:MM:SS" (local time; also without seconds, date alone, "T")."""
    m = STAMP_RE.fullmatch(value.strip())
    if not m:
        return None
    y, mo, d, h, mi, sec = (int(x) if x else 0 for x in m.groups())
    try:
        return datetime(y, mo, d, h, mi, sec)
    except ValueError:
        return None


def format_stamp(when: datetime) -> str:
    return when.strftime("%Y-%m-%d %H:%M:%S")


# Escapes (SPEC §2.1, §9b point 5): \| \[ \] \{ \} \" \\ \# write the character itself in lyrics, {text}/{c},
# annotations and names. Each line is read with these sequences swapped for private-use characters,
# which the grammar treats as plain text; unescape() puts the characters back in the finished song.
ESCAPABLE = '|[]{}"\\#'
_ESC = {ch: chr(0xE100 + i) for i, ch in enumerate(ESCAPABLE)}
_UNESC = {v: k for k, v in _ESC.items()}


def escape_line(line: str) -> str:
    """The line with every backslash + escapable character replaced by its placeholder."""
    return re.sub(r"\\(.)", lambda m: _ESC.get(m.group(1), m.group(0)), line)


def unescape(text: str) -> str:
    """Placeholders back to the characters they stand for."""
    return "".join(_UNESC.get(c, c) for c in text) if text else text


def split_directive(body: str) -> tuple[str, str]:
    name, _, value = body.partition(":")
    return name.strip().lower(), value.strip()


class Parser:
    def __init__(self, text: str, transpose: int = 0, base_dir: Path | None = None,
                 files: dict[Path, str] | None = None):
        self.text = text
        self.base_dir = base_dir or Path(".")
        self.files = {Path(p).resolve(): t for p, t in (files or {}).items()}   # in-memory MusicXML
        self.transpose = transpose
        self.song = Song()
        self.key = "C"
        self.num, self.den = 4, 4
        self.bpl: int | None = None
        self.section: Section | None = None
        self.pending: dict = {}
        self.open_volta = False
        self.open_volta_label = None
        self.lineno = 0
        self.text_pending: list[str] = []        # {text: …} waiting for the next bar of the section
        self.notes: notes_mod.NoteReader | None = None   # inside {start_of_notes} … {end_of_notes}
        self.notes_row: list[Bar] = []           # bars of the last row of notes (for its w: line)
        self.tab_pos: int | None = None          # {tab_position: N}: hand position for the tablature
        # {bar_width} / {notation} written between sections: they hold "from here on", for the sections
        # that follow (in the header they are the song's, inside a section that section's only)
        self.running: dict[str, str | None] = {"bar_width": None, "notation": None}

    # -- helpers ---------------------------------------------------------------
    def warn(self, msg: str) -> None:
        self.song.warnings.append(f"line {self.lineno}: {msg}")

    def set_key(self, value: str) -> str:
        """The key in force after `{key: value}`, already transposed (an invalid key: unchanged)."""
        try:
            parse_key(value)
        except ValueError as e:
            self.warn(str(e))
            return self.key
        return transpose_key(value, self.transpose)

    def close_volta(self, how: str) -> None:
        """Close an open ending bracket on the last bar written. A later ending (2nd, 3rd…)
        that does not repeat back ends the repeated structure: it gets a double bar line."""
        if self.open_volta and self.song.bars:
            last = self.song.bars[-1]
            if not last.volta_end:
                last.volta_end = how
            if self.open_volta_label and not self.open_volta_label.startswith("1.") and not last.repeat_end:
                last.double_after = True
        self.open_volta = False
        self.open_volta_label = None

    def push_bar(self, bar: Bar) -> None:
        """Append a finished bar to the current section, applying what directives left pending for
        "the next bar" (time and key changes, {br}, repeat start, ending, start marks, {text} lines).
        Directives are read before the bar they affect exists, hence this queue."""
        if self.pending.pop("time", False):
            bar.time_change = True
        if "key" in self.pending:
            prev = self.pending.pop("key")
            if prev != bar.key:
                bar.key_change, bar.prev_key = True, prev
                if self.song.bars:                   # engraving convention: a double bar before a new key
                    self.song.bars[-1].double_after = True
        if self.pending.pop("br", False):
            bar.break_before = True
        if self.pending.pop("repeat_start", False):
            bar.repeat_start = True
        if "volta" in self.pending:
            bar.volta = self.pending.pop("volta")
            self.open_volta = True
            self.open_volta_label = bar.volta
        bar.marks_start += self.pending.pop("marks", [])
        if self.text_pending:
            bar.text_before, self.text_pending = self.text_pending, []
            bar.break_before = True                  # text lines sit between rows
        if not self.section.bars:
            # the section's key is the key of its first bar: a {key} written inside the section, before
            # its music, counts. {ref} transposes from it (it was the key when the section opened, so a
            # chorus with {key: A} inside it was transposed from the key before, by the wrong interval)
            self.section.key = bar.key
        self.section.bars.append(bar)

    def new_bar(self) -> Bar:
        return Bar(self.num, self.den, self.key)

    CHORD_WORDS = {"fermata": "fermata", "diamond": "diamond", "<>": "diamond", "~": "tie", "tie": "tie"}

    def event(self, raw: str) -> Event:
        """A chord token's inside: [<<(Name):dur~,,, fermata diamond "note"] → Event with its marks."""
        note = ""
        m = re.search(r'"([^"]*)"?', raw)                 # an annotation, possibly with spaces
        if m:
            note, raw = " ".join(m.group(1).split()), raw[:m.start()] + " " + raw[m.end():]
        words = raw.split()
        head, marks = (words[0] if words else ""), {}
        for w in words[1:]:
            if w.lower() in self.CHORD_WORDS:
                marks[self.CHORD_WORDS[w.lower()]] = True
            else:
                self.warn(f"unknown chord mark '{w}' (fermata, diamond, <>, ~)")
        push = len(head) - len(head.lstrip("<"))
        if push > 2:
            self.warn(f"'{head}': at most two '<' (an eighth or a sixteenth early)")
        head = head.lstrip("<")
        name, colon, dur = head.partition(":")
        tail = ""                                  # trailing ~ and commas: after the duration, the name,

        def strip_tail(s: str) -> str:             # or inside the parentheses of an optional chord
            nonlocal tail
            while s and s[-1] in "~,":
                tail, s = s[-1] + tail, s[:-1]
            return s
        dur, name = strip_tail(dur), strip_tail(name)
        optional = False
        if name.endswith("?"):
            optional, name = True, strip_tail(name[:-1])
        if len(name) > 2 and name.startswith("(") and name.endswith(")") and name.count("(") == name.count(")"):
            optional, name = True, strip_tail(name[1:-1]).removesuffix("?")
        chord, d = self.chord(name + colon + dur)
        return Event(chord, dur=d, optional=optional, push=min(push, 2), tie="~" in tail or "tie" in marks,
                     strokes=tail.count(","), fermata="fermata" in marks, diamond="diamond" in marks, note=note)

    def chord(self, raw: str) -> tuple[str, float | None]:
        """`Name:duration` → (transposed chord or None for %, duration in quarters or None). The
        duration is written in notes of the time signature's denominator, multiples of half of one
        (the grid cannot place anything finer): [C:3] in 6/8 = three eighths (SPEC §2.4)."""
        name, _, dur = raw.partition(":")
        name = name.strip()
        d = None
        if dur.strip():
            try:
                d = float(dur)
                if d <= 0 or (d * 2) % 1:
                    self.warn(f"duration '{dur}' must be a positive multiple of 0.5")
                    d = max(HALF, round(d * 2) / 2)
                # written in notes of the time signature's denominator (quarters in 4/4, eighths in 6/8,
                # halves in 2/2: SPEC §2.4, §9b point 3); the engine counts in quarters
                d = d * 4 / self.den
            except ValueError:
                self.warn(f"invalid duration '{dur}'")
        if name not in ("/", "%") and not CHORD_RE.match(name):
            self.warn(f"unrecognised chord '{name}'")
        if name == "%":
            name = None
        return transpose_chord(name, self.transpose, self.key) if name else None, d

    # -- directives ------------------------------------------------------------
    def directive(self, body: str) -> None:
        """Apply one `{name: value}`. A {key} or {time} before the first bar is the song's (header);
        once a bar exists it is always a change, attached to the next bar (pending), even in a song
        without a header (the bars before it are then in C, 4/4, which becomes the song's).
        Layout directives ({bar_width}, {notation}, {bars_per_line}): in the header the whole song's,
        between sections from there on, inside a section that section's only (SPEC §2.10, §9b).
        Song-wide directives (SONG_ONLY) after the first section still apply, with a warning."""
        name, value = split_directive(body)
        if name in SONG_ONLY and self.song.sections:
            self.warn(f"{{{name}}} applies to the whole song: write it in the header, before the first section")
        if name == "key":
            new = self.set_key(value)
            if "key" not in self.song.meta and not self.song.bars:
                self.song.meta["key"] = new
            else:
                self.song.meta.setdefault("key", self.key)   # no header: the song starts in the key so far
                # setdefault: two {key} lines before the next bar are one change, from the first key
                self.pending.setdefault("key", self.key)
            self.key = new
        elif name == "time":
            m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", value)
            if not m:
                self.warn(f"invalid time signature '{value}'")
                return
            if "time" not in self.song.meta and not self.song.bars:
                self.num, self.den = int(m.group(1)), int(m.group(2))
                self.song.meta["time"] = f"{self.num}/{self.den}"
            else:
                self.song.meta.setdefault("time", f"{self.num}/{self.den}")   # no header: the time so far
                self.num, self.den = int(m.group(1)), int(m.group(2))
                self.pending["time"] = True
        elif name == "bars_per_line":
            n = int(value) if value.isdigit() else None
            if self.section is not None:
                self.section.bars_per_line = n
            else:
                self.bpl = n
        elif name == "tuning":
            if tab_mod.parse_tuning(value) is None:
                self.warn(f"tuning '{value}': expected a name (standard, drop D, DADGAD, open G, open D, open E, "
                          "half step down, bass, ukulele) or the open strings (D A D G B E)")
            else:
                self.song.meta["tuning"] = value
        elif name == "tab_position":
            v = value.strip().lower()
            if v in ("", "auto"):
                self.tab_pos = None
            elif v.isdigit() and 0 <= int(v) <= 20:
                self.tab_pos = int(v)
            else:
                self.warn(f"tab_position '{value}': expected a fret (0-20) or auto")
            if self.notes is not None:
                self.notes.tab_pos = self.tab_pos
        elif name == "notation":
            mode = value.strip().lower()
            if mode not in NOTATIONS:
                self.warn(f"notation '{value}': expected staff, both or tab")
            elif self.section is not None:
                self.section.notation = mode        # this section only
            elif self.song.sections:
                self.running["notation"] = mode     # between sections: from here on
            else:
                self.song.meta["notation"] = mode   # header: the whole song
        elif name == "bar_width" and (self.section is not None or self.song.sections):
            mode = value.strip().lower()
            if mode not in ("uniform", "fit"):
                self.warn(f"bar_width '{value}': expected uniform or fit")
            elif self.section is not None:
                self.section.bar_width = mode       # this section only (in the header: the whole song, META_KEYS)
            else:
                self.running["bar_width"] = mode    # between sections: from here on
        elif name == "br":
            self.pending["br"] = True
        elif name == "volta":
            self.close_volta("open")
            nums = [x.strip().rstrip(".") for x in value.split(",") if x.strip()] or ["1"]
            self.pending["volta"] = ", ".join(f"{x}." for x in nums)
        elif name == "volta_end":
            how = value.strip().lower()
            if how in ("closed", "chiusa"):          # synonyms of earlier versions: English only now (§9b point 6)
                self.warn(f"volta_end '{value.strip()}': write {{volta_end: hook}}")
            elif how not in ("", "hook"):
                self.warn(f"volta_end '{value.strip()}': expected hook (closed bracket) or nothing (open)")
            self.close_volta("hook" if how in ("hook", "closed", "chiusa") else "open")
        elif name == "row_spacing" and row_spacing_factor(value) is None:
            self.warn(f"row_spacing '{value}': expected compact, normal, wide, extra or a percentage (50%-300%)")
        elif name in META_KEYS:
            self.song.meta[name] = value
        elif name == "start_of_notes":
            self.start_notes()
        elif name == "end_of_notes":
            if self.notes is None:
                self.warn("{end_of_notes} without {start_of_notes}")
            self.end_notes()
        elif name.startswith("start_of_"):
            self.start_section(name[9:], value)
        elif name.startswith("end_of_"):
            if self.notes is not None:
                self.warn("{start_of_notes} not closed before the end of the section")
                self.end_notes()
            self.close_volta("open")
            if self.section is not None and self.text_pending:
                self.section.text_after += self.text_pending
            self.text_pending = []
            if self.pending.get("marks"):
                self.warn(f"{{{self.pending['marks'][-1]}}} at the end of a section: no bar follows it")
                self.pending.pop("marks")
            if self.section is None or self.section.kind != name[7:]:
                self.warn(f"{{{name}}} without matching start")
            self.section = None
        elif name == "tags":
            add_tags(self.song.tags, value)
        elif name in START_MARKS:
            self.pending.setdefault("marks", []).append(name)
        elif name in END_MARKS:
            self.end_mark(name, value, self.song.bars[-1] if self.song.bars else None)
        elif name in ("text", "comment", "c"):        # {comment}/{c}: printed, as in ChordPro (hidden: #)
            if self.section is None:
                self.warn("{text} outside a section: ignored")
            elif value:
                self.text_pending.append(value)
        elif name in ("created", "modified"):
            if parse_stamp(value) is None:
                self.warn(f"{{{name}}}: invalid date '{value}' (expected YYYY-MM-DD HH:MM:SS)")
            else:
                self.song.meta[name] = value
        elif name == "ref":
            self.reference(value)
        elif name == "musicxml":
            self.musicxml(value)
        elif name == "format":
            pass                          # format: read by formats.detect() before parsing
        else:
            self.warn(f"unknown directive '{name}'")

    def end_mark(self, name: str, value: str, bar: Bar | None) -> None:
        """{to_coda}, {fine}, {dc: …}, {ds: …} go at the end of `bar` (the bar they are written in, or
        the last one written). {fine} also gets a double bar line."""
        if bar is None:
            self.warn(f"{{{name}}} before any bar: ignored")
            return
        bar.marks_end.append((name, value))
        if name == "fine" and not bar.repeat_end:
            bar.double_after = True

    def start_section(self, kind: str, label: str) -> None:
        """Open a section ({start_of_KIND: label}); the label defaults to the kind ("Verse")."""
        self.tab_pos = None                      # a hand position lasts until the end of its section
        if self.section is not None:
            self.warn(f"section '{self.section.label}' not closed before '{kind}'")
        self.section = Section(kind=kind, label=label or kind.replace("_", " ").capitalize(),
                               key=self.key, bars_per_line=self.bpl, bar_width=self.running["bar_width"],
                               notation=self.running["notation"])
        self.song.sections.append(self.section)

    def reference(self, value: str) -> None:
        """{ref: Label} / {ref: Label x2 $volta 2 = New label | note}: repeat an earlier section here, as
        copies of its bars, optionally shown under another label (`= …`; the colour stays the original's).
        `$volta N`: the section played once straight to its ending N (see ending_pass).
        `$once`: the section without any repeat, each repeated part played once (see once_pass).
        `$short`: only the section's box (label, xN, note) and no bars, to save room on the page; if the
        key has changed since the original, the box says the new key, since no bar shows it.

        The copy is transposed from the original's key to the key in force here, so a chorus
        recalled after a key change is printed in the new key. Signs, marks and {text} lines stay
        with the original (repeating "D.S. al Coda" in the copy would be wrong), and the copy's first
        bar does not repeat the original's time/key change or line break."""
        target, _, note = value.partition("|")
        target, _, shown = target.partition("=")
        target, note, shown = target.strip(), note.strip(), shown.strip()
        whole = " ".join(value.split())
        labels = {s.label.lower() for s in self.song.sections if not s.is_ref}
        named = whole.lower() in labels
        if named:
            # the whole text is a section's name ("Strofa x2", "Do = La", "A | B"): no options in it
            target, note, shown = whole, "", ""
        times, volta, once, short = 1, None, False, False
        # options after the label, in any order: xN, $volta N, $once, $short. The $ tells them apart from
        # the words of a label: {ref: Prima volta 2} is the section "Prima volta 2"
        while not named and target.lower() not in labels:    # stop at a section's name ("Strofa x2" x2)
            m = re.search(r"\s+(?:x(\d+)|\$volta\s*(\d+)\.?|\$(once)|\$(short))\s*$", target, re.I)
            if not m:
                break
            if m.group(1):
                times = int(m.group(1))
            elif m.group(2):
                volta = int(m.group(2))
            elif m.group(3):
                once = True
            else:
                short = True
            target = target[: m.start()].strip()
        originals = [s for s in self.song.sections if not s.is_ref]
        src = next((s for s in originals if s.label.lower() == target.lower()), None) or \
            next((s for s in originals if s.kind == target.lower()), None)
        if src is None:
            # the options of 0.45.0-0.46.0 were written without $: say how to write them now
            words, rest = [], target
            while (m := re.search(r"\s+(x\d+|volta\s*\d+\.?|once|short)\s*$", rest, re.I)):
                words.insert(0, " ".join(m.group(1).lower().rstrip(".").split()))
                rest = rest[: m.start()].strip()
            old = [w for w in words if not w.startswith("x")]
            if old and (rest.lower() in labels or any(s.kind == rest.lower() for s in originals)):
                written = ", ".join(f"'{w}'" for w in old)
                wanted = " ".join(w if w.startswith("x") else f"${w}" for w in words)
                tail = (f" = {shown}" if shown else "") + (f" | {note}" if note else "")
                self.warn(f"ref: {written} is an old syntax, now written with $: {{ref: {rest} {wanted}{tail}}}")
                return
            self.warn(f"ref: section '{target}' not found (only earlier sections can be referenced)")
            return
        bars = src.bars
        if once:
            bars, found = self.once_pass(src.bars, volta)
            if volta is not None and not found:
                self.warn(f"ref: section '{src.label}' has no ending {volta}: the last ending of each repeat")
        elif volta is not None:
            bars = self.ending_pass(src.bars, volta)
            if bars is None:
                self.warn(f"ref: section '{src.label}' has no ending {volta}: copied whole")
                bars = src.bars
        semis = semitones_between(src.key, self.key)
        sec = Section(kind=src.kind, label=shown or src.label, key=self.key, note=note, is_ref=True,
                      ref_label=src.label,
                      times=times, bars_per_line=src.bars_per_line or self.bpl, bar_width=src.bar_width,
                      notation=src.notation)
        self.song.sections.append(sec)
        if short:
            # no bars: a pending key/time change stays for the next bar written (that is where it is seen)
            sec.short = True
            sec.ref_key = self.key if semis % 12 else ""
            return
        outer, self.section = self.section, sec
        for _ in range(times):
            for b in bars:
                nb = b if (once or volta is not None) and bars is not src.bars else copy.deepcopy(b)
                nb.key = transpose_key(b.key, semis)
                nb.marks_start, nb.marks_end, nb.text_before = [], [], []   # signs and notes stay with the original
                nb.prev_key = transpose_key(b.prev_key, semis) if b.prev_key else None
                nb.double_after = b.double_after
                if b is bars[0]:
                    nb.time_change = nb.key_change = nb.break_before = False
                for e in nb.events:
                    e.chord = transpose_chord(e.chord, semis, nb.key)
                if nb.notation:
                    transpose_notes(nb.notation.notes, semis, nb.key)
                self.push_bar(nb)
        self.section = outer

    @staticmethod
    def ending_pass(bars: list[Bar], n: int) -> list[Bar] | None:
        """Copies of the bars of one pass through a section that goes straight to its ending n: the
        bars of the other endings are left out, and the repeat that held the endings is gone (no
        repeat start before them, no repeat end, no ending brackets), so the copy reads straight
        through. Repeats elsewhere in the section stay. None if the section has no ending n."""
        current: set[int] | None = None        # endings of the bracket the bar is in
        member: list[set[int] | None] = []
        for b in bars:
            if b.volta:
                current = {int(x) for x in re.findall(r"\d+", b.volta)}
            member.append(current)
            if b.volta_end or (current is not None and b.repeat_end):
                current = None
        if not any(m and n in m for m in member):
            return None
        first = next(i for i, m in enumerate(member) if m is not None)
        start = max((i for i in range(first + 1) if bars[i].repeat_start), default=None)
        out = []
        for i, (b, m) in enumerate(zip(bars, member)):
            if m is not None and n not in m:
                continue
            nb = copy.deepcopy(b)
            if m is not None:
                nb.volta = nb.volta_end = None
                nb.repeat_end = 0
            if i == start:
                nb.repeat_start = False
            out.append(nb)
        return out

    @staticmethod
    def once_pass(bars: list[Bar], n: int | None = None) -> tuple[list[Bar], bool]:
        """Copies of the bars of a section played once, without any repeat: repeat signs and ending
        brackets are dropped, and of each group of endings only one is kept: ending n if the group has
        it, else its last one (the ending that leaves the repeat). Returns the bars and whether ending
        n was found."""
        groups: list[int | None] = []          # per bar: index of its ending bracket, or None
        labels: list[set[int]] = []
        current: int | None = None
        for b in bars:
            if b.volta:
                labels.append({int(x) for x in re.findall(r"\d+", b.volta)})
                current = len(labels) - 1
            groups.append(current)
            if b.volta_end or (current is not None and b.repeat_end):
                current = None
        # consecutive brackets (no bar outside an ending between them) belong to the same repeat
        block_of: list[int] = []
        block = -1
        for i in range(len(labels)):
            first = groups.index(i)
            if i == 0 or groups[first - 1] is None:
                block += 1
            block_of.append(block)
        keep: set[int] = set()
        found = False
        for blk in set(block_of):
            members = [i for i in range(len(labels)) if block_of[i] == blk]
            chosen = next((i for i in members if n is not None and n in labels[i]), None)
            found = found or chosen is not None
            keep.add(chosen if chosen is not None else max(members, key=lambda i: max(labels[i])))
        out = []
        for b, g in zip(bars, groups):
            if g is not None and g not in keep:
                continue
            nb = copy.deepcopy(b)
            nb.repeat_start, nb.repeat_end, nb.volta, nb.volta_end = False, 0, None, None
            out.append(nb)
        return out, found

    def musicxml(self, value: str) -> None:
        """{musicxml: file.musicxml} or {musicxml: file.musicxml | 3-6}: notated bars from MusicXML."""
        file, _, opts = value.partition("|")
        path = (self.base_dir / file.strip()).resolve()
        try:
            measures, _ = read_musicxml(path, self.files.get(path))
        except Exception as e:                      # missing file, bad XML…
            self.warn(f"musicxml '{file.strip()}': {e}")
            return
        measures = measure_range(measures, opts)
        if self.section is None:
            self.warn("musicxml outside a section: opening an untitled one")
            self.start_section("instrumental", "")
        # the file is written in the song's own key: compare its key signature with the key before
        # transposition (the parser's self.key is already transposed)
        original_key = transpose_key(self.key, -self.transpose)
        for i, ms in enumerate(measures):
            if (ms["beats"], ms["beat_type"]) != (self.num, self.den):
                if "time" not in self.song.meta and not self.song.bars:
                    self.num, self.den = ms["beats"], ms["beat_type"]
                    self.song.meta["time"] = f"{self.num}/{self.den}"
                else:
                    self.song.meta.setdefault("time", f"{self.num}/{self.den}")
                    self.num, self.den = ms["beats"], ms["beat_type"]
                    self.pending["time"] = True
            if i == 0 and ms["fifths"] != key_signature(original_key):
                self.warn(f"musicxml '{file.strip()}': key signature ({ms['fifths']:+d}) differs from {{key: {original_key}}}")
            bar = self.new_bar()
            if abs(ms["length"] - bar.beats) > 1e-6:
                self.warn(f"musicxml measure {ms['number']}: {ms['length']:g} beats in {bar.num}/{bar.den}")
            notes = copy.deepcopy(ms["notes"])
            for n in notes:
                n.tab_pos = self.tab_pos
            transpose_notes(notes, self.transpose, self.key)
            bar.notation = Notation(notes, path.name)
            if ms["repeat_start"]:
                self.pending["repeat_start"] = True
            if ms["volta"]:
                self.pending["volta"] = ms["volta"]
            harm = [(t, transpose_chord(ch, self.transpose, self.key)) for t, ch in ms["harmonies"] if t < bar.beats]
            # chord symbols become the bar's events, each lasting until the next; if the first one is
            # not on beat 1, the bar starts with a "continuation" event (the previous chord goes on)
            if not harm or harm[0][0] > 0:
                harm.insert(0, (0.0, None))
            for j, (t, ch) in enumerate(harm):
                end = harm[j + 1][0] if j + 1 < len(harm) else bar.beats
                bar.events.append(Event(ch, t, end - t))
            self.push_bar(bar)
            bar.repeat_end = ms["repeat_end"]
            if ms["double_bar"] and not bar.repeat_end:
                bar.double_after = True
            if ms["volta_end"]:
                self.close_volta(ms["volta_end"])

    # -- notes written in the source (SPEC §2.12b) --------------------------------
    def start_notes(self) -> None:
        """{start_of_notes}: the following rows are notes (SPEC §2.12b), read by a NoteReader that
        keeps the current duration and octave from note to note until {end_of_notes}."""
        if self.notes is not None:
            self.warn("{start_of_notes} inside a notes block")
            return
        if self.section is None:
            self.warn("{start_of_notes} outside a section: opening an untitled one")
            self.start_section("instrumental", "")
        # notes are written in the source's key; accidentals are checked against it before transposing
        self.notes = notes_mod.NoteReader(transpose_key(self.key, -self.transpose), self.warn)
        self.notes.tab_pos = self.tab_pos
        self.notes_row = []

    def end_notes(self) -> None:
        if self.notes is not None:
            self.notes.end_block()
        self.notes, self.notes_row = None, []

    def notes_line(self, line: str) -> None:
        """One row of notated bars: bar lines and directives as in the explicit mode, chords before
        the note they sit on, notes and rests read by notes.NoteReader."""
        reader = self.notes
        notes: list[Note] = []
        chords: list[tuple[Fraction, Event]] = []
        t = Fraction(0)
        opened = False
        ends: list[tuple[str, str]] = []
        self.notes_row = []

        def close(force: bool) -> Bar | None:
            """Finish the bar read so far: notes → a notated bar whose chord symbols last from their
            note to the next symbol; only chords → an ordinary bar. `force`: make a bar even if empty."""
            nonlocal notes, chords, t
            reader.end_bar()
            if not (notes or chords or force):
                return None
            bar = self.new_bar()
            beats = Fraction(bar.num * 4, bar.den)
            if notes:
                if t != beats:
                    self.warn(f"notes bar {len(self.section.bars) + 1}: {float(t):g} beats in {bar.num}/{bar.den}")
                transpose_notes(notes, self.transpose, self.key)
                notes_mod.beam_bar(notes, bar.num, bar.den)
                bar.notation = Notation(notes, "notes")
                events = [ev for _, ev in chords]
                if not chords or chords[0][0] > 0:
                    events.insert(0, Event(None))
                    starts = [Fraction(0)] + [at for at, _ in chords]
                else:
                    starts = [at for at, _ in chords]
                for j, ev in enumerate(events):
                    end = starts[j + 1] if j + 1 < len(starts) else beats
                    ev.start, ev.dur = float(starts[j]), float(end - starts[j])
                bar.events = events
            else:                                   # chords only: an ordinary bar
                # (a bar of chords inside a notes block is drawn as a normal chord bar, so a riff
                # can end on bars of chords without closing the block)
                bar.events = [ev for _, ev in chords] or [Event(None)]
                self.resolve(bar)
            self.push_bar(bar)
            self.notes_row.append(bar)
            for name, value in ends:
                self.end_mark(name, value, bar)
            ends.clear()
            notes, chords, t = [], [], Fraction(0)
            return bar

        for tk in notes_mod.tokenize(line):
            if tk in ("|", "||", "|:") or tk.startswith(":|"):
                bar = close(force=opened and tk != "|:")
                opened = True
                last = bar or (self.section.bars[-1] if self.section.bars else None)
                if tk == "||" and last:
                    last.double_after = True
                elif tk == "|:":
                    self.pending["repeat_start"] = True
                elif tk.startswith(":|") and last:
                    m = re.search(r"x(\d+)", tk)
                    last.repeat_end = int(m.group(1)) if m else 2
                    self.close_volta("hook")
            elif tk.startswith("{"):
                name, value = split_directive(tk[1:-1])
                if name in END_MARKS and (notes or chords):
                    ends.append((name, value))
                else:
                    self.directive(tk[1:-1])
            elif tk.startswith("["):
                ev = self.event(tk[1:-1])
                if ev.dur is not None:
                    self.warn(f"'{tk}': no duration on chords between notes (they sit on the next note)")
                    ev.dur = None
                chords.append((t, ev))
            elif tk.endswith("(") and tk[0].isdigit():
                reader.open_tuplet(tk)
            elif tk == ")":
                reader.close_tuplet()
            else:
                beats = Fraction(self.num * 4, self.den)
                got = reader.read(tk, t, beats)
                if got:
                    notes += got[0]
                    t += got[1]
        if notes or chords:
            close(force=False)
        for name, value in ends:
            self.end_mark(name, value, self.song.bars[-1] if self.song.bars else None)
        # an ending goes on past the end of the line: it closes at :|, at the next {volta}, at
        # {volta_end} or at the end of the section (SPEC §2.7, §9b point 4)

    def notes_lyrics(self, text: str) -> None:
        """`w: …` under a row of notes: one syllable per note of the row just read (notes_row)."""
        bars = [b.notation.notes if b.notation else [] for b in self.notes_row]
        if not bars:
            self.warn("w: line without a row of notes before it")
            return
        notes_mod.assign_lyrics(bars, text, self.warn)

    # -- music lines -----------------------------------------------------------
    def resolve(self, bar: Bar) -> None:
        """Give every chord of a bar its start and duration: chords with `:n` keep it, the others
        share what is left equally, rounded down to half a note of the denominator, the last one
        taking the remainder ([C] [G] in 3/4 → 1.5 + 1.5; [C] [F] [G] in 4/4 → 1 + 1 + 2). Durations
        here are in quarters (the written ones were converted by chord())."""
        fixed = sum(e.dur for e in bar.events if e.dur is not None)
        free = [e for e in bar.events if e.dur is None]
        rest = bar.beats - fixed
        if rest < -1e-9:
            self.warn(f"bar too long: {fixed * bar.den / 4:g}/{bar.den} in {bar.num}/{bar.den}")   # in the written unit
            rest = 0
        if free:
            step = 2 / bar.den                    # half a note of the denominator, in quarters
            share = int(rest / len(free) / step + 1e-9) * step
            for e in free[:-1]:
                e.dur = share
            free[-1].dur = rest - share * (len(free) - 1)
        elif rest > 1e-9 and bar.events:
            bar.events[-1].dur += rest            # short explicit bar: last event fills it
        t = 0.0
        for e in bar.events:
            e.start, t = t, t + e.dur

    def explicit_line(self, tokens: list[str]) -> None:
        """A source line with bar lines: every `|` closes a bar with the chords and lyrics read since.
        Lyrics before the first chord of a bar (`lead`) belong to its first chord; directives right
        after a bar line apply to the next bar, end marks written inside a bar to that bar."""
        events: list[Event] = []
        lead = ""
        opened = False
        ends: list[tuple[str, str]] = []        # end marks written inside the bar being read

        def close(force: bool) -> Bar | None:
            nonlocal events, lead
            if not (events or lead.strip() or force):
                return None
            if not events:
                events = [Event(None)]
            if lead.strip():
                events[0].lyric = (lead.strip() + " " + events[0].lyric).strip()
            bar = self.new_bar()
            bar.events = events
            for e in events:
                e.lyric = e.lyric.strip()
            self.resolve(bar)
            self.push_bar(bar)
            for name, value in ends:
                self.end_mark(name, value, bar)
            events, lead = [], ""
            ends.clear()
            return bar

        for tk in tokens:
            if tk in ("|", "||", "|:") or tk.startswith(":|"):
                bar = close(force=opened and tk != "|:")    # "|:" only opens: never an empty bar before it
                opened = True
                last = bar or (self.section.bars[-1] if self.section.bars else None)
                if tk == "||" and last:
                    last.double_after = True
                elif tk == "|:":
                    self.pending["repeat_start"] = True
                elif tk.startswith(":|") and last:
                    m = re.search(r"x(\d+)", tk)
                    last.repeat_end = int(m.group(1)) if m else 2
                    self.close_volta("hook")
            elif tk.startswith("{"):
                name, value = split_directive(tk[1:-1])
                if name in END_MARKS and (events or lead.strip()):
                    ends.append((name, value))           # inside a bar: at the end of that bar
                else:
                    self.directive(tk[1:-1])             # right after a bar line: the bar before
            elif tk.startswith("["):
                events.append(self.event(tk[1:-1]))
            elif events:
                events[-1].lyric += tk
            else:
                lead += tk
        close(force=False)
        for name, value in ends:                 # only text after the last bar line: no bar was closed
            self.end_mark(name, value, self.song.bars[-1] if self.song.bars else None)
        # an ending goes on past the end of the line (closed by :|, the next {volta}, {volta_end} or the
        # end of the section): line breaks in the file never change the music (SPEC §2.7, §9b point 4)

    def implicit_line(self, tokens: list[str]) -> None:
        """No bar lines: each chord lasts its duration (default: one bar) and
        bars are filled in order; a chord crossing a bar line continues (%)."""
        items: list[Event] = []
        marks: list[tuple[int, str, str]] = []   # (items before it, name, value): placed once bars exist
        for tk in tokens:
            if tk.startswith("["):
                items.append(self.event(tk[1:-1]))
            elif tk.startswith("{"):
                name, value = split_directive(tk[1:-1])
                if items and (name in END_MARKS or name in START_MARKS):
                    marks.append((len(items), name, value))
                else:
                    self.directive(tk[1:-1])
            elif items:
                items[-1].lyric += tk
            elif tk.strip():
                # text before any chord, with no bar line: it has no bar to go to and would be lost
                self.warn("text without chords or bar lines: ignored (a line of text in the sheet: {text: …})")
                break
        first_bar: dict[int, Bar] = {}           # item index → bar where it starts / ends
        last_bar: dict[int, Bar] = {}
        bar, t = None, 0.0
        for idx, it in enumerate(items):
            left = it.dur if it.dur is not None else self.num * 4 / self.den
            first = True
            while left > 1e-9:
                if bar is None:
                    bar, t = self.new_bar(), 0.0
                first_bar.setdefault(idx, bar)
                last_bar[idx] = bar
                take = min(left, bar.beats - t)
                bar.events.append(dataclasses.replace(it, start=t, dur=take, lyric=it.lyric.strip()) if first
                                  else Event(None, t, take))
                t += take
                left -= take
                first = False
                if t >= bar.beats - 1e-9:
                    self.push_bar(bar)
                    bar = None
        if bar is not None:
            self.warn("incomplete bar at end of line")
            bar.events[-1].dur += bar.beats - t
            self.push_bar(bar)
        for k, name, value in marks:
            if name in END_MARKS:                 # after the k-th chord: the bar where that chord ends
                self.end_mark(name, value, last_bar.get(k - 1))
            elif k < len(items):                  # before a chord: the bar where that chord starts
                first_bar[k].marks_start.append(name)
            else:                                 # after the last chord: the next bar
                self.pending.setdefault("marks", []).append(name)

    # -- main ------------------------------------------------------------------
    def parse(self) -> Song:
        """Read the whole source line by line: comments are skipped, a line holding only a directive
        is a directive, inside a notes block rows of notes and `w:` lines, otherwise a line of music
        (explicit with bar lines, implicit without). Problems become warnings with the line number;
        the parser never stops on them, so the preview always shows what can be read."""
        for self.lineno, raw in enumerate(self.text.splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            line = escape_line(line)               # \| \[ … are text from here on
            m = DIRECTIVE_LINE_RE.match(line)
            if m:
                self.directive(m.group(1))
                continue
            if self.notes is not None:
                if line.startswith("w:"):
                    self.notes_lyrics(line[2:])
                elif re.search(r"\||:\|", line):
                    self.notes_line(line)
                else:
                    self.warn("inside {start_of_notes}: a row of bars (| … |) or a w: line expected")
                continue
            if self.section is None:
                self.warn("music outside a section: opening an untitled one")
                self.start_section("verse", "")
            tokens = TOKEN_RE.findall(line)
            if any(t in ("|", "||", "|:") or t.startswith(":|") for t in tokens):
                self.explicit_line(tokens)
            else:
                self.implicit_line(tokens)
        if self.notes is not None:
            self.warn("{start_of_notes} not closed at end of file")
            self.end_notes()
        if self.section is not None:
            self.warn(f"section '{self.section.label}' not closed at end of file")
        self.song.meta.setdefault("key", self.key)
        self.song.meta.setdefault("time", f"{self.num}/{self.den}")
        self.restore_escapes()
        return self.song


    def restore_escapes(self) -> None:
        """Put the escaped characters back in every text of the song (see escape_line)."""
        song = self.song
        song.meta = {k: unescape(v) if isinstance(v, str) else v for k, v in song.meta.items()}
        song.warnings[:] = [unescape(w) for w in song.warnings]
        for sec in song.sections:
            sec.label, sec.note, sec.ref_label = unescape(sec.label), unescape(sec.note), unescape(sec.ref_label)
            sec.text_after = [unescape(t) for t in sec.text_after]
        for b in song.bars:
            b.text_before = [unescape(t) for t in b.text_before]
            b.marks_end = [(n, unescape(v)) for n, v in b.marks_end]
            for e in b.events:
                e.lyric, e.note = unescape(e.lyric), unescape(e.note)
            if b.notation:
                for n in b.notation.notes:
                    n.lyric = unescape(n.lyric)

def parse(text: str, transpose: int = 0, base_dir: Path | str | None = None,
          files: dict[Path, str] | None = None) -> Song:
    """base_dir: folder used to resolve {musicxml: …} paths (usually the .chs file's folder)."""
    return Parser(text, transpose, Path(base_dir) if base_dir else None, files).parse()

