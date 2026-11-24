"""Editor support for .chs sources: syntax highlighting tokens and directive completion.

Standard library only, no Flet: the app turns the tokens into coloured text spans and shows the
completions in a popup when a `{` is typed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .formats import CURRENT
from .i18n import tr

OPEN, CLOSE = "‹", "›"            # placeholder in a completion snippet: selected after inserting ("‹›" = caret)

# token kinds: text, comment, brace, directive, section, value, chord, duration, bar, note, rest
_NOTES_RE = re.compile(                # a row of bars inside {start_of_notes} … {end_of_notes}
    r"(?P<directive>\{[^}\n]*\}?)"
    r"|(?P<chord>\[[^\]\n]*\]?)"
    r"|(?P<bar>\|:|:\|(?:\s*x\d+)?|\|\||\||\d+(?::\d+)?\(|\)|-|~[1-9])"
    r"|(?P<brace>[<>])"
    r"|(?P<rest>[Rr]\*?)"
    r"|(?P<note>[A-Ga-g](?:##|bb|#|b|n)?(?:[',]+|@-?\d*)?)"
    r"|(?P<duration>/?(?:32|16|[1248])\.{0,2}|/|\.+)"
    r"|(?P<text>\s+|.)"
)
_PIECE_RE = re.compile(
    r"(?P<directive>\{[^}\n]*\}?)"
    r"|(?P<chord>\[[^\]\n]*\]?)"
    r"|(?P<bar>\|:|:\|(?:\s*x\d+)?|\|\||\|)"
    r"|(?P<text>[^{\[|:\n]+|:)"
)
_NAME_RE = re.compile(r"[A-Za-z_]*")


def tokens(text: str) -> list[tuple[str, str]]:
    """Split a .chs source into (kind, text) runs that together give back `text` exactly.
    Unclosed `{…` and `[…` are coloured up to the end of the line, so they show while typing."""
    out: list[tuple[str, str]] = []

    def add(kind: str, s: str):
        if not s:
            return
        if out and out[-1][0] == kind:
            out[-1] = (kind, out[-1][1] + s)
        else:
            out.append((kind, s))

    in_notes = False
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        eol = line[len(body):]
        stripped = body.strip().lower().replace(" ", "")
        if body.lstrip().startswith("#"):
            add("comment", body)
        elif in_notes and body.lstrip().startswith("w:"):
            lead = len(body) - len(body.lstrip())
            add("text", body[:lead])
            add("directive", "w:")
            add("text", body[lead + 2:])
        elif in_notes and not stripped.startswith("{"):
            for m in _NOTES_RE.finditer(body):
                kind, s = m.lastgroup, m.group()
                if kind == "directive":
                    _directive(s, add)
                elif kind == "chord":
                    _chord(s, add)
                else:
                    add(kind, s)
        else:
            for m in _PIECE_RE.finditer(body):
                kind, s = m.lastgroup, m.group()
                if kind == "directive":
                    _directive(s, add)
                elif kind == "chord":
                    _chord(s, add)
                else:
                    add(kind, s)
        add("text", eol)
        if stripped.startswith("{start_of_notes"):
            in_notes = True
        elif stripped.startswith("{end_of_"):
            in_notes = False
    return out


def _directive(s: str, add):
    closed = s.endswith("}") and len(s) > 1
    inner = s[1:-1] if closed else s[1:]
    name, colon, value = inner.partition(":")
    key = name.strip().lower()
    add("brace", "{")
    add("section" if key.startswith(("start_of_", "end_of_")) else "directive", name + colon)
    add("value", value)
    if closed:
        add("brace", "}")


def _chord(s: str, add):
    closed = s.endswith("]") and len(s) > 1
    inner = s[1:-1] if closed else s[1:]
    name, colon, dur = inner.partition(":")
    add("chord", "[" + name)
    add("duration", colon + dur)
    if closed:
        add("chord", "]")


# ---------------------------------------------------------------- completion
@dataclass(frozen=True)
class Completion:
    name: str            # directive name, used for filtering
    snippet: str         # text that replaces what follows "{" (‹…› marks the selected placeholder)
    hint: str            # short description shown in the popup (current UI language)


SECTIONS = ["intro", "verse", "chorus", "bridge", "solo", "instrumental", "outro", "coda"]

# (name, snippet) — the hint is i18n "hint.<name>"
_PLAIN = [
    ("format", f"format: ‹v{CURRENT}›}}"),
    ("title", "title: ‹›}"),
    ("subtitle", "subtitle: ‹›}"),
    ("artist", "artist: ‹›}"),
    ("composer", "composer: ‹›}"),
    ("key", "key: ‹›}"),
    ("time", "time: ‹4/4›}"),
    ("tempo", "tempo: ‹›}"),
    ("capo", "capo: ‹›}"),
    ("tags", "tags: ‹›}"),
    None,                                          # the start_of_… sections go here
    ("br", "br}‹›"),
    ("volta", "volta: ‹1›}"),
    ("volta_end", "volta_end}‹›"),
    ("ref", "ref: ‹›}"),
    ("text", "text: ‹›}"),
    ("segno", "segno}‹›"),
    ("to_coda", "to_coda}‹›"),
    ("ds", "ds: ‹al Coda›}"),
    ("dc", "dc: ‹al Fine›}"),
    ("fine", "fine}‹›"),
    ("coda", "coda}‹›"),
    ("musicxml", "musicxml: ‹›}"),
    ("start_of_notes", "start_of_notes}\n| ‹C4 D E F› |\n{end_of_notes}"),
    ("bars_per_line", "bars_per_line: ‹4›}"),
    ("bar_width", "bar_width: ‹fit›}"),
    ("row_spacing", "row_spacing: ‹wide›}"),
    ("notation", "notation: ‹both›}"),
    ("tuning", "tuning: ‹drop D›}"),
    ("tab_position", "tab_position: ‹5›}"),
    ("label_colors", "label_colors: ‹by_type›}"),
    ("section_colors", "section_colors: ‹verse=#33cc66›}"),
    ("comment", "comment: ‹›}"),
]


def directives() -> list[Completion]:
    """All directive completions, with hints and default section labels in the current UI language."""
    out: list[Completion] = []
    for item in _PLAIN:
        if item is None:
            for k in SECTIONS:
                label = tr(f"section.{k}")
                out.append(Completion(f"start_of_{k}", f"start_of_{k}: ‹{label}›}}\n\n{{end_of_{k}}}",
                                      tr("hint.section", label=label)))
        else:
            out.append(Completion(item[0], item[1], tr(f"hint.{item[0]}")))
    return out


def context(text: str, caret: int) -> tuple[int, str] | None:
    """If the caret is right after `{` plus an optional partial directive name (on the same line),
    return (offset where the name starts, the partial name); otherwise None."""
    if caret < 1 or caret > len(text):
        return None
    line_start = text.rfind("\n", 0, caret) + 1
    brace = text.rfind("{", line_start, caret)
    if brace < 0:
        return None
    prefix = text[brace + 1:caret]
    if not _NAME_RE.fullmatch(prefix):
        return None
    return brace + 1, prefix


def open_section(text: str, upto: int) -> str | None:
    """Kind of the section still open at offset `upto` (start_of_X without its end_of_X)."""
    kind = None
    for m in re.finditer(r"\{\s*(start|end)_of_([A-Za-z_]+)", text[:upto]):
        if m.group(2).lower() == "notes":
            continue                       # a notes block sits inside a section, it is not one
        kind = m.group(2).lower() if m.group(1) == "start" else None
    return kind


def open_notes(text: str, upto: int) -> bool:
    """True if a {start_of_notes} block is still open at offset `upto`."""
    state = False
    for m in re.finditer(r"\{\s*(start_of_notes|end_of_[A-Za-z_]+)", text[:upto]):
        state = m.group(1).lower() == "start_of_notes"
    return state


def suggestions(text: str, caret: int) -> list[Completion]:
    """Directives matching the partial name before the caret: names starting with it first, then
    names containing it. Inside an open section its end_of_… comes first and start_of_… is dropped."""
    ctx = context(text, caret)
    if ctx is None:
        return []
    start, prefix = ctx
    section = open_section(text, start - 1)
    items = directives()
    if section:
        items = [Completion(f"end_of_{section}", f"end_of_{section}}}‹›", tr("hint.end_section"))] + \
                [c for c in items if not c.name.startswith("start_of_") or c.name == "start_of_notes"]
    if open_notes(text, start - 1):
        items = [Completion("end_of_notes", "end_of_notes}‹›", tr("hint.end_of_notes"))] + \
                [c for c in items if c.name != "start_of_notes"]
    p = prefix.lower()
    first = [c for c in items if c.name.startswith(p)]
    return first + [c for c in items if p in c.name and c not in first]


def apply(text: str, caret: int, completion: Completion) -> tuple[str, int, int]:
    """Insert `completion` at the `{` before the caret; returns (new text, selection start, selection end):
    the snippet's placeholder is selected, so typing replaces it.
    If the directive is already written after the caret (`{ti|tle: …}`), only the name is completed."""
    ctx = context(text, caret)
    if ctx is None:
        return text, caret, caret
    start, _ = ctx
    end = caret + len(_NAME_RE.match(text, caret).group())
    if end < len(text) and text[end] in ":}":
        new = completion.name
        return text[:start] + new + text[end:], start + len(new), start + len(new)
    snippet = completion.snippet
    a = snippet.index(OPEN)
    b = snippet.index(CLOSE) - 1
    snippet = snippet.replace(OPEN, "").replace(CLOSE, "")
    return text[:start] + snippet + text[end:], start + a, start + b


# ---------------------------------------------------------------- caret position (for the popup)
_WORD_RE = re.compile(r"\S+\s*|\s+")


def caret_row_col(text: str, caret: int, columns: int) -> tuple[int, int]:
    """Visual (row, column) of `caret` in `text` shown in a monospaced box `columns` characters wide,
    wrapping like Flutter: between words (after spaces), words longer than a row are split."""
    columns = max(1, columns)
    row = 0
    pos = 0
    for line in text.split("\n"):
        end = pos + len(line)
        r, c = 0, 0                       # current row and column inside this source line
        at = pos
        for m in _WORD_RE.finditer(line):
            word = m.group()
            ink = len(word.rstrip())      # trailing spaces may hang past the edge
            if c and c + ink > columns:
                r, c = r + 1, 0
            for ch_i in range(len(word)):
                if at + ch_i == caret:
                    return row + r, c
                if c >= columns and ch_i < ink:
                    r, c = r + 1, 0
                c += 1
            at += len(word)
        if caret <= end:
            return row + r, c
        row += r + 1
        pos = end + 1
    return row, 0
