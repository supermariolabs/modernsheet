"""Editor support for MusicXML sources: syntax highlighting tokens and element completion.

Same interface as syntax.py (tokens, context, suggestions, apply), so the app's editor uses either
module depending on the open file. Standard library only.

Token kinds: text, comment, decl (<?xml …?>, <!DOCTYPE …>), brace (< </ > />), tag, attr, value,
entity (&amp; …).
"""
from __future__ import annotations

import re

from .i18n import tr
from .syntax import CLOSE, OPEN, Completion

_NAME = r"[A-Za-z_][\w.\-]*"
_PIECE_RE = re.compile(
    r"(?P<comment><!--.*?(?:-->|\Z))"
    r"|(?P<decl><[?!][^>]*(?:>|\Z))"
    r"|(?P<tag></?" + _NAME + r"[^<>]*(?:>|(?=<)|\Z)|</?(?=\s|$|>))"
    r"|(?P<entity>&#?\w+;)"
    r"|(?P<text>[^<&]+|[<&])",
    re.DOTALL,
)
_TAG_PARTS_RE = re.compile(
    r"(?P<open></?)(?P<name>" + _NAME + r")?"
    r"|(?P<attr>" + _NAME + r")(?P<eq>\s*=\s*)?(?P<value>\"[^\"]*\"?|'[^']*'?)?"
    r"|(?P<close>/?>)"
    r"|(?P<space>\s+|.)",
    re.DOTALL,
)


def tokens(text: str) -> list[tuple[str, str]]:
    """Split a MusicXML source into (kind, text) runs that together give back `text` exactly.
    An unclosed tag or comment is coloured up to where the next one starts (or the end)."""
    out: list[tuple[str, str]] = []

    def add(kind: str, s: str):
        if not s:
            return
        if out and out[-1][0] == kind:
            out[-1] = (kind, out[-1][1] + s)
        else:
            out.append((kind, s))

    for m in _PIECE_RE.finditer(text):
        kind, s = m.lastgroup, m.group()
        if kind != "tag":
            add(kind, s)
            continue
        for p in _TAG_PARTS_RE.finditer(s):
            if p.group("open") is not None:
                add("brace", p.group("open"))
                add("tag", p.group("name") or "")
            elif p.group("attr") is not None:
                add("attr", p.group("attr"))
                add("brace", p.group("eq") or "")
                add("value", p.group("value") or "")
            elif p.group("close") is not None:
                add("brace", p.group("close"))
            else:
                add("text", p.group("space"))
    return out


# ---------------------------------------------------------------- completion
# Elements read by the app's MusicXML reader (and the usual skeleton), with the snippet that replaces
# what follows "<" (‹…› marks the selected placeholder); hints are i18n "xml.<name>".
ELEMENTS: dict[str, str] = {
    "measure": 'measure number="‹1›">\n  \n</measure>',
    "note": "note>\n  <pitch><step>‹C›</step><octave>4</octave></pitch>\n  <duration>1</duration>\n"
            "  <type>quarter</type>\n</note>",
    "pitch": "pitch><step>‹C›</step><octave>4</octave></pitch>",
    "step": "step>‹C›</step>",
    "alter": "alter>‹-1›</alter>",
    "octave": "octave>‹4›</octave>",
    "rest": "rest/>‹›",
    "chord": "chord/>‹›",
    "duration": "duration>‹1›</duration>",
    "type": "type>‹quarter›</type>",
    "dot": "dot/>‹›",
    "voice": "voice>‹1›</voice>",
    "tie": 'tie type="‹start›"/>',
    "beam": 'beam number="1">‹begin›</beam>',
    "time-modification": "time-modification><actual-notes>‹3›</actual-notes><normal-notes>2</normal-notes>"
                         "</time-modification>",
    "notations": "notations>‹›</notations>",
    "tuplet": 'tuplet type="‹start›"/>',
    "tied": 'tied type="‹start›"/>',
    "lyric": "lyric><syllabic>single</syllabic><text>‹›</text></lyric>",
    "syllabic": "syllabic>‹single›</syllabic>",
    "text": "text>‹›</text>",
    "attributes": "attributes>\n  <divisions>‹1›</divisions>\n</attributes>",
    "divisions": "divisions>‹1›</divisions>",
    "key": "key><fifths>‹0›</fifths></key>",
    "fifths": "fifths>‹0›</fifths>",
    "time": "time><beats>‹4›</beats><beat-type>4</beat-type></time>",
    "beats": "beats>‹4›</beats>",
    "beat-type": "beat-type>‹4›</beat-type>",
    "clef": "clef><sign>‹G›</sign><line>2</line></clef>",
    "harmony": "harmony>\n  <root><root-step>‹C›</root-step></root>\n  <kind>major</kind>\n</harmony>",
    "root": "root><root-step>‹C›</root-step></root>",
    "root-step": "root-step>‹C›</root-step>",
    "root-alter": "root-alter>‹-1›</root-alter>",
    "kind": "kind>‹major›</kind>",
    "bass": "bass><bass-step>‹C›</bass-step></bass>",
    "degree": "degree><degree-value>‹9›</degree-value><degree-alter>0</degree-alter>"
              "<degree-type>add</degree-type></degree>",
    "barline": 'barline location="‹right›">\n  \n</barline>',
    "bar-style": "bar-style>‹light-heavy›</bar-style>",
    "repeat": 'repeat direction="‹backward›"/>',
    "ending": 'ending number="‹1›" type="start"/>',
    "backup": "backup><duration>‹1›</duration></backup>",
    "forward": "forward><duration>‹1›</duration></forward>",
    "part": 'part id="‹P1›">\n  \n</part>',
}

