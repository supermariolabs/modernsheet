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
