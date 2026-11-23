"""Import from Chord Sheet Maker (chordsheet.com) → .chs source.

Chord Sheet Maker keeps title, artist, key, tempo and time signature in form fields and
the music in a plain-text "Chords" field. This importer reads that text, optionally
preceded by header lines such as `Title: …`, `Artist: …`, `Key: …`, `BPM: …`, `Time: 3/4`.

Supported syntax (chordsheet.com manual):
  chords separated by blanks, one bar each       A B C D
  several chords in one bar (glue)               Dm7_G7
  double bar line                                ||
  repeats                                        (A B)  (A B)x3  (A B)3x  |:A B:|
  endings                                        (A B 1. C D 2. E F)   1.-3.+5.
  simile marks                                   %  %%  %1 %2
  empty bar (chord still to decide)              *
  rests                                          r1 r2 r4
  inline time signature                          3:4
  section titles                                 : Title   = Title (also a double bar)   <= A
  text lines → {text}, comments → #               - text    ; text    # text
  page break (+ optional new section)            +   + Chorus
  navigation markers → {segno} {to_coda} {coda}  $ (or §)  o  O  fine  D.C. …  D.S. …
                       {fine} {dc: …} {ds: …}
  rhythm marks → [<C] [<<C] [C,,] [C~] [C fermata] [C diamond]
                                                 <C  <<C  C,,  C^ or a lone ^  Cfermata  Cdiamond  C<>
  optional chords → [(C)]                        C?   [G_D+7] (brackets around one or more chords)
  annotations → [A "1°"]                          A"1°"   Dm7 "a II-V-I"   (quoted text after a chord)
  beat placeholders in a split bar → [%]         *_B_*_*   (B on beat 2)
  ignored: indentation X, colour palette P0-P9    X X 2. Cm7   P1 … P0
  Nashville numbers (need a key)                 1 4 5 6m b7
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..formats import CURRENT
from ..theory import CHORD_RE, PITCH, spelling_for

HEADER_RE = re.compile(r"^\s*(title|titolo|artist|artista|composer|compositore|key|tonalit[aà]|bpm|tempo|"
                       r"time|metro|capo|subtitle|annotation)\s*[:=]\s*(.+?)\s*$", re.I)
VOLTA_RE = re.compile(r"^\d+\.(?:[-+]\d+\.)*$")
TIME_RE = re.compile(r"^(\d+):(\d+)$")
GROUP_END_RE = re.compile(r"^(.*?)(\)|:\|)(?:(\d+)x|x(\d+))?$")
NASHVILLE_RE = re.compile(r"^([b#]?)([1-7])(.*)$")
SCALE = [0, 2, 4, 5, 7, 9, 11]

SECTION_KINDS = {
    "intro": "intro", "verse": "verse", "strofa": "verse", "chorus": "chorus", "ritornello": "chorus",
    "rit": "chorus", "refrain": "chorus", "bridge": "bridge", "inciso": "bridge", "pre-chorus": "bridge",
    "prechorus": "bridge", "solo": "solo", "assolo": "solo", "interlude": "instrumental",
    "instrumental": "instrumental", "interludio": "instrumental", "outro": "outro", "coda": "coda",
    "ending": "outro", "finale": "outro", "tag": "outro", "vamp": "bridge",
}


QUOTE_RE = re.compile("\x00(\\d+)\x00")


def chord_token(ch: str, dur: str, mk: dict) -> str:
    """[<<(Name):dur~,, fermata diamond "note"] (SPEC §2.4b)."""
    name = f"({ch})" if mk.get("optional") and ch not in ("/", "%") else ch
    words = "".join(f" {w}" for w in ("fermata", "diamond") if mk.get(w))
    if mk.get("note"):
        words += ' "' + mk["note"].replace('"', "'") + '"'
    return f"[{'<' * mk.get('push', 0)}{name}{dur}{'~' if mk.get('tie') else ''}{',' * mk.get('strokes', 0)}{words}]"


def nav_text(words: list[str]) -> str:
    """The rest of a D.C./D.S. instruction: "al coda con rep." → "al Coda con rep."."""
    return " ".join({"coda": "Coda", "fine": "Fine", "segno": "Segno"}.get(w.lower(), w) for w in words)


@dataclass
class _Bar:
    items: list = field(default_factory=list)      # (chord, fraction_of_bar | None, marks dict)
    repeat_start: bool = False
    repeat_end: int = 0
    volta: str | None = None
    volta_end: bool = False
    double_after: bool = False
    time: str | None = None
    marks: list = field(default_factory=list)      # signs at the start: "segno", "coda"
    end_marks: list = field(default_factory=list)  # at the end: ("to_coda" | "fine" | "dc" | "ds", text)


@dataclass
class Conversion:
    chs: str
    notes: list[str]          # what could not be converted 1:1


class _Converter:
    def __init__(self, text: str, meta: dict):
        self.lines = text.replace("\r\n", "\n").split("\n")
        self.meta = {k: v for k, v in meta.items() if v}
        self.sections: list[dict] = []            # {kind, label, items: [("comment", s) | ("line", [bars])]}
        self.notes: list[str] = []
        self.dropped: dict[str, int] = {}
        self.all_bars: list[_Bar] = []
        self.pending: dict = {}
        self.group: dict | None = None            # open repeat group
        self.opt_group = False                    # inside [ … ]: optional chords
        self.last_group_end = None                # bar that closed the last repeat group (for "x4")
        self.quotes: list[str] = []               # annotations of the current line
        self.preamble: list[str] = []             # comments before the first section

    # ---- helpers
    def note(self, msg):
        if msg not in self.notes:
            self.notes.append(msg)

    def drop(self, what):
        self.dropped[what] = self.dropped.get(what, 0) + 1

    def section(self, label: str | None = None, kind: str | None = None, double_before: bool = False):
        if double_before and self.all_bars:
            self.all_bars[-1].double_after = True
        label = (label or "").strip()
        if kind is None:
            key = re.sub(r"[\s\d]+$", "", label.lower()).strip()
            kind = SECTION_KINDS.get(key, "part")
        self.sections.append({"kind": kind, "label": label, "items": []})

    def cur(self):
        if not self.sections:
            self.section("", "part")
        return self.sections[-1]

    def new_bar(self) -> _Bar:
        b = _Bar()
        if self.pending.pop("repeat_start", False):
            b.repeat_start = True
        if "volta" in self.pending:
            b.volta = self.pending.pop("volta")
        if "time" in self.pending:
            b.time = self.pending.pop("time")
        if "marks" in self.pending:
            b.marks += self.pending.pop("marks")
        self.all_bars.append(b)
        return b

    def end_mark(self, bars, name, text):
        target = bars[-1] if bars else (self.all_bars[-1] if self.all_bars else None)
        if target is None:
            self.note(f"'{name}' prima di qualsiasi battuta: ignorato.")
            return
        target.end_marks.append((name, text))

    def nashville(self, tok: str) -> str | None:
        m = NASHVILLE_RE.match(tok)
        if not m or "key" not in self.meta:
            return None
        acc, deg, rest = m.groups()
        key = self.meta["key"].strip()
        root_name = key[:-1] if key.endswith("m") and len(key) > 1 else key
        if root_name not in PITCH:
            return None
        pc = (PITCH[root_name] + SCALE[int(deg) - 1] + {"b": -1, "#": 1, "": 0}[acc]) % 12
        if "/" in rest:                               # 1/3 → C/E
            q, _, b = rest.partition("/")
            bm = NASHVILLE_RE.match(b)
            if bm and not bm.group(3):
                bpc = (PITCH[root_name] + SCALE[int(bm.group(2)) - 1] + {"b": -1, "#": 1, "": 0}[bm.group(1)]) % 12
                return spelling_for(key)[pc] + q + "/" + spelling_for(key)[bpc]
        rest = "m" + rest[1:] if rest.startswith("-") else rest
        return spelling_for(key)[pc] + rest

    def chord(self, raw: str, in_glue: bool = False):
        """One glued item → (chord, fraction, marks) or None. marks: push (1-2), optional, tie,
        strokes, fermata, diamond (SPEC §2.4b)."""
        t = raw
        marks: dict = {}
        q = QUOTE_RE.search(t)
        if q:                                           # A"1°" → annotation of A
            marks["note"] = self.quotes[int(q.group(1))]
            t = t[:q.start()] + t[q.end():]
        if t in ("*", "X") and in_glue:                 # a free beat: the chord before continues
            return ("%", None, marks)
        if t in ("N.C.", "NC", "N.C", "n.c."):
            return ("/", None, marks)
        m = re.fullmatch(r"r(1|2|4|8)", t)
        if m:
            return ("/", {"1": None, "2": 0.5, "4": 0.25, "8": 0.125}[m.group(1)], marks)
        while t.startswith("<") and not t.startswith("<>"):
            t = t[1:]
            marks["push"] = min(2, marks.get("push", 0) + 1)
        for suffix, mark in (("fermata", "fermata"), ("diamond", "diamond"), ("<>", "diamond")):
            if t.endswith(suffix) and len(t) > len(suffix):
                t = t[: -len(suffix)]
                marks[mark] = True
        while t and t[-1] in ",^?":
            c = t[-1]
            if c == ",":
                marks["strokes"] = marks.get("strokes", 0) + 1
            else:
                marks["tie" if c == "^" else "optional"] = True
            t = t[:-1]
        if self.opt_group:
            marks["optional"] = True
        if not t:
            return None
        if not CHORD_RE.match(t):
            nv = self.nashville(t)
            if nv:
                return (nv, None, marks)
            if NASHVILLE_RE.match(t):
                self.note(f"Numeri Nashville ('{t}'): indica la tonalità (Key: …) per convertirli in accordi.")
            else:
                self.note(f"Accordo non riconosciuto: '{t}' (lasciato com'è).")
        return (t, None, marks)

    def volta_label(self, tok: str) -> str:
        nums = []
        for part in tok.split("+"):
            m = re.fullmatch(r"(\d+)\.(?:-(\d+)\.)?", part)
            if m:
                a, b = int(m.group(1)), int(m.group(2) or m.group(1))
                nums += list(range(a, b + 1))
        return ", ".join(str(n) for n in nums) or "1"

    # ---- chord lines
    def chord_line(self, line: str) -> list[_Bar]:
        bars: list[_Bar] = []
        # quoted annotations may contain spaces: put them aside, a placeholder keeps their place
        self.quotes = []

        def keep(m):
            self.quotes.append(" ".join(m.group(1).split()).replace("]", ")"))
            return f"\x00{len(self.quotes) - 1}\x00"
        line = re.sub(r'"([^"]*)"?', keep, line)
        toks = line.split()
        i = 0
        prev_tok = ""
        while i < len(toks):
            t = toks[i]
            i += 1
            # "1.C" / "2.%)": an ending glued to what follows; "%"note"": a note glued to a simile mark
            m = re.fullmatch(r"(\(?\d+\.(?:[-+]\d+\.)*)(\S+)", t)
            if m and not re.fullmatch(r"\d+", m.group(2)):
                t, toks[i:i] = m.group(1), [m.group(2)]
            q = QUOTE_RE.search(t)
            if q and re.fullmatch(r"\(?%%?\d*\)?(\d+x|x\d+)?", t[:q.start()] + t[q.end():]):
                t, toks[i:i] = t[:q.start()] + t[q.end():], [q.group(0)]
            last_tok, prev_tok = prev_tok, t
            if QUOTE_RE.fullmatch(t):                    # a lone annotation: for the chord before it
                prev = bars[-1] if bars else (self.all_bars[-1] if self.all_bars else None)
                note = self.quotes[int(t.strip("\x00"))]
                if prev is not None and prev.items:
                    ch, frac, mk = prev.items[-1]
                    prev.items[-1] = (ch, frac, {**mk, "note": f"{mk['note']} {note}".strip() if mk.get("note") else note})
                elif prev is not None:                  # a repeated bar (%): the note goes on the bar itself
                    prev.items = [("%", None, {"note": note})]
                else:
                    self.note("Annotazione senza un accordo prima: ignorata.")
                continue
            if re.fullmatch(r"X+|P\d", t):               # indentation spacer, colour palette switch
                continue
            m = re.fullmatch(r"x(\d+)|(\d+)x", t)      # "( … ) x4": the count after a space
            if m and self.last_group_end is not None and GROUP_END_RE.match(last_tok or "") and \
                    last_tok.endswith((")", ":|")):
                n = int(m.group(1) or m.group(2))
                if self.last_group_end.repeat_end:
                    self.last_group_end.repeat_end = n
                continue
            if t.startswith(("D.C.", "D.S.")):           # navigation instruction, may span words
                words = [t]
                while i < len(toks) and toks[i].lower().rstrip(".") in ("al", "fine", "coda", "con", "senza", "rep", "segno"):
                    words.append(toks[i])
                    i += 1
                self.end_mark(bars, "dc" if t.startswith("D.C.") else "ds", nav_text(words[1:]))
                continue
            if t == "^":                                # a lone tie: the last chord is held over
                prev = bars[-1] if bars else (self.all_bars[-1] if self.all_bars else None)
                if prev is not None and prev.items:
                    ch, frac, mk = prev.items[-1]
                    prev.items[-1] = (ch, frac, {**mk, "tie": True})
                continue
            close_opt = False
            if t.startswith("[") and len(t) > 1:        # [G_D+7 … ]: chords in parentheses
                self.opt_group, t = True, t[1:]
            if t.endswith("]") and self.opt_group:
                close_opt, t = True, t[:-1]
            # prefixes: repeat start
            while t.startswith(("|:", "(")):
                self.pending["repeat_start"] = True
                self.group = {"has_volta": False}
                t = t[2:] if t.startswith("|:") else t[1:]
            # suffix: repeat end with optional count
            end_count = None
            m = GROUP_END_RE.match(t)
            if m and m.group(2) == ")" and m.group(1).count("(") >= m.group(1).count(")") + 1:
                m = None                                # ")" closes a chord's own "(", e.g. C7(b9)
            if m:
                t = m.group(1)
                end_count = int(m.group(3) or m.group(4) or 2)
            bar = None
            if t in ("", "|"):
                pass
            elif t == "||":
                if bars or self.all_bars:
                    (bars[-1] if bars else self.all_bars[-1]).double_after = True
            elif VOLTA_RE.match(t):
                prev = bars[-1] if bars else (self.all_bars[-1] if self.all_bars else None)
                if self.group and self.group["has_volta"] and prev is not None and not prev.repeat_end:
                    prev.repeat_end = 2                 # previous ending goes back to the start
                    prev.volta_end = True
                if self.group:
                    self.group["has_volta"] = True
                self.pending["volta"] = self.volta_label(t)
            elif TIME_RE.match(t):
                a, b = TIME_RE.match(t).groups()
                self.pending["time"] = f"{a}/{b}"
            elif t in ("$", "§", "O"):                  # segno / coda: at the start of the next bar
                self.pending.setdefault("marks", []).append("coda" if t == "O" else "segno")
            elif t in ("o", "fine", "Fine"):            # to coda / fine: at the end of the bar before
                self.end_mark(bars, "to_coda" if t == "o" else "fine", "")
            elif re.fullmatch(r"%%|%\d*", t):
                n = 2 if t == "%%" else int(t[1:] or 1)
                prev = self.all_bars[-n:] if len(self.all_bars) >= n else []
                if not prev:
                    self.note(f"'{t}' senza battute precedenti: ignorato.")
                for src in prev:
                    bar = self.new_bar()
                    # a one-chord bar repeated → empty bar (the chord continues, rendered as %)
                    bar.items = [] if (n == 1 and len(src.items) == 1 and src.items[0][1] is None) else list(src.items)
                    bars.append(bar)
                bar = bars[-1] if prev else None
            elif t == "*":
                bar = self.new_bar()
                bars.append(bar)
                self.note("'*' (accordo da decidere) → battuta vuota.")
            else:
                parts = [p for p in t.split("_") if p]
                items = [x for x in (self.chord(p, len(parts) > 1) for p in parts) if x]
                if items:
                    bar = self.new_bar()
                    bar.items = items
                    bars.append(bar)
            if close_opt:
                self.opt_group = False
            if end_count is not None:
                target = bar or (bars[-1] if bars else (self.all_bars[-1] if self.all_bars else None))
                self.last_group_end = target
                if target is not None:
                    if self.group and self.group["has_volta"]:
                        target.volta_end = True          # last ending: no repeat sign
                    else:
                        target.repeat_end = end_count
                self.group = None
        return bars

    # ---- main
    def run(self) -> Conversion:
        lines = list(self.lines)
        # optional header lines
        while lines and (not lines[0].strip() or HEADER_RE.match(lines[0])):
            m = HEADER_RE.match(lines.pop(0))
            if m:
                k, v = m.group(1).lower(), m.group(2)
                k = {"titolo": "title", "artista": "artist", "compositore": "artist", "composer": "artist",
                     "tonalità": "key", "tonalita": "key", "bpm": "tempo", "metro": "time",
                     "annotation": "subtitle"}.get(k, k)
                self.meta.setdefault(k, v)
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            c = line[0]
            if c == "#":
                if self.sections:
                    self.cur()["items"].append(("comment", line[1:].strip()))
                else:
                    self.preamble.append(line[1:].strip())
            elif c == "+":
                if line[1:].strip():
                    self.section(line[1:].strip())
            elif line.startswith("<="):
                self.section(line[2:].strip(), double_before=False)
            elif line.startswith(("<-", ">-", ">=")):
                self.cur()["items"].append(("comment", line[2:].strip()))
            elif c in ":=":
                self.section(line[1:].strip(), double_before=(c == "="))
            elif c in "-;":                              # text lines (";" keeps spaces there: not here)
                if line[1:].strip():
                    self.cur()["items"].append(("text", " ".join(line[1:].split())))
            else:
                if re.match(r"^X+\s", line):              # indentation spacer: our 2nd endings align by themselves
                    line = re.sub(r"^X+\s*", "", line)
                bars = self.chord_line(line)
                if bars:
                    self.cur()["items"].append(("line", bars))
        for what, n in self.dropped.items():
            self.note(f"Segni ritmici non supportati, rimossi: {what} ×{n}.")
        return Conversion(self.serialize(), self.notes)

    # ---- output
    def serialize(self) -> str:
        m = self.meta
        num, den = (m.get("time") or "4/4").replace(":", "/").split("/")
        beats = int(num) * 4 / int(den)
        out = ["# Importato da Chord Sheet Maker (chordsheet.com)", f"{{format: v{CURRENT}}}"]
        for k in ("title", "subtitle", "artist", "key", "tempo", "capo"):
            if m.get(k):
                out.append(f"{{{k}: {m[k]}}}")
        out.append(f"{{time: {num}/{den}}}")
        # bars per line: the most common line length of the original (long lines wrap by themselves,
        # shorter ones keep their break thanks to {br})
        widths = [len(it[1]) for s in self.sections for it in s["items"] if it[0] == "line"]
        bpl = max(set(widths), key=lambda w: (widths.count(w), w == 4)) if widths else 4
        if bpl != 4:
            out.append(f"{{bars_per_line: {bpl}}}")
        out += [f"# {c}" if c else "#" for c in self.preamble]
        if self.notes:
            out.append("#")
            out.append("# Note di conversione:")
            out += [f"#  - {n}" for n in self.notes]
        cur_beats = beats
        for s in self.sections:
            if not s["items"]:
                continue
            out.append("")
            out.append(f"{{start_of_{s['kind']}{': ' + s['label'] if s['label'] else ''}}}")
            buf, volta_open = "", False
            first_line = True
            for kind, val in s["items"]:
                if kind in ("comment", "text"):
                    if buf:
                        out.append(buf)
                        buf = ""
                    if kind == "text":
                        out.append("{text: " + val.replace("{", "(").replace("}", ")") + "}")
                    else:
                        out.append(f"# {val}" if val else "#")
                    continue
                parts = []
                if not first_line:
                    parts.append("{br}")
                first_line = False
                parts.append("|:" if val[0].repeat_start else "|")
                for j, b in enumerate(val):
                    if b.time:
                        parts.append(f"{{time: {b.time}}}")
                        n_, d_ = b.time.split("/")
                        cur_beats = int(n_) * 4 / int(d_)
                    if b.volta:
                        parts.append(f"{{volta: {b.volta}}}")
                        volta_open = True
                    parts += [f"{{{mk}}}" for mk in b.marks]
                    for ch, frac, mk in b.items:
                        dur = "" if frac is None else f":{frac * cur_beats:g}"
                        parts.append(chord_token(ch, dur, mk))
                    parts += [f"{{{n}: {v}}}" if v else f"{{{n}}}" for n, v in b.end_marks]
                    if b.repeat_end:
                        parts.append(":|" + (f" x{b.repeat_end}" if b.repeat_end > 2 else ""))
                        volta_open = False
                    elif b.double_after:
                        parts.append("||")
                    else:
                        parts.append("|")
                    if b.volta_end and not b.repeat_end:
                        parts.append("{volta_end}")
                        volta_open = False
                    if j + 1 < len(val) and val[j + 1].repeat_start:
                        parts.append("|:")
                line = " ".join(parts)
                buf = f"{buf} {line}".strip() if buf else line
                if not volta_open:                      # an ending must stay on one source line
                    out.append(buf)
                    buf = ""
            if buf:
                out.append(buf)
            out.append(f"{{end_of_{s['kind']}}}")
        return "\n".join(out) + "\n"


def convert(text: str, *, title: str = "", artist: str = "", key: str = "", tempo: str = "", time: str = "") -> Conversion:
    """chordsheet.com text → Conversion(chs, notes). Keyword arguments fill in metadata that
    chordsheet.com keeps in form fields (they win over header lines in the text)."""
    return _Converter(text, dict(title=title, artist=artist, key=key, tempo=tempo, time=time)).run()