# typical children: offered first inside that element
CHILDREN: dict[str, list[str]] = {
    "score-partwise": ["part"],
    "part": ["measure"],
    "measure": ["note", "attributes", "harmony", "barline", "backup", "forward"],
    "note": ["pitch", "rest", "chord", "duration", "type", "dot", "voice", "tie", "beam", "time-modification",
             "notations", "lyric"],
    "pitch": ["step", "alter", "octave"],
    "attributes": ["divisions", "key", "time", "clef"],
    "key": ["fifths"],
    "time": ["beats", "beat-type"],
    "harmony": ["root", "kind", "bass", "degree"],
    "root": ["root-step", "root-alter"],
    "barline": ["bar-style", "repeat", "ending"],
    "notations": ["tuplet", "tied"],
    "lyric": ["syllabic", "text"],
}

_CTX_RE = re.compile(r"<(/?)([\w.\-]*)$")
_OPEN_TAGS_RE = re.compile(r"<!--.*?-->|<[?!][^>]*>|<(/?)(" + _NAME + r")[^<>]*?(/?)>", re.DOTALL)


def context(text: str, caret: int) -> tuple[int, str] | None:
    """If the caret is right after `<` or `</` plus an optional partial element name (same line),
    return (offset where the name starts, the partial name); otherwise None."""
    if caret < 1 or caret > len(text):
        return None
    line = text[text.rfind("\n", 0, caret) + 1:caret]
    m = _CTX_RE.search(line)
    if not m:
        return None
    return caret - len(m.group(2)), m.group(2)


def open_elements(text: str, upto: int) -> list[str]:
    """Stack of elements still open at offset `upto` (outermost first)."""
    stack: list[str] = []
    for m in _OPEN_TAGS_RE.finditer(text[:upto]):
        if m.group(2) is None:
            continue                                   # comment or declaration
        closing, name, selfclosing = m.group(1), m.group(2), m.group(3)
        if closing:
            if name in stack:
                del stack[len(stack) - 1 - stack[::-1].index(name):]
        elif not selfclosing:
            stack.append(name)
    return stack


