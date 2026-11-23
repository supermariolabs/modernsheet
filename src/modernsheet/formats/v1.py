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
from pathlib import Path

from ..theory import *  # noqa: F401,F403
from ..model import *  # noqa: F401,F403
from ..musicxml import *  # noqa: F401,F403

# =============================================================================
# Parser
# =============================================================================

TOKEN_RE = re.compile(
    r"\|:"                       # repeat start
    r"|:\|(?:\s*x\d+)?"          # repeat end, optional count
    r"|\|\|"                     # double bar
    r"|\|"                       # bar
    r"|\{[^}]*\}"                # inline directive
    r"|\[[^\]]*\]"               # chord
    r"|[^\[\]{}|:]+|:"           # lyrics
)
DIRECTIVE_LINE_RE = re.compile(r"^\{([^}]*)\}$")
META_KEYS = {"title", "subtitle", "artist", "composer", "tempo", "capo", "bar_width", "label_colors",
             "section_colors"}
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

    # -- helpers ---------------------------------------------------------------
    def warn(self, msg: str) -> None:
        self.song.warnings.append(f"line {self.lineno}: {msg}")

    def set_key(self, value: str) -> str:
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
        if self.pending.pop("time", False):
            bar.time_change = True
        if "key" in self.pending:
            prev = self.pending.pop("key")
            if prev != bar.key:
                bar.key_change, bar.prev_key = True, prev
                if self.song.bars:
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
        name, _, dur = raw.partition(":")
        name = name.strip()
        d = None
        if dur.strip():
            try:
                d = float(dur)
                if d <= 0 or (d * 2) % 1:
                    self.warn(f"duration '{dur}' must be a positive multiple of 0.5")
                    d = max(HALF, round(d * 2) / 2)
            except ValueError:
                self.warn(f"invalid duration '{dur}'")
        if name not in ("/", "%") and not CHORD_RE.match(name):
            self.warn(f"unrecognised chord '{name}'")
        if name == "%":
            name = None
        return transpose_chord(name, self.transpose, self.key) if name else None, d

    # -- directives ------------------------------------------------------------
    def directive(self, body: str) -> None:
        name, value = split_directive(body)
        if name == "key":
            new = self.set_key(value)
            if "key" not in self.song.meta:
                self.song.meta["key"] = new
            else:
                self.pending.setdefault("key", self.key)
            self.key = new
        elif name == "time":
            m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", value)
            if not m:
                self.warn(f"invalid time signature '{value}'")
                return
            self.num, self.den = int(m.group(1)), int(m.group(2))
            if "time" not in self.song.meta:
                self.song.meta["time"] = f"{self.num}/{self.den}"
            else:
                self.pending["time"] = True
        elif name == "bars_per_line":
            n = int(value) if value.isdigit() else None
            if self.section is not None:
                self.section.bars_per_line = n
            else:
                self.bpl = n
        elif name == "br":
            self.pending["br"] = True
        elif name == "volta":
            self.close_volta("open")
            nums = [x.strip().rstrip(".") for x in value.split(",") if x.strip()] or ["1"]
            self.pending["volta"] = ", ".join(f"{x}." for x in nums)
        elif name == "volta_end":
            self.close_volta("hook" if value.strip().lower() in ("hook", "closed", "chiusa") else "open")
        elif name in META_KEYS:
            self.song.meta[name] = value
        elif name.startswith("start_of_"):
            self.start_section(name[9:], value)
        elif name.startswith("end_of_"):
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
        elif name == "text":
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
        elif name in ("comment", "c", "format"):
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
        if self.section is not None:
            self.warn(f"section '{self.section.label}' not closed before '{kind}'")
        self.section = Section(kind=kind, label=label or kind.replace("_", " ").capitalize(),
                               key=self.key, bars_per_line=self.bpl)
        self.song.sections.append(self.section)

    def reference(self, value: str) -> None:
        target, _, note = value.partition("|")
        target, note = target.strip(), note.strip()
        times = 1
        m = re.search(r"\s+x(\d+)$", target)
        if m:
            times, target = int(m.group(1)), target[: m.start()].strip()
        originals = [s for s in self.song.sections if not s.is_ref]
        src = next((s for s in originals if s.label.lower() == target.lower()), None) or \
            next((s for s in originals if s.kind == target.lower()), None)
        if src is None:
            self.warn(f"ref: section '{target}' not found (only earlier sections can be referenced)")
            return
        semis = semitones_between(src.key, self.key)
        sec = Section(kind=src.kind, label=src.label, key=self.key, note=note, is_ref=True,
                      times=times, bars_per_line=src.bars_per_line or self.bpl)
        self.song.sections.append(sec)
        outer, self.section = self.section, sec
        for _ in range(times):
            for b in src.bars:
                nb = copy.deepcopy(b)
                nb.key = transpose_key(b.key, semis)
                nb.marks_start, nb.marks_end, nb.text_before = [], [], []   # signs and notes stay with the original
                nb.prev_key = transpose_key(b.prev_key, semis) if b.prev_key else None
                nb.double_after = b.double_after
                if b is src.bars[0]:
                    nb.time_change = nb.key_change = nb.break_before = False
                for e in nb.events:
                    e.chord = transpose_chord(e.chord, semis, nb.key)
                if nb.notation:
                    transpose_notes(nb.notation.notes, semis, nb.key)
                self.push_bar(nb)
        self.section = outer

    def musicxml(self, value: str) -> None:
        """{musicxml: file.musicxml} or {musicxml: file.musicxml | 3-6}: notated bars from MusicXML."""
        file, _, opts = value.partition("|")
        path = (self.base_dir / file.strip()).resolve()
        try:
            measures, _ = read_musicxml(path, self.files.get(path))
        except Exception as e:                      # missing file, bad XML…
            self.warn(f"musicxml '{file.strip()}': {e}")
            return
        m = re.search(r"(\d+)\s*(?:-\s*(\d+))?", opts)
        if m:
            a, b = int(m.group(1)), int(m.group(2) or m.group(1))
            measures = measures[a - 1:b]
        if self.section is None:
            self.warn("musicxml outside a section: opening an untitled one")
            self.start_section("instrumental", "")
        original_key = transpose_key(self.key, -self.transpose)
        for i, ms in enumerate(measures):
            if (ms["beats"], ms["beat_type"]) != (self.num, self.den):
                self.num, self.den = ms["beats"], ms["beat_type"]
                if "time" not in self.song.meta:
                    self.song.meta["time"] = f"{self.num}/{self.den}"
                else:
                    self.pending["time"] = True
            if i == 0 and ms["fifths"] != key_signature(original_key):
                self.warn(f"musicxml '{file.strip()}': key signature ({ms['fifths']:+d}) differs from {{key: {original_key}}}")
            bar = self.new_bar()
            if abs(ms["length"] - bar.beats) > 1e-6:
                self.warn(f"musicxml measure {ms['number']}: {ms['length']:g} beats in {bar.num}/{bar.den}")
            notes = copy.deepcopy(ms["notes"])
            transpose_notes(notes, self.transpose, self.key)
            bar.notation = Notation(notes, path.name)
            if ms["repeat_start"]:
                self.pending["repeat_start"] = True
            if ms["volta"]:
                self.pending["volta"] = ms["volta"]
            harm = [(t, transpose_chord(ch, self.transpose, self.key)) for t, ch in ms["harmonies"] if t < bar.beats]
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

    # -- music lines -----------------------------------------------------------
    def resolve(self, bar: Bar) -> None:
        fixed = sum(e.dur for e in bar.events if e.dur is not None)
        free = [e for e in bar.events if e.dur is None]
        rest = bar.beats - fixed
        if rest < -1e-9:
            self.warn(f"bar too long: {fixed:g} beats in {bar.num}/{bar.den}")
            rest = 0
        if free:
            share = int(rest / len(free) / HALF) * HALF
            for e in free[:-1]:
                e.dur = share
            free[-1].dur = rest - share * (len(free) - 1)
        elif rest > 1e-9 and bar.events:
            bar.events[-1].dur += rest            # short explicit bar: last event fills it
        t = 0.0
        for e in bar.events:
            e.start, t = t, t + e.dur

    def explicit_line(self, tokens: list[str]) -> None:
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
        self.close_volta("open")          # an ending bracket never runs past its source line

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
        for self.lineno, raw in enumerate(self.text.splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            m = DIRECTIVE_LINE_RE.match(line)
            if m:
                self.directive(m.group(1))
                continue
            if self.section is None:
                self.warn("music outside a section: opening an untitled one")
                self.start_section("verse", "")
            tokens = TOKEN_RE.findall(line)
            if any(t in ("|", "||", "|:") or t.startswith(":|") for t in tokens):
                self.explicit_line(tokens)
            else:
                self.implicit_line(tokens)
        if self.section is not None:
            self.warn(f"section '{self.section.label}' not closed at end of file")
        self.song.meta.setdefault("key", self.key)
        self.song.meta.setdefault("time", f"{self.num}/{self.den}")
        return self.song


def parse(text: str, transpose: int = 0, base_dir: Path | str | None = None,
          files: dict[Path, str] | None = None) -> Song:
    """base_dir: folder used to resolve {musicxml: …} paths (usually the .chs file's folder)."""
    return Parser(text, transpose, Path(base_dir) if base_dir else None, files).parse()

