"""Notes written in the .chs source ({start_of_notes} … {end_of_notes}, SPEC §2.12b).

A compact text notation for the few notated bars of a lead sheet, read into the same `Note` objects
as the MusicXML reader, so that layout and rendering do not change:

    | [Gm7] G8 Bb D F [C7] A G E C | [Am7] C E G B [D7] C# A 3(F E D) |
    w: syl- la- bles …

Notes: name A–G (accidental #, b, ##, bb, n = explicit natural; always the real pitch, also when it is
in the key signature), octave relative to the previous note (nearest, within a fourth) with ' and , to
move it, or absolute with @N (C4 = middle C; the duration then follows a slash: C@5/2), duration as a
figure (1 2 4 8 16 32, dots), kept until it changes; R = rest, R* = whole-bar rest; - = tie to the
next note; <C E G>2 = notes on one stem; 3( … ) = triplet, N:M( … ) = N notes in the time of M.

Standard library only. The parser (formats/v1.py) owns bar lines, chords and directives; this module
reads note tokens, lyrics, beams, and converts MusicXML measures to this notation.
"""
from __future__ import annotations

import re
from fractions import Fraction

from .musicxml import NOTE_TYPES, STEP_PC, STEPS, Note
from .theory import key_signature

FIGURES = {1: "whole", 2: "half", 4: "quarter", 8: "eighth", 16: "16th", 32: "32nd"}
TYPE_FIGURE = {v: k for k, v in FIGURES.items()}
ALTERS = {None: 0, "": 0, "n": 0, "#": 1, "##": 2, "b": -1, "bb": -2}
B4 = 4 * 7 + STEPS.index("B")          # the middle line of the treble staff: first note of a block

TOKEN_RE = re.compile(
    r"\|:"                               # repeat start
    r"|:\|(?:\s*x\d+)?"                  # repeat end, optional count
    r"|\|\|"                             # double bar
    r"|\|"                               # bar
    r"|\{[^}]*\}"                        # inline directive
    r"|\[[^\]]*\]"                       # chord symbol
    r"|\d+(?::\d+)?\("                   # tuplet start: 3( or 5:4(
    r"|\)"                               # tuplet end
    r"|<[^>]*>[^\s\[\]|<>(){}]*"         # notes on one stem, with duration / tie after >
    r"|[^\s\[\]|<>(){}]+"                # a note or a rest
)
# One note: name, accidental (n = natural), octave (' and , relative, or @N absolute), duration
# figure, dots, tie (-), string (~N). The absolute octave is ONE digit on purpose: with @\d+, `C@54`
# (octave 5, quarter… written without the slash) was read as octave 54. A duration after @N needs a
# slash (C@5/4), which keeps the two numbers apart and lets read() warn about the ambiguous form.
NOTE_RE = re.compile(r"(?P<step>[A-Ga-g])(?P<acc>##|bb|#|b|n)?(?P<oct>[',]+|@-?\d)?"
                     r"(?P<slash>/)?(?P<fig>32|16|1|2|4|8)?(?P<dots>\.{0,2})(?P<tie>-)?(?:~(?P<string>[1-9]))?")
REST_RE = re.compile(r"[Rr](?:(?P<star>\*)|(?P<fig>32|16|1|2|4|8)?(?P<dots>\.{0,2}))")


def tokenize(line: str) -> list[str]:
    return TOKEN_RE.findall(line)


def figure_quarters(fig: int, dots: int) -> Fraction:
    base = Fraction(4, fig)
    return base * (Fraction(3, 2) if dots == 1 else Fraction(7, 4) if dots == 2 else 1)


def default_normal(actual: int) -> int:
    """The usual "in the time of" for N notes: 2 → 3, otherwise the largest power of two below N."""
    if actual == 2:
        return 3
    m = 1
    while m * 2 < actual:
        m *= 2
    return m