def suggestions(text: str, caret: int) -> list[Completion]:
    """After `</`: the innermost open element. After `<`: the typical children of the enclosing
    element first, then the other known elements; names starting with the typed letters first,
    then names containing them."""
    ctx = context(text, caret)
    if ctx is None:
        return []
    start, prefix = ctx
    p = prefix.lower()
    stack = open_elements(text, start - 1 - (1 if text[start - 2:start] == "</" else 0))
    if text[start - 2:start] == "</":
        names = list(reversed(stack))[:1]
        items = [Completion(n, f"{n}>‹›", tr("xml.close", name=n)) for n in names]
        return [c for c in items if c.name.lower().startswith(p)]
    parent = stack[-1] if stack else ""
    order = CHILDREN.get(parent, []) + [n for n in ELEMENTS if n not in CHILDREN.get(parent, [])]
    items = [Completion(n, ELEMENTS[n], tr(f"xml.{n}")) for n in order if n in ELEMENTS]
    first = [c for c in items if c.name.startswith(p)]
    return first + [c for c in items if p in c.name and c not in first]


def apply(text: str, caret: int, completion: Completion) -> tuple[str, int, int]:
    """Insert `completion` after the `<` before the caret; returns (new text, selection start, end).
    Multi-line snippets are indented like the current line. If the tag already continues after the
    caret (`<no|te>`), only the name is completed."""
    ctx = context(text, caret)
    if ctx is None:
        return text, caret, caret
    start, _ = ctx
    end = caret + len(re.match(r"[\w.\-]*", text[caret:]).group())
    if end < len(text) and text[end] in " />\t":
        new = completion.name
        return text[:start] + new + text[end:], start + len(new), start + len(new)
    line_start = text.rfind("\n", 0, start) + 1
    indent = re.match(r"[ \t]*", text[line_start:]).group()
    snippet = completion.snippet.replace("\n", "\n" + indent)
    a = snippet.index(OPEN)
    b = snippet.index(CLOSE) - 1
    snippet = snippet.replace(OPEN, "").replace(CLOSE, "")
    return text[:start] + snippet + text[end:], start + a, start + b


# ---------------------------------------------------------------- indentation
INDENT = "  "
_STRUCT_RE = re.compile(
    r"(?P<comment><!--.*?-->)"
    r"|(?P<cdata><!\[CDATA\[.*?\]\]>)"
    r"|(?P<decl><[?!][^>]*>)"
    r"|(?P<end></(?P<ename>" + _NAME + r")\s*>)"
    r"|(?P<start><(?P<sname>" + _NAME + r")(?:\"[^\"]*\"|'[^']*'|[^<>\"'])*?(?P<empty>/?)>)"
    r"|(?P<text>[^<]+)",
    re.DOTALL,
)


def xml_error(text: str) -> tuple[int, str] | None:
    """(line, message) if `text` is not well-formed XML, else None."""
    import xml.etree.ElementTree as ET
    try:
        ET.fromstring(text.encode("utf-8"))
    except ET.ParseError as err:
        return err.position[0], str(err)
    return None


def format_xml(text: str) -> str:
    """Re-indent a well-formed XML source: one element per line, INDENT per level; an element holding
    only text stays on one line (<step>C</step>). Tags, attributes, text and comments are kept as they
    are; only the whitespace between elements changes. Check `xml_error` first: on a malformed source
    the result is a best effort."""
    kinds = []
    for m in _STRUCT_RE.finditer(text):
        kind = next(k for k in ("comment", "cdata", "decl", "end", "start", "text") if m.group(k) is not None)
        if kind == "text" and not m.group().strip():
            continue                                    # whitespace between elements: rebuilt below
        kinds.append((kind, m))
    lines: list[str] = []
    depth, i = 0, 0
    while i < len(kinds):
        kind, m = kinds[i]
        s = m.group()
        if kind == "start" and not m.group("empty"):
            name = m.group("sname")
            nxt = kinds[i + 1] if i + 1 < len(kinds) else None
            nxt2 = kinds[i + 2] if i + 2 < len(kinds) else None
            if nxt and nxt[0] == "end" and nxt[1].group("ename") == name:
                lines.append(INDENT * depth + s + nxt[1].group())
                i += 2
                continue
            if nxt and nxt[0] in ("text", "cdata") and nxt2 and nxt2[0] == "end" and nxt2[1].group("ename") == name:
                lines.append(INDENT * depth + s + nxt[1].group() + nxt2[1].group())
                i += 3
                continue
            lines.append(INDENT * depth + s)
            depth += 1
        elif kind == "end":
            depth = max(0, depth - 1)
            lines.append(INDENT * depth + s)
        elif kind == "text":
            lines.append(INDENT * depth + s.strip())    # mixed content (not used by MusicXML)
        else:
            lines.append(INDENT * depth + s)
        i += 1
    return "\n".join(lines) + "\n"


