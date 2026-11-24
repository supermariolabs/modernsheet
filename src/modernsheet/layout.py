"""Layout layer: themes, chord typography, rows and bars, notation → DisplayList."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from . import fonts
from . import tab as tab_mod
from .display import DisplayList, Surface
from .model import *  # noqa: F401,F403
from .musicxml import NOTE_TYPES, STEPS, Note  # noqa: F401
from .parser import HALF
from .theory import *  # noqa: F401,F403

# SMuFL code points (Petaluma)
SMUFL = {
    "clef": "\uE050", "sharp": "\uE262", "flat": "\uE260", "natural": "\uE261",
    "percent": "\uE500", "quarter": "\uECA5",
    "maj": "\uE873", "dim": "\uE870", "halfdim": "\uE871",
    "segno": "\uE047", "coda": "\uE048",
    "fermata": "\uE4C0", "slash": "\uE101", "diamond": "\uE0D8",
}
# characters some text fonts lack: routed to the music font
SYMBOL_SUBS = {"♩": SMUFL["quarter"], "Δ": SMUFL["maj"], "°": SMUFL["dim"],
               "♯": SMUFL["sharp"], "♭": SMUFL["flat"], "♮": SMUFL["natural"]}


SYMBOL_SCALE = {"Δ": 1.0, "°": 0.8}


def label_text_color(bg: tuple) -> tuple:
    """White on dark boxes; near-black on light ones (e.g. orange, light green), whichever reads better."""
    def lum(c):
        c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    L = lum(bg)
    white = 1.05 / (L + 0.05)
    dark = (L + 0.05) / (lum((0.1, 0.1, 0.12)) + 0.05)
    return (1, 1, 1) if white >= 3.0 or white >= dark else (0.1, 0.1, 0.12)


def hex_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


DEFAULT_LABEL_COLOR = hex_rgb("#0066CC")   # section boxes, unless configured otherwise

# Section-label colours when label_colors = "by_type" (all keep white text >= 4.5:1 contrast)
SECTION_PALETTE = {
    "verse": "#1F3A5F",        # blu notte
    "chorus": "#8B1E3F",       # bordeaux
    "bridge": "#0F5C5C",       # verde petrolio
    "instrumental": "#8A5300", # ocra scuro (also solo, interlude)
    "frame": "#3A3A42",        # antracite (intro, outro, coda, ending)
}
SECTION_KIND_GROUP = {
    "verse": "verse", "strofa": "verse",
    "chorus": "chorus", "ritornello": "chorus", "refrain": "chorus",
    "bridge": "bridge", "inciso": "bridge", "prechorus": "bridge", "pre_chorus": "bridge",
    "instrumental": "instrumental", "solo": "instrumental", "assolo": "instrumental",
    "interlude": "instrumental", "interludio": "instrumental",
    "intro": "frame", "outro": "frame", "coda": "frame", "ending": "frame", "finale": "frame",
}


@dataclass
class Theme:
    name: str
    text: str            # lyrics, header, footer
    title: str
    chord: str
    label: str
    note: str            # italic-ish notes
    music: str           # font for clef / accidentals / time signatures
    smufl: bool          # music font uses SMuFL code points
    ink: tuple = (0.06, 0.06, 0.06)
    staff_lines: tuple = (0.72, 0.72, 0.72)
    staff_ink: tuple = (0.55, 0.55, 0.55)
    lyric_ink: tuple = (0.2, 0.2, 0.2)
    grey: tuple = (0.45, 0.45, 0.45)
    accent: tuple = (0.33, 0.29, 0.72)
    boxed_labels: bool = True       # section label in a filled rounded box, white text
    bold_chords: bool = False       # embolden chord symbols by stroking the outline
    bold_stroke: float = 0.045      # outline width as a fraction of the font size
    superscript: bool = False       # chord extensions raised and smaller
    centered_title: bool = False
    title_size: float = 20
    chord_size: float = 13.5
    chord_fit_size: float = 11      # below this a crowded bar takes more grid slots
    chord_min_size: float = 9
    lyric_size: float = 8.6
    label_size: float = 10.5
    staff_line_width: float = 0.6
    barline_width: float = 0.9


THEMES = {
    "clean": Theme("clean", text="Sans", title="SansB", chord="SansB", label="SansB", note="SansI",
                   music="Sym", smufl=False, accent=DEFAULT_LABEL_COLOR),
    "realbook": Theme("realbook", text="PScript", title="PScript", chord="PScript", label="PScript",
                      note="PScript", music="Petaluma", smufl=True,
                      staff_lines=(0.62, 0.62, 0.62), staff_ink=(0.42, 0.42, 0.42), accent=DEFAULT_LABEL_COLOR,
                      boxed_labels=True, bold_chords=True, superscript=True, centered_title=False, title_size=26,
                      chord_size=17, chord_fit_size=13, chord_min_size=11, lyric_size=9.5, label_size=13,
                      staff_line_width=0.75, barline_width=1.2),
}

# Jazz chord-symbol spelling (option --chord-symbols jazz)
JAZZ_SUBS = [(r"^maj", "Δ"), (r"^ma", "Δ"), (r"^M(?=\d|$)", "Δ"), (r"^m7b5", "ø7"), (r"^dim", "°"),
             (r"^min", "-"), (r"^m(?!a)", "-")]


@dataclass
class Style:
    margin: float = 42
    staff_space: float = 5.6
    row_height: float = 62
    section_height: float = 26


def natural_count(sig: int, prev: int | None) -> int:
    if not prev:
        return 0
    if sig == 0 or (prev > 0) != (sig > 0):
        return abs(prev)
    return max(0, abs(prev) - abs(sig))


PAGE_SIZES = {"a4": (595.2755905511812, 841.8897637795277), "letter": (612.0, 792.0)}


class Layout:
    """Layout layer: places everything on pages and records it as a DisplayList.
    It draws on a recording Surface, so it needs no rendering library."""

    def __init__(self, song: Song, *, bars_per_line: int = 4, bar_width: str = "uniform", row_spacing="normal",
                 notation: str = "staff", notation_force: bool = False,
                 paper: str = "A4", theme: str = "realbook", chord_symbols: str = "text",
                 label_colors: str = "theme", style: Style | None = None):
        self.metrics = fonts.registry(theme)
        self.theme_name = theme
        self.song = song
        self.st = style or Style()
        self.th = THEMES[theme]
        self.chord_symbols = chord_symbols
        self.label_colors = song.meta.get("label_colors", label_colors)   # theme | by_type | #RRGGBB
        self.bpl_default = bars_per_line
        self.bar_width = song.meta.get("bar_width", bar_width)
        if self.bar_width not in ("uniform", "fit"):
            song.warnings.append(f"bar_width '{self.bar_width}' unknown, using 'uniform'")
            self.bar_width = "uniform"
        self.song_bar_width = self.bar_width      # sections may override it ({bar_width} inside a section)
        # space between rows: the song's {row_spacing}, else the option; scales the free space under each staff
        self.row_spacing = row_spacing_factor(song.meta.get("row_spacing", row_spacing)) or \
            row_spacing_factor(row_spacing) or 1.0
        # notated bars: staff, staff + guitar tablature, or tablature only (song's {notation}, else the option)
        # notation_force: the viewer's own choice (the app's switch over the sheet) beats song and sections
        self.notation_force = notation_force
        self.song_notation = notation if notation_force else song.meta.get("notation", notation)
        if self.song_notation not in NOTATIONS:
            song.warnings.append(f"notation '{self.song_notation}' unknown, using 'staff'")
            self.song_notation = "staff"
        self.notation_mode = self.song_notation
        self.tuning = tab_mod.parse_tuning(song.meta.get("tuning", "standard")) or tab_mod.STANDARD
        self.tab_n = len(self.tuning)
        self.TAB_H = (self.tab_n - 1) * self.TAB_SP        # as many lines as strings
        if any(self.section_notation(s) != "staff" for s in song.sections):
            self.assign_tab()
        self.page_w, self.page_h = PAGE_SIZES.get(paper.lower(), PAGE_SIZES["a4"])
        self.c = Surface((self.page_w, self.page_h), self.metrics)
        self.c.setTitle(song.meta.get("title", "Chord sheet"))
        self.c.setAuthor(song.meta.get("artist", ""))
        self.page = 1
        self.y = self.page_h - self.st.margin
        self.SP = self.st.staff_space
        self.STAFF_H = 4 * self.SP
        self._cmaps = {}
        self.pending_ties = {}
        self.volta_carry = None
        self.tie_carry = False             # a [C~] tie continues on the next row
        self.cur_mid = 0.0
        self.cur_row_lyrics = False
        self.cur_row = []
        self.row_events = []

    # -- text with per-character font fallback ----------------------------------
    def covers(self, font, ch):
        if font not in self._cmaps:
            self._cmaps[font] = set(self.metrics.getFont(font).face.charToGlyph)
        return ord(ch) in self._cmaps[font]

    def runs(self, text, font):
        """Split text into (string, font, scale) runs the fonts can actually draw."""
        out = []
        for ch in text:
            if self.covers(font, ch):
                f, s, g = font, 1.0, ch
            elif self.th.smufl and ch in SYMBOL_SUBS:
                f, s, g = "Petaluma", SYMBOL_SCALE.get(ch, 1.6), SYMBOL_SUBS[ch]
            elif ch in "♭♯♮♩":
                f, s, g = "Sym", 1.15, ch
            else:
                f, s, g = "Sans", 0.9, ch
            if out and out[-1][1] == f and out[-1][2] == s:
                out[-1][0] += g
            else:
                out.append([g, f, s])
        return out

    def text_width(self, text, font, size):
        return sum(self.metrics.stringWidth(g, f, size * s) for g, f, s in self.runs(text, font))

    def text(self, x, y, text, font, size, color=None, bold=False):
        """Draw text with font fallback. bold=True strokes the outline (fill+stroke render
        mode) to embolden fonts that have no bold weight, such as Petaluma Script."""
        color = color or self.th.ink
        c = self.c
        c.saveState()
        c.setFillColorRGB(*color)
        c.setStrokeColorRGB(*color)
        c.setLineJoin(1)
        for g, f, s in self.runs(text, font):
            t = c.beginText(x, y)
            t.setFont(f, size * s)
            if bold:
                c.setLineWidth(size * s * self.th.bold_stroke)
                t.setTextRenderMode(2)
            t.textOut(g)
            c.drawText(t)
            x += self.metrics.stringWidth(g, f, size * s)
        c.restoreState()
        return x

    def fit(self, text, font, size, room):
        if self.text_width(text, font, size) <= room:
            return text
        while text and self.text_width(text.rstrip() + "…", font, size) > room:
            text = text[:-1]
        return text.rstrip() + "…"

    # -- chord symbols -------------------------------------------------------------
    def chord_runs(self, chord):
        """(text, scale, rise) runs: root full size, extensions raised and smaller (realbook)."""
        if chord == "/":
            return [("/", 1.0, 0.0)]
        m = CHORD_RE.match(chord)
        if not m:
            return [(pretty_chord(chord), 1.0, 0.0)]
        root, quality, bass = m.groups()
        if self.chord_symbols == "jazz":
            for pat, rep in JAZZ_SUBS:
                new = re.sub(pat, rep, quality)
                if new != quality:
                    quality = new
                    break
        sup = self.th.superscript
        acc = lambda a: a.replace("b", "♭").replace("#", "♯")
        runs = [(root[0], 1.0, 0.0)]
        if len(root) > 1:
            runs.append((acc(root[1]), 0.72 if sup else 1.0, 0.3 if sup else 0.0))
        if quality:
            q = re.sub(r"b(?=\d)", "♭", quality).replace("#", "♯")
            if sup and q.startswith("-"):
                runs.append(("-", 1.0, 0.0))
                q = q[1:]
            elif sup and re.match(r"m(?!a)", q):     # minor 'm' stays on the line, extensions go up
                runs.append(("m", 0.8, 0.0))
                q = q[1:]
            if q:
                runs.append((q, 0.62 if sup else 1.0, 0.36 if sup else 0.0))
        if bass:
            runs.append(("/" + bass[0], 0.85 if sup else 1.0, 0.0))
            if len(bass) > 1:
                runs.append((acc(bass[1]), 0.62 if sup else 1.0, 0.25 if sup else 0.0))
        return runs

    def chord_width(self, chord, size):
        return sum(self.text_width(t, self.th.chord, size * sc) for t, sc, _ in self.chord_runs(chord))

    def draw_chord(self, x, y, chord, size):
        for t, sc, rise in self.chord_runs(chord):
            x = self.text(x, y + rise * size, t, self.th.chord, size * sc, bold=self.th.bold_chords)
        return x

    # -- chord marks: optional (C), push <C, diamond --------------------------------
    PUSH_SCALE = 0.62
    DIAMOND_SCALE = 1.45

    def push_text(self, e) -> str:
        return "<" * e.push

    def event_width(self, e, size) -> float:
        """Width of a chord with its marks: push before it, parentheses around, diamond after."""
        w = self.chord_width(e.chord, size)
        if e.push:
            w += self.text_width(self.push_text(e), self.th.chord, size * self.PUSH_SCALE) + 1.5
        if e.optional:
            w += self.text_width("()", self.th.chord, size)
        if e.diamond:
            w += self.metrics.stringWidth(SMUFL["diamond"], "Petaluma", self.STAFF_H * self.DIAMOND_SCALE) + 3
        return w

    def draw_event(self, x, y, e, size) -> float:
        """Draw the chord and its marks from x (baseline y); returns the right edge."""
        th = self.th
        if e.push:
            x = self.text(x, y + size * 0.3, self.push_text(e), th.chord, size * self.PUSH_SCALE,
                          bold=th.bold_chords) + 1.5
        if e.optional:
            x = self.text(x, y, "(", th.chord, size, bold=th.bold_chords)
        x = self.draw_chord(x, y, e.chord, size)
        if e.optional:
            x = self.text(x, y, ")", th.chord, size, bold=th.bold_chords)
        if e.diamond:
            x += 3
            self.c.setFillColorRGB(*th.ink)
            size_d = self.STAFF_H * self.DIAMOND_SCALE
            self.c.setFont("Petaluma", size_d)
            g = SMUFL["diamond"]
            self.c.drawString(x, self.cur_mid - 0.1 * size_d, g)
            x += self.metrics.stringWidth(g, "Petaluma", size_d)
        return x

    # -- page furniture ----------------------------------------------------------
    def header(self):
        """Song header: drawn on the first page only; later pages carry just score and footer."""
        m, th, L, R = self.song.meta, self.th, self.st.margin, self.page_w - self.st.margin
        title = m.get("title", "Untitled")
        title_base = self.y - th.title_size * 0.85
        if th.centered_title:
            w = self.text_width(title, th.title, th.title_size)
            self.text((self.page_w - w) / 2, title_base, title, th.title, th.title_size)
            sub_base = title_base - 20
            info_base = sub_base
        else:
            self.text(L, title_base, title, th.title, th.title_size, bold=th.bold_chords)
            sub_base = title_base - 16
            info_base = title_base
        sub = " - ".join(v for v in (m.get("subtitle"), m.get("artist") or m.get("composer")) if v)
        self.text(L, sub_base, sub, th.text, 9.5, th.grey)
        sep = "   " if th.smufl else "   ·   "
        second = [m["time"]] + ([f"♩ = {m['tempo']}"] if m.get("tempo") else [])
        if m.get("capo"):
            second.append(f"Capo {m['capo']}")
        lines = [pretty_chord(f"Key {m['key']}"), sep.join(second)]
        for i, ln in enumerate(lines):
            self.text(R - self.text_width(ln, th.text, 10), info_base - i * 14, ln, th.text, 10, th.grey)
        line_y = min(sub_base, info_base - 14) - 10
        self.c.setStrokeColorRGB(0.8, 0.8, 0.8)
        self.c.setLineWidth(0.6)
        self.c.line(L, line_y, R, line_y)
        self.y = line_y - 14

    def footer(self):
        txt = f"{self.song.meta.get('title', '')} - p. {self.page}"
        self.text((self.page_w - self.text_width(txt, self.th.text, 8.5)) / 2, self.st.margin - 20,
                  txt, self.th.text, 8.5, self.th.grey)

    def ensure(self, h):
        if self.y - h < self.st.margin:
            self.footer()
            self.c.showPage()
            self.page += 1
            self.y = self.page_h - self.st.margin

    # -- staff primitives --------------------------------------------------------
    def staff_lines(self, x0, x1, top):
        self.c.setStrokeColorRGB(*self.th.staff_lines)
        self.c.setLineWidth(self.th.staff_line_width)
        for i in range(5):
            self.c.line(x0, top - i * self.SP, x1, top - i * self.SP)

    def step_y(self, top, step):
        return top - self.STAFF_H + step * self.SP / 2

    def music_glyph(self, x, y, name):
        """Draw a SMuFL glyph (realbook) at staff size; returns its advance."""
        g = SMUFL[name]
        self.c.setFillColorRGB(*self.th.staff_ink)
        self.c.setFont("Petaluma", self.STAFF_H)
        self.c.drawString(x, y, g)
        return self.metrics.stringWidth(g, "Petaluma", self.STAFF_H)

    def clef(self, x, top):
        if self.th.smufl:
            self.music_glyph(x + 1, top - 3 * self.SP, "clef")
            return 24
        self.c.setFillColorRGB(*self.th.staff_ink)
        self.c.setFont("Sym", 34)
        self.c.drawString(x, top - self.STAFF_H - 6.5, "𝄞")
        return 22

    ACC_W = 6.4

    def accidental(self, x, y, glyph):
        if self.th.smufl:
            self.music_glyph(x, y, {"♯": "sharp", "♭": "flat", "♮": "natural"}[glyph])
            return
        self.c.setFillColorRGB(*self.th.staff_ink)
        self.c.setFont("Sym", 15)
        self.c.drawString(x, y + {"♯": -4.6, "♮": -4.6, "♭": -2.4}[glyph], glyph)

    def key_signature_width(self, sig, prev=None):
        n = natural_count(sig, prev)
        return n * self.ACC_W + (3 if n else 0) + abs(sig) * self.ACC_W + (4 if sig or n else 0)

    def draw_key_signature(self, x, top, sig, prev=None):
        w = 0
        n = natural_count(sig, prev)
        if n:
            steps = SHARP_STEPS if prev > 0 else FLAT_STEPS
            keep = abs(prev) - n
            for s in steps[keep:abs(prev)]:
                self.accidental(x + w, self.step_y(top, s), "♮")
                w += self.ACC_W
            w += 3
        steps = SHARP_STEPS if sig > 0 else FLAT_STEPS
        for s in steps[:abs(sig)]:
            self.accidental(x + w, self.step_y(top, s), "♯" if sig > 0 else "♭")
            w += self.ACC_W
        return w + (4 if sig or n else 0)

    def time_signature(self, x, top, num, den):
        if self.th.smufl:
            for val, y in ((num, top - self.SP), (den, top - 3 * self.SP)):
                g = "".join(chr(0xE080 + int(d)) for d in str(val))
                fs = self.STAFF_H * 0.52         # Petaluma digits are ~4 spaces tall: fit each in half the staff
                w = self.metrics.stringWidth(g, "Petaluma", fs)
                self.c.setFillColorRGB(*self.th.staff_ink)
                self.c.setFont("Petaluma", fs)
                self.c.drawString(x + 6 - w / 2, y, g)
            return 15
        self.c.setFillColorRGB(*self.th.staff_ink)
        self.c.setFont("SansB", 12.5)
        self.c.drawCentredString(x + 6, top - self.SP * 2 + 1.4, str(num))
        self.c.drawCentredString(x + 6, top - self.SP * 4 + 1.4, str(den))
        return 15

    def barline(self, x, top, kind):
        c, bot = self.c, top - self.STAFF_H
        c.setStrokeColorRGB(*self.th.staff_ink)
        lw = self.th.barline_width
        c.setLineWidth(lw)
        if kind == "single":
            c.line(x, top, x, bot)
        elif kind == "double":
            c.line(x - 2.8, top, x - 2.8, bot)
            c.line(x, top, x, bot)
        elif kind == "final":
            c.line(x - 5, top, x - 5, bot)
            c.setLineWidth(3.2)
            c.line(x - 1.6, top, x - 1.6, bot)

    def repeat_sign(self, x, top, side):
        c = self.c
        c.setStrokeColorRGB(*self.th.ink)
        c.setFillColorRGB(*self.th.ink)
        sgn = 1 if side == "start" else -1
        c.setLineWidth(3.2)
        c.line(x + sgn * 1.6, top, x + sgn * 1.6, top - self.STAFF_H)
        c.setLineWidth(self.th.barline_width)
        c.line(x + sgn * 5.2, top, x + sgn * 5.2, top - self.STAFF_H)
        for yy in (top - 1.5 * self.SP, top - 2.5 * self.SP):
            c.circle(x + sgn * 9.2, yy, 1.6, stroke=0, fill=1)

    def percent(self, cx, mid):
        if self.th.smufl:
            g = SMUFL["percent"]
            w = self.metrics.stringWidth(g, "Petaluma", self.STAFF_H)
            self.knockout(cx - w / 2 - 2, mid - 9, w + 4, 18)
            self.c.setFillColorRGB(*self.th.ink)
            self.c.setFont("Petaluma", self.STAFF_H)
            self.c.drawString(cx - w / 2, mid, g)
            return
        self.knockout(cx - 9, mid - 8, 18, 16)
        self.c.setFillColorRGB(*self.th.ink)
        self.c.setFont("SansB", 16)
        self.c.drawCentredString(cx, mid - 5.8, "%")

    KEY_LABEL_SIZE = 9

    def key_label(self, x, top, row, key):
        """At a key change: the new key spelled out under the staff ("Key E♭"), below the key signature
        (under the lyrics of notated bars, if any)."""
        below = self.notation_room(row)[1]
        y = top - self.STAFF_H - 10 - below
        self.text(x, y, pretty_chord(f"Key {key}"), self.th.note, self.KEY_LABEL_SIZE, self.th.grey)

    def slash(self, x, mid):
        g = SMUFL["slash"]
        w = self.metrics.stringWidth(g, "Petaluma", self.STAFF_H)
        self.knockout(x - 1, mid - self.SP, w + 2, 2 * self.SP)
        self.c.setFillColorRGB(*self.th.ink)
        self.c.setFont("Petaluma", self.STAFF_H)
        self.c.drawString(x, mid, g)

    def mark_glyph(self, x, y, name, center=False):
        g = SMUFL[name]
        w = self.metrics.stringWidth(g, "Petaluma", self.STAFF_H)
        self.c.setFillColorRGB(*self.th.ink)
        self.c.setFont("Petaluma", self.STAFF_H)
        self.c.drawString(x - w / 2 if center else x, y, g)

    def draw_ties(self, row_start, row_end):
        """Ties between consecutive chords of the row (the arc goes over the chord symbols); a tie to a
        chord on the next row runs to the end of this one and starts again at the next row's start."""
        evs = self.row_events
        if self.tie_carry and evs:
            self.tie_arc(min(row_start, evs[0][1] - 18), evs[0][1] - 2, evs[0][3], False)
        self.tie_carry = False
        for i, (e, xl, xr, y) in enumerate(evs):
            if not e.tie:
                continue
            if i + 1 < len(evs):
                self.tie_arc(xr + 1, evs[i + 1][1] - 2, y, False)
            else:
                self.tie_arc(xr + 1, row_end, y, False)
                self.tie_carry = True

    def knockout(self, x, y, w, h):
        self.c.setFillColorRGB(1, 1, 1)
        self.c.rect(x, y, w, h, stroke=0, fill=1)

    # -- notated zones (MusicXML) ---------------------------------------------------
    NOTE_GLYPHS = {"whole": "", "half": ""}
    REST_GLYPHS = {"whole": "", "half": "", "quarter": "", "eighth": "",
                   "16th": "", "32nd": ""}
    FLAGS = {("eighth", "up"): "", ("eighth", "down"): "",
             ("16th", "up"): "", ("16th", "down"): ""}
    NOTATION_ABOVE = 26     # extra room above the staff in rows with notation (chord symbols)
    NOTATION_BELOW = 22     # extra room below the staff (lyrics, low notes)
    TAB_SP = 6.0            # guitar tablature: space between its six lines
    TAB_H = 5 * TAB_SP
    TAB_GAP = 10            # "both": between the staff (or its lyrics) and the tablature
    RHYTHM_ROOM = 20        # "tab": stems and beams under the tablature
    TAB_NUM = 7.6           # fret numbers

    def row_has_notation(self, row) -> bool:
        return any(b.notation for b in row)

    def notation_room(self, row) -> tuple[float, float]:
        """Extra space (above, below) a row needs for notated bars: chord symbols and high notes
        above; lyrics and low notes below. Rows without notation need none."""
        nbars = [b for b in row if b.notation]
        if not nbars:
            return 0.0, 0.0
        notes = [n for b in nbars for n in b.notation.notes if n.step]
        if self.notation_mode == "tab":              # six lines in place of the staff, the rhythm under them
            above = self.NOTATION_ABOVE if any(e.chord for b in nbars for e in b.events) else 8
            below = (self.TAB_H - self.STAFF_H) + self.RHYTHM_ROOM + (9 if any(n.tuplet for n in notes) else 0)
            return above, below + (self.NOTATION_BELOW if any(n.lyric for n in notes) else 0)
        high = max([n.diatonic - 30 for n in notes] + [0])
        low = min([n.diatonic - 30 for n in notes] + [8])
        above = (self.NOTATION_ABOVE if any(e.chord for b in nbars for e in b.events) else 8)
        above += max(0, high - 7) * self.SP / 2          # notes/stems over the staff push chords up
        if any(n.tuplet for n in notes):
            above += 1.2 * self.SP
        below = self.NOTATION_BELOW if any(n.lyric for n in notes) else 0
        below += max(0, 1 - low) * self.SP / 2
        if self.notation_mode == "both":             # the tablature under the staff (and the lyrics)
            below += self.TAB_GAP + self.TAB_H + 4
        return above, below

    VOLTA_ROOM = 15
    MARK_ROOM = 21          # lane above the endings for segno / coda signs and D.S., To Coda, Fine
    MARK_ROOM_LOW = 4       # rows without lyrics: the signs sit just above the staff, where lyrics would go
    TEXT_SIZE = 10.5        # {text: …} lines
    TEXT_LEAD = 14

    def row_has_volta(self, row) -> bool:
        return self.volta_carry is not None or any(b.volta for b in row)

    def row_has_marks(self, row) -> bool:
        return any(b.marks_start or b.marks_end for b in row)

    NOTE_SIZE = 8.5         # chord annotations [A "1°"]
    NOTE_INK = (0.25, 0.25, 0.3)
    NOTE_ROOM = 10          # their own lane, above the lyrics, in rows that have both

    def row_has_lyrics(self, row) -> bool:
        return any(e.lyric for b in row for e in b.events)

    def row_has_notes(self, row) -> bool:
        return any(e.note for b in row for e in b.events)

    def note_room(self, row) -> float:
        return self.NOTE_ROOM if self.row_has_notes(row) and self.row_has_lyrics(row) else 0.0

    def marks_low(self, row) -> bool:
        """Signs right above the staff: only when nothing else uses that space (no lyrics, annotations,
        endings or notated bars in the row)."""
        return not (self.row_has_lyrics(row) or self.row_has_notes(row) or self.row_has_volta(row)
                    or self.row_has_notation(row))

    def mark_room(self, row) -> float:
        if not self.row_has_marks(row):
            return 0.0
        return self.MARK_ROOM_LOW if self.marks_low(row) else self.MARK_ROOM

    def row_height(self, row) -> float:
        above, below = self.notation_room(row)
        gap = self.st.row_height - 20 - self.STAFF_H          # the free space under a plain row's staff
        return (self.st.row_height + gap * (self.row_spacing - 1) + above + below
                + (self.VOLTA_ROOM if self.row_has_volta(row) else 0) + self.mark_room(row) + self.note_room(row))

    # -- navigation marks and free text -------------------------------------------
    END_MARK_TEXT = {"to_coda": "To Coda", "fine": "Fine", "dc": "D.C.", "ds": "D.S."}

    def end_mark_text(self, name: str, value: str) -> str:
        if name in ("dc", "ds"):
            return f"{self.END_MARK_TEXT[name]} {value}".strip()
        return value or self.END_MARK_TEXT[name]

    def sign(self, x, y, name, size) -> float:
        """Segno / coda sign (SMuFL, Petaluma in every theme) in ink; returns its width."""
        g = SMUFL[name]
        self.c.setFillColorRGB(*self.th.ink)
        self.c.setFont("Petaluma", size)
        self.c.drawString(x, y, g)
        return self.metrics.stringWidth(g, "Petaluma", size)

    def draw_marks(self, row, spans, base):
        """Signs at the start of a bar (segno, coda) and instructions at its end (To Coda ⊕, Fine,
        D.S. al Coda…), on one baseline above the endings."""
        size, font = 12.5, self.th.label
        sign_size = self.STAFF_H * 0.85
        for b, (x0, x1) in zip(row, spans):
            x = x0 + 4 + (8 if b.repeat_start else 0)
            for name in b.marks_start:
                x += self.sign(x, base - 1, name, sign_size) + 4
            if b.marks_end:
                parts = [self.end_mark_text(n, v) for n, v in b.marks_end]
                text = "   ".join(parts)
                coda = any(n == "to_coda" for n, _ in b.marks_end)
                gw = self.metrics.stringWidth(SMUFL["coda"], "Petaluma", sign_size) + 3 if coda else 0
                right = x1 - 3
                if b.repeat_end > 2:                       # keep clear of the "x3" over the repeat sign
                    right -= self.text_width(f"x{b.repeat_end}", self.th.chord, 13) + 6
                tw = self.text_width(text, font, size)
                self.text(right - gw - tw, base, text, font, size, self.th.ink, bold=self.th.bold_chords)
                if coda:
                    self.sign(right - gw + 3, base - 1, "coda", sign_size)

    def wrap(self, text, font, size, width) -> list[str]:
        lines, cur = [], ""
        for word in text.split():
            trial = f"{cur} {word}".strip()
            if cur and self.text_width(trial, font, size) > width:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        return lines + ([cur] if cur else [])

    def text_lines(self, texts) -> list[str]:
        width = self.page_w - 2 * self.st.margin
        return [ln for t in texts for ln in self.wrap(t, self.th.note, self.TEXT_SIZE, width)]

    def texts_height(self, texts) -> float:
        n = len(self.text_lines(texts))
        return n * self.TEXT_LEAD + 6 if n else 0

    def draw_texts(self, texts):
        """{text: …} lines between rows: full width, wrapped, in the theme's note font."""
        for ln in self.text_lines(texts):
            self.ensure(self.TEXT_LEAD + 6)
            self.text(self.st.margin, self.y - self.TEXT_LEAD + 3, ln, self.th.note, self.TEXT_SIZE, self.th.lyric_ink)
            self.y -= self.TEXT_LEAD
        if texts:
            self.y -= 6

    def draw_voltas(self, row, xs, line_y):
        """Ending brackets: horizontal line with the number; closed ends hook down. A bracket that
        runs past the end of a line continues on the next one."""
        c = self.c
        c.setStrokeColorRGB(*self.th.ink)
        c.setLineWidth(0.9)
        hook = 11
        open_span = None
        if self.volta_carry is not None:
            open_span = [xs[0][0] + 2, None, False]
            self.volta_carry = None
        for b, (x0, x1) in zip(row, xs):
            if b.volta:
                open_span = [x0 + 3, b.volta, True]
            if open_span and b.volta_end:
                xa, label, start_hook = open_span
                xb = x1 - 4
                c.line(xa, line_y, xb, line_y)
                if start_hook:
                    c.line(xa, line_y, xa, line_y - hook)
                if b.volta_end == "hook":
                    c.line(xb, line_y, xb, line_y - hook)
                if label:
                    self.text(xa + 3, line_y - 10, label, self.th.text, 10, bold=True)
                open_span = None
        if open_span:                                     # continues on the next line
            xa, label, start_hook = open_span
            xb = xs[-1][1] - 2
            c.line(xa, line_y, xb, line_y)
            if start_hook:
                c.line(xa, line_y, xa, line_y - hook)
            if label:
                self.text(xa + 3, line_y - 10, label, self.th.text, 10, bold=True)
            self.volta_carry = True

    def note_accidentals(self, notes: list[Note], key: str) -> dict:
        sig = key_signature(key)
        default = {s: 0 for s in STEPS}
        for s in ("FCGDAEB"[:sig] if sig > 0 else ""):
            default[s] = 1
        for s in ("BEADGCF"[:-sig] if sig < 0 else ""):
            default[s] = -1
        state, out = {}, {}
        for n in notes:
            if n.step is None:
                continue
            expected = state.get((n.step, n.octave), default[n.step])
            if n.tie_stop:
                state[(n.step, n.octave)] = n.alter
            elif n.alter != expected:
                out[id(n)] = {-1: "flat", 0: "natural", 1: "sharp", -2: "flat", 2: "sharp"}[n.alter]
                state[(n.step, n.octave)] = n.alter
        return out

    def notation_need(self, b: Bar) -> float:
        notes = b.notation.notes
        acc = self.note_accidentals(notes, b.key)
        need = 10.0
        for t in sorted({n.start for n in notes if not n.chord}):
            at = [n for n in notes if n.start == t]
            need += 15 + (9 if any(id(n) in acc for n in at) else 0) + (5 if any(n.dots for n in at) else 0)
        chords = sum(self.chord_width(e.chord, self.th.chord_fit_size) + 8 for e in b.events if e.chord)
        return max(need, chords)

    def nglyph(self, x, y, g, color=None):
        self.c.setFillColorRGB(*(color or self.th.ink))
        self.c.setFont("Petaluma", self.STAFF_H)
        self.c.drawString(x, y, g)
        return self.metrics.stringWidth(g, "Petaluma", self.STAFF_H)

    def tie_arc(self, x1, x2, y, below):
        c, sp = self.c, self.SP
        sgn = -1 if below else 1
        y0 = y + sgn * 0.75 * sp
        h = sgn * min(1.1 * sp, 0.15 * (x2 - x1) + 0.4 * sp)
        p = c.beginPath()
        p.moveTo(x1, y0)
        p.curveTo(x1 + (x2 - x1) * 0.25, y0 + h, x2 - (x2 - x1) * 0.25, y0 + h, x2, y0)
        p.curveTo(x2 - (x2 - x1) * 0.25, y0 + h * 0.72, x1 + (x2 - x1) * 0.25, y0 + h * 0.72, x1, y0)
        p.close()
        c.setFillColorRGB(*self.th.ink)
        c.setStrokeColorRGB(*self.th.ink)
        c.setLineWidth(0.3)
        c.drawPath(p, stroke=1, fill=1)

    def flush_ties(self, x_end):
        for (x1, y, below) in self.pending_ties.values():
            self.tie_arc(x1, x_end, y, below)
        self.pending_ties = {}

    def draw_notation(self, b: Bar, ax, right, top):
        c, sp, th = self.c, self.SP, self.th
        notes = b.notation.notes
        bottom = top - self.STAFF_H
        ypos = lambda n: bottom + (n.diatonic - 30) * sp / 2          # 30 = E4, bottom line
        hw = self.metrics.stringWidth("", "Petaluma", self.STAFF_H)
        acc = self.note_accidentals(notes, b.key)

        # ---- horizontal spacing: one column per onset (notes and chord symbols)
        times = sorted({n.start for n in notes if not n.chord} | {e.start for e in b.events if e.chord})
        if not times:
            return
        weights = []
        for i, t in enumerate(times):
            d = (times[i + 1] if i + 1 < len(times) else b.beats) - t
            at = [n for n in notes if n.start == t]
            w = 0.55 + max(d, 0.25) ** 0.6
            w += 0.45 if any(id(n) in acc for n in at) else 0
            w += 0.25 if any(n.dots for n in at) else 0
            weights.append(w)
        usable = right - ax - hw - 4
        xs, acc_w = {}, 0.0
        for t, w in zip(times, weights):
            xs[t] = ax + 2 + usable * acc_w / sum(weights)
            acc_w += w
        first_acc = any(id(n) in acc for n in notes if n.start == times[0])
        if first_acc:
            for t in xs:
                xs[t] += 5 * (1 - (xs[t] - ax) / max(right - ax, 1))

        # ---- group notes into stems (head + stacked chord notes)
        stems = []
        for n in notes:
            if n.chord and stems:
                stems[-1]["heads"].append(n)
            else:
                stems.append({"n": n, "heads": [n]})

        # beam groups (from the file; else auto-beam eighths/16ths within each beat)
        has_beams = any(s["n"].beams for s in stems)
        groups, cur = [], []
        for s in stems:
            n = s["n"]
            if n.step is None or NOTE_TYPES.get(n.type, 1) >= 1:
                if cur:
                    groups.append(cur)
                cur = []
                continue
            if has_beams:
                st = n.beams.get(1)
                if st == "begin":
                    cur = [s]
                elif st in ("continue", "end") and cur:
                    cur.append(s)
                    if st == "end":
                        groups.append(cur)
                        cur = []
            else:
                if cur and int(cur[-1]["n"].start) != int(n.start):
                    groups.append(cur)
                    cur = []
                cur.append(s)
        if cur:
            groups.append(cur)
        groups = [g for g in groups if len(g) > 1]
        in_group = {id(s): g for g in groups for s in g}

        # stem direction and natural tips
        for s in stems:
            n = s["n"]
            s["x"] = xs[n.start]
            if n.step is None:
                continue
            ys = [ypos(h) for h in s["heads"]]
            s["ys"] = ys
            avg = sum(h.diatonic - 30 for h in s["heads"]) / len(s["heads"])
            s["up"] = avg < 4
        for g in groups:
            up = sum(sum(h.diatonic - 30 for h in s["heads"]) / len(s["heads"]) for s in g) / len(g) < 4
            for s in g:
                s["up"] = up
        for s in stems:
            if s["n"].step is None or s["n"].type == "whole":
                continue
            up = s["up"]
            s["stem_x"] = s["x"] + (hw - 0.45 if up else 0.45)
            s["base_y"] = (min(s["ys"]) if up else max(s["ys"]))
            far = max(s["ys"]) if up else min(s["ys"])
            s["tip"] = far + (3.5 * sp if up else -3.5 * sp)

        # beams: straight line between end tips, slope limited, every stem >= 2.75 spaces
        for g in groups:
            up = g[0]["up"]
            x0, x1 = g[0]["stem_x"], g[-1]["stem_x"]
            y0, y1 = g[0]["tip"], g[-1]["tip"]
            slope = 0.0 if x1 == x0 else max(-0.12, min(0.12, (y1 - y0) / (x1 - x0)))
            line = lambda x, y0=y0, x0=x0, slope=slope: y0 + slope * (x - x0)
            shift = 0.0
            for s in g:
                far = max(s["ys"]) if up else min(s["ys"])
                need = far + (2.75 * sp if up else -2.75 * sp)
                y = line(s["stem_x"]) + shift
                if up and y < need:
                    shift += need - y
                if not up and y > need:
                    shift -= y - need
            for s in g:
                s["tip"] = line(s["stem_x"]) + shift
            g_info = (up, line, shift)
            for s in g:
                s["beam"] = g_info

        ink = th.ink
        hi, lo = top, bottom
        if self.notation_mode == "tab":              # fret numbers on six lines, the rhythm under them
            lo = self.draw_tab(stems, groups, hw, top, rhythm=True, ax=ax, right=right)
        else:
            if self.notation_mode == "both":         # the tablature goes under the row (draw_row)
                self.row_tabs.append((stems, groups, hw))
            # ---- draw: ledger lines, heads, accidentals, dots
            c.setStrokeColorRGB(*th.staff_ink)
            c.setLineWidth(th.staff_line_width + 0.2)
            for s in stems:
                n, x = s["n"], s["x"]
                if n.step is None:
                    if n.measure_rest or (n.type == "whole" and len(stems) == 1):
                        gx = (ax + right) / 2 - 5
                        self.nglyph(gx, top - sp, self.REST_GLYPHS["whole"])
                    else:
                        self.nglyph(x, top - 2 * sp, self.REST_GLYPHS.get(n.type, self.REST_GLYPHS["quarter"]))
                        if n.dots:
                            c.setFillColorRGB(*ink)
                            c.circle(x + hw + 0.5 * sp, top - 1.5 * sp, 0.22 * sp, stroke=0, fill=1)
                    continue
                for h in s["heads"]:
                    pos = h.diatonic - 30
                    y = ypos(h)
                    for p in (range(-2, pos - 1, -2) if pos <= -2 else range(10, pos + 1, 2) if pos >= 10 else []):
                        ly = bottom + p * sp / 2
                        c.setStrokeColorRGB(*th.staff_ink)
                        c.line(x - 0.45 * sp, ly, x + hw + 0.45 * sp, ly)
                    self.nglyph(x, y, self.NOTE_GLYPHS.get(h.type, ""))
                    if id(h) in acc:
                        g = SMUFL[acc[id(h)]]
                        aw = self.metrics.stringWidth(g, "Petaluma", self.STAFF_H)
                        self.nglyph(x - aw - 0.25 * sp, y, g)
                    for k in range(h.dots):
                        dy = sp / 2 if pos % 2 == 0 else 0
                        c.setFillColorRGB(*ink)
                        c.circle(x + hw + (0.55 + 0.5 * k) * sp, y + dy, 0.22 * sp, stroke=0, fill=1)
                    hi, lo = max(hi, y + sp), min(lo, y - sp)
                    # ties
                    key_ = h.midi
                    if h.tie_stop:
                        if key_ in self.pending_ties:
                            x1, ty, below = self.pending_ties.pop(key_)
                            self.tie_arc(x1, x - 1, ty, below)
                        else:
                            self.tie_arc(x - 14, x - 1, y, s.get("up", True))
                    if h.tie_start:
                        self.pending_ties[key_] = (x + hw + 1, y, s.get("up", True))

                # stems and flags
                if "tip" in s:
                    c.setStrokeColorRGB(*ink)
                    c.setLineWidth(0.85)
                    c.line(s["stem_x"], s["base_y"], s["stem_x"], s["tip"])
                    hi, lo = max(hi, s["tip"]), min(lo, s["tip"])
                    if "beam" not in s and n.type in ("eighth", "16th"):
                        up = s["up"]
                        self.nglyph(s["stem_x"] - (0.4 if up else 0.45), s["tip"], self.FLAGS[(n.type, "up" if up else "down")])

            # beams (primary + secondary for 16ths)
            thick = 0.5 * sp
            for g in groups:
                up, line, shift = g[0]["beam"]
                sgn = -1 if up else 1                         # beam thickness grows towards the heads

                def beam(xa, xb, level):
                    off = sgn * level * 0.75 * sp
                    ya, yb = line(xa) + shift + off, line(xb) + shift + off
                    p = c.beginPath()
                    p.moveTo(xa, ya)
                    p.lineTo(xb, yb)
                    p.lineTo(xb, yb + sgn * thick)
                    p.lineTo(xa, ya + sgn * thick)
                    p.close()
                    c.setFillColorRGB(*ink)
                    c.drawPath(p, stroke=0, fill=1)

                beam(g[0]["stem_x"] - 0.4, g[-1]["stem_x"] + 0.4, 0)
                for i, s in enumerate(g):
                    if s["n"].type != "16th":
                        continue
                    nxt = g[i + 1] if i + 1 < len(g) else None
                    prv = g[i - 1] if i > 0 else None
                    if nxt and nxt["n"].type == "16th":
                        beam(s["stem_x"] - 0.4, nxt["stem_x"] + 0.4, 1)
                    elif not (prv and prv["n"].type == "16th"):
                        stub = 1.1 * sp
                        if nxt:
                            beam(s["stem_x"], s["stem_x"] + stub, 1)
                        else:
                            beam(s["stem_x"] - stub, s["stem_x"], 1)

            # ---- tuplets: SMuFL digit over the beam, or a bracket when not all beamed together
            tgroups, curt = [], []
            for s in stems:
                n = s["n"]
                if not n.tuplet:
                    if curt:
                        tgroups.append(curt)
                    curt = []
                    continue
                if n.tuplet_start and curt:
                    tgroups.append(curt)
                    curt = []
                curt.append(s)
                span = sum(x["n"].dur for x in curt)
                normal_span = NOTE_TYPES.get(curt[0]["n"].type, 1) * n.tuplet[1] * (1.5 if curt[0]["n"].dots else 1)
                if n.tuplet_stop or (not any(x["n"].tuplet_start for x in curt) and span >= normal_span - 1e-6):
                    tgroups.append(curt)
                    curt = []
            if curt:
                tgroups.append(curt)
            for tg in tgroups:
                actual = tg[0]["n"].tuplet[0]
                pitched = [x for x in tg if "ys" in x]
                ups = [x["up"] for x in pitched if "up" in x]
                above = (sum(ups) >= len(ups) / 2) if ups else True
                x0 = tg[0]["x"]
                x1 = tg[-1]["x"] + hw
                cx = (x0 + x1) / 2
                beamed = all("beam" in x for x in tg) and len({id(x["beam"]) for x in tg}) == 1
                ext = []
                for x in tg:
                    ext += x.get("ys", [top - 2 * sp]) + ([x["tip"]] if "tip" in x else [])
                if above:
                    y = max(ext + [top]) + 0.9 * sp
                else:
                    y = min(ext + [bottom]) - 0.9 * sp - 0.9 * sp
                digit = "".join(chr(0xE880 + int(d)) for d in str(actual))
                dw = self.metrics.stringWidth(digit, "Petaluma", self.STAFF_H * 0.75)
                c.setFillColorRGB(*ink)
                c.setFont("Petaluma", self.STAFF_H * 0.75)
                c.drawString(cx - dw / 2, y + (0 if above else 0.2 * sp), digit)
                if not beamed:                                   # bracket with a gap for the number
                    c.setStrokeColorRGB(*ink)
                    c.setLineWidth(0.7)
                    yb = y + 0.45 * sp
                    hook = -0.6 * sp if above else 0.6 * sp
                    c.line(x0, yb + hook, x0, yb)
                    c.line(x0, yb, cx - dw / 2 - 2, yb)
                    c.line(cx + dw / 2 + 2, yb, x1, yb)
                    c.line(x1, yb, x1, yb + hook)
                if above:
                    hi = max(hi, y + 1.2 * sp)
                else:
                    lo = min(lo, y - 0.3 * sp)

        # ---- chord symbols above, lyrics below
        chords = [e for e in b.events if e.chord]
        size = th.chord_size
        for i, e in enumerate(chords):
            nx = xs[chords[i + 1].start] if i + 1 < len(chords) else right + 2
            limit = nx - xs[e.start] - 7
            w = self.event_width(e, th.chord_size)
            if w > limit:
                size = min(size, th.chord_size * limit / w)
        size = max(th.chord_min_size, size)
        # chord symbols and lyrics are drawn once per row (draw_row), all on the same line:
        # above the highest note of the whole row, below its lowest one
        for e in chords:
            self.row_chords.append((xs[e.start] - 1, e.chord, size))
        for s in stems:
            n = s["n"]
            if n.lyric:
                w = self.text_width(n.lyric, th.text, th.lyric_size)
                self.row_lyrics.append((s["x"] + hw / 2 - w / 2, n.lyric))
        self.row_hi = max(self.row_hi, hi)
        self.row_lo = min(self.row_lo, lo)

    # -- guitar tablature --------------------------------------------------------
    def tab_lines(self, x0, x1, top):
        self.c.setStrokeColorRGB(*self.th.staff_lines)
        self.c.setLineWidth(self.th.staff_line_width)
        for i in range(self.tab_n):
            self.c.line(x0, top - i * self.TAB_SP, x1, top - i * self.TAB_SP)

    def tab_clef(self, x, top) -> float:
        """T A B written down the left of the tablature, or the names of the open strings on their lines
        for any tuning but the standard one; returns the width (as the treble clef's)."""
        if self.tuning != tab_mod.STANDARD:
            names = tab_mod.string_names(self.tuning)
            size = self.TAB_SP * 1.1
            for i, name in enumerate(reversed(names)):            # highest string on top
                w = self.text_width(name, self.th.label, size)
                self.knockout(x + 9 - w / 2 - 1, top - i * self.TAB_SP - size * 0.42, w + 2, size * 0.84)
                self.text(x + 9 - w / 2, top - i * self.TAB_SP - size * 0.34, name, self.th.label, size,
                          self.th.staff_ink, bold=True)
            return 24 if self.th.smufl else 22
        size = self.TAB_SP * 1.45
        for k, ch in enumerate("TAB"):
            w = self.text_width(ch, self.th.label, size)
            self.text(x + 8 - w / 2, top - self.TAB_H / 2 - size * 0.36 + (1 - k) * 1.62 * self.TAB_SP, ch,
                      self.th.label, size,
                      self.th.staff_ink, bold=True)
        return 24 if self.th.smufl else 22

    def tab_barline(self, x, top, bottom):
        self.c.setStrokeColorRGB(*self.th.staff_ink)
        self.c.setLineWidth(self.th.barline_width)
        self.c.line(x, top, x, bottom)

    def draw_tab(self, stems, groups, hw, tab_top, rhythm, ax=None, right=None) -> float:
        """Fret numbers of a notated bar on six lines from `tab_top` (1st string on top), aligned with
        the note columns; with `rhythm`, stems, beams, flags, dots, rests and tuplet numbers under the
        lines. Returns the lowest y used."""
        c, th, sp = self.c, self.th, self.TAB_SP
        bottom = tab_top - self.TAB_H
        low = bottom
        size = self.TAB_NUM
        y_end = bottom - 3 - 12                       # where the stems end (and the beams sit)
        for s in stems:
            n = s["n"]
            cx = s["x"] + hw / 2
            if n.step is None:
                if rhythm:
                    if n.measure_rest and ax is not None:
                        self.nglyph((ax + right) / 2 - 5, tab_top - 2 * sp, self.REST_GLYPHS["whole"])
                    else:
                        self.nglyph(cx - hw / 2, tab_top - 2.5 * sp,
                                    self.REST_GLYPHS.get(n.type, self.REST_GLYPHS["quarter"]))
                continue
            for h in s["heads"]:
                if h.fret is None:
                    continue
                y = tab_top - (self.tab_n - 1 - h.string) * sp
                label = f"({h.fret})" if h.tie_stop else str(h.fret)
                w = self.text_width(label, th.text, size)
                self.knockout(cx - w / 2 - 1, y - size * 0.4, w + 2, size * 0.8)
                self.text(cx - w / 2, y - size * 0.34, label, th.text, size, th.ink)
            if rhythm and n.type != "whole":
                length = 8 if n.type == "half" else 12
                c.setStrokeColorRGB(*th.ink)
                c.setLineWidth(0.85)
                c.line(cx, bottom - 3, cx, bottom - 3 - length)
                s["tab_x"] = cx
                if n.dots:
                    c.setFillColorRGB(*th.ink)
                    for k in range(n.dots):
                        c.circle(cx + 2.6 + 2.2 * k, bottom - 3 - length + 1.6, 0.85, stroke=0, fill=1)
                if "beam" not in s and n.type in ("eighth", "16th", "32nd"):
                    levels = {"eighth": 1, "16th": 2, "32nd": 3}[n.type]
                    for k in range(levels):
                        yy = bottom - 3 - length + 2.6 * k
                        c.line(cx, yy, cx + 4, yy + 3.5)
                low = min(low, bottom - 3 - length)
        if not rhythm:
            return low
        for g in groups:                              # flat beams at the end of the stems
            xs = [s["x"] + hw / 2 for s in g]
            c.setFillColorRGB(*th.ink)
            c.rect(xs[0] - 0.4, y_end, xs[-1] - xs[0] + 0.8, 1.9, stroke=0, fill=1)
            for i, s in enumerate(g):
                if s["n"].type not in ("16th", "32nd"):
                    continue
                nxt = g[i + 1] if i + 1 < len(g) else None
                prv = g[i - 1] if i > 0 else None
                if nxt and nxt["n"].type in ("16th", "32nd"):
                    c.rect(xs[i] - 0.4, y_end + 3, xs[i + 1] - xs[i] + 0.8, 1.9, stroke=0, fill=1)
                elif not (prv and prv["n"].type in ("16th", "32nd")):
                    stub = 4.5
                    x0 = xs[i] if nxt else xs[i] - stub
                    c.rect(x0, y_end + 3, stub, 1.9, stroke=0, fill=1)
            low = min(low, y_end)
        run: list = []                               # tuplet numbers under the rhythm
        for s in stems + [None]:
            n = s["n"] if s else None
            if n is not None and n.tuplet and not (n.tuplet_start and run):
                run.append(s)
                if not n.tuplet_stop:
                    continue
            if run:
                x0, x1 = run[0]["x"] + hw / 2, run[-1]["x"] + hw / 2
                label = str(run[0]["n"].tuplet[0])
                w = self.text_width(label, th.text, 7.5)
                self.text((x0 + x1) / 2 - w / 2, low - 8, label, th.text, 7.5, th.ink)
                low = min(low, low - 9)
                run = [s] if (n is not None and n.tuplet and n.tuplet_start and not n.tuplet_stop) else []
        return low

    def row_lines(self, left, x, widths, row, top):
        """The staff of a row; with tablature only, six lines under the notated bars instead."""
        if self.notation_mode != "tab" or not any(b.notation for b in row):
            self.staff_lines(left, x + sum(widths), top)
            return
        spans = [(left, x, row[0].notation is not None)]
        bx = x
        for b, w in zip(row, widths):
            spans.append((bx, bx + w, b.notation is not None))
            bx += w
        for x0, x1, tabbed in spans:
            if x1 > x0:
                (self.tab_lines if tabbed else self.staff_lines)(x0, x1, top)

    def draw_row_tab(self, row, spans, left, tab_top):
        """"both": the six lines under the notated bars of the row, with their bar lines and numbers."""
        bottom = tab_top - self.TAB_H
        for i, (b, (x0, x1)) in enumerate(zip(row, spans)):
            if not b.notation:
                continue
            start = left if i == 0 else x0
            self.tab_lines(start, x1, tab_top)
            if i == 0:
                self.tab_clef(left, tab_top)
            elif not row[i - 1].notation:
                self.tab_barline(x0, tab_top, bottom)
            self.tab_barline(x1, tab_top, bottom)
        for stems, groups, hw in self.row_tabs:
            self.draw_tab(stems, groups, hw, tab_top, rhythm=False)

    # -- layout --------------------------------------------------------------
    def prefix_width(self, row, first_row):
        b0 = row[0]
        prev = key_signature(b0.prev_key) if b0.key_change else None
        w = (24 if self.th.smufl else 22) + 2 + self.key_signature_width(key_signature(b0.key), prev) + 2
        if first_row or b0.time_change:
            w += 19
        return w

    def bar_extra(self, b: Bar, first_in_row: bool) -> float:
        extra = 7 + (8 if b.repeat_start else 0)
        if not first_in_row and b.key_change:
            extra += self.key_signature_width(key_signature(b.key), key_signature(b.prev_key))
        if not first_in_row and b.time_change:
            extra += 17
        return extra

    def bar_need(self, b: Bar, first_in_row: bool = False) -> float:
        """Width needed so every chord fits at chord_fit_size without overlapping."""
        if b.notation:
            return self.bar_extra(b, first_in_row) + (12 if b.repeat_end else 3) + self.notation_need(b)
        chords = [e for e in b.events if e.chord]
        cell = 0.0
        for j, e in enumerate(chords):
            end = chords[j + 1].start if j + 1 < len(chords) else b.beats
            w = self.event_width(e, self.th.chord_fit_size) + 8
            cell = max(cell, w / max(end - e.start, HALF))
        return self.bar_extra(b, first_in_row) + (12 if b.repeat_end else 3) + cell * b.beats

    def slots(self, b: Bar, capacity: int) -> int:
        """Uniform mode: a crowded bar spans 2 (or more) standard bar widths,
        so the column grid is preserved and chords never shrink below fit size."""
        if self.bar_width != "uniform":
            return 1
        return max(1, min(capacity, math.ceil(self.bar_need(b) / self.uniform_bw - 1e-6)))

    def build_rows(self, sec: Section):
        bpl = sec.bars_per_line or self.bpl_default
        rows, row, used = [], [], 0.0
        fit_avail = self.page_w - 2 * self.st.margin - 60
        late_volta, break_next = False, False
        for b in sec.bars:
            if self.bar_width == "uniform":
                cost, cap = self.slots(b, bpl), bpl
            else:   # fit: wrap only when what the bars really need would not fit (bar_widths shares the rest)
                cost = self.bar_need(b, not row)
                cap = fit_avail
            full = len(row) >= bpl if self.bar_width == "fit" else False
            # a 2nd (3rd…) ending starts its own line, right-aligned under the 1st ending
            starts_late = bool(b.volta) and not b.volta.startswith("1.")
            if row and (b.break_before or full or used + cost > cap + 1e-6 or starts_late or break_next):
                if self.bar_width == "fit" and not (b.break_before or starts_late or break_next):
                    self.full_rows.add(id(row[0]))   # closed for lack of room: it spans the whole width
                rows.append(row)
                row, used = [], 0.0
            break_next = False
            if starts_late:
                late_volta = True
                self.right_rows.add(id(b))           # keyed by the row's first bar
            row.append(b)
            used += cost
            if late_volta and b.volta_end:
                late_volta, break_next = False, True  # nothing else shares the right-aligned line
        if row:
            rows.append(row)
        return rows, bpl

    def section_notation(self, sec: Section) -> str:
        if self.notation_force:
            return self.song_notation
        return sec.notation if sec.notation in NOTATIONS else self.song_notation

    def assign_tab(self):
        """String and fret for the notes of every run of consecutive notated bars (tab.py)."""
        capo = int(self.song.meta.get("capo", "0")) if str(self.song.meta.get("capo", "0")).strip().isdigit() else 0
        seen = set(self.song.warnings)
        for sec in self.song.sections:
            run: list = []
            for b in sec.bars + [None]:
                if b is not None and b.notation:
                    run.append(b.notation.notes)
                    continue
                if run:
                    for w in tab_mod.assign(run, capo, self.tuning):
                        if w not in seen:
                            seen.add(w)
                            self.song.warnings.append(w)
                run = []

    def section_mode(self, sec: Section) -> str:
        """Bar width of a section: its own {bar_width}, else the song's (header or app option)."""
        return sec.bar_width if sec.bar_width in ("uniform", "fit") else self.song_bar_width

    def plan(self):
        self.right_rows = set()
        self.full_rows: set[int] = set()        # fit rows that wrapped because the next bar did not fit
        # the grid (uniform bar width, aligned columns) is shared by all the uniform sections
        uniform = [s for s in self.song.sections if self.section_mode(s) == "uniform"]
        self.max_bars = max([s.bars_per_line or self.bpl_default for s in uniform] or [4])
        self.max_prefix = self.prefix_width([Bar(4, 4, self.song.meta["key"])], True)
        for _ in range(3):                      # prefix width and row breaks depend on each other
            self.uniform_bw = (self.page_w - 2 * self.st.margin - self.max_prefix) / self.max_bars
            self.layout = []
            self.full_rows = set()
            for sec in self.song.sections:
                self.bar_width = self.section_mode(sec)
                rows, bpl = self.build_rows(sec)
                self.layout.append((sec, rows, bpl))
            self.bar_width = self.song_bar_width
            flat = [(r, i == 0 and j == 0) for i, (sec, rows, _) in enumerate(self.layout) for j, r in enumerate(rows)
                    if self.section_mode(sec) == "uniform"]
            new_prefix = max(self.prefix_width(r, f) for r, f in flat) if flat else 60
            if abs(new_prefix - self.max_prefix) < 0.5:
                break
            self.max_prefix = new_prefix

    def bar_widths(self, row, bpl, x):
        avail = self.page_w - self.st.margin - x
        if self.bar_width == "uniform":
            widths = [self.uniform_bw * self.slots(b, bpl) for b in row]
        else:
            base = avail / bpl
            ref = row[0].beats
            needs = [self.bar_need(b, i == 0) for i, b in enumerate(row)]
            prefs = [base * b.beats / ref + (self.bar_extra(b, i == 0) - 7) for i, b in enumerate(row)]
            widths = [max(p, n) for p, n in zip(prefs, needs)]
            if len(row) == bpl or id(row[0]) in self.full_rows or sum(widths) > avail:
                widths = self.share(prefs, needs, avail)
        return widths

    @staticmethod
    def share(prefs: list[float], needs: list[float], avail: float) -> list[float]:
        """Widths summing to `avail`, proportional to `prefs` but never below `needs`: bars that need
        more keep their need, the others share what is left. If even the needs do not fit, scale them."""
        if sum(needs) >= avail:
            k = avail / sum(needs)
            return [n * k for n in needs]
        fixed: set[int] = set()
        while True:
            left = avail - sum(needs[i] for i in fixed)
            free = [i for i in range(len(prefs)) if i not in fixed]
            total = sum(prefs[i] for i in free)
            widths = [needs[i] if i in fixed else prefs[i] * left / total for i in range(len(prefs))]
            short = [i for i in free if widths[i] < needs[i] - 1e-9]
            if not short:
                return widths
            fixed.update(short)

    # -- drawing -------------------------------------------------------------
    def run(self) -> DisplayList:
        self.plan()
        self.header()
        first_row = True
        last_bar = self.song.bars[-1] if self.song.bars else None
        for sec, rows, bpl in self.layout:
            self.bar_width = self.section_mode(sec)
            self.notation_mode = self.section_notation(sec)
            first_h = (self.texts_height(rows[0][0].text_before) + self.row_height(rows[0])) if rows else \
                self.texts_height(sec.text_after) or self.st.row_height
            self.ensure(self.st.section_height + first_h)
            self.section_header(sec)
            for row in rows:
                h = self.row_height(row)
                if row[0].text_before:
                    self.ensure(self.texts_height(row[0].text_before) + h)   # the note stays with its row
                    self.draw_texts(row[0].text_before)
                self.ensure(h)
                self.draw_row(row, bpl, first_row, row[-1] is last_bar)
                first_row = False
                self.y -= h
            self.draw_texts(sec.text_after)
        self.footer()
        self.c.save()
        dl = self.c.dl
        dl.fonts = {n: p for n, p in self.metrics.paths().items() if n in fonts.fonts_for_theme(self.theme_name)}
        dl.warnings = list(self.song.warnings)
        return dl

    def custom_section_colors(self) -> dict:
        """{section_colors: intro=#3366ff, verse=#33cc66, chorus=#ff9900, Bridge=#ff33cc}
        Keys match a section label, its type, or its group (verse, chorus, bridge, instrumental, frame)."""
        if not hasattr(self, "_custom_colors"):
            self._custom_colors = {}
            for part in re.split(r"[,;]", self.song.meta.get("section_colors", "")):
                k, _, v = part.partition("=")
                if k.strip() and re.fullmatch(r"#?[0-9a-fA-F]{6}", v.strip()):
                    self._custom_colors[k.strip().lower()] = hex_rgb(v.strip())
        return self._custom_colors

    def label_color(self, sec: Section) -> tuple:
        custom = self.custom_section_colors()
        if custom:
            for key in (sec.label.lower(), sec.kind, SECTION_KIND_GROUP.get(sec.kind, "frame")):
                if key in custom:
                    return custom[key]
        if self.label_colors == "by_type":
            return hex_rgb(SECTION_PALETTE[SECTION_KIND_GROUP.get(sec.kind, "frame")])
        if self.label_colors.startswith("#"):
            return hex_rgb(self.label_colors)
        return self.th.accent

    def section_header(self, sec: Section):
        th, L = self.th, self.st.margin
        label = sec.label + (f"  x{sec.times}" if sec.times > 1 else "")
        lw = self.text_width(label, th.label, th.label_size)
        base = self.y - 17
        if th.boxed_labels:
            pad_x, h = 7, th.label_size + 8
            self.c.setFillColorRGB(*self.label_color(sec))
            self.c.roundRect(L, base - 5, lw + 2 * pad_x, h, 4, stroke=0, fill=1)
            self.text(L + pad_x, base, label, th.label, th.label_size, label_text_color(self.label_color(sec)), bold=True)
            lw += 2 * pad_x
        else:
            self.text(L, base, label, th.label, th.label_size, self.label_color(sec), bold=True)
        note = " - ".join(p for p in (("reprise" if sec.is_ref else ""), sec.note) if p)
        if note:
            self.text(L + lw + 8, base, note, th.note, 9.5, th.grey)
        self.y -= self.st.section_height

    def draw_row(self, row, bpl, first_row, is_last_row):
        has_volta = self.row_has_volta(row)
        mark_room = self.mark_room(row)
        row_top = self.y
        top = (self.y - 20 - self.notation_room(row)[0] - (self.VOLTA_ROOM if has_volta else 0) - mark_room
               - self.note_room(row))
        self.cur_row_lyrics = self.row_has_lyrics(row)
        self.cur_row = row
        L = self.st.margin
        b0 = row[0]
        prev = key_signature(b0.prev_key) if b0.key_change else None
        natural_prefix = self.prefix_width(row, first_row)
        x = L + (self.max_prefix if self.bar_width == "uniform" else natural_prefix)
        widths = self.bar_widths(row, bpl, x)
        staff_end = x + sum(widths)
        if any(b.volta and b.volta.startswith("1.") for b in row):
            self.volta1_end = staff_end                # where the 1st ending's line ends
        left = L
        if id(b0) in self.right_rows:
            # 2nd ending: right-aligned under the 1st, drawn as bare bars (no clef/key);
            # the space on the left stays blank
            full_end = (x + self.uniform_bw * bpl) if self.bar_width == "uniform" else self.page_w - self.st.margin
            if getattr(self, "volta1_end", None):
                full_end = self.volta1_end
            full_end = min(full_end, self.page_w - self.st.margin)
            x += max(0.0, full_end - staff_end)
            staff_end = x + sum(widths)                # a later ending longer than the 1st runs past it
            left = x                                   # just the bars: no clef, no key signature
            self.row_lines(left, x, widths, row, top)
            if not b0.repeat_start:
                self.barline(left, top, "single")
        elif self.notation_mode == "tab" and b0.notation:    # tablature: TAB instead of clef and key
            cx = left + self.tab_clef(left, top)
            cx += 6
            if first_row or b0.time_change:                  # centred on the six lines
                self.time_signature(cx, top - (self.TAB_H - self.STAFF_H) / 2, b0.num, b0.den)
            self.row_lines(left, x, widths, row, top)
        else:
            cx = left + self.clef(left, top)
            if b0.key_change:
                self.key_label(cx + 2, top, row, b0.key)
            cx += self.draw_key_signature(cx + 2, top, key_signature(b0.key), prev) + 4
            if first_row or b0.time_change:
                self.time_signature(cx, top, b0.num, b0.den)
            self.row_lines(left, x, widths, row, top)
        bx1 = x
        spans = []
        self.row_chords, self.row_lyrics, self.row_events = [], [], []
        self.row_tabs = []
        self.row_hi, self.row_lo = top, top - self.STAFF_H
        for i, b in enumerate(row):
            bx0, bx1 = bx1, bx1 + widths[i]
            spans.append((bx0, bx1))
            self.draw_bar(b, bx0, bx1, top, i == 0)
            if b.repeat_end:
                self.repeat_sign(bx1, top, "end")
                if b.repeat_end > 2:
                    txt = f"x{b.repeat_end}"
                    self.text(bx1 - 2 - self.text_width(txt, self.th.chord, 13), top + 18, txt, self.th.chord, 13,
                              bold=True)
            else:
                last = is_last_row and i == len(row) - 1
                self.barline(bx1, top, "final" if last else "double" if b.double_after else "single")
            if self.notation_mode == "tab" and (b.notation or (i + 1 < len(row) and row[i + 1].notation)):
                self.tab_barline(bx1 - (1.6 if b.repeat_end else 0), top - self.STAFF_H, top - self.TAB_H)
        self.flush_ties(bx1 - 2)          # a tie that crosses the end of the line
        self.draw_ties(x - 8, bx1 - 4)    # ties between chord symbols ([C~]); a carried one starts by the key
        if self.row_chords:                # notated bars: one baseline for every chord symbol of the row
            chord_y = max(top + 10, self.row_hi + 5)
            for cx, chord, size in self.row_chords:
                self.draw_chord(cx, chord_y, chord, size)
        lyric_y = min(top - self.STAFF_H - 14, self.row_lo - 11)
        if self.row_lyrics:
            for lx, lyr in self.row_lyrics:
                self.text(lx, lyric_y, lyr, self.th.text, self.th.lyric_size, self.th.lyric_ink)
        if self.row_tabs:                  # "both": the tablature under the staff and its lyrics
            tab_top = (lyric_y - self.TAB_GAP) if self.row_lyrics else (self.row_lo - self.TAB_GAP)
            self.draw_row_tab(row, spans, left, tab_top)
        if has_volta:
            self.draw_voltas(row, spans, row_top - 4 - mark_room)
        if mark_room:
            self.draw_marks(row, spans, top + 8 if self.marks_low(row) else row_top - mark_room + 5)

    def draw_bar(self, b: Bar, bx0, bx1, top, first_in_row):
        th = self.th
        ax = bx0 + 7
        if b.repeat_start:
            self.repeat_sign(bx0, top, "start")
            ax += 8
        if not first_in_row and b.key_change:
            self.key_label(ax, top, self.cur_row, b.key)
            ax += self.draw_key_signature(ax, top, key_signature(b.key), key_signature(b.prev_key))
        if not first_in_row and b.time_change:
            ax += self.time_signature(ax - 2, top, b.num, b.den) + 2
        right = bx1 - (12 if b.repeat_end else 3)
        if b.notation:
            self.draw_notation(b, ax, right, top)
            return
        cell = (right - ax) / b.beats
        mid = top - 2 * self.SP
        self.cur_mid = mid
        chords = [e for e in b.events if e.chord]

        if not chords:                                   # chord continues: %
            self.percent((ax + right) / 2, mid)

        # one chord size for the whole bar: the largest at which every chord fits
        size = th.chord_size
        for e in chords:
            nxt = [o for o in chords if o.start > e.start]
            limit = (ax + nxt[0].start * cell if nxt else right + 2) - (ax + e.start * cell) - 7
            w = self.event_width(e, th.chord_size)
            if w > limit:
                size = min(size, th.chord_size * limit / w)
        size = max(th.chord_min_size, size)

        for e in b.events:
            ex = ax + e.start * cell - 1
            if e.chord:
                w = self.event_width(e, size)
                self.knockout(ex - 1.5, mid - size * 0.5, w + 3, size * 1.05)
                xr = self.draw_event(ex, mid - size * 0.34, e, size)
                self.row_events.append((e, ex, xr, mid + size * 0.55))
                if e.strokes:                            # rhythm slashes on the following beats
                    step = (e.dur or b.beats) / (e.strokes + 1)
                    for k in range(1, e.strokes + 1):
                        self.slash(ax + (e.start + k * step) * cell, mid)
                above = top + (17 if self.cur_row_lyrics else 6)   # annotation: over the lyrics, if any
                if e.note:
                    nxt = [o for o in chords if o.start > e.start and o.note]
                    room = (ax + nxt[0].start * cell - 4 if nxt else bx1 - 2) - ex
                    self.text(ex, above, self.fit(e.note, th.note, self.NOTE_SIZE, max(room, 12)), th.note,
                              self.NOTE_SIZE, self.NOTE_INK)
                if e.fermata:
                    self.mark_glyph(ex + w / 2, above - 2 + (11 if e.note else 0), "fermata", center=True)
            elif e.note:                                 # [% "note"]: a note on a repeated bar
                self.text(ex + 2, top + (17 if self.cur_row_lyrics else 6),
                          self.fit(e.note, th.note, self.NOTE_SIZE, bx1 - ex - 6), th.note, self.NOTE_SIZE,
                          self.NOTE_INK)
            if e.lyric:
                nxt = [o for o in b.events if o.start > e.start and (o.lyric or o.chord)]
                room = (ax + nxt[0].start * cell - 1 if nxt else bx1) - ex - 4
                self.text(ex, top + 6, self.fit(e.lyric, th.text, th.lyric_size, room),
                          th.text, th.lyric_size, th.lyric_ink)