class NoteReader:
    """Reads the note tokens of one {start_of_notes} block (state carries across its lines and bars:
    previous pitch for the relative octave, current duration, an open tie)."""

    def __init__(self, key: str, warn):
        self.warn = warn
        self.prev = B4                    # diatonic index (octave * 7 + step) of the previous pitch
        self.fig, self.dots = 4, 0
        self.tie_from: list[Note] = []    # notes whose tie waits for the next note
        self.tuplet: tuple[int, int] | None = None
        self.tuplet_notes: list[Note] = []
        self.tab_pos: int | None = None   # {tab_position: N} for the notes that follow
        sig = key_signature(key)
        self.sig = {s: 0 for s in STEPS}
        for s in ("FCGDAEB"[:sig] if sig > 0 else ""):
            self.sig[s] = 1
        for s in ("BEADGCF"[:-sig] if sig < 0 else ""):
            self.sig[s] = -1

    # -- pitches ----------------------------------------------------------------
    def pitch(self, m: re.Match, ref: int, tok: str) -> tuple[str, int, int]:
        """(step, alter, octave) of a note match; `ref` = diatonic index the octave is relative to."""
        step = m.group("step").upper()
        acc = m.group("acc")
        if acc is None and self.sig[step]:
            self.warn(f"note '{tok}': {step} without accidental, but the key signature has "
                      f"{step}{'#' if self.sig[step] > 0 else 'b'} (write {step}{'#' if self.sig[step] > 0 else 'b'}, "
                      f"or {step}n for a natural)")
        idx = STEPS.index(step)
        octv = m.group("oct") or ""
        # relative octave (as in LilyPond): the octave that puts the note nearest to the previous one,
        # i.e. within a fourth; ' and , move it up or down from there. @N sets it outright
        if octv.startswith("@"):
            octave = int(octv[1:])
        else:
            base = (ref - idx) // 7
            octave = min((base, base + 1), key=lambda o: abs(o * 7 + idx - ref))
            octave += octv.count("'") - octv.count(",")
        return step, ALTERS[acc], octave

    # -- durations --------------------------------------------------------------
    def duration(self, fig: str | None, dots: str, tok: str) -> tuple[Fraction, str, int]:
        """Duration in quarters, type and dots. A figure stays in force until another is written, so
        `G8 A B C` are four eighths; inside a tuplet the duration is scaled (3 in the time of 2)."""
        if fig:
            self.fig, self.dots = int(fig), len(dots)
        elif dots:
            self.warn(f"'{tok}': a dot needs a figure before it (e.g. 4.)")
        d = figure_quarters(self.fig, self.dots)
        if self.tuplet:
            d = d * self.tuplet[1] / self.tuplet[0]
        return d, FIGURES[self.fig], self.dots

    def tie(self, notes: list[Note], tied: bool, tok: str) -> None:
        """Close the tie waiting from the previous note (`A2-`) on these notes, if the pitch matches,
        and open a new one if this token ends with `-`. A tie that finds no matching pitch is
        dropped with a warning instead of drawing an arc to the wrong note."""
        if self.tie_from:
            prev = {(n.step, n.alter, n.octave) for n in self.tie_from}
            matched = False
            for n in notes:
                if n.step is not None and (n.step, n.alter, n.octave) in prev:
                    n.tie_stop = matched = True
            if not matched:
                self.warn(f"tie to '{tok}': the next note must have the same pitch")
                for n in self.tie_from:
                    n.tie_start = False
        self.tie_from = []
        if tied:
            if any(n.step is None for n in notes):
                self.warn(f"'{tok}': a rest cannot be tied")
                return
            for n in notes:
                n.tie_start = True
            self.tie_from = notes

    def in_tuplet(self, notes: list[Note]) -> None:
        if self.tuplet:
            for n in notes:
                n.tuplet = self.tuplet
            if not self.tuplet_notes:
                notes[0].tuplet_start = True
            self.tuplet_notes.append(notes[0])

    # -- tokens -----------------------------------------------------------------
    def read(self, tok: str, start: Fraction, bar_beats: Fraction) -> tuple[list[Note], Fraction] | None:
        """Notes for one token starting at `start` (quarters from the bar start) and their duration;
        None (with a warning) if the token is not a note, a rest or a stacked chord."""
        m = REST_RE.fullmatch(tok)
        if m:
            if m.group("star"):
                if start:
                    self.warn("R*: a whole-bar rest must be alone in its bar")
                n = Note(None, start=float(start), dur=float(bar_beats), type="whole", measure_rest=True)
                self.tie([n], False, tok)
                return [n], bar_beats
            d, typ, dots = self.duration(m.group("fig"), m.group("dots"), tok)
            n = Note(None, start=float(start), dur=float(d), type=typ, dots=dots)
            self.tie([n], False, tok)
            self.in_tuplet([n])
            return [n], d
        if tok.startswith("<"):
            inner, _, after = tok[1:].partition(">")
            m = re.fullmatch(r"(?P<fig>32|16|1|2|4|8)?(?P<dots>\.{0,2})(?P<tie>-)?", after)
            heads = inner.split()
            if not m or not heads:
                self.warn(f"unrecognised notes '{tok}'")
                return None
            # inside < > each note is relative to the one before it (written bottom to top), but the
            # next token is relative to the FIRST note of the chord, as in LilyPond
            pitches, ref, strings = [], self.prev, []
            for h in heads:
                hm = NOTE_RE.fullmatch(h)
                if not hm or hm.group("fig") or hm.group("dots") or hm.group("tie") or hm.group("slash"):
                    self.warn(f"'{h}' in '{tok}': inside < > only note names (duration and tie after >)")
                    return None
                p = self.pitch(hm, ref, h)
                ref = p[2] * 7 + STEPS.index(p[0])
                pitches.append(p)
                strings.append(int(hm.group("string")) if hm.group("string") else None)
            self.prev = pitches[0][2] * 7 + STEPS.index(pitches[0][0])
            d, typ, dots = self.duration(m.group("fig"), m.group("dots"), tok)
            notes = [Note(s, a, o, start=float(start), dur=float(d), type=typ, dots=dots, chord=i > 0,
                          tab_string=strings[i], tab_pos=self.tab_pos)
                     for i, (s, a, o) in enumerate(pitches)]
            self.tie(notes, bool(m.group("tie")), tok)
            self.in_tuplet(notes)
            return notes, d
        m = NOTE_RE.fullmatch(tok)
        if not m:
            self.warn(f"unrecognised note '{tok}' (e.g. G, Bb8, F#4., C@5/2, R4, R*)")
            return None
        octv = m.group("oct") or ""
        if octv.startswith("@") and m.group("fig") and not m.group("slash"):
            self.warn(f"'{tok}': after @N write the duration after a slash (C@5/2)")
        elif m.group("slash") and not octv.startswith("@"):
            self.warn(f"'{tok}': the slash is only for a duration after @N (C@5/2)")
        step, alter, octave = self.pitch(m, self.prev, tok)
        self.prev = octave * 7 + STEPS.index(step)
        d, typ, dots = self.duration(m.group("fig"), m.group("dots"), tok)
        n = Note(step, alter, octave, start=float(start), dur=float(d), type=typ, dots=dots,
                 tab_string=int(m.group("string")) if m.group("string") else None, tab_pos=self.tab_pos)
        self.tie([n], bool(m.group("tie")), tok)
        self.in_tuplet([n])
        return [n], d

    def open_tuplet(self, tok: str) -> None:
        if self.tuplet:
            self.warn(f"'{tok}': tuplets cannot be nested")
            return
        a, _, b = tok[:-1].partition(":")
        actual = int(a)
        normal = int(b) if b else default_normal(actual)
        if actual < 2 or normal < 1:
            self.warn(f"'{tok}': invalid tuplet")
            return
        self.tuplet, self.tuplet_notes = (actual, normal), []

    def close_tuplet(self) -> None:
        if not self.tuplet:
            self.warn("')' without an open tuplet")
            return
        if self.tuplet_notes:
            self.tuplet_notes[-1].tuplet_stop = True
        else:
            self.warn("empty tuplet")
        self.tuplet, self.tuplet_notes = None, []

    def end_bar(self) -> None:
        if self.tuplet:
            self.warn("tuplet not closed before the bar line")
            self.close_tuplet()

    def end_block(self) -> None:
        self.end_bar()
        if self.tie_from:
            self.warn("tie at the end of the notes block: nothing to tie to")
            for n in self.tie_from:
                n.tie_start = False
            self.tie_from = []