def reindent_xml(text: str) -> str:
    """Indent each line by the nesting of the elements around it (INDENT per level), keeping the lines
    as they are: only the leading whitespace changes. Lines inside a multi-line comment, tag or text
    are left alone."""
    depth = 0
    events: list[tuple[int, int, int, bool]] = []      # (start, end, depth before, is end tag)
    for m in _STRUCT_RE.finditer(text):
        is_end = m.group("end") is not None
        if m.group("text") is not None and not m.group().strip():
            continue
        events.append((m.start(), m.end(), depth, is_end))
        if m.group("start") is not None and not m.group("empty"):
            depth += 1
        elif is_end:
            depth = max(0, depth - 1)
    out, pos, k = [], 0, 0
    for line in text.split("\n"):
        end = pos + len(line)
        body = line.lstrip(" \t")
        first = pos + len(line) - len(body)
        while k < len(events) and events[k][1] <= first:
            k += 1
        inside = k < len(events) and events[k][0] < first < events[k][1]
        if body and not inside:
            at = events[k] if k < len(events) and events[k][0] == first else None
            if at is not None:
                level = at[2] - (1 if at[3] else 0)
            else:                                     # text at the start of a line
                level = events[k - 1][2] + (1 if k and not events[k - 1][3] else 0) if k else 0
            out.append(INDENT * max(0, level) + body)
        else:
            out.append(line)
        pos = end + 1
    return "\n".join(out)


# ---------------------------------------------------------------- folding
FOLD = "⋯"


def elements(text: str) -> list[tuple[str, int, int, int]]:
    """Balanced elements of `text` as (name, start, end of the start tag, end), in document order of
    their start. Unbalanced tags are skipped."""
    found: list[tuple[str, int, int, int]] = []
    stack: list[tuple[str, int, int]] = []
    for m in _STRUCT_RE.finditer(text):
        if m.group("start") is not None and not m.group("empty"):
            stack.append((m.group("sname"), m.start(), m.end()))
        elif m.group("end") is not None:
            name = m.group("ename")
            if any(n == name for n, _, _ in stack):
                while stack:
                    n, a, b = stack.pop()
                    if n == name:
                        found.append((n, a, b, m.end()))
                        break
    return sorted(found, key=lambda e: e[1])


class _Fold:
    __slots__ = ("start", "marker", "block", "inner")

    def __init__(self, start: int, marker: str, block: str, inner: list["_Fold"]):
        self.start, self.marker, self.block, self.inner = start, marker, block, inner

    @property
    def end(self) -> int:
        return self.start + len(self.marker)


def _expand(text: str, folds: list[_Fold]) -> str:
    out, pos = [], 0
    for f in folds:
        out += [text[pos:f.start], _expand(f.block, f.inner)]
        pos = f.end
    return "".join(out) + text[pos:]


class Folds:
    """Collapsed elements of an XML source in the editor. `view` is the text the editor shows: every
    collapsed multi-line element is replaced by one line, its start tag + " ⋯ " + its end tag. `full()`
    gives back the whole source. Folds nest (collapsing an element that holds collapsed ones)."""

    def __init__(self, text: str):
        self.view = text
        self.folds: list[_Fold] = []          # top level, by position in view

    def __bool__(self) -> bool:
        return bool(self.folds)

    def full(self) -> str:
        return _expand(self.view, self.folds)

    def ellipses(self) -> list[int]:
        """Offsets in `view` of the ⋯ of each collapsed element (to paint them)."""
        return [f.start + f.marker.index(FOLD) for f in self.folds]

    def _line(self, caret: int) -> tuple[int, int]:
        a = self.view.rfind("\n", 0, caret) + 1
        b = self.view.find("\n", caret)
        return a, len(self.view) if b < 0 else b

    def _fold(self, name: str, start: int, open_end: int, end: int) -> None:
        block = self.view[start:end]
        marker = re.sub(r"\s*\n\s*", " ", self.view[start:open_end]) + f" {FOLD} </{name}>"
        inner = [_Fold(f.start - start, f.marker, f.block, f.inner) for f in self.folds if start <= f.start < end]
        delta = len(marker) - len(block)
        rest = []
        for f in self.folds:
            if f.start < start:
                rest.append(f)
            elif f.start >= end:
                f.start += delta
                rest.append(f)
        rest.append(_Fold(start, marker, block, inner))
        self.folds = sorted(rest, key=lambda f: f.start)
        self.view = self.view[:start] + marker + self.view[end:]

    def foldable(self) -> list[tuple[str, int, int, int]]:
        return [e for e in elements(self.view) if "\n" in self.view[e[1]:e[3]]]

    def fold_at(self, caret: int) -> bool:
        """Collapse the innermost multi-line element on the caret's line; False if there is none."""
        a, b = self._line(caret)
        hits = [e for e in self.foldable() if e[1] <= b and e[3] >= a]
        if not hits:
            return False
        self._fold(*max(hits, key=lambda e: e[1]))
        return True

    def fold_all(self, name: str = "measure") -> int:
        """Collapse every multi-line `name` element; returns how many."""
        todo = [e for e in self.foldable() if e[0] == name]
        for e in reversed(todo):              # from the end: earlier offsets stay valid
            self._fold(*e)
        return len(todo)

    def fold_index(self, caret: int, line: bool = True) -> int | None:
        """The collapsed element at the caret (on its line if `line`, else inside the marker)."""
        a, b = self._line(caret) if line else (caret, caret)
        for i, f in enumerate(self.folds):
            if f.start <= b and f.end >= a and (line or f.start < caret < f.end):
                return i
        return None

    def unfold(self, index: int) -> None:
        f = self.folds.pop(index)
        delta = len(f.block) - len(f.marker)
        for g in self.folds:
            if g.start > f.start:
                g.start += delta
        self.folds += [_Fold(g.start + f.start, g.marker, g.block, g.inner) for g in f.inner]
        self.folds.sort(key=lambda g: g.start)
        self.view = self.view[:f.start] + f.block + self.view[f.end:]

    def unfold_at(self, caret: int) -> bool:
        i = self.fold_index(caret)
        if i is None:
            return False
        self.unfold(i)
        return True

    def unfold_all(self) -> None:
        self.view, self.folds = self.full(), []

    def edit(self, new: str) -> bool:
        """Apply an edit of the view (the editor's new text). False, and nothing changes, if the edit
        touches a collapsed element's line marker: it must be expanded first. An edit that brings in a ⋯
        is refused too: it means the editor shows collapsed lines this object does not know about (the
        editor and the document drifted apart), and accepting it would put a marker line in the source
        in place of the element. When the same edit could
        have happened in several places (typing "<" just before "<measure"), the one that leaves the
        markers alone is chosen."""
        old = self.view
        n = min(len(old), len(new))

        def common(a: str, b: str, limit: int, back: bool) -> int:
            k = 0
            while k < limit and (a[len(a) - 1 - k] == b[len(b) - 1 - k] if back else a[k] == b[k]):
                k += 1
            return k

        p = common(old, new, n, False)
        s = common(old, new, n - p, True)
        s2 = common(old, new, n, True)
        p2 = common(old, new, n - s2, False)
        span1, span2 = len(old) - p - s, len(old) - p2 - s2
        if span1 == 0 or len(new) - p - s == 0:            # pure insertion or deletion: it can slide
            choices = [(x, x + span1) for x in range(p, min(p, p2) - 1, -1)]
        else:
            choices = [(p, p + span1), (p2, p2 + span2)]

        def safe(a: int, b: int) -> bool:
            return all(not (f.start < b and a < f.end) if a < b else not (f.start < a < f.end)
                       for f in self.folds)

        hit = next((c for c in choices if safe(*c)), None)
        delta = len(new) - len(old)
        if hit is None or FOLD in new[hit[0]:hit[1] + delta]:
            return False
        for f in self.folds:
            if f.start >= hit[1]:
                f.start += delta
        self.view = new
        return True