# ---------------------------------------------------------------- lyrics
def assign_lyrics(bars: list[list[Note]], text: str, warn) -> None:
    """A `w:` line: one syllable per note (rests, tied continuations and stacked heads skipped);
    `_` skips a note, `|` jumps to the next bar, a syllable ending in `-` continues the word."""
    slots: list[list[Note]] = [[n for n in notes if n.step is not None and not n.tie_stop and not n.chord]
                               for notes in bars]
    b, i = 0, 0
    extra = 0
    for word in text.split():
        parts = [word] if word == "|" else [p for p in re.split(r"(\|)", word) if p]
        for w in parts:
            if w == "|":
                b, i = b + 1, 0
                continue
            while b < len(slots) and i >= len(slots[b]):
                b, i = b + 1, 0
            if b >= len(slots):
                extra += 1
                continue
            if w != "_":
                slots[b][i].lyric = w
            i += 1
    if extra:
        warn(f"w: {extra} syllable(s) more than the notes of the line")


# ---------------------------------------------------------------- beams
def beam_bar(notes: list[Note], num: int, den: int) -> None:
    """Beam eighths and shorter within each beat (a dotted quarter in 6/8, 9/8, 12/8); in 4/4 four
    eighths on the same half bar share one beam. Rests and quarters break beams."""
    beat = Fraction(3, 2) if den == 8 and num % 3 == 0 and num > 3 else Fraction(4, den)
    stems = [n for n in notes if not n.chord]
    groups: list[list[Note]] = []
    cur: list[Note] = []
    cur_beat = None
    for n in stems:
        short = n.step is not None and NOTE_TYPES.get(n.type, 1) < 1
        b = int(Fraction(n.start).limit_denominator(96) / beat)
        if not short or b != cur_beat:
            if len(cur) > 1:
                groups.append(cur)
            cur = []
        if short:
            cur.append(n)
            cur_beat = b
        else:
            cur_beat = None
    if len(cur) > 1:
        groups.append(cur)
    # in 4/4, four plain eighths on beats 1-2 or 3-4 are printed under one beam, as notation software
    # does (never across the middle of the bar); this is the one visible difference with the bundled
    # MusicXML examples, which beam eighths in pairs
    if (num, den) == (4, 4):
        merged: list[list[Note]] = []
        for g in groups:
            prev = merged[-1] if merged else None
            if prev and len(prev) == 2 and len(g) == 2 and all(x.type == "eighth" and not x.dots and not x.tuplet
                                                                 for x in prev + g) \
                    and int(prev[0].start) % 2 == 0 and int(g[0].start) == int(prev[0].start) + 1:
                merged[-1] = prev + g
            else:
                merged.append(g)
        groups = merged
    for g in groups:
        for k, n in enumerate(g):
            n.beams = {1: "begin" if k == 0 else "end" if k == len(g) - 1 else "continue"}


# ---------------------------------------------------------------- MusicXML → notes
def _name(n: Note) -> str:
    return n.step + {0: "", 1: "#", 2: "##", -1: "b", -2: "bb"}[n.alter]


def to_notes_text(measures: list[dict], key: str = "C", per_row: int = 4) -> str:
    """A {start_of_notes} block for MusicXML measures (as read by musicxml.read_musicxml): chords,
    notes, rests, ties, tuplets, repeats, endings; lyrics on a `w:` line under each row of bars.
    The reader gives back the same notes: relative octaves with ' and , and @N for bigger jumps."""
    sig = key_signature(key)
    altered = {s: bool(sig > 0 and s in "FCGDAEB"[:sig] or sig < 0 and s in "BEADGCF"[:-sig]) for s in STEPS}
    prev, fig_dots = B4, (4, 0)
    out = ["{start_of_notes}"]

    def measure(ms: dict) -> tuple[str, list[str]]:
        """One measure as notes text and its syllables. Mirrors NoteReader in reverse: it tracks the
        previous pitch and the current figure exactly as the reader will, so it writes a duration only
        when it changes, ' or , for an octave step and @N only for bigger jumps, and `n` where the key
        signature alters a note that is natural. Chord symbols are emitted before the note they fall
        on (the remaining ones, after the last note, at the end). An empty measure stays empty."""
        nonlocal prev, fig_dots
        parts: list[str] = []
        if ms.get("volta"):
            parts.append("{volta: " + ms["volta"].replace(".", "").replace(" ", "") + "}")
        harm = list(ms.get("harmonies", []))
        syl: list[str] = []
        tuplet_open = False
        for n in ms["notes"]:
            if n.chord:
                continue
            while harm and harm[0][0] <= n.start + 1e-6:
                parts.append(f"[{harm.pop(0)[1]}]")
            if n.tuplet and n.tuplet_start and not tuplet_open:
                a, b = n.tuplet
                parts.append(f"{a}(" if b == default_normal(a) else f"{a}:{b}(")
                tuplet_open = True
            if n.measure_rest:
                parts.append("R*")
            else:
                fig = TYPE_FIGURE.get(n.type, 4)
                dur = "" if (fig, n.dots) == fig_dots else str(fig) + "." * n.dots
                fig_dots = (fig, n.dots)
                if n.step is None:
                    parts.append("R" + dur)
                else:
                    heads = [n] + [x for x in ms["notes"] if x.chord and abs(x.start - n.start) < 1e-6]
                    names, ref = [], prev
                    for h in heads:
                        idx = STEPS.index(h.step)
                        base = (ref - idx) // 7
                        near = min((base, base + 1), key=lambda o: abs(o * 7 + idx - ref))
                        shift = h.octave - near
                        name = _name(h) if h.alter or not altered[h.step] else h.step + "n"
                        string_hint = f"~{h.tab_string}" if h.tab_string else ""
                        if abs(shift) <= 1:
                            name += "'" if shift > 0 else "," if shift < 0 else ""
                        else:
                            name += f"@{h.octave}" + ("/" if dur and len(heads) == 1 else "")
                        names.append((name, string_hint))
                        ref = h.octave * 7 + idx
                    prev = heads[0].octave * 7 + STEPS.index(heads[0].step)
                    if len(heads) > 1:
                        tok = f"<{' '.join(a + b for a, b in names)}>" + dur + ("-" if n.tie_start else "")
                    else:
                        tok = names[0][0] + dur + ("-" if n.tie_start else "") + names[0][1]
                    parts.append(tok)
                    if not n.tie_stop:
                        syl.append(n.lyric or "_")
            if tuplet_open and n.tuplet_stop:
                parts.append(")")
                tuplet_open = False
        if tuplet_open:
            parts.append(")")
        parts += [f"[{ch}]" for _, ch in harm]
        return " ".join(parts), syl

    for r in range(0, len(measures), per_row):
        row = measures[r:r + per_row]
        tokens, lyr, any_lyric = [], [], False
        for k, ms in enumerate(row):
            if ms.get("repeat_start"):
                tokens.append("|:")
            elif k == 0:
                tokens.append("|")
            body, syl = measure(ms)
            tokens.append(body)
            times = ms.get("repeat_end") or 0
            nxt = row[k + 1] if k + 1 < len(row) else None
            if times:
                tokens.append(":|" + (f" x{times}" if times != 2 else ""))
            elif ms.get("double_bar"):
                tokens.append("||")
            elif not (nxt and nxt.get("repeat_start")):
                tokens.append("|")
            any_lyric |= any(x != "_" for x in syl)
            lyr.append(" ".join(syl))
        out.append(" ".join(t for t in tokens if t))
        if any_lyric:
            out.append(re.sub(r"\s+", " ", "w: " + " | ".join(lyr)).rstrip())
    out.append("{end_of_notes}")
    return "\n".join(out) + "\n"
